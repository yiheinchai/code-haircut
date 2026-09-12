from pathlib import Path

from haircut.tracer import Tracer

FIXTURES = Path(__file__).parent / "fixtures"


def test_tracer_records_only_included_package(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    output = tmp_path / "trace.jsonl"

    from tiny_pkg.core import Calculator, used

    with Tracer(output, include=["tiny_pkg"]) as tracer:
        used(3)
        Calculator().add(1, 2)

    assert tracer.events > 0
    text = output.read_text(encoding="utf-8")
    assert "tiny_pkg" in text
    assert "core.py" in text
    assert "extra.py" not in text
    assert any(cov.functions for cov in tracer.coverage.files.values())
