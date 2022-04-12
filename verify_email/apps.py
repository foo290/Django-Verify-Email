from django.apps import AppConfig


class VerifyEmailConfig(AppConfig):
    name = 'verify_email'

    def ready(self):
        print('[Email Verification] : importing signals    - OK.')
        import verify_email.signals
