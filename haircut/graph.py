"""Index a package and compute the symbol closure needed to run traced code."""

from __future__ import annotations

import ast
import builtins
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from haircut.parse import FileCoverage
from haircut.paths import is_app_migration_path

_BUILTIN_NAMES = set(dir(builtins)) | {
    "self",
    "cls",
    "__name__",
    "__file__",
    "__package__",
    "__doc__",
    "__annotations__",
}

_DOTTED_REF_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")


@dataclass(frozen=True)
class Symbol:
    module: str
    name: str


@dataclass
class DefInfo:
    symbol: Symbol
    kind: str
    lineno: int
    end_lineno: int
    used_names: set[str] = field(default_factory=set)
    used_attrs: set[tuple[str, str]] = field(default_factory=set)
    bases: tuple[str, ...] = ()
    inner_imports: tuple[ImportInfo, ...] = ()


@dataclass
class ImportInfo:
    lineno: int
    end_lineno: int
    level: int
    raw_module: str | None
    resolved: str | None
    names: tuple[tuple[str, str], ...]
    star: bool


@dataclass
class ModuleIndex:
    name: str
    path: Path
    is_init: bool
    source: str
    defs: dict[str, DefInfo] = field(default_factory=dict)
    methods: dict[str, DefInfo] = field(default_factory=dict)
    imports: list[ImportInfo] = field(default_factory=list)
    aliases: dict[str, Symbol] = field(default_factory=dict)
    module_used_names: set[str] = field(default_factory=set)
    module_used_attrs: set[tuple[str, str]] = field(default_factory=set)
    instances: dict[str, str] = field(default_factory=dict)
    string_refs: set[str] = field(default_factory=set)


@dataclass
class FilePlan:
    keep_linenos: set[int] = field(default_factory=set)
    keep_import_asnames: set[str] = field(default_factory=set)
    keep_names: set[str] = field(default_factory=set)
    star_names: dict[int, list[str]] = field(default_factory=dict)
    drop_import_linenos: set[int] = field(default_factory=set)


@dataclass
class PackageGraph:
    modules: dict[str, ModuleIndex] = field(default_factory=dict)
    by_path: dict[Path, ModuleIndex] = field(default_factory=dict)

    def resolve_name(self, module: str, name: str) -> Symbol | None:
        return _resolve_name(self, module, name, set())


def build_graph(paths: Iterable[Path], strip_root: Path) -> PackageGraph:
    graph = PackageGraph()
    for path in paths:
        path = path.resolve()
        if path.suffix != ".py":
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError, ValueError):
            continue
        name = _module_name(path, strip_root)
        if not name:
            continue
        index = _index_module(name, path, source, tree)
        graph.modules[name] = index
        graph.by_path[path] = index
    _bind_imports(graph)
    return graph


def executed_roots(
    graph: PackageGraph,
    coverage_by_path: dict[Path, FileCoverage],
) -> set[Symbol]:
    roots: set[Symbol] = set()
    for path, coverage in coverage_by_path.items():
        index = graph.by_path.get(path.resolve())
        if index is None:
            continue
        for defn in _all_defs(index):
            if not _executed(defn, coverage):
                continue
            roots.add(defn.symbol)
            if defn.kind == "method":
                class_name = defn.symbol.name.split(".", 1)[0]
                class_def = index.defs.get(class_name)
                if class_def is not None:
                    roots.add(class_def.symbol)
    return roots


