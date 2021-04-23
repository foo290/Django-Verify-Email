from .app_configurations import GetFieldFromSettings

from django.core import signing
from binascii import Error as BASE64ERROR
from base64 import urlsafe_b64encode, urlsafe_b64decode
from django.contrib.auth.tokens import default_token_generator


class TokenManager(signing.TimestampSigner):
    """
    This class is responsible for creating encrypted links.

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
        self.inline_sep = '-'
        self.max_age = self.settings.get('max_age', raise_exception=False)

        key = self.settings.get('key', raise_exception=False)
        salt = self.settings.get('salt', raise_exception=False)
        sep = self.settings.get('sep', raise_exception=False)

        super().__init__(key, sep, salt)

    @staticmethod
    def perform_encoding(plain_entity):
        return urlsafe_b64encode(str(plain_entity).encode('UTF-8')).decode('UTF-8')

    @staticmethod
    def perform_decoding(encoded_entity):
        try:
            return urlsafe_b64decode(encoded_entity).decode('UTF-8')
        except BASE64ERROR:
            return False

    def __generate_token(self, user):
        user_token = default_token_generator.make_token(user)
        if self.max_age is None:
            return self.perform_encoding(user_token)
        signed_token = self.sign(user_token)
        return self.perform_encoding(signed_token)

    def generate_link(self, request, inactive_user, user_email):
        token = self.__generate_token(inactive_user)
        encoded_email = urlsafe_b64encode(str(user_email).encode('utf-8')).decode('utf-8')

        link = f"/verification/user/verify-email/{encoded_email}/{token}/"

        absolute_link = request.build_absolute_uri(link)
        return absolute_link

    def decrypt_link(self, encoded_email, encoded_token):
        decoded_email = self.perform_decoding(encoded_email)
        decoded_token = self.perform_decoding(encoded_token)

        if decoded_email and decoded_token:
            if self.max_age:
                try:
                    decrypted_token = self.unsign(decoded_token, self.max_age)
                    return decoded_email, decrypted_token,
                except signing.SignatureExpired:
                    print(f'\n{"~"*40}\n[ERROR] : The link is Expired!\n{"~"*40}\n')
                    return False
                except signing.BadSignature:
                    print(f'\n{"~"*40}\n[CRITICAL] : X_x --> CAUTION : LINK SIGNATURE ALTERED! <-- x_X\n{"~"*40}\n')
                    return False
            else:
                return decoded_email, decoded_token,
        else:
            print(f'\n{"~"*40}\n[ERROR] : Error occurred in decoding the link!\n{"~"*40}\n')
            return False
