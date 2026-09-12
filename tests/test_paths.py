from pathlib import Path

from haircut.paths import infer_output_root, resolve_path, top_package_dir

SRC = Path(__file__).parent / "fixtures" / "src"


def test_resolve_truncated_hunter_path():
    raw = "[...]/django/django/db/models/options.py"
    resolved = resolve_path(raw, [SRC])
    assert resolved == (SRC / "django/db/models/options.py").resolve()


def test_resolve_eats_truncated_prefix_junk():
    raw = "[...]go/django/db/models/options.py"
    resolved = resolve_path(raw, [SRC])
    assert resolved == (SRC / "django/db/models/options.py").resolve()


def test_top_package_and_output_root():
    file = SRC / "django/db/models/options.py"
    assert top_package_dir(file).name == "django"
    assert infer_output_root([file]) == SRC.resolve()


def test_is_app_migration_path():
    from haircut.paths import is_app_migration_path

    assert is_app_migration_path(Path("django/contrib/auth/migrations/0001_initial.py"))
    assert not is_app_migration_path(Path("django/db/migrations/executor.py"))