def compute_closure(
    graph: PackageGraph,
    roots: set[Symbol],
    seed_modules: Iterable[str] | None = None,
) -> set[Symbol]:
    keep: set[Symbol] = set()
    queue: list[Symbol] = []

    def add(symbol: Symbol | None) -> None:
        if symbol is None or symbol in keep:
            return
        keep.add(symbol)
        queue.append(symbol)
        if "." in symbol.name:
            add(Symbol(symbol.module, symbol.name.split(".", 1)[0]))

    for root in roots:
        add(root)

    seeded: set[str] = set()

    def seed_module(module: str) -> None:
        if module in seeded:
            return
        seeded.add(module)
        index = graph.modules.get(module)
        if index is None:
            return
        for name in index.module_used_names:
            add(graph.resolve_name(module, name))
        for base_name, attr in index.module_used_attrs:
            _follow_attr(graph, module, base_name, attr, add)
        for dotted in index.string_refs:
            symbol = _resolve_dotted(graph, dotted)
            add(symbol)
            _add_class_methods(graph, symbol, add)

    for root in list(roots):
        seed_module(root.module)
    for module in seed_modules or ():
        seed_module(module)

    while queue:
        symbol = queue.pop()
        seed_module(symbol.module)
        defn = _def_for(graph, symbol)
        if defn is None:
            continue
        for name in set(defn.used_names) | set(defn.bases):
            if "." in name:
                head, tail = name.split(".", 1)
                _follow_attr(graph, symbol.module, head, tail.split(".", 1)[0], add)
            add(graph.resolve_name(symbol.module, name.split(".", 1)[0]))
        for base_name, attr in defn.used_attrs:
            _follow_attr(graph, symbol.module, base_name, attr, add)
            if base_name == "cls":
                modules = {symbol.module} | {item.module for item in keep}
                suffix = "." + attr
                for owner_name in modules:
                    owner = graph.modules.get(owner_name)
                    if owner is None:
                        continue
                    for method in owner.methods.values():
                        if method.symbol.name.endswith(suffix):
                            add(method.symbol)
        if defn.kind == "method" and "." in symbol.name:
            _follow_self_attrs(graph, symbol, defn, add)
            _follow_super_methods(graph, symbol, add)
        for imp in defn.inner_imports:
            _follow_inner_import(graph, symbol.module, imp, add)
        if defn.kind == "class":
            add(defn.symbol)
            _keep_class_protocol_methods(graph, defn, add)

    return keep


def plans_for_keep_set(graph: PackageGraph, keep: set[Symbol]) -> dict[Path, FilePlan]:
    plans: dict[Path, FilePlan] = {}
    for index in graph.modules.values():
        names_here = {
            symbol.name.split(".", 1)[0]
            for symbol in keep
            if symbol.module == index.name
        }
        needed = set(names_here)
        needed.update(index.module_used_names)
        for defn in _all_defs(index):
            if defn.symbol in keep:
                needed.update(defn.used_names)
                needed.update(base.split(".", 1)[0] for base in defn.bases)
        plan = FilePlan()
        for defn in _all_defs(index):
            if defn.symbol in keep:
                plan.keep_linenos.add(defn.lineno)
                if defn.kind == "method":
                    class_def = index.defs.get(defn.symbol.name.split(".", 1)[0])
                    if class_def is not None:
                        plan.keep_linenos.add(class_def.lineno)
        for name in names_here:
            class_def = index.defs.get(name)
            if class_def is not None:
                plan.keep_linenos.add(class_def.lineno)

        for imp in index.imports:
            if imp.star:
                imported = _star_needed(graph, index, imp, keep, needed)
                if imported:
                    plan.star_names[imp.lineno] = imported
                    plan.keep_import_asnames.update(imported)
                else:
                    plan.drop_import_linenos.add(imp.lineno)
                continue
            kept_as = _named_import_needed(graph, index, imp, keep, needed)
            if kept_as:
                plan.keep_import_asnames.update(kept_as)
            else:
                plan.drop_import_linenos.add(imp.lineno)

        if plan.keep_linenos or plan.keep_import_asnames:
            plan.keep_names = needed | plan.keep_import_asnames
            plans[index.path] = plan
    return plans


