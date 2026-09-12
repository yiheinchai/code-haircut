import ast
import sys
from pathlib import Path

from haircut.api import slice_trace
from haircut.tracer import Tracer

FIXTURES = Path(__file__).parent / "fixtures"


def test_slice_trace_roundtrip(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.jsonl"

    from tiny_pkg.core import Calculator, used

    with Tracer(trace, include=["tiny_pkg"]):
        assert used(3) == 12
        assert Calculator().add(1, 2) == 6

    output = tmp_path / "slim"
    report = slice_trace(trace, output, include=["tiny_pkg"])
    assert report.files_written >= 2
    core = (output / "tiny_pkg" / "core.py").read_text(encoding="utf-8")
    ast.parse(core)
    assert "def used" in core
    assert "def unused" not in core
    assert "class Calculator" in core
    assert "def unused_method" not in core
    assert "class UnusedClass" not in core
    extra = output / "tiny_pkg" / "extra.py"
    assert not extra.exists()

    util = (output / "tiny_pkg" / "util.py").read_text(encoding="utf-8")
    assert "def double" in util
    assert "def unused_helper" not in util

    sys.path.insert(0, str(output))
    try:
        sys.modules.pop("tiny_pkg", None)
        sys.modules.pop("tiny_pkg.core", None)
        sys.modules.pop("tiny_pkg.util", None)
        from tiny_pkg.core import Calculator as SlicedCalc
        from tiny_pkg.core import used as sliced_used

        assert sliced_used(3) == 12
        assert SlicedCalc().add(1, 2) == 6
    finally:
        sys.path.remove(str(output))


def test_slice_with_prune_branches(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.jsonl"

    from tiny_pkg.core import used

    with Tracer(trace, include=["tiny_pkg/core.py"]):
        used(3)

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["tiny_pkg"], prune_branches=True)
    core = (output / "tiny_pkg" / "core.py").read_text(encoding="utf-8")
    ast.parse(core)
    assert "return -x" not in core
    assert "double(x)" in core
