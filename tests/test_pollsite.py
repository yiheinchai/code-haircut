from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLLSITE = ROOT / "examples" / "pollsite"


def _env(*pythonpath: Path) -> dict[str, str]:
    parts = [str(path) for path in pythonpath if path]
    merged = os.pathsep.join(parts + [os.environ.get("PYTHONPATH", "")]).strip(
        os.pathsep
    )
    return {**os.environ, "PYTHONPATH": merged, "DJANGO_SETTINGS_MODULE": "pollsite.settings"}


def _manage(*args: str, pythonpath: list[Path], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=POLLSITE,
        env=_env(*pythonpath),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def test_pollsite_tests_pass_on_full_and_sliced_django(tmp_path):
    pytest.importorskip("django")

    full = _manage("test", "-v", "1", pythonpath=[POLLSITE])
    assert full.returncode == 0, full.stderr + full.stdout

    slim = tmp_path / "packages"
    built = subprocess.run(
        [
            sys.executable,
            "-m",
            "haircut",
            "build",
            "--django",
            "-o",
            str(slim),
            "--trace",
            str(tmp_path / "trace.json"),
            "--",
            sys.executable,
            "manage.py",
            "test",
            "-v",
            "1",
        ],
        cwd=POLLSITE,
        env=_env(ROOT, POLLSITE),
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    assert built.returncode == 0, built.stderr + built.stdout
    assert "Bytes kept" in built.stdout
    assert "Support files" in built.stdout
    assert (slim / "django" / "__init__.py").is_file()
    assert list((slim / "django" / "contrib" / "auth" / "migrations").glob("*.py"))
    assert list((slim / "django" / "contrib" / "contenttypes" / "migrations").glob("*.py"))
    assert not list(slim.glob("django/contrib/admin/static/**/*"))
    assert not list(slim.glob("django/contrib/gis/gdal/**/*.py"))

    replay = _manage("test", "-v", "1", pythonpath=[slim, POLLSITE], timeout=180)
    assert replay.returncode == 0, replay.stderr + replay.stdout
    assert "OK" in replay.stderr or "OK" in replay.stdout
