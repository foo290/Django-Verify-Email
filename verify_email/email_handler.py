from django.core.mail import BadHeaderError, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from smtplib import SMTPException
from .app_configurations import GetFieldFromSettings

from .token_manager import TokenManager


class _VerifyEmail:
    """
    This class does two things:
    1. set each user as inactive and saves it
    2. sends the email to user with that link.
    """

    def __init__(self):
        self.settings = GetFieldFromSettings()
        self.token_manager = TokenManager()

    # Private :
    def __send_email(self, msg, useremail):
        subject = self.settings.get('subject')
        try:
            send_mail(subject, strip_tags(msg), from_email=self.settings.get('from_alias'),
                      recipient_list=[useremail], html_message=msg)
            return True
        except (BadHeaderError, SMTPException):
            return False

    # Public :
    def send_verification_link(self, request, form):
        inactive_user = form.save(commit=False)
        inactive_user.is_active = False
        inactive_user.save()

        try:
            useremail = form.cleaned_data.get(self.settings.get('email_field_name'))
            if not useremail:
                raise KeyError(
                    'No key named "email" in your form. Your field should be named as email in form OR set a variable'
                    ' "EMAIL_FIELD_NAME" with the name of current field in settings.py if you want to use current name '
                    'as email field.'
                )

            verification_url = self.token_manager.generate_link(request, inactive_user, useremail)
            msg = render_to_string(self.settings.get('html_message_template', raise_exception=True),
                                   {"link": verification_url})

            if self.__send_email(msg, useremail):
                return inactive_user
            inactive_user.delete()
            return False

        except Exception as error:

            inactive_user.delete()
            if self.settings.get('debug_settings'):
                raise Exception(error)

    def resend_verification_link(self, request, encoded_email, encoded_token):
        """
        This method needs the previously sent link to get encoded email and token from that.
        """
        assert encoded_email is not None
        assert encoded_token is not None
        link = self.token_manager.request_new_link(request, encoded_email, encoded_token)
        email = self.token_manager.perform_decoding(encoded_email)
        if link:
            msg = render_to_string(self.settings.get('html_message_template', raise_exception=True),
                                   {"link": link})
            try:
                self.__send_email(msg, email)
                return True
            except (BadHeaderError, SMTPException):
                return False
        else:
            return link


#  These is supposed to be called outside of this module
def send_verification_email(request, form):
    return _VerifyEmail().send_verification_link(request, form)


#  These is supposed to be called outside of this module
def resend_verification_email(request, encoded_email, encoded_token):
    return _VerifyEmail().resend_verification_link(request, encoded_email, encoded_token)
