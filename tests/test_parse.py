from __future__ import annotations

from pathlib import Path

from haircut.parse import detect_format, dump_coverage, load_trace, parse_hunter, parse_jsonl

FIXTURES = Path(__file__).parent / "fixtures"


def test_detect_hunter_and_jsonl():
    hunter = (FIXTURES / "hunter_sample.txt").read_text(encoding="utf-8")
    assert detect_format(hunter) == "hunter"
    jsonl = '{"file": "a.py", "line": 1, "event": "line"}\n'
    assert detect_format(jsonl) == "jsonl"
    coverage = '{"format": "haircut-coverage-v1", "files": {}}\n'
    assert detect_format(coverage) == "coverage"
    hunter = (FIXTURES / "hunter_sample.txt").read_text(encoding="utf-8")
    assert detect_format(hunter) == "hunter"
    jsonl = '{"file": "a.py", "line": 1, "event": "line"}\n'
    assert detect_format(jsonl) == "jsonl"


def test_parse_hunter_sample():
    coverage = load_trace(FIXTURES / "hunter_sample.txt")
    manager = coverage.coverage_for("[...]/django/django/db/models/manager.py")
    assert 184 in manager.call_lines
    assert 185 in manager.lines
    assert "__get__" in manager.functions
    options = coverage.coverage_for("[...]/django/django/db/models/options.py")
    assert 404 in options.call_lines
    assert "swapped" in options.functions


def test_parse_hunter_windows_path():
    coverage = parse_hunter(
        [r"C:\site-packages\django\db\models\query.py:316   line                     return self._query"]
    )
    key = r"C:\site-packages\django\db\models\query.py"
    assert 316 in coverage.coverage_for(key).lines


def test_parse_jsonl_roundtrip():
    lines = [
        '{"file": "/tmp/core.py", "line": 4, "event": "call", "func": "used"}',
        '{"file": "/tmp/core.py", "line": 6, "event": "line", "func": "used"}',
        '{"file": "/tmp/core.py", "line": 0, "event": "call", "func": "<module>"}',
    ]
    coverage = parse_jsonl(lines)
    cov = coverage.coverage_for("/tmp/core.py")
    assert cov.call_lines == {4}
    assert 6 in cov.lines
    assert 0 not in cov.lines
    assert "used" in cov.functions


def test_merge_traces(tmp_path):
    from haircut.api import merge_traces

    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    first.write_text(
        dump_coverage(
            parse_jsonl(['{"file": "a.py", "line": 1, "event": "line", "func": "one"}'])
        ),
        encoding="utf-8",
    )
    second.write_text(
        dump_coverage(
            parse_jsonl(
                [
                    '{"file": "a.py", "line": 2, "event": "call", "func": "two"}',
                    '{"file": "b.py", "line": 3, "event": "line", "func": "three"}',
                ]
            )
        ),
        encoding="utf-8",
    )
    combined_path = tmp_path / "c.json"
    combined = merge_traces([first, second], combined_path)
    assert 1 in combined.coverage_for("a.py").lines
    assert 2 in combined.coverage_for("a.py").call_lines
    assert 3 in combined.coverage_for("b.py").lines
    loaded = load_trace(combined_path)
    assert loaded.total_lines == combined.total_lines
