"""Platforms module for rental listing sources."""

from .base import PlatformAdapter
from .wuba import WubaAdapter
from .factory import PlatformFactory

__all__ = ["PlatformAdapter", "WubaAdapter", "PlatformFactory"]
