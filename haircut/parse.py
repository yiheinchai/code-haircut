"""Load execution traces into per-file coverage."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from haircut.errors import TraceParseError

HUNTER_LINE_RE = re.compile(
    r"^(?P<file>.+):(?P<line>\d+)\s+"
    r"(?P<event>call|line|return|exception)\s+"
    r"(?P<body>.*)$"
)
CALL_NAME_RE = re.compile(r"=>\s*([^\s(]+)")
RETURN_NAME_RE = re.compile(r"<=\s*([^:]+)")


@dataclass
class FileCoverage:
    """Executed lines and call sites for one source file."""

    path: str
    lines: set[int] = field(default_factory=set)
    call_lines: set[int] = field(default_factory=set)
    functions: set[str] = field(default_factory=set)

    def add(self, line: int, event: str = "line", func: str | None = None) -> None:
        self.lines.add(line)
        if event == "call":
            self.call_lines.add(line)
            if func:
                self.functions.add(func)


@dataclass
class CoverageMap:
    """Coverage keyed by the path string found in the trace."""

    files: dict[str, FileCoverage] = field(default_factory=dict)

    def coverage_for(self, path: str) -> FileCoverage:
        cov = self.files.get(path)
        if cov is None:
            cov = FileCoverage(path=path)
            self.files[path] = cov
        return cov

    def add(
        self,
        path: str,
        line: int,
        event: str = "line",
        func: str | None = None,
    ) -> None:
        self.coverage_for(path).add(line, event=event, func=func)

    def __len__(self) -> int:
        return len(self.files)

    @property
    def total_lines(self) -> int:
        return sum(len(cov.lines) for cov in self.files.values())


def detect_format(text: str) -> str:
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("{"):
            return "jsonl"
        return "hunter"
    raise TraceParseError("Trace file is empty.")


def load_trace(path: str | Path) -> CoverageMap:
    """Auto-detect Hunter CallPrinter text or JSONL and load coverage."""
    trace_path = Path(path)
    try:
        text = trace_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise TraceParseError(f"Could not read trace file {trace_path}: {exc}") from exc
    kind = detect_format(text)
    if kind == "jsonl":
        return parse_jsonl(text.splitlines())
    return parse_hunter(text.splitlines())


def parse_jsonl(lines: Iterable[str]) -> CoverageMap:
    coverage = CoverageMap()
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceParseError(f"Invalid JSONL on line {lineno}: {exc}") from exc
        file_path = _first_present(rec, "file", "filename", "path")
        line_no = _first_present(rec, "line", "lineno")
        if file_path is None or line_no is None:
            raise TraceParseError(
                f"JSONL line {lineno} must include file and line fields."
            )
        try:
            line_no = int(line_no)
        except (TypeError, ValueError) as exc:
            raise TraceParseError(f"JSONL line {lineno} has a non-integer line.") from exc
        if line_no < 1:
            continue
        event = str(rec.get("event") or "line")
        func = rec.get("func") or rec.get("function")
        coverage.add(str(file_path), line_no, event=event, func=func)
    if not coverage:
        raise TraceParseError("JSONL trace contained no events.")
    return coverage


def parse_hunter(lines: Iterable[str]) -> CoverageMap:
    coverage = CoverageMap()
    parsed = 0
    for lineno, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        event = _parse_hunter_line(raw)
        if event is None:
            continue
        file_path, line_no, kind, func = event
        if line_no < 1:
            continue
        coverage.add(file_path, line_no, event=kind, func=func)
        parsed += 1
    if parsed == 0:
        raise TraceParseError(
            "No Hunter trace lines matched. Expected "
            "'path:lineno event code' CallPrinter output."
        )
    return coverage


def _parse_hunter_line(raw: str) -> tuple[str, int, str, str | None] | None:
    match = HUNTER_LINE_RE.match(raw.rstrip("\n"))
    if not match:
        return None
    func = _hunter_func(match.group("event"), match.group("body"))
    return (
        match.group("file").strip(),
        int(match.group("line")),
        match.group("event"),
        func,
    )


def _first_present(record: dict, *keys: str):
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None


def _hunter_func(event: str, body: str) -> str | None:
    if event == "call":
        match = CALL_NAME_RE.search(body)
        return match.group(1) if match else None
    if event == "return":
        match = RETURN_NAME_RE.search(body)
        return match.group(1).strip() if match else None
    return None
