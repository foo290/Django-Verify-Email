from typing import TypeVar

from django.contrib.auth import get_user_model

User = TypeVar("User", bound=get_user_model())
