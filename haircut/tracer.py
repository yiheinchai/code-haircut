"""Record execution coverage with sys.settrace."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from types import FrameType
from typing import Any, Iterable, TextIO

from haircut.parse import CoverageMap

_SKIP_PREFIXES = ("<",)
_SELF_DIR = Path(__file__).resolve().parent


class Tracer:
    """Write JSONL coverage events for the code that actually ran.

    Use as a context manager around the workload you care about::

        with Tracer("trace.jsonl", include=["django"]) as tracer:
            run_app()
    """

    def __init__(
        self,
        output: str | Path | TextIO,
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
        *,
        buffer_size: int = 256,
    ) -> None:
        self._output = output
        self._include = tuple(include or ())
        self._exclude = tuple(exclude or ())
        self._buffer_size = buffer_size
        self._stream: TextIO | None = None
        self._owns_stream = False
        self._buffer: list[str] = []
        self._previous: Any = None
        self._thread_previous: Any = None
        self.events = 0
        self.coverage = CoverageMap()

    def start(self) -> None:
        if self._stream is not None:
            return
        if hasattr(self._output, "write"):
            self._stream = self._output  # type: ignore[assignment]
            self._owns_stream = False
        else:
            path = Path(self._output)  # type: ignore[arg-type]
            path.parent.mkdir(parents=True, exist_ok=True)
            self._stream = path.open("w", encoding="utf-8")
            self._owns_stream = True
        self._previous = sys.gettrace()
        self._thread_previous = threading.gettrace()
        sys.settrace(self._trace)
        threading.settrace(self._trace)

    def stop(self) -> None:
        sys.settrace(self._previous)
        threading.settrace(self._thread_previous)
        self._flush()
        if self._owns_stream and self._stream is not None:
            self._stream.close()
        self._stream = None
        self._owns_stream = False

    def __enter__(self) -> "Tracer":
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()

    def _trace(self, frame: FrameType, event: str, arg: Any) -> Any:
        if event not in ("call", "line", "return", "exception"):
            return self._trace
        filename = frame.f_code.co_filename
        if not self._should_trace(filename):
            return None
        func = frame.f_code.co_name
        line = frame.f_lineno
        if line < 1:
            return self._trace
        self.coverage.add(filename, line, event=event, func=func)
        record = {
            "file": filename,
            "line": line,
            "event": event,
            "func": func,
        }
        self._buffer.append(json.dumps(record, ensure_ascii=True))
        self.events += 1
        if len(self._buffer) >= self._buffer_size:
            self._flush()
        return self._trace

    def _should_trace(self, filename: str) -> bool:
        if not filename or filename.startswith(_SKIP_PREFIXES):
            return False
        try:
            resolved = str(Path(filename).resolve())
        except OSError:
            resolved = filename
        if resolved.startswith(str(_SELF_DIR)):
            return False
        text = resolved.replace("\\", "/")
        for item in self._exclude:
            if item and item.replace("\\", "/") in text:
                return False
        if not self._include:
            return True
        return any(item.replace("\\", "/") in text for item in self._include if item)

    def _flush(self) -> None:
        if not self._buffer or self._stream is None:
            self._buffer.clear()
            return
        self._stream.write("\n".join(self._buffer) + "\n")
        self._buffer.clear()
