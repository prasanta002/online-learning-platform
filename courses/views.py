from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse


import os
import razorpay
from django.conf import settings

from .models import Course, Enrollment, Lesson, LessonProgress, Category, Certificate , Payment
ALLOWED_VIDEO_EXTENSIONS = [
    ".mp4",
    ".webm",
    ".mov",
]

MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB

def course_list(request):

    search_query = request.GET.get("search", "")
    selected_category = request.GET.get("category", "")
    selected_sort = request.GET.get("sort", "newest")

    courses = Course.objects.filter(
        is_published=True
    )

    categories = Category.objects.all()

    # Search by course title
    if search_query:

        courses = courses.filter(
            title__icontains=search_query
        )

    # Filter by category
    if selected_category:

        courses = courses.filter(
            category_id=selected_category
        )

    # Sort courses
    if selected_sort == "oldest":

        courses = courses.order_by("created_at")

    elif selected_sort == "price_low":

        courses = courses.order_by("price")

    elif selected_sort == "price_high":

        courses = courses.order_by("-price")

    else:

        courses = courses.order_by("-created_at")

    return render(
        request,
        "courses/course_list.html",
        {
            "courses": courses,
            "categories": categories,
            "search_query": search_query,
            "selected_category": selected_category,
            "selected_sort": selected_sort,
        }
    )

     

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        is_published=True
    )

    lessons = course.lessons.all().order_by("order")

    completed_lessons = LessonProgress.objects.filter(
        student=request.user,
        lesson__course=course,
        completed=True
    ).count()

    total_lessons = lessons.count()

    if total_lessons > 0:
        progress_percentage = int(
            (completed_lessons / total_lessons) * 100
        )
    else:
        progress_percentage = 0

    # Check whether the student completed the course
    course_completed = (
        total_lessons > 0
        and completed_lessons == total_lessons
    )

    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).exists()

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "lessons": lessons,
            "completed_lessons": completed_lessons,
            "total_lessons": total_lessons,
            "progress_percentage": progress_percentage,
            "course_completed": course_completed,
            "is_enrolled": is_enrolled,
        }
    )
   
        


@login_required
def enroll_course(request, course_id):

    # Enrollment must use POST
    if request.method != "POST":
        messages.error(
            request,
            "Invalid request."
        )

        return redirect(
            "course_detail",
            course_id=course_id
        )

    course = get_object_or_404(
        Course,
        id=course_id,
        is_published=True
    )

    # Paid course
    if course.price > 0:

        messages.info(
            request,
            "This is a paid course. Please complete the payment first."
        )

        return redirect(
            "course_detail",
            course_id=course.id
        )

    # Free course
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    if created:

        messages.success(
            request,
            f"You successfully enrolled in {course.title}!"
        )

    else:

        messages.info(
            request,
            "You are already enrolled in this course."
        )

    return redirect(
        "course_detail",
        course_id=course.id
    )

  



@login_required
def my_courses(request):

    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related("course")

    enrolled_courses = []

    for enrollment in enrollments:

        course = enrollment.course

        total_lessons = course.lessons.count()

        completed_lessons = LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course,
            completed=True
        ).count()

        if total_lessons > 0:
            progress_percentage = int(
                (completed_lessons / total_lessons) * 100
            )
        else:
            progress_percentage = 0

        # Find the first incomplete lesson
        next_lesson = course.lessons.exclude(
            lessonprogress__student=request.user,
            lessonprogress__completed=True
        ).order_by("order").first()

        # If all lessons are completed
        if next_lesson is None:
            next_lesson = course.lessons.order_by("order").first()

        enrolled_courses.append({
            "course": course,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_percentage": progress_percentage,
            "next_lesson": next_lesson,
        })

    return render(
        request,
        "courses/my_courses.html",
        {
            "enrolled_courses": enrolled_courses,
        }
    )


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__is_published=True
    )

    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=lesson.course
    ).exists()

    if not is_enrolled:
        messages.warning(
            request,
            "Please enroll in this course before watching the lessons."
        )

        return redirect(
            "course_detail",
            course_id=lesson.course.id
        )

    progress = LessonProgress.objects.filter(
        student=request.user,
        lesson=lesson
    ).first()

    # Get all lessons of this course
    lessons = Lesson.objects.filter(
        course=lesson.course
    ).order_by("order")

    # Find previous and next lessons
    previous_lesson = None
    next_lesson = None

    for index, current_lesson in enumerate(lessons):

        if current_lesson.id == lesson.id:

            if index > 0:
                previous_lesson = lessons[index - 1]

            if index < len(lessons) - 1:
                next_lesson = lessons[index + 1]

            break

    return render(
        request,
        "courses/lesson_detail.html",
        {
            "lesson": lesson,
            "progress": progress,
            "previous_lesson": previous_lesson,
            "next_lesson": next_lesson,
        }
    )
      

@login_required
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id
    )

    # Check enrollment
    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=lesson.course
    ).exists()

    if not is_enrolled:
        messages.warning(
            request,
            "Please enroll in this course first."
        )

        return redirect(
            "course_detail",
            course_id=lesson.course.id
        )

    # Mark lesson as completed
    progress, created = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )

    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()

    # Check course progress
    total_lessons = Lesson.objects.filter(
        course=lesson.course
    ).count()

    completed_lessons = LessonProgress.objects.filter(
        student=request.user,
        lesson__course=lesson.course,
        completed=True
    ).count()

    # Create certificate when all lessons are completed
    if (
        total_lessons > 0
        and completed_lessons == total_lessons
    ):
        Certificate.objects.get_or_create(
            student=request.user,
            course=lesson.course,
            defaults={
                "certificate_id": (
                    f"CERT-{request.user.id}-"
                    f"{lesson.course.id}"
                )
            }
        )

        messages.success(
            request,
            "🎉 Congratulations! You completed the course."
        )

    else:
        messages.success(
            request,
            "Lesson marked as completed!"
        )

    return redirect(
        "lesson_detail",
        lesson_id=lesson.id
    )

@login_required
def certificate_view(request, course_id):
    certificate = get_object_or_404(
        Certificate,
        student=request.user,
        course_id=course_id
    )

    return render(
        request,
        "courses/certificate.html",
        {
            "certificate": certificate,
        }
    )



@login_required
def instructor_create_course(request):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to create courses."
        )
        return redirect("dashboard")

    if request.method == "POST":

        title = request.POST.get("title")
        category_id = request.POST.get("category")
        description = request.POST.get("description")
        price = request.POST.get("price")
        is_published = request.POST.get("is_published") == "on"

        category = get_object_or_404(
            Category,
            id=category_id
        )

        Course.objects.create(
            title=title,
            category=category,
            description=description,
            instructor=request.user,
            price=price,
            is_published=is_published
        )

        messages.success(
            request,
            "Course created successfully!"
        )

        return redirect("instructor_dashboard")

    categories = Category.objects.all()

    return render(
        request,
        "instructor/create_course.html",
        {
            "categories": categories,
        }
    )


@login_required
def instructor_edit_course(request, course_id):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to edit courses."
        )
        return redirect("dashboard")

    course = get_object_or_404(
        Course,
        id=course_id,
        instructor=request.user
    )

    if request.method == "POST":

        course.title = request.POST.get("title")
        course.description = request.POST.get("description")
        course.price = request.POST.get("price")

        category_id = request.POST.get("category")

        course.category = get_object_or_404(
            Category,
            id=category_id
        )

        course.is_published = (
            request.POST.get("is_published") == "on"
        )

        course.save()

        messages.success(
            request,
            "Course updated successfully!"
        )

        return redirect("instructor_dashboard")

    categories = Category.objects.all()

    return render(
        request,
        "instructor/edit_course.html",
        {
            "course": course,
            "categories": categories,
        }
    )

@login_required
def instructor_delete_course(request, course_id):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to delete courses."
        )
        return redirect("dashboard")

    course = get_object_or_404(
        Course,
        id=course_id,
        instructor=request.user
    )

    if request.method == "POST":
        course.delete()

        messages.success(
            request,
            "Course deleted successfully!"
        )

        return redirect("instructor_dashboard")

    return render(
        request,
        "instructor/delete_course.html",
        {
            "course": course,
        }
    )


def validate_video_file(video_file):

    if not video_file:
        return None

    extension = os.path.splitext(
        video_file.name
    )[1].lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return (
            "Invalid video format. "
            "Only MP4, WebM, and MOV files are allowed."
        )

    if video_file.size > MAX_VIDEO_SIZE:
        return (
            "Video file is too large. "
            "Maximum allowed size is 100 MB."
        )

    return None

@login_required
def instructor_create_lesson(request, course_id):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to add lessons."
        )
        return redirect("dashboard")

    course = get_object_or_404(
        Course,
        id=course_id,
        instructor=request.user
    )

    if request.method == "POST":

        title = request.POST.get("title")
        description = request.POST.get("description")
        video_url = request.POST.get("video_url")
        video_file = request.FILES.get("video_file")
        error = validate_video_file(video_file)

        if error:
            messages.error(request, error)

            return redirect(
                    "instructor_create_lesson",
                   course_id=course.id
            )  
                    
        order = request.POST.get("order")

        Lesson.objects.create(
            course=course,
            title=title,
            description=description,
            video_url=video_url,
            video_file=video_file,
            order=order
        )

        messages.success(
            request,
            "Lesson created successfully!"
        )

        return redirect("instructor_dashboard")

    return render(
        request,
        "instructor/create_lesson.html",
        {
            "course": course,
        }
    )

@login_required
def instructor_edit_lesson(request, lesson_id):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to edit lessons."
        )
        return redirect("dashboard")

    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__instructor=request.user
    )

    if request.method == "POST":

        lesson.title = request.POST.get("title")
        lesson.description = request.POST.get("description")
        lesson.video_url = request.POST.get("video_url")
        lesson.order = request.POST.get("order")

        # Check if a new video was uploaded
        video_file = request.FILES.get("video_file")

        if video_file:

           error = validate_video_file(video_file)

           if error:
              messages.error(request, error)

              return redirect(
                   "instructor_edit_lesson",
                    lesson_id=lesson.id
                )

        lesson.video_file = video_file

        lesson.save()

        messages.success(
            request,
            "Lesson updated successfully!"
        )

        return redirect("instructor_dashboard")

    return render(
        request,
        "instructor/edit_lesson.html",
        {
            "lesson": lesson,
        }
    )

@login_required
def instructor_delete_lesson(request, lesson_id):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to delete lessons."
        )
        return redirect("dashboard")

    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course__instructor=request.user
    )

    if request.method == "POST":

        lesson.delete()

        messages.success(
            request,
            "Lesson deleted successfully!"
        )

        return redirect("instructor_dashboard")

    return render(
        request,
        "instructor/delete_lesson.html",
        {
            "lesson": lesson,
        }
    )

@login_required
def instructor_students(request):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to view students."
        )
        return redirect("dashboard")

    enrollments = Enrollment.objects.filter(
        course__instructor=request.user,
        student__is_staff=False
    ).select_related(
        "student",
        "course"
    ).order_by("-enrolled_at")

    return render(
        request,
        "instructor/students.html",
        {
            "enrollments": enrollments,
        }
    )


@login_required
def instructor_student_progress(request):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to view student progress."
        )
        return redirect("dashboard")

    enrollments = Enrollment.objects.filter(
        course__instructor=request.user,
        student__is_staff=False
    ).select_related(
        "student",
        "course"
    ).order_by("-enrolled_at")

    progress_data = []

    for enrollment in enrollments:

        course = enrollment.course
        student = enrollment.student

        total_lessons = Lesson.objects.filter(
            course=course
        ).count()

        completed_lessons = LessonProgress.objects.filter(
            student=student,
            lesson__course=course,
            completed=True
        ).count()

        if total_lessons > 0:
            progress_percentage = int(
                (completed_lessons / total_lessons) * 100
            )
        else:
            progress_percentage = 0

        progress_data.append({
            "student": student,
            "course": course,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_percentage": progress_percentage,
        })

    return render(
        request,
        "instructor/student_progress.html",
        {
            "progress_data": progress_data,
        }
    )    


