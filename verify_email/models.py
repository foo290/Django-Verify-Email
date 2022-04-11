from django.db import models
from django.contrib.auth import get_user_model

USER = get_user_model()


class LinkCounter(models.Model):
    requester = models.OneToOneField(USER, on_delete=models.CASCADE)
    sent_count = models.IntegerField()

    def __str__(self):
        return str(self.requester.get_username())

    def __repr__(self):
        return str(self.requester.get_username())

