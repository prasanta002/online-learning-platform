from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required 

from courses.models import Enrollment, LessonProgress


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        messages.success(request, "Account created successfully!")
        return redirect("login")

    return render(request, "accounts/register.html")



def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if user.is_staff:
                messages.error(
                    request,
                    "Officer accounts must use the Officer Login."
                )
                return redirect("login")

            login(request, user)

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "accounts/login.html"
    )





@login_required
def dashboard(request):

    

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

        enrolled_courses.append({
            "course": course,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_percentage": progress_percentage,
        })

    return render(
        request,
        "accounts/dashboard.html",
        {
            "enrolled_courses": enrolled_courses,
        }
    )

@login_required
def user_logout(request):
    logout(request)
    return redirect("home")

@login_required
def profile(request):
    return render(
        request,
        "accounts/profile.html"
    )

@login_required
def edit_profile(request):

    if request.method == "POST":

        request.user.first_name = request.POST.get("first_name")
        request.user.last_name = request.POST.get("last_name")
        request.user.email = request.POST.get("email")

        request.user.save()

        messages.success(
            request,
            "Profile updated successfully!"
        )

        return redirect("profile")

    return render(
        request,
        "accounts/edit_profile.html"
    )
# Create your views here.
