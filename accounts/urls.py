from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("logout/", views.user_logout, name="logout"),

    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/accounts/password-change/done/"
        ),
        name="password_change"
    ),

    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done"
    ),

    path(
         "password-reset/",
          auth_views.PasswordResetView.as_view(
              template_name="accounts/password_reset.html",
              email_template_name="accounts/password_reset_email.txt"
        ),
         name="password_reset"
    ),


    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
           template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
          template_name="accounts/password_reset_confirm.html"
       ),
        name="password_reset_confirm"
    ),

    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
           template_name="accounts/password_reset_complete.html"
       ),
        name="password_reset_complete"
    ),
]