"""
This is the core module for:
    1. Generating unique hashed Token for each user.
    2. Generate a link for confirmation from client's side by /...<encoded email>/<encoded token>/.
    3. Set the new user as inactive and saves it.
    4. Send an email to user with specified template containing the link.
    5. Verifies the link and token.
    6. Destroy token and set the user's "is_active" status as True and "last_login" as timezone.now()

The module contains private classes and method (starting with "_" or "__") which aren't suppose to be used outside.

Only two global functions are supposed to be used outside of this module as they provide a wrap for making object and 
calling method with params to reduce one level of extra code.
"""

from django.core.mail import BadHeaderError, send_mail
from django.contrib.sites.shortcuts import get_current_site
from base64 import urlsafe_b64encode
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from smtplib import SMTPException
from .app_configurations import GetFieldFromSettings


class _VerifyEmail:
    """
    This class does four things:
    1. creates tokens for each user.
    2. set each user as inactive and saves it
    3. embed encoded token with encoded email to make verification link.
    4. sends the email to user with that link.
    """

    def __init__(self):
        self.settings = GetFieldFromSettings()

    def __get_hashed_token(self, user):
        return urlsafe_b64encode(str(default_token_generator.make_token(user)).encode('utf-8')).decode('utf-8')

    def __make_verification_url(self, current_site, inactive_user, useremail):
        token = self.__get_hashed_token(inactive_user)
        email_enc = urlsafe_b64encode(str(useremail).encode('utf-8')).decode('utf-8')
        link = f"{current_site}/verification/user/verify-email/{email_enc}/{token}/"

        return link

    def send_verification_link(self, request, form):
        inactive_user = form.save(commit=False)
        inactive_user.is_active = False
        inactive_user.save()
        try:
            current_site = get_current_site(request)
            try:
                useremail = form.cleaned_data[self.settings.get('email_field_name')]
            except:
                raise KeyError(
                    'No key named "email" in your form. Your field should be named as email in form OR set a variable'
                    ' "EMAIL_FIELD_NAME" with the name of current field in settings.py if you want to use current name '
                    'as email field.'
                )

            verification_url = self.__make_verification_url(current_site, inactive_user, useremail)
            subject = self.settings.get('subject')
            msg = render_to_string(self.settings.get('html_message_template', raise_exception=True),
                                   {"link": verification_url})

            try:
                send_mail(subject, strip_tags(msg), from_email=self.settings.get('from_alias'),
                          recipient_list=[useremail], html_message=msg)
                return True
            except (BadHeaderError, SMTPException):
                inactive_user.delete()
                return False

        except Exception as error:
            inactive_user.delete()
            if self.settings.get('debug_settings'):
                raise Exception(error)


#  These is supposed to be called outside of this module
def send_verification_email(request, form):
    return _VerifyEmail().send_verification_link(request, form)
