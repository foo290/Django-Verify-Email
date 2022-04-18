import logging
from datetime import timedelta
from binascii import Error as BASE64ERROR
from base64 import urlsafe_b64encode, urlsafe_b64decode

from django.core import signing
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator

from .app_configurations import GetFieldFromSettings
from .errors import UserAlreadyActive, MaxRetriesExceeded, UserNotFound, WrongTimeInterval, InvalidToken

__all__ = [
    "TokenManager"
]

logger = logging.getLogger(__name__)


class TokenManager(signing.TimestampSigner):
    """
    This class is responsible for creating encrypted links / verifying them / applying several checks for token lifetime
    and generating new verification links on request.

    ENCRYPTION KEY :
        The link is encrypted using the key variable from django settings.
            - If you want to provide a custom key (other than default secret key of django project), then
              you can set a variable name "HASHING_KEY" in settings.py. (by default it will use your project's secret key
              which if fine in most cases)

    ENCRYPTION SALT :
        The salt value which will be used in algo along with the key to generate hash digest. (by default None)

    SEPARATOR :
        A separator used to separate plain and encrypted text. (by default is ":")
            - If you decide to change this, keep in mind that separator cannot be in
              URL safe base64 alphabet. read : <https://tools.ietf.org/html/rfc4648.html#section-5>

    """

    def __init__(self):
        self.settings = GetFieldFromSettings()
        self.max_age = self.settings.get('max_age', raise_exception=False)
        self.max_reties = self.settings.get('max_retries') + 1
        self._time_units = ['s', 'm', 'h', 'd']

        assert self.max_reties >= 1 if self.max_reties else None

        key = self.settings.get('key', raise_exception=False)
        salt = self.settings.get('salt', raise_exception=False)
        sep = self.settings.get('sep', raise_exception=False)

        super().__init__(key, sep, salt)

    # Private :
    def __get_seconds(self, interval):
        """
        converts the time specified in settings.py "EXPIRE_AFTER" into seconds.
            By default the time will be considered in seconds, to specify days/minutes/hours
            suffix the time with relevant unit.
                - for example:
                    for 1 day, it'll be : "1d"
                    and so on.

            If integer is specified, that will be considered in seconds
        """
        if isinstance(interval, int):
            return interval
        if isinstance(interval, str):
            unit = [i for i in self._time_units if interval.endswith(i)]
            if not unit:
                unit = 's'
                interval += unit
            else:
                unit = unit[0]
            try:
                digit_time = int(interval[:-1])
                if digit_time <= 0:
                    raise WrongTimeInterval('Time must be greater than 0')

                if unit == 's':
                    return digit_time
                if unit == 'm':
                    return timedelta(minutes=digit_time).total_seconds()
                if unit == 'h':
                    return timedelta(hours=digit_time).total_seconds()
                if unit == 'd':
                    return timedelta(days=digit_time).total_seconds()
                else:
                    return WrongTimeInterval(f'Time unit must be from : {self._time_units}')

            except ValueError:
                raise WrongTimeInterval(f'Time unit must be from : {self._time_units}')
        else:
            raise WrongTimeInterval(f'Time unit must be from : {self._time_units}')

    @staticmethod
    def __get_sent_count(user):
        """
        Returns the no. of times email has already been sent to a user.
        """
        try:
            return int(user.linkcounter.sent_count)
        except Exception as e:
            logger.error(e)
            return False

    @staticmethod
    def __increment_sent_counter(user):
        """
        Increment count by one after resending the verification link.
        """
        user.linkcounter.sent_count += 1
        user.linkcounter.save()

    def __generate_token(self, user):
        """
        If "EXPIRE_AFTER" is specified in settings.py, will generate a timestamped signed encrypted token for
        user, otherwise will generate encrypted token without timestamp.
        """
        user_token = default_token_generator.make_token(user)
        if self.max_age is None:
            return self.perform_encoding(user_token)

        signed_token = self.sign(user_token)
        return self.perform_encoding(signed_token)

    def __verify_attempts(self, user):
        """
        Compares the no. of already sent and maximum no. of times that a user is permitted to request new link.
        """
        attempts = self.__get_sent_count(user)
        if attempts and attempts >= self.max_reties:
            return False
        return True

    @staticmethod
    def get_user_by_token(plain_email, encrypted_token):
        """
        returns either a bool or user itself which fits the token and is not active.
        Exceptions Raised
        -----------------
            - UserAlreadyActive
            - InvalidToken
            - UserNotFound
        """
        inactive_users = get_user_model().objects.filter(email=plain_email)
        encrypted_token = encrypted_token.split(':')[0]
        for unique_user in inactive_users:
            valid = default_token_generator.check_token(unique_user, encrypted_token)
            if valid:
                if unique_user.is_active:
                    raise UserAlreadyActive(f'The user with email: {plain_email} is already active')
                return unique_user
            else:
                raise InvalidToken('Token is invalid')
        else:
            raise UserNotFound(f'User with {plain_email} not found')

    def __decrypt_expired_user(self, expired_token):
        """ After the link expires, it decrypt the token without a time stamp to parse out the user token. """
        return self.unsign(expired_token)

    # Public :
    @staticmethod
    def perform_encoding(plain_entity):
        return urlsafe_b64encode(str(plain_entity).encode('UTF-8')).decode('UTF-8')

    @staticmethod
    def perform_decoding(encoded_entity):
        try:
            return urlsafe_b64decode(encoded_entity).decode('UTF-8')
        except BASE64ERROR:
            return False

    def generate_link(self, request, inactive_user, user_email):
        """
        Generates link for the first time.
        """
        token = self.__generate_token(inactive_user)
        encoded_email = urlsafe_b64encode(str(user_email).encode('utf-8')).decode('utf-8')

        link = f"/verification/user/verify-email/{encoded_email}/{token}/"

        absolute_link = request.build_absolute_uri(link)
        return absolute_link

    def request_new_link(self, request, inactive_user, user_email):
        """
        generate link when user clicks on request new link. Perform several checks and returns either a link or bool
        """
        if self.__verify_attempts(inactive_user):  # noqa
            link = self.generate_link(request, inactive_user, user_email)
            self.__increment_sent_counter(inactive_user)  # noqa
            return link
        else:
            raise MaxRetriesExceeded(f'Maximum retries for user with email: {user_email} has been exceeded.')

    def decrypt_link(self, encoded_email, encoded_token):
        """
        main verification and decryption happens here.
        Exceptions Raised
        ------------------
            - signing.SignatureExpired
            - MaxRetriesExceeded
            - signing.BadSignature
            - UserAlreadyActive
            - InvalidToken
        """
        decoded_email = self.perform_decoding(encoded_email)
        decoded_token = self.perform_decoding(encoded_token)

        if decoded_email and decoded_token:
            if self.max_age:
                alive_time = self.__get_seconds(self.max_age)
                try:
                    user_token = self.unsign(decoded_token, alive_time)
                    user = self.get_user_by_token(decoded_email, user_token)
                    if user:
                        return user
                    return False

                except signing.SignatureExpired:
                    logger.warning(f'\n{"~" * 40}\n[WARNING] : The link is Expired!\n{"~" * 40}\n')
                    user = self.get_user_by_token(decoded_email, self.__decrypt_expired_user(decoded_token))
                    if not self.__verify_attempts(user):
                        raise MaxRetriesExceeded()
                    raise

                except signing.BadSignature:
                    logger.critical(
                        f'\n{"~" * 40}\n[CRITICAL] : X_x --> CAUTION : LINK SIGNATURE ALTERED! <-- x_X\n{"~" * 40}\n'
                    )
                    raise
            else:
                user = self.get_user_by_token(decoded_email, decoded_token)
                return user if user else False
        else:
            logger.error(f'\n{"~" * 40}\nError occurred in decoding the link!\n{"~" * 40}\n')
            return False
