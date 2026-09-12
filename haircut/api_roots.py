"""Capture public library names imported by the caller's code.

Coverage only records files inside ``--include``. User modules such as
``pollsite/urls.py`` do ``from django.urls import path`` without those names
being used *inside* Django, so the slicer would drop the re-export. At the end
of a recorded run we parse every loaded non-library module and keep those API
uses as extra roots.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable

from haircut.paths import path_allowed

_SKIP_SUFFIXES = {".so", ".pyd", ".pyc"}
_SELF_DIR = Path(__file__).resolve().parent


def collect_api_uses(include: Iterable[str]) -> list[tuple[str, str]]:
    """Return ``(module, name)`` pairs imported from included packages."""
    include_tuple = tuple(item for item in include if item)
    if not include_tuple:
        return []
    found: set[tuple[str, str]] = set()
    stdlib_root = Path(sys.base_prefix).resolve()
    for module in list(sys.modules.values()):
        filename = _module_filename(module)
        if filename is None:
            continue
        if path_allowed(filename, include=include_tuple):
            continue
        if _is_stdlib(filename, stdlib_root):
            continue
        try:
            resolved = str(Path(filename).resolve())
        except OSError:
            resolved = filename
        if resolved.startswith(str(_SELF_DIR)):
            continue
        try:
            source = Path(filename).read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=filename)
        except (OSError, SyntaxError, ValueError, TypeError):
            continue
        package = getattr(module, "__package__", None) or getattr(module, "__name__", "") or ""
        found.update(_api_uses_in_tree(tree, package, include_tuple))
    return sorted(found)


def _module_filename(module: object) -> str | None:
    filename = getattr(module, "__file__", None)
    if not isinstance(filename, str) or not filename:
        return None
    if Path(filename).suffix.lower() in _SKIP_SUFFIXES:
        return None
    return filename


def _is_stdlib(filename: str, stdlib_root: Path) -> bool:
    try:
        resolved = Path(filename).resolve()
    except OSError:
        return False
    try:
        resolved.relative_to(stdlib_root)
    except ValueError:
        return False
    return "site-packages" not in resolved.as_posix()


def _api_uses_in_tree(
    tree: ast.AST,
    package: str,
    include: tuple[str, ...],
) -> set[tuple[str, str]]:
    aliases: dict[str, tuple[str, str]] = {}
    star_modules: list[str] = []
    uses: set[tuple[str, str]] = set()

    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                target = alias.name
                if not _module_is_included(target, include):
                    continue
                asname = alias.asname or alias.name.split(".", 1)[0]
                aliases[asname] = (target, "")
                uses.add((target, ""))
        elif isinstance(stmt, ast.ImportFrom):
            resolved = _absolute_module(package, stmt.module, stmt.level)
            if not resolved or not _module_is_included(resolved, include):
                continue
            for alias in stmt.names:
                if alias.name == "*":
                    star_modules.append(resolved)
                    uses.add((resolved, "*"))
                    continue
                asname = alias.asname or alias.name
                child = f"{resolved}.{alias.name}"
                if _module_is_included(child, include):
                    aliases[asname] = (child, "")
                    uses.add((child, ""))
                else:
                    aliases[asname] = (resolved, alias.name)
                    uses.add((resolved, alias.name))

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base = aliases.get(node.value.id)
            if base is None:
                continue
            module, name = base
            if name == "":
                uses.add((module, node.attr))
            else:
                uses.add((module, f"{name}.{node.attr}"))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in aliases:
                uses.add(aliases[node.id])
            for star_mod in star_modules:
                if _name_exported(star_mod, node.id):
                    uses.add((star_mod, node.id))
    return uses


def _module_is_included(modname: str, include: tuple[str, ...]) -> bool:
    if not modname:
        return False
    module = sys.modules.get(modname)
    if not isinstance(module, ModuleType):
        return False
    filename = getattr(module, "__file__", None)
    if isinstance(filename, str) and filename:
        return path_allowed(filename, include=include)
    return any(modname == item or modname.startswith(item + ".") for item in include)


def _name_exported(modname: str, name: str) -> bool:
    module = sys.modules.get(modname)
    if module is None or name.startswith("_"):
        return False
    exported = getattr(module, "__all__", None)
    if exported is not None:
        return name in set(exported)
    return hasattr(module, name)


def _absolute_module(package: str, module: str | None, level: int) -> str | None:
    if level == 0:
        return module
    parts = package.split(".") if package else []
    drop = level - 1
    if drop > len(parts):
        return None
    base = parts[: len(parts) - drop] if drop else parts
    if module:
        return ".".join([*base, *module.split(".")]) if base else module
    return ".".join(base) if base else None
