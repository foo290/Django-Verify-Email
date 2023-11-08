import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class VerifyEmailConfig(AppConfig):
    name = 'verify_email'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        logger.info('[Email Verification] : importing signals    - OK.')
        import verify_email.signals
