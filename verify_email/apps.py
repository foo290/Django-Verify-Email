from django.apps import AppConfig


class VerifyEmailConfig(AppConfig):
    name = 'verify_email'

    def ready(self):
        print('importing signals')
        import verify_email.signals
