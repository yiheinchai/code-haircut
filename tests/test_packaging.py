import ast
import sys
from pathlib import Path

from haircut.api import slice_trace
from haircut.packaging import apply_slim, tree_bytes
from haircut.paths import is_app_migration_path
from haircut.tracer import Tracer
from haircut.errors import HaircutError
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def test_is_app_migration_path_skips_django_db_migrations():
    assert is_app_migration_path("django/contrib/auth/migrations/0001_initial.py")
    assert is_app_migration_path("/site/django/contrib/contenttypes/migrations/__init__.py")
    assert not is_app_migration_path("django/db/migrations/recorder.py")
    assert not is_app_migration_path("django/db/migrations/operations/base.py")
    assert not is_app_migration_path("shop/catalog.py")


def test_slice_copies_package_data_and_intact_migrations(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from datapkg.api import used

    with Tracer(trace, include=["datapkg"]):
        assert used() == "ok"

    output = tmp_path / "slim"
    report = slice_trace(trace, output, include=["datapkg"])
    assert report.support_files >= 3
    assert report.original_bytes > 0
    assert report.slim_bytes > 0
    assert "Bytes kept" in report.summary()

    api = (output / "datapkg" / "api.py").read_text(encoding="utf-8")
    ast.parse(api)
    assert "def used" in api
    assert "def unused" not in api

    assert (output / "datapkg" / "data.json").is_file()
    assert (output / "datapkg" / "templates" / "hello.html").is_file()
    assert (output / "datapkg" / "locale" / "en" / "LC_MESSAGES" / "django.po").is_file()

    migration = (
        output / "datapkg" / "migrations" / "0001_initial.py"
    ).read_text(encoding="utf-8")
    assert "def unused_in_migration" in migration
    assert "class Migration" in migration


def test_apply_refuses_without_yes_and_replaces_with_backup(tmp_path, monkeypatch):
    site = tmp_path / "site"
    installed = site / "mypkg"
    installed.mkdir(parents=True)
    (installed / "__init__.py").write_text("X = 1\n", encoding="utf-8")

    slim_root = tmp_path / "slim"
    slim_pkg = slim_root / "mypkg"
    slim_pkg.mkdir(parents=True)
    (slim_pkg / "__init__.py").write_text("X = 2\n", encoding="utf-8")

    monkeypatch.syspath_prepend(str(site))
    sys.modules.pop("mypkg", None)
    try:
        import mypkg

        assert mypkg.X == 1
        with pytest.raises(HaircutError, match="--yes"):
            apply_slim(slim_root, yes=False)

        old = tree_bytes(installed)
        results = apply_slim(slim_root, yes=True)
        assert len(results) == 1
        name, dest, old_bytes, new_bytes = results[0]
        assert name == "mypkg"
        assert dest == installed.resolve()
        assert old_bytes == old
        assert (installed / "__init__.py").read_text(encoding="utf-8") == "X = 2\n"
        backup = installed.with_name("mypkg.haircut-bak")
        assert backup.is_dir()
        assert (backup / "__init__.py").read_text(encoding="utf-8") == "X = 1\n"
    finally:
        sys.modules.pop("mypkg", None)
