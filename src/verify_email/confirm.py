from django.utils import timezone
from .token_manager import TokenManager


class _UserActivationProcess:
    """
    This class is pretty self.explanatory...
    Exceptions Raised
    ------------------
        - MaxRetriesExceeded    (by) verify_user()
        - BadSignature          (by) verify_user()
        - SignatureExpired      (by) verify_user()
        - ValueError            (by) verify_user()
        - TypeError             (by) verify_user()
        - InvalidToken          (by) verify_user()
    """

    def __init__(self):
        self.token_manager = TokenManager()

    @staticmethod
    def __activate_user(user):
        user.is_active = True
        user.last_login = timezone.now()
        user.save()

    def verify_token(self, useremail, usertoken):
        user = self.token_manager.decrypt_link(useremail, usertoken)
        if user:
            self.__activate_user(user)
            return True
        return False


def verify_user(useremail, usertoken):
    return _UserActivationProcess().verify_token(useremail, usertoken)