def discover_package_files(package_dirs: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in package_dirs:
        directory = directory.resolve()
        if directory.is_file():
            files.append(directory)
            continue
        files.extend(
            path
            for path in directory.rglob("*.py")
            if path.is_file() and not is_app_migration_path(path)
        )
    return files


def _is_external_import(graph: PackageGraph, imp: ImportInfo, orig: str) -> bool:
    """True for stdlib/third-party imports that are not part of the sliced package."""
    if imp.raw_module is None and imp.level == 0:
        return orig not in graph.modules and not _has_prefix(graph, orig)
    if imp.level:
        return False
    resolved = imp.resolved or orig
    return resolved not in graph.modules and not _has_prefix(graph, resolved)


def _star_needed(
    graph: PackageGraph,
    index: ModuleIndex,
    imp: ImportInfo,
    keep: set[Symbol],
    names_here: set[str],
) -> list[str]:
    if not imp.resolved or imp.resolved not in graph.modules:
        return []
    target = graph.modules[imp.resolved]
    imported: set[str] = set()
    for orig, defn in target.defs.items():
        if orig.startswith("_"):
            continue
        if defn.symbol in keep:
            imported.add(orig)
    if target.is_init:
        for orig in target.aliases:
            if orig.startswith("_"):
                continue
            aliased = graph.resolve_name(target.name, orig)
            if aliased is not None and aliased in keep:
                imported.add(orig)
    return sorted(imported)


def _named_import_needed(
    graph: PackageGraph,
    index: ModuleIndex,
    imp: ImportInfo,
    keep: set[Symbol],
    names_here: set[str],
) -> list[str]:
    kept: list[str] = []
    for orig, asname in imp.names:
        if asname in names_here or Symbol(index.name, asname) in keep:
            kept.append(asname)
            continue
        if _is_external_import(graph, imp, orig):
            kept.append(asname)
            continue
        if not index.is_init:
            continue
        if imp.resolved:
            target = graph.resolve_name(imp.resolved, orig)
            if target is not None and target in keep:
                kept.append(asname)
                continue
            target_mod = graph.modules.get(imp.resolved)
            if target_mod and orig in target_mod.defs:
                if target_mod.defs[orig].symbol in keep:
                    kept.append(asname)
                    continue
        child_mod = orig if imp.raw_module is None else (
            f"{imp.resolved}.{orig}" if imp.resolved else orig
        )
        if child_mod and (
            child_mod in graph.modules or _has_prefix(graph, child_mod)
        ):
            if any(
                symbol.module == child_mod or symbol.module.startswith(child_mod + ".")
                for symbol in keep
            ):
                kept.append(asname)
    return kept


def _keep_class_protocol_methods(graph: PackageGraph, defn: DefInfo, add) -> None:
    owner = graph.modules.get(defn.symbol.module)
    if owner is None:
        return
    prefix = defn.symbol.name + "."
    for method in owner.methods.values():
        if not method.symbol.name.startswith(prefix):
            continue
        short = method.symbol.name[len(prefix) :]
        if "." in short:
            continue
        if short.startswith("__") and short.endswith("__"):
            add(method.symbol)
    for name in defn.used_names:
        method = Symbol(defn.symbol.module, f"{defn.symbol.name}.{name}")
        if method.name in owner.methods:
            add(method)
    for base_name, attr in defn.used_attrs:
        candidates = [base_name]
        if base_name in {"self", "cls"}:
            candidates.append(attr)
        for candidate in candidates:
            method = Symbol(defn.symbol.module, f"{defn.symbol.name}.{candidate}")
            if method.name in owner.methods:
                add(method)


def _follow_self_attrs(graph: PackageGraph, symbol: Symbol, defn: DefInfo, add) -> None:
    class_name = symbol.name.split(".", 1)[0]
    owner = graph.modules.get(symbol.module)
    if owner is None:
        return
    for base_name, attr in defn.used_attrs:
        if base_name not in {"self", "cls", "type"}:
            continue
        sibling = f"{class_name}.{attr}"
        if sibling in owner.methods:
            add(Symbol(symbol.module, sibling))


def _follow_super_methods(graph: PackageGraph, symbol: Symbol, add) -> None:
    class_name, method_name = symbol.name.split(".", 1)
    index = graph.modules.get(symbol.module)
    if index is None:
        return
    class_def = index.defs.get(class_name)
    if class_def is None:
        return
    for base in class_def.bases:
        base_sym = graph.resolve_name(symbol.module, base.split(".", 1)[0])
        if base_sym is None or not base_sym.name:
            continue
        add(base_sym)
        parent = Symbol(base_sym.module, f"{base_sym.name}.{method_name}")
        parent_index = graph.modules.get(base_sym.module)
        if parent_index is not None and parent.name in parent_index.methods:
            add(parent)


def _follow_inner_import(graph: PackageGraph, module: str, imp: ImportInfo, add) -> None:
    """Keep names imported inside a kept function (Django AppConfig.ready lazy imports)."""
    index = graph.modules.get(module)
    if index is None:
        return
    package = index.name if index.is_init else (
        index.name.rsplit(".", 1)[0] if "." in index.name else ""
    )
    if imp.raw_module is None and imp.level == 0:
        for orig, _asname in imp.names:
            if orig in graph.modules or _has_prefix(graph, orig):
                add(Symbol(
                    orig if orig in graph.modules else _longest_prefix(graph, orig),
                    "",
                ))
            else:
                add(graph.resolve_name(module, orig))
        return
    resolved = _absolute_module(package, imp.raw_module, imp.level)
    if not resolved:
        return
    if imp.star:
        target = graph.modules.get(resolved)
        if target is not None:
            for orig, defn in target.defs.items():
                if not orig.startswith("_"):
                    add(defn.symbol)
        return
    for orig, _asname in imp.names:
        child = f"{resolved}.{orig}"
        if child in graph.modules or _has_prefix(graph, child):
            add(Symbol(
                child if child in graph.modules else _longest_prefix(graph, child),
                "",
            ))
            continue
        add(graph.resolve_name(resolved, orig) or Symbol(resolved, orig))


def _follow_attr(graph: PackageGraph, module: str, base_name: str, attr: str, add) -> None:
    if base_name in _BUILTIN_NAMES:
        return
    index = graph.modules.get(module)
    ctor = index.instances.get(base_name) if index is not None else None
    if ctor:
        class_sym = graph.resolve_name(module, ctor)
        if class_sym is not None:
            add(class_sym)
            method = Symbol(class_sym.module, f"{class_sym.name}.{attr}")
            class_index = graph.modules.get(class_sym.module)
            if class_index is not None and method.name in class_index.methods:
                add(method)
            nested = graph.resolve_name(class_sym.module, attr)
            if nested is not None:
                add(nested)
            return
    base = graph.resolve_name(module, base_name)
    if base is None:
        add(graph.resolve_name(module, base_name))
        return
    add(base)
    if base.name == "":
        add(graph.resolve_name(base.module, attr))
        return
    method = Symbol(base.module, f"{base.name}.{attr}")
    owner = graph.modules.get(base.module)
    if owner is not None and method.name in owner.methods:
        add(method)
    nested = graph.resolve_name(base.module, attr)
    if nested is not None:
        add(nested)


def _resolve_name(
    graph: PackageGraph,
    module: str,
    name: str,
    seen: set[tuple[str, str]],
) -> Symbol | None:
    key = (module, name)
    if key in seen:
        return None
    seen.add(key)
    index = graph.modules.get(module)
    if index is None:
        return None
    if name in index.defs:
        return index.defs[name].symbol
    alias = index.aliases.get(name)
    if alias is None:
        return None
    if alias.name == "":
        return alias
    return _resolve_name(graph, alias.module, alias.name, seen) or alias


def _def_for(graph: PackageGraph, symbol: Symbol) -> DefInfo | None:
    index = graph.modules.get(symbol.module)
    if index is None:
        return None
    if "." in symbol.name:
        return index.methods.get(symbol.name)
    return index.defs.get(symbol.name)


def _all_defs(index: ModuleIndex) -> Iterator[DefInfo]:
    yield from index.defs.values()
    yield from index.methods.values()


def _executed(defn: DefInfo, coverage: FileCoverage) -> bool:
    if defn.kind in {"assign", "class"}:
        return False
    end = defn.end_lineno
    if coverage.call_lines & set(range(defn.lineno, end + 1)):
        return True
    body_start = min(end, defn.lineno + 1)
    return bool(coverage.lines & set(range(body_start, end + 1)))


def _module_name(path: Path, strip_root: Path) -> str:
    try:
        rel = path.resolve().relative_to(strip_root.resolve())
    except ValueError:
        return ""
    parts = list(rel.with_suffix("").parts)
    if not parts:
        return ""
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _dotted_string_refs(tree: ast.AST) -> set[str]:
    refs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _DOTTED_REF_RE.match(node.value):
                refs.add(node.value)
    return refs


def _resolve_dotted(graph: PackageGraph, dotted: str) -> Symbol | None:
    parts = dotted.split(".")
    for split in range(len(parts) - 1, 0, -1):
        module = ".".join(parts[:split])
        rest = ".".join(parts[split:])
        index = graph.modules.get(module)
        if index is None:
            continue
        if rest in index.defs:
            return index.defs[rest].symbol
        if rest in index.methods:
            return index.methods[rest].symbol
        head = rest.split(".", 1)[0]
        if head in index.defs:
            return index.defs[head].symbol
    return None


def _add_class_methods(graph: PackageGraph, symbol: Symbol | None, add) -> None:
    if symbol is None or "." in symbol.name:
        return
    index = graph.modules.get(symbol.module)
    if index is None:
        return
    defn = index.defs.get(symbol.name)
    if defn is None or defn.kind != "class":
        return
    prefix = symbol.name + "."
    for method in index.methods.values():
        if method.symbol.name.startswith(prefix):
            add(method.symbol)


def _index_module(name: str, path: Path, source: str, tree: ast.Module) -> ModuleIndex:
    is_init = path.name == "__init__.py"
    index = ModuleIndex(name=name, path=path, is_init=is_init, source=source)
    index.string_refs = _dotted_string_refs(tree)
    imported = {
        (alias.asname or alias.name.split(".")[0])
        for stmt in tree.body
        if isinstance(stmt, (ast.Import, ast.ImportFrom))
        for alias in stmt.names
        if alias.name != "*"
    }
    for stmt in tree.body:
        if _is_type_checking_if(stmt):
            continue
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            used_names, used_attrs = _uses(stmt, skip_locals=True, imported=imported)
            index.defs[stmt.name] = DefInfo(
                symbol=Symbol(name, stmt.name),
                kind="func",
                lineno=stmt.lineno,
                end_lineno=stmt.end_lineno or stmt.lineno,
                used_names=used_names,
                used_attrs=used_attrs,
                inner_imports=_inner_imports(stmt),
            )
        elif isinstance(stmt, ast.ClassDef):
            used_names, used_attrs = _uses(stmt, skip_locals=False, imported=imported)
            bases = tuple(_base_name(base) for base in stmt.bases if _base_name(base))
            index.defs[stmt.name] = DefInfo(
                symbol=Symbol(name, stmt.name),
                kind="class",
                lineno=stmt.lineno,
                end_lineno=stmt.end_lineno or stmt.lineno,
                used_names=used_names - {stmt.name},
                used_attrs=used_attrs,
                bases=bases,
                inner_imports=_inner_imports(stmt),
            )
            for child in stmt.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_names, m_attrs = _uses(child, skip_locals=True, imported=imported)
                    method_name = f"{stmt.name}.{child.name}"
                    index.methods[method_name] = DefInfo(
                        symbol=Symbol(name, method_name),
                        kind="method",
                        lineno=child.lineno,
                        end_lineno=child.end_lineno or child.lineno,
                        used_names=m_names,
                        used_attrs=m_attrs,
                        inner_imports=_inner_imports(child),
                    )
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
            index.imports.append(_import_info(stmt))
        else:
            names, attrs = _uses(stmt, skip_locals=False, imported=imported)
            index.module_used_names.update(names)
            index.module_used_attrs.update(attrs)
            for target in _assignment_names(stmt):
                if target not in index.defs:
                    index.defs[target] = DefInfo(
                        symbol=Symbol(name, target),
                        kind="assign",
                        lineno=stmt.lineno,
                        end_lineno=stmt.end_lineno or stmt.lineno,
                        used_names=names,
                        used_attrs=attrs,
                    )
                ctor = _constructor_class(stmt)
                if ctor:
                    index.instances[target] = ctor
    return index


def _inner_imports(node: ast.AST) -> tuple[ImportInfo, ...]:
    found: list[ImportInfo] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.Import, ast.ImportFrom)):
            found.append(_import_info(child))
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        else:
            found.extend(_inner_imports(child))
    return tuple(found)


