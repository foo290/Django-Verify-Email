import logging
from dataclasses import dataclass, field
from typing import Union, List
from datetime import timedelta
from binascii import Error as BASE64ERROR
from base64 import urlsafe_b64encode, urlsafe_b64decode

from django.core import signing
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator

from .custom_types import User
from .app_configurations import GetFieldFromSettings
from .errors import (
    UserAlreadyActive,
    MaxRetriesExceeded,
    UserNotFound,
    WrongTimeInterval,
    InvalidToken,
    DecodingFailed,
)

__all__ = ["TokenManager"]

logger = logging.getLogger(__name__)


@dataclass
class GeneralConfig:
    settings: GetFieldFromSettings = field(default_factory=GetFieldFromSettings)
    time_units: List[str] = field(default_factory=lambda: ["s", "m", "h", "d"])

    def __post_init__(self):
        self.max_age = self.settings.get("max_age", raise_exception=False)
        self.max_retries = self.settings.get("max_retries") + 1


@dataclass
class SafeURL:
    @staticmethod
    def perform_encoding(plain_entity):
        return urlsafe_b64encode(str(plain_entity).encode("UTF-8")).decode("UTF-8")

    @staticmethod
    def perform_decoding(encoded_entity):
        try:
            return urlsafe_b64decode(encoded_entity).decode("UTF-8")
        except BASE64ERROR:
            return False


@dataclass
class ActivationLinkManager(GeneralConfig):

    @staticmethod
    def _get_sent_count(user: User):
        """
        Returns the no. of times email has already been sent to a user.
        """
        return int(user.linkcounter.sent_count)

    @staticmethod
    def _increment_sent_counter(user: User) -> None:
        """
        Increment count by one after resending the verification link.
        """
        user.linkcounter.sent_count += 1
        user.linkcounter.save()

    def can_request_new_link(self, user: User) -> bool:
        """
        Checks if the user has remaining attempts to request a new link.

        Compares the user's current request count with the maximum allowed retries.
        Returns False if the maximum retries have been reached, True otherwise.

        Parameters
        ----------
        user : User
            The user for whom the attempt count is being verified.

        Returns
        -------
        bool
            True if the user has remaining attempts, False if the maximum is exceeded.
        """
        attempts = self._get_sent_count(user)
        if attempts and attempts >= self.max_retries:
            return False
        return True

    @staticmethod
    def generate_link(token, user_email):
        """
        Generates an email verification link for an inactive user.

        This method creates a signed token for the user and encodes the user's email
        to construct a unique verification link.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object, used to build the absolute URL for the link.
        token : str
            user encrpted encode token
        user_email : str
            The email address of the user, which will be included in the verification link.

        Returns
        -------
        str
            The absolute URL of the verification link.
        """
        encoded_email = urlsafe_b64encode(str(user_email).encode("utf-8")).decode(
            "utf-8"
        )
        return f"/verification/user/verify-email/{encoded_email}/{token}/"

    def get_absolute_verification_url(self, request, token, user_email):
        return request.build_absolute_uri(self.generate_link(token, user_email))

    def request_new_link(self, request, inactive_user, token, user_email):
        """
        generate link when user clicks on request new link. Perform several checks and returns either a link or bool
        """
        if self.can_request_new_link(inactive_user):  # noqa
            link = self.get_absolute_verification_url(request, token, user_email)
            self._increment_sent_counter(inactive_user)  # noqa
            return link
        else:
            raise MaxRetriesExceeded(
                f"Maximum retries for user with email: {user_email} has been exceeded."
            )


