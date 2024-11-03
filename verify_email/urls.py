from django.urls import path
from .views import verify_and_activate_user, request_new_link

urlpatterns = [
    path(
        "user/verify-email/<user_email>/<user_token>/",
        verify_and_activate_user,
        name="verify-email",
    ),
    path(
        "user/verify-email/request-new-link/<user_email>/<user_token>/",
        request_new_link,
        name="request-new-link-from-token",
    ),
    path(
        "user/verify-email/request-new-link/",
        request_new_link,
        name="request-new-link-from-email",
    ),
]
