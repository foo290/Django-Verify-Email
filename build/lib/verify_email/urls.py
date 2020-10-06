from django.urls import path
from .views import verify_user_and_activate

urlpatterns = [
    path(f'user/verify-email/<useremail>/<usertoken>/', verify_user_and_activate, name='verify-email'),
]