@dataclass
class TokenManager(signing.TimestampSigner, GeneralConfig):
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

    safe_url_encoder: SafeURL = field(default_factory=SafeURL)
    link_manager: ActivationLinkManager = field(default_factory=ActivationLinkManager)

    def __post_init__(self):
        GeneralConfig.__post_init__(self)

        self.key = self.settings.get("key", raise_exception=False)
        self.salt = self.settings.get("salt", raise_exception=False)
        self.sep = self.settings.get("sep", raise_exception=False)

        signing.TimestampSigner.__init__(self, key=self.key, sep=self.sep, salt=self.salt)

    @staticmethod
    def is_token_valid(plain_email, encrypted_user_token) -> bool:
        """
        Validates the token associated with a user's email.

        Checks if the provided token is valid for the user identified by the given email.
        Raises an exception if no user is found.

        Parameters
        ----------
        plain_email : str
            The email of the user to validate.
        encrypted_user_token : str
            The token associated with the user, where the token prefix is used for validation.

        Returns
        -------
        bool
            True if the token is valid, False otherwise.

        Raises
        ------
        UserNotFound
            If no user is found with the provided email.
        """
        inactive_user: list = get_user_model().objects.filter(email=plain_email)
        encrypted_token = encrypted_user_token.split(":")[0]

        if not inactive_user:
            raise UserNotFound(f"User with {plain_email} not found")
        inactive_user = inactive_user[0]
        return default_token_generator.check_token(inactive_user, encrypted_token)

    # Private :
    def _get_seconds(self, interval):
        """
        Converts a time interval specified in the settings into seconds.

        The interval can be given as an integer (considered in seconds)
        or as a string with a suffix indicating the unit of time.
        Supported units are seconds (s), minutes (m), hours (h), and days (d).

        Parameters
        ----------
        interval : int or str
            The time interval to convert. An integer is interpreted as seconds,
            while a string should end with a time unit suffix.

        Returns
        -------
        float
            The equivalent time in seconds.

        Raises
        ------
        WrongTimeInterval
            If the time is not greater than 0 or if an unsupported time unit is specified.

        Examples
        --------
        >>> self._get_seconds(10)
        10.0

        >>> self._get_seconds("5m")
        300.0

        >>> self._get_seconds("1h")
        3600.0

        >>> self._get_seconds("2d")
        172800.0

        >>> self._get_seconds("15s")
        15.0

        >>> self._get_seconds("invalid_input")
        WrongTimeInterval: Time unit must be from : ['s', 'm', 'h', 'd']
        """
        if isinstance(interval, int):
            return interval
        if isinstance(interval, str):
            unit = [i for i in self.time_units if interval.endswith(i)]
            if not unit:
                unit = "s"
                interval += unit
            else:
                unit = unit[
                    0
                ]  # TODO: look into this, this might cook my ass in some cases
            try:
                digit_time = int(interval[:-1])
                if digit_time <= 0:
                    raise WrongTimeInterval("Time must be greater than 0")

                if unit == "s":
                    return digit_time
                if unit == "m":
                    return timedelta(minutes=digit_time).total_seconds()
                if unit == "h":
                    return timedelta(hours=digit_time).total_seconds()
                if unit == "d":
                    return timedelta(days=digit_time).total_seconds()
                else:
                    return WrongTimeInterval(
                        f"Time unit must be from : {self.time_units}"
                    )

            except ValueError:
                raise WrongTimeInterval(f"Time unit must be from : {self.time_units}")
        else:
            raise WrongTimeInterval(f"Time unit must be from : {self.time_units}")

    def _get_inactive_user_by_email_and_token(
        self, plain_email: str, enc_token: str
    ) -> User:
        """
        Retrieves an inactive user by email and token.

        Verifies the provided token against the email, raising an exception if invalid.
        Returns the user associated with the email if the token is valid.

        Parameters
        ----------
        plain_email : str
            The email of the user in plaintext.
        enc_token : str
            The encrypted token for validation.

        Returns
        -------
        User
            The inactive user associated with the given email.

        Raises
        ------
        InvalidToken
            If the token is invalid for the provided email.
        """
        if not self.is_token_valid(plain_email, enc_token):
            raise InvalidToken("Token is invalid")

        return get_user_model().objects.filter(email=plain_email)[
            0
        ]  # this list will always have a value

    def _decrypt_expired_user(self, expired_token):
        """
        Decrypts an expired token without validating the timestamp.

        Used to retrieve the user token from a link after it has expired by decrypting
        without timestamp validation.

        Parameters
        ----------
        expired_token : str
            The expired token to decrypt.

        Returns
        -------
        str
            The decrypted user token.
        """
        return self.unsign(expired_token)

    def generate_token_for_user(self, user: User, get_url_encoded: bool = True) -> str:
        """
        Generates a signed and encrypted token for the user.

        If "EXPIRE_AFTER" is specified in settings, a timestamped token is created.
        Otherwise, an encrypted token without a timestamp is generated.

        Parameters
        ----------
        user : User
            The user for whom the token is being generated.
        get_url_encoded: bool
            Returns token url base64 encoded if true else normal

        Returns
        -------
        str
            The signed and encrypted, URL encoded, token for the user.
        """
        user_token = default_token_generator.make_token(user)
        if self.max_age:
            user_token = self.sign(user_token)
        return (
            self.safe_url_encoder.perform_encoding(user_token)
            if get_url_encoded
            else user_token
        )

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
        encrypted_token = encrypted_token.split(":")[0]
        for unique_user in inactive_users:
            valid = default_token_generator.check_token(unique_user, encrypted_token)
            if valid:
                if unique_user.is_active:
                    raise UserAlreadyActive(
                        f"The user with email: {plain_email} is already active"
                    )
                return unique_user
            else:
                raise InvalidToken("Token is invalid")
        else:
            raise UserNotFound(f"User with {plain_email} not found")

    def decrypt_token_and_get_user(
        self,
        encoded_email: str,
        encoded_token: str,
    ) -> Union[User, None]:
        """
        Verifies and decrypts the token, then retrieves the associated user.

        This method decodes the provided email and token, verifies the token's validity,
        and retrieves the inactive user from the database if the token is valid.

        Parameters
        ----------
        encoded_email : str
            The encoded email address of the user.
        encoded_token : str
            The encoded token associated with the user.

        Returns
        -------
        Union[User, None]
            The inactive user instance if token verification is successful; otherwise, None.

        Exceptions Raised
        ------------------
        DecodingFailed
            Raised if decoding the email or token fails.
        UserNotFound
            Raised if no user is found with the given email.
        signing.SignatureExpired
            Raised if the token has expired.
        MaxRetriesExceeded
            Raised if the maximum retry attempts have been exceeded for token validation.
        signing.BadSignature
            Raised if the token signature has been altered or is invalid.
        InvalidToken
            Raised if the provided token does not match the user's email.

        Notes
        -----
        - If the `max_age` (token timeout) is enabled, token expiration is checked.
        - Logs critical, warning, or error messages depending on the error encountered.
        """
        decoded_email = self.safe_url_encoder.perform_decoding(encoded_email)
        decoded_token = self.safe_url_encoder.perform_decoding(encoded_token)

        # Check if decoding was successful
        if not decoded_email or not decoded_token:
            logger.error(
                f'\n{"~" * 40}\nError occurred in decoding the link!'
                f' Either link or email could not be decoded\n{"~" * 40}\n'
            )
            raise DecodingFailed("Failed to decode either email or token")

        # Token timeout check
        if not self.max_age:
            return self._get_inactive_user_by_email_and_token(
                decoded_email, decoded_token
            )
        try:
            alive_time = self._get_seconds(self.max_age)
            user_token = self.unsign(decoded_token, alive_time)
            # Retrieve the user if valid
            return self._get_inactive_user_by_email_and_token(decoded_email, user_token)

        except UserNotFound:
            logger.error("User with the given email not found in db")
            raise

        except signing.SignatureExpired:
            logger.warning(
                f'\n{"~" * 40}\n[WARNING] : The link is Expired!\n{"~" * 40}\n'
            )
            user = self._get_inactive_user_by_email_and_token(
                decoded_email, self._decrypt_expired_user(decoded_token)
            )
            if not self.link_manager.can_request_new_link(user):
                raise MaxRetriesExceeded()
            raise

        except signing.BadSignature:
            logger.critical(
                f'\n{"~" * 40}\n[CRITICAL] : X_x --> CAUTION : LINK SIGNATURE ALTERED! <-- x_X\n{"~" * 40}\n'
            )
            raise