def _constructor_class(stmt: ast.AST) -> str | None:
    """Return the class name for ``name = Foo()`` so instance attributes follow Foo."""
    if not isinstance(stmt, ast.Assign) or not isinstance(stmt.value, ast.Call):
        return None
    func = stmt.value.func
    if isinstance(func, ast.Name):
        if func.id in _BUILTIN_NAMES:
            return None
        return func.id
    return None


def _import_info(stmt: ast.Import | ast.ImportFrom) -> ImportInfo:
    if isinstance(stmt, ast.Import):
        names = tuple(
            (alias.name, alias.asname or alias.name.split(".")[0]) for alias in stmt.names
        )
        return ImportInfo(
            lineno=stmt.lineno,
            end_lineno=stmt.end_lineno or stmt.lineno,
            level=0,
            raw_module=None,
            resolved=None,
            names=names,
            star=False,
        )
    star = any(alias.name == "*" for alias in stmt.names)
    names = tuple(
        (alias.name, alias.asname or alias.name)
        for alias in stmt.names
        if alias.name != "*"
    )
    return ImportInfo(
        lineno=stmt.lineno,
        end_lineno=stmt.end_lineno or stmt.lineno,
        level=stmt.level,
        raw_module=stmt.module,
        resolved=None,
        names=names,
        star=star,
    )


