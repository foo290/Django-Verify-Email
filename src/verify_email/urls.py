from django.urls import path
from .views import verify_user_and_activate, request_new_link

urlpatterns = [
    path(f'user/verify-email/<useremail>/<usertoken>/', verify_user_and_activate, name='verify-email'),
    path(f'user/verify-email/request-new-link/<useremail>/<usertoken>/', request_new_link, name='request-new-link-from-token'),
    path(f'user/verify-email/request-new-link/', request_new_link, name='request-new-link-from-email'),
]
