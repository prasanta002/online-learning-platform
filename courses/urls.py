from django.urls import path
from . import views


urlpatterns = [
    path("", views.course_list, name="course_list"),

     path(
            "free/",
            views.free_courses,
            name="free_courses"
        ),

     path(
         "paid/",
         views.paid_courses,
         name="paid_courses"
       ),

    path(
        "<int:course_id>/",
        views.course_detail,
        name="course_detail"
    ),

    path(
        "<int:course_id>/enroll/",
        views.enroll_course,
        name="enroll_course"
    ),

    path("my-courses/", 
         views.my_courses, 
         name="my_courses"
    ),

    path(
        "lesson/<int:lesson_id>/",
         views.lesson_detail,
         name="lesson_detail"
    ),

    path(
        "lesson/<int:lesson_id>/complete/",
         views.mark_lesson_complete,
         name="mark_lesson_complete"
    ),

    path(
        "certificate/<int:course_id>/",
         views.certificate_view,
         name="certificate_view"
    ),

    path(
        "instructor/create-course/",
        views.instructor_create_course,
        name="instructor_create_course"
    ),

    path(
        "instructor/edit-course/<int:course_id>/",
        views.instructor_edit_course,
        name="instructor_edit_course"
    ),

    path(
        "instructor/delete-course/<int:course_id>/",
        views.instructor_delete_course,
        name="instructor_delete_course"
    ),

    path(
        "instructor/course/<int:course_id>/add-lesson/",
        views.instructor_create_lesson,
        name="instructor_create_lesson"
    ),

    path(
        "instructor/lesson/<int:lesson_id>/edit/",
        views.instructor_edit_lesson,
        name="instructor_edit_lesson"
    ),

    path(
        "instructor/lesson/<int:lesson_id>/delete/",
        views.instructor_delete_lesson,
        name="instructor_delete_lesson"
    ),

    path(
        "instructor/students/",
        views.instructor_students,
        name="instructor_students"
    ),

    path(
        "instructor/student-progress/",
         views.instructor_student_progress,
         name="instructor_student_progress"
    ),

    path(
        "instructor/payments/",
         views.instructor_payments,
         name="instructor_payments"
    ),

    path(
        "payment/<int:course_id>/",
         views.create_payment_order,
         name="create_payment_order"
    ),

    path(
        "payment/verify/",
        views.verify_payment,
        name="verify_payment"
    ),

    path(
        "payment-history/",
        views.payment_history,
        name="payment_history"
    ),

   

   
]