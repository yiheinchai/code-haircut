"""Resolve truncated Hunter paths and decide output layout."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence


def normalize_trace_path(raw: str) -> str:
    return raw.strip().replace("\\", "/")


def resolve_path(raw: str, search_roots: Sequence[Path | str]) -> Path | None:
    """Map a trace path (absolute, relative, or Hunter-truncated) to a real file."""
    raw = normalize_trace_path(raw)
    direct = Path(raw)
    if direct.is_file():
        return direct.resolve()

    suffix = raw
    if "[...]" in suffix:
        suffix = suffix.split("[...]", 1)[1]
    suffix = suffix.lstrip("/").replace("\\", "/")
    if not suffix:
        return None

    parts = Path(suffix).parts
    roots = [Path(root).resolve() for root in search_roots]
    for start in range(len(parts)):
        rel = Path(*parts[start:])
        matches = _find_suffix(roots, rel)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return _prefer_shortest(matches)
    return None


def _find_suffix(roots: Sequence[Path], rel: Path) -> list[Path]:
    needle = str(rel).replace("\\", "/")
    matches: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            candidates = [root]
        else:
            # Match by filename first, then filter by path suffix.
            candidates = root.rglob(rel.name)
        for candidate in candidates:
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            haystack = str(resolved).replace("\\", "/")
            if haystack.endswith("/" + needle) or haystack.endswith(needle):
                seen.add(resolved)
                matches.append(resolved)
    return matches


def _prefer_shortest(paths: Sequence[Path]) -> Path:
    return sorted(paths, key=lambda p: (len(p.parts), str(p)))[0]


def is_app_migration_path(path: Path | str) -> bool:
    """True for Django *app* migration modules, not ``django.db.migrations``."""
    parts = Path(path).parts
    for index, part in enumerate(parts):
        if part != "migrations":
            continue
        if index > 0 and parts[index - 1] == "db":
            continue
        return True
    return False


def path_allowed(
    path: str,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> bool:
    text = path.replace("\\", "/")
    if exclude:
        for item in exclude:
            if item and item.replace("\\", "/") in text:
                return False
    if include:
        return any(item.replace("\\", "/") in text for item in include if item)
    return True


def top_package_dir(file: Path) -> Path:
    """Directory of the outermost Python package containing *file*."""
    file = file.resolve()
    current = file.parent
    top = current
    while True:
        if (current / "__init__.py").is_file() or (current / "__init__.pyi").is_file():
            top = current
            parent = current.parent
            if parent == current:
                break
            current = parent
            continue
        break
    return top


def infer_output_root(files: Sequence[Path]) -> Path:
    """Directory to strip so output paths start at the top package name."""
    resolved = [path.resolve() for path in files]
    if not resolved:
        return Path.cwd()
    parents = [top_package_dir(path).parent for path in resolved]
    return Path(os.path.commonpath([str(p) for p in parents]))


def relative_to_root(file: Path, root: Path) -> Path:
    try:
        return file.resolve().relative_to(root.resolve())
    except ValueError:
        return Path(file.name)


def ensure_package_inits(output_dir: Path, written: Iterable[Path]) -> list[Path]:
    """Create empty __init__.py files so sliced packages stay importable."""
    created: list[Path] = []
    for file in written:
        current = file.parent
        try:
            current.relative_to(output_dir)
        except ValueError:
            continue
        while current != output_dir and current != current.parent:
            init = current / "__init__.py"
            if not init.exists():
                init.write_text("", encoding="utf-8")
                created.append(init)
            current = current.parent
    return created
