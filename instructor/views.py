from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout

from courses.models import Course, Enrollment, Lesson


def is_instructor(user):
    return user.is_staff


# =========================
# OFFICER LOGIN
# =========================
def officer_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            messages.error(
                request,
                "Invalid officer username or password."
            )
            return redirect("officer_login")

        if not user.is_staff:
            messages.error(
                request,
                "You are not authorized as an officer."
            )
            return redirect("officer_login")

        login(request, user)

        return redirect("instructor_dashboard")

    return render(
        request,
        "instructor/login.html"
    )


#OFFICER LOGOUT

def officer_logout(request):

    logout(request)

    return redirect("home")


# =========================
# OFFICER DASHBOARD
# =========================
@login_required
@user_passes_test(is_instructor)
def instructor_dashboard(request):

    total_courses = Course.objects.filter(
        instructor=request.user
    ).count()

    total_lessons = Lesson.objects.filter(
        course__instructor=request.user
    ).count()

    total_students = Enrollment.objects.filter(
        course__instructor=request.user
    ).values(
        "student"
    ).distinct().count()

    total_enrollments = Enrollment.objects.filter(
        course__instructor=request.user
    ).count()

    courses = Course.objects.filter(
        instructor=request.user
    )

    return render(
        request,
        "instructor/dashboard.html",
        {
            "total_courses": total_courses,
            "total_lessons": total_lessons,
            "total_students": total_students,
            "total_enrollments": total_enrollments,
            "courses": courses,
        }
    )


