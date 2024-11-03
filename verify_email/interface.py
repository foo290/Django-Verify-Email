from typing import Union, Any
from dataclasses import dataclass


@dataclass
class DefaultConfig:
    """Default configuration for the application."""

    setting_field: str
    default_value: Union[str, Any]
