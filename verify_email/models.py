from django.db import models
from django.contrib.auth import get_user_model

USER = get_user_model()


class LinkCounter(models.Model):
    """
    Represents a count of links sent by a user.

    Attributes
    ----------
    requester : OneToOneField
        A one-to-one relationship with the user who made the request.
    sent_count : int
        The total number of links sent by the requester.

    Methods
    -------
    __str__() -> str:
        Returns the username of the requester as a string.

    __repr__() -> str:
        Returns the username of the requester for representation.
    """

    requester = models.OneToOneField(USER, on_delete=models.CASCADE)
    sent_count = models.IntegerField()

    def __str__(self) -> str:
        """
        Returns the username of the requester when converting the object to a string.

        Returns
        -------
        str
            The username of the requester.
        """
        return str(self.requester.get_username())

    def __repr__(self) -> str:
        """
        Returns a string representation of the LinkCounter instance.

        Returns
        -------
        str
            The username of the requester.
        """
        return str(self.requester.get_username())
