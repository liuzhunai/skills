"""Recognizers module."""

from .base import BaseRecognizer, RecognizerResult
from .slider import SliderRecognizer
from .text import TextRecognizer
from .click import ClickRecognizer

__all__ = [
    "BaseRecognizer",
    "RecognizerResult",
    "SliderRecognizer",
    "TextRecognizer",
    "ClickRecognizer",
]