@login_required
def create_payment_order(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id,
        is_published=True
    )

    # Make sure this is a paid course
    if course.price <= 0:
        messages.error(
            request,
            "This is a free course."
        )
        return redirect(
            "course_detail",
            course_id=course.id
        )

    # Check if already enrolled
    if Enrollment.objects.filter(
        student=request.user,
        course=course
    ).exists():

        messages.info(
            request,
            "You are already enrolled in this course."
        )

        return redirect(
            "course_detail",
            course_id=course.id
        )

    # Create Razorpay client
    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # Razorpay uses paise
    amount = int(course.price * 100)

    # Create Razorpay order
    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    # Save payment record
    Payment.objects.create(
        student=request.user,
        course=course,
        razorpay_order_id=order["id"],
        amount=course.price,
        status="created"
    )

    return render(
        request,
        "courses/payment.html",
        {
            "course": course,
            "order": order,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        }
    )

@login_required
def verify_payment(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method."
            },
            status=400
        )

    payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    order_id = request.POST.get(
        "razorpay_order_id"
    )

    signature = request.POST.get(
        "razorpay_signature"
    )

    # Make sure all Razorpay values were received
    if not payment_id or not order_id or not signature:
        return JsonResponse(
            {
                "success": False,
                "message": "Missing payment information."
            },
            status=400
        )

    # Find the payment belonging to the logged-in student
    payment = get_object_or_404(
        Payment,
        razorpay_order_id=order_id,
        student=request.user
    )

    # Prevent reusing an already completed payment
    if payment.status == "paid":
        return JsonResponse(
            {
                "success": False,
                "message": "This payment has already been verified."
            },
            status=400
        )

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # Verify Razorpay signature
    try:

        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            }
        )

    except razorpay.errors.SignatureVerificationError:

        payment.status = "failed"
        payment.save(
            update_fields=["status"]
        )

        return JsonResponse(
            {
                "success": False,
                "message": "Payment verification failed."
            },
            status=400
        )

    # Fetch payment details directly from Razorpay
    try:

        razorpay_payment = client.payment.fetch(
            payment_id
        )

    except Exception:

        return JsonResponse(
            {
                "success": False,
                "message": "Unable to verify payment details."
            },
            status=400
        )

    # Verify the payment amount
    expected_amount = int(
        payment.amount * 100
    )

    if razorpay_payment.get("amount") != expected_amount:

        payment.status = "failed"
        payment.save(
            update_fields=["status"]
        )

        return JsonResponse(
            {
                "success": False,
                "message": "Payment amount does not match."
            },
            status=400
        )

    # Verify currency
    if razorpay_payment.get("currency") != "INR":

        payment.status = "failed"
        payment.save(
            update_fields=["status"]
        )

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid payment currency."
            },
            status=400
        )

    # Verify Razorpay payment was captured
    if razorpay_payment.get("status") != "captured":

        payment.status = "failed"
        payment.save(
            update_fields=["status"]
        )

        return JsonResponse(
            {
                "success": False,
                "message": "Payment has not been captured."
            },
            status=400
        )

    # Everything is verified
    payment.razorpay_payment_id = payment_id
    payment.status = "paid"

    payment.save(
        update_fields=[
            "razorpay_payment_id",
            "status"
        ]
    )

    # Enroll the student
    Enrollment.objects.get_or_create(
        student=request.user,
        course=payment.course
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Payment successful! You are now enrolled."
        }
    )

  

@login_required
def payment_history(request):

    payments = Payment.objects.filter(
        student=request.user
    ).order_by("-created_at")

    return render(
        request,
        "courses/payment_history.html",
        {
            "payments": payments
        }
    )





def free_courses(request):

    courses = Course.objects.filter(
        is_published=True,
        price=0
    ).order_by("-created_at")

    return render(
        request,
        "courses/free_courses.html",
        {
            "courses": courses
        }
    )


def paid_courses(request):

    courses = Course.objects.filter(
        is_published=True
    ).exclude(
        price=0
    ).order_by("-created_at")

    return render(
        request,
        "courses/paid_courses.html",
        {
            "courses": courses
        }
    )


@login_required
def instructor_payments(request):

    if not request.user.is_staff:
        messages.error(
            request,
            "You are not authorized to view payments."
        )
        return redirect("dashboard")

    payments = Payment.objects.filter(
        course__instructor=request.user
    ).select_related(
        "student",
        "course"
    ).order_by("-created_at")

    return render(
        request,
        "instructor/payments.html",
        {
            "payments": payments,
        }
    )





# Create your views here.
