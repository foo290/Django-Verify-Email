from base64 import urlsafe_b64decode
from binascii import Error as BASE64ERROR
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from .token_manager import TokenManager



class _UserActivationProcess:
    """
    This class is pretty self.explanatory...
    """

    def __init__(self):
        self.token_manager = TokenManager()

    def __activate_user(self, user):
        user.is_active = True
        user.last_login = timezone.now()
        user.save()

    def verify_token(self, useremail, usertoken):
        try:
            email, token = self.token_manager.decrypt_link(useremail, usertoken)
        except (ValueError, TypeError):
            return False

        inactive_users = get_user_model().objects.filter(email=email)
        try:
            if inactive_users:
                for unique_user in inactive_users:
                    valid = default_token_generator.check_token(unique_user, token)
                    if valid:
                        self.__activate_user(unique_user)
                        return valid
                return False
            return False
        except:
            return False


def _verify_user(useremail, usertoken):
    return _UserActivationProcess().verify_token(useremail, usertoken)
