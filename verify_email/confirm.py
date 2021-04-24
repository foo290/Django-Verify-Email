from django.utils import timezone
from .token_manager import TokenManager, error_type, MaxRetriesExceeded
from django.core.signing import SignatureExpired, BadSignature


class _UserActivationProcess:
    """
    This class is pretty self.explanatory...
    """

    def __init__(self):
        self.token_manager = TokenManager()

    @staticmethod
    def __activate_user(user):
        user.is_active = True
        user.last_login = timezone.now()
        user.save()

    def verify_token(self, useremail, usertoken):
        try:
            user = self.token_manager.decrypt_link(useremail, usertoken)
            if user:
                self.__activate_user(user)
                return True
            return False
        except (ValueError, TypeError):
            return error_type.failed
        except SignatureExpired:
            return error_type.expired
        except BadSignature:
            return error_type.tempered
        except MaxRetriesExceeded:
            return error_type.mre


def _verify_user(useremail, usertoken):
    return _UserActivationProcess().verify_token(useremail, usertoken)
