"""Record execution coverage with sys.settrace or sys.monitoring."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from types import FrameType
from typing import Any, Iterable, TextIO

from haircut.parse import CoverageMap, dump_coverage
from haircut.api_roots import collect_api_uses

_SKIP_PREFIXES = ("<",)
_SELF_DIR = Path(__file__).resolve().parent


class Tracer:
    """Write coverage for the code that actually ran.

    Compact JSON (default) stores unique file/line sets, which stays tractable
    for large libraries. A `.jsonl` output path keeps the per-event log.

        with Tracer("trace.json", include=["django"]) as tracer:
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
        self._tool_id: int | None = None
        self._jsonl = False
        self.events = 0
        self.coverage = CoverageMap()

    def start(self) -> None:
        if self._stream is not None:
            return
        if hasattr(self._output, "write"):
            self._stream = self._output  # type: ignore[assignment]
            self._owns_stream = False
            self._jsonl = True
        else:
            path = Path(self._output)  # type: ignore[arg-type]
            path.parent.mkdir(parents=True, exist_ok=True)
            self._jsonl = path.suffix.lower() == ".jsonl"
            self._stream = path.open("w", encoding="utf-8")
            self._owns_stream = True
        if hasattr(sys, "monitoring"):
            self._start_monitoring()
        else:
            self._start_settrace()

    def stop(self) -> None:
        self._stop_hooks()
        if self._include:
            self.coverage.api = collect_api_uses(self._include)
        if self._jsonl:
            self._flush()
        elif self._stream is not None:
            self._stream.write(dump_coverage(self.coverage))
        if self._owns_stream and self._stream is not None:
            self._stream.close()
        self._stream = None
        self._owns_stream = False

    def __enter__(self) -> "Tracer":
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()

    def _start_settrace(self) -> None:
        self._previous = sys.gettrace()
        self._thread_previous = threading.gettrace()
        sys.settrace(self._trace)
        threading.settrace(self._trace)

    def _start_monitoring(self) -> None:
        monitoring = sys.monitoring
        self._tool_id = None
        for tool_id in range(6):
            try:
                monitoring.use_tool_id(tool_id, "haircut")
                self._tool_id = tool_id
                break
            except ValueError:
                continue
        if self._tool_id is None:
            self._start_settrace()
            return
        events = monitoring.events
        monitoring.register_callback(self._tool_id, events.PY_START, self._on_py_start)
        monitoring.register_callback(self._tool_id, events.LINE, self._on_line)
        monitoring.set_events(self._tool_id, events.PY_START | events.LINE)

    def _stop_hooks(self) -> None:
        if self._tool_id is not None and hasattr(sys, "monitoring"):
            monitoring = sys.monitoring
            monitoring.set_events(self._tool_id, 0)
            monitoring.register_callback(self._tool_id, monitoring.events.PY_START, None)
            monitoring.register_callback(self._tool_id, monitoring.events.LINE, None)
            try:
                monitoring.free_tool_id(self._tool_id)
            except ValueError:
                pass
            self._tool_id = None
            return
        sys.settrace(self._previous)
        threading.settrace(self._thread_previous)

    def _on_py_start(self, code: Any, instruction_offset: int) -> Any:
        filename = code.co_filename
        if not self._should_trace(filename):
            return sys.monitoring.DISABLE
        line = code.co_firstlineno
        if line < 1:
            return None
        self._record(filename, line, "call", code.co_name)
        return None

    def _on_line(self, code: Any, line_number: int) -> Any:
        filename = code.co_filename
        if not self._should_trace(filename):
            return sys.monitoring.DISABLE
        if line_number < 1:
            return None
        self._record(filename, line_number, "line", code.co_name)
        return None

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
        self._record(filename, line, event, func)
        return self._trace

    def _record(self, filename: str, line: int, event: str, func: str | None) -> None:
        self.coverage.add(filename, line, event=event, func=func)
        self.events += 1
        if not self._jsonl:
            return
        record = {
            "file": filename,
            "line": line,
            "event": event,
            "func": func,
        }
        self._buffer.append(json.dumps(record, ensure_ascii=True))
        if len(self._buffer) >= self._buffer_size:
            self._flush()

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
