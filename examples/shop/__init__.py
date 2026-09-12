"""Tiny library used by the demo app — most of it is unused on purpose."""

from .catalog import Catalog
from .payments import charge

__all__ = ["Catalog", "charge"]
