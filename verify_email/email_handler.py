from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .app_configurations import GetFieldFromSettings
from .errors import InvalidTokenOrEmail
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
        send_mail(
            subject, strip_tags(msg),
            from_email=self.settings.get('from_alias'),
            recipient_list=[useremail], html_message=msg
        )

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
            msg = render_to_string(
                self.settings.get('html_message_template', raise_exception=True),
                {"link": verification_url, "inactive_user": inactive_user}, 
                request=request
            )

            self.__send_email(msg, useremail)
            return inactive_user
        except Exception:
            inactive_user.delete()
            raise

    def resend_verification_link(self, request, email, **kwargs):
        """
        This method needs the previously sent link to get encoded email and token from that.
        Exceptions Raised
        -----------------
            - UserAlreadyActive (by) get_user_by_token()
            - MaxRetryExceeded  (by) request_new_link()
            - InvalidTokenOrEmail
        
        These exception should be handled in caller function.
        """
        inactive_user = kwargs.get('user')
        user_encoded_token = kwargs.get('token')
        encoded = kwargs.get('encoded', True)

        if encoded:
            decoded_encrypted_user_token = self.token_manager.perform_decoding(user_encoded_token)
            email = self.token_manager.perform_decoding(email)
            inactive_user = self.token_manager.get_user_by_token(email, decoded_encrypted_user_token)

        if not inactive_user or not email:
            raise InvalidTokenOrEmail(f'Either token or email is invalid. user: {inactive_user}, email: {email}')

        # At this point, we have decoded email(if it was encoded), and inactive_user, and we can request new link
        link = self.token_manager.request_new_link(request, inactive_user, email)
        msg = render_to_string(
            self.settings.get('html_message_template', raise_exception=True),
            {"link": link}, request=request
        )
        self.__send_email(msg, email)
        return True



#  These is supposed to be called outside of this module
def send_verification_email(request, form):
    return _VerifyEmail().send_verification_link(request, form)


#  These is supposed to be called outside of this module
def resend_verification_email(request, email, **kwargs):
    return _VerifyEmail().resend_verification_link(request, email, **kwargs)
