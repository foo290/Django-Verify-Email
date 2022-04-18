import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import LinkCounter, USER

logger = logging.getLogger(__name__)


@receiver(post_save, sender=USER)
def increase_count(sender, instance, created, **kwargs):
    if created:
        LinkCounter.objects.create(requester=instance, sent_count=1)


@receiver(post_save, sender=USER)
def save_count(sender, instance, **kwargs):
    try:
        instance.linkcounter.save()
    except Exception as err:
        logger.error(err)
