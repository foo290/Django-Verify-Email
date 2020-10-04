from base64 import urlsafe_b64decode
from binascii import Error as BASE64ERROR
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from .app_configurations import GetFieldFromSettings

success_redirect = GetFieldFromSettings().get('verification_success_redirect')
failed_redirect = GetFieldFromSettings().get('verification_failed_redirect')

success_msg = GetFieldFromSettings().get('verification_success_msg')
failed_msg = GetFieldFromSettings().get('verification_failed_msg')

failed_template = GetFieldFromSettings().get('verification_failed_template')
success_template = GetFieldFromSettings().get('verification_success_template')


class _UserActivationProcess:
    """
    This class is pretty self.explanatory...
    """

    def __init__(self):
        pass

    def __activate_user(self, user):
        user.is_active = True
        user.last_login = timezone.now()
        user.save()

    def verify_token(self, useremail, usertoken):
        try:
            email = urlsafe_b64decode(useremail).decode('utf-8')
            token = urlsafe_b64decode(usertoken).decode('utf-8')
        except BASE64ERROR:
            return False

        inactive_unique_user = get_user_model().objects.get(email=email)
        try:
            valid = default_token_generator.check_token(inactive_unique_user, token)
            if valid:
                self.__activate_user(inactive_unique_user)
                return valid
            else:
                return False
        except:
            return False


def _verify_user(useremail, usertoken):
    return _UserActivationProcess().verify_token(useremail, usertoken)


def verify_user_and_activate(request, useremail, usertoken):
    """
    A view function already implemented for you so you don't have to implement any function for verification
    as this function will be automatically be called when user clicks on verification link.

    verify the user's email and token and redirect'em accordingly.
    """

    if _verify_user(useremail, usertoken):
        if success_redirect and not success_template:
            messages.SUCCESS(request, 'Successfully Verified!')
            return redirect(to=success_redirect)
        return render(
            request,
            template_name=success_template,
            context={
                'msg': success_msg,
                'status': 'Verification Successful!',
                'link': reverse(success_redirect)
            }
        )
    else:
        return render(
            request,
            template_name=failed_template,
            context={
                'msg': failed_msg,
                'status': 'Verification Failed!',
            }
        )