def _bind_imports(graph: PackageGraph) -> None:
    for index in graph.modules.values():
        package = index.name if index.is_init else (
            index.name.rsplit(".", 1)[0] if "." in index.name else ""
        )
        for imp in index.imports:
            if imp.raw_module is None and imp.level == 0:
                for orig, asname in imp.names:
                    target = orig
                    if target in graph.modules or _has_prefix(graph, target):
                        index.aliases[asname] = Symbol(
                            target if target in graph.modules else _longest_prefix(graph, target),
                            "",
                        )
                continue
            resolved = _absolute_module(package, imp.raw_module, imp.level)
            imp.resolved = resolved
            if not resolved:
                continue
            if imp.star:
                target = graph.modules.get(resolved)
                if target is not None:
                    for orig, defn in target.defs.items():
                        if orig.startswith("_"):
                            continue
                        index.aliases[orig] = defn.symbol
                continue
            for orig, asname in imp.names:
                child = f"{resolved}.{orig}"
                if child in graph.modules or _has_prefix(graph, child):
                    index.aliases[asname] = Symbol(
                        child if child in graph.modules else _longest_prefix(graph, child),
                        "",
                    )
                else:
                    index.aliases[asname] = Symbol(resolved, orig)


def _has_prefix(graph: PackageGraph, mod: str) -> bool:
    return any(name == mod or name.startswith(mod + ".") for name in graph.modules)


def _longest_prefix(graph: PackageGraph, mod: str) -> str:
    parts = mod.split(".")
    for i in range(len(parts), 0, -1):
        candidate = ".".join(parts[:i])
        if candidate in graph.modules:
            return candidate
    return mod


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


def _uses(
    node: ast.AST,
    *,
    skip_locals: bool,
    imported: set[str] | None = None,
) -> tuple[set[str], set[tuple[str, str]]]:
    local: set[str] = set()
    if skip_locals:
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                local.add(child.id)
            if isinstance(child, ast.arg):
                local.add(child.arg)
    names: set[str] = set()
    attrs: set[tuple[str, str]] = set()
    builtin_skip = _BUILTIN_NAMES - (imported or set())
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            if child.id not in local and child.id not in builtin_skip:
                names.add(child.id)
        elif isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
            if child.value.id not in local:
                attrs.add((child.value.id, child.attr))
    return names, attrs


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = _base_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return ""


def _assignment_names(stmt: ast.AST) -> list[str]:
    names: list[str] = []
    if isinstance(stmt, ast.Assign):
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        names.append(stmt.target.id)
    return names


def _is_type_checking_if(stmt: ast.AST) -> bool:
    if not isinstance(stmt, ast.If):
        return False
    test = stmt.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
