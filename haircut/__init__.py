"""Slice Python packages down to the code your program actually executes."""

from haircut.api import load_coverage, merge_traces, slice_trace
from haircut.packaging import apply_slim
from haircut.tracer import Tracer

__version__ = "0.2.0"
__all__ = [
    "Tracer",
    "apply_slim",
    "load_coverage",
    "merge_traces",
    "slice_trace",
    "__version__",
]
