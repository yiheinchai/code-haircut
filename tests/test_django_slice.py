import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
WORKLOAD = FIXTURES / "django_workload.py"


def test_sliced_django_runs_contenttype_create_get(tmp_path):
    pytest.importorskip("django")

    trace = tmp_path / "django.json"
    slim = tmp_path / "slim"
    env = {**os.environ, "PYTHONPATH": str(ROOT)}

    recorded = subprocess.run(
        [
            sys.executable,
            "-m",
            "haircut",
            "record",
            "-o",
            str(trace),
            "--include",
            "django",
            str(WORKLOAD),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert recorded.returncode == 0, recorded.stderr + recorded.stdout
    assert "thing" in recorded.stdout
    assert trace.is_file()

    sliced = subprocess.run(
        [
            sys.executable,
            "-m",
            "haircut",
            "slice",
            str(trace),
            "-o",
            str(slim),
            "--include",
            "django",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert sliced.returncode == 0, sliced.stderr + sliced.stdout
    assert "Files written" in sliced.stdout
    assert "Bytes kept" in sliced.stdout
    assert not list(slim.glob("django/contrib/gis/**/*.py"))
    assert not list(slim.glob("django/contrib/admin/**/*.py"))

    replay = subprocess.run(
        [sys.executable, str(WORKLOAD)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(slim)},
        text=True,
        capture_output=True,
        check=False,
    )
    assert replay.returncode == 0, replay.stderr + replay.stdout
    assert replay.stdout.strip() == "thing"
