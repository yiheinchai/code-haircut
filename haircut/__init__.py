"""Slice Python packages down to the code your program actually executes."""

from haircut.api import load_coverage, slice_trace
from haircut.tracer import Tracer

__version__ = "0.1.0"
__all__ = ["Tracer", "load_coverage", "slice_trace", "__version__"]
