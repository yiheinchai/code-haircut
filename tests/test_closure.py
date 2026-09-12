import ast
import sys
from pathlib import Path

from haircut.api import slice_trace
from haircut.tracer import Tracer

FIXTURES = Path(__file__).parent / "fixtures"


def test_closure_keeps_helpers_and_drops_unused_subsystems(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from biglib.models import Model

    with Tracer(trace, include=["biglib"]):
        assert Model().save("  ok  ") == "ok"

    output = tmp_path / "slim"
    report = slice_trace(trace, output, include=["biglib"])
    assert report.files_written >= 2

    base = (output / "biglib" / "models" / "base.py").read_text(encoding="utf-8")
    ast.parse(base)
    assert "def prepare" in base
    assert "def save" in base
    assert "def unused_helper" not in base
    assert "def delete" not in base

    models_init = (output / "biglib" / "models" / "__init__.py").read_text(encoding="utf-8")
    assert "aggregates" not in models_init
    assert "from .base import Model" in models_init

    assert not (output / "biglib" / "http").exists() or not any(
        (output / "biglib" / "http").rglob("*.py")
    )
    assert not (output / "biglib" / "models" / "aggregates.py").exists()

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "biglib" or name.startswith("biglib."):
                sys.modules.pop(name)
        from biglib.models import Model as SlicedModel

        assert SlicedModel().save("  ok  ") == "ok"
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "biglib" or name.startswith("biglib."):
                sys.modules.pop(name)
