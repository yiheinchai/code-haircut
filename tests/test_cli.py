import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
APP = FIXTURES / "tiny_app.py"


def _run(args: list[str], env_pythonpath: str | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(**{**subprocess.os.environ, "PYTHONPATH": str(ROOT)})
    if env_pythonpath:
        env["PYTHONPATH"] = env_pythonpath + subprocess.os.pathsep + env["PYTHONPATH"]
    return subprocess.run(
        [sys.executable, "-m", "haircut", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_record_slice_report(tmp_path):
    trace = tmp_path / "trace.jsonl"
    slim = tmp_path / "slim"
    recorded = _run(
        [
            "record",
            "-o",
            str(trace),
            "--include",
            "tiny_pkg",
            str(APP),
        ],
        env_pythonpath=str(FIXTURES),
    )
    assert recorded.returncode == 0, recorded.stderr
    assert trace.is_file()
    assert "events" in recorded.stdout

    report = _run(["report", str(trace)])
    assert report.returncode == 0, report.stderr
    assert "Files:" in report.stdout

    sliced = _run(
        ["slice", str(trace), "-o", str(slim), "--source", str(FIXTURES), "--include", "tiny_pkg"]
    )
    assert sliced.returncode == 0, sliced.stderr
    assert "CodeHaircut" in sliced.stdout
    assert (slim / "tiny_pkg" / "core.py").is_file()
