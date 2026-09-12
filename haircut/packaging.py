"""Copy package data, measure trees, and apply a sliced package over an install."""

from __future__ import annotations

import shutil
from pathlib import Path

from haircut.errors import HaircutError
from haircut.paths import is_app_migration_path, relative_to_root, top_package_dir

_DATA_DIRS = {"templates", "locale", "jinja2", "static"}
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.pyd")
_SKIP_SIDECAR_SUFFIXES = {".py", ".pyc", ".pyo", ".pyd"}


def tree_bytes(root: Path) -> int:
    if not root.exists():
        return 0
    if root.is_file():
        return root.stat().st_size
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    return total


def copy_package_support_files(
    written: list[Path],
    output_dir: Path,
    strip_root: Path,
) -> list[Path]:
    """Copy templates, locales, static files, and intact app migrations."""
    copied: list[Path] = []
    seen_src: set[Path] = set()
    for dest_py in written:
        try:
            rel_dir = dest_py.parent.relative_to(output_dir)
        except ValueError:
            continue
        src_dir = strip_root / rel_dir
        if not src_dir.is_dir():
            continue
        copied.extend(_copy_sidecars(src_dir, dest_py.parent, seen_src))
        if _has_non_init_module(dest_py.parent, written):
            copied.extend(_copy_data_dirs(src_dir, dest_py.parent, seen_src))
            copied.extend(_copy_app_migrations(src_dir, dest_py.parent, seen_src))
    return copied


def _has_non_init_module(dest_dir: Path, written: list[Path]) -> bool:
    return any(path.parent == dest_dir and path.name != "__init__.py" for path in written)


def _copy_sidecars(src_dir: Path, dest_dir: Path, seen: set[Path]) -> list[Path]:
    copied: list[Path] = []
    for src in src_dir.iterdir():
        if not src.is_file() or src.suffix.lower() in _SKIP_SIDECAR_SUFFIXES:
            continue
        resolved = src.resolve()
        if resolved in seen:
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        seen.add(resolved)
        copied.append(dest)
    return copied


def _copy_data_dirs(src_dir: Path, dest_dir: Path, seen: set[Path]) -> list[Path]:
    copied: list[Path] = []
    for src in src_dir.iterdir():
        if not src.is_dir() or src.name not in _DATA_DIRS:
            continue
        resolved = src.resolve()
        if resolved in seen:
            continue
        dest = dest_dir / src.name
        shutil.copytree(src, dest, dirs_exist_ok=True, ignore=_IGNORE)
        seen.add(resolved)
        copied.extend(path for path in dest.rglob("*") if path.is_file())
    return copied


def _copy_app_migrations(src_dir: Path, dest_dir: Path, seen: set[Path]) -> list[Path]:
    src_mig = src_dir / "migrations"
    if not src_mig.is_dir():
        return []
    if not is_app_migration_path(src_mig / "__init__.py"):
        return []
    resolved = src_mig.resolve()
    if resolved in seen:
        return []
    dest_mig = dest_dir / "migrations"
    shutil.copytree(src_mig, dest_mig, dirs_exist_ok=True, ignore=_IGNORE)
    seen.add(resolved)
    return [path for path in dest_mig.rglob("*") if path.is_file()]


def apply_slim(slim_dir: Path, *, yes: bool = False) -> list[tuple[str, Path, int, int]]:
    """Replace installed packages with sliced copies. Returns (name, dest, old, new)."""
    slim_dir = slim_dir.resolve()
    if not slim_dir.is_dir():
        raise HaircutError(f"Slim directory not found: {slim_dir}")
    packages = [
        path
        for path in slim_dir.iterdir()
        if path.is_dir() and (path / "__init__.py").exists()
    ]
    if not packages:
        raise HaircutError(f"No packages found under {slim_dir}")
    replacements: list[tuple[str, Path, Path]] = []
    for package in packages:
        try:
            module = __import__(package.name)
        except ImportError as exc:
            raise HaircutError(
                f"Cannot import installed {package.name} to replace: {exc}"
            ) from exc
        file = Path(getattr(module, "__file__", "") or "")
        if not file:
            raise HaircutError(f"Installed {package.name} has no __file__")
        installed = file.parent if file.name == "__init__.py" else file
        if installed.name != package.name:
            installed = top_package_dir(file)
        replacements.append((package.name, package, installed.resolve()))
    if not yes:
        listing = "\n".join(f"  {name}: {dest}" for name, _src, dest in replacements)
        raise HaircutError(
            "Refusing to overwrite site-packages without --yes. Would replace:\n"
            + listing
        )
    results: list[tuple[str, Path, int, int]] = []
    for name, src, dest in replacements:
        old = tree_bytes(dest)
        backup = dest.with_name(dest.name + ".haircut-bak")
        if backup.exists():
            shutil.rmtree(backup)
        if dest.exists():
            dest.rename(backup)
        shutil.copytree(src, dest)
        new = tree_bytes(dest)
        results.append((name, dest, old, new))
    return results


def original_package_bytes(written: list[Path], output_dir: Path, strip_root: Path) -> int:
    packages: set[Path] = set()
    for dest in written:
        try:
            rel = relative_to_root(dest, output_dir)
        except Exception:
            continue
        src = strip_root / rel
        if src.exists():
            packages.add(top_package_dir(src))
    return sum(tree_bytes(pkg) for pkg in packages)
