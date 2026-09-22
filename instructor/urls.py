from django.urls import path
from . import views

urlpatterns = [

    path(
        "login/",
        views.officer_login,
        name="officer_login"
    ),

    path(
        "logout/",
        views.officer_logout,
        name="officer_logout"
    ),

    path(
        "",
        views.instructor_dashboard,
        name="instructor_dashboard"
    ),
]