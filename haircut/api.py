"""High-level API: load a trace and emit a sliced package."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from haircut.errors import SourceNotFoundError, TraceParseError
from haircut.graph import (
    Symbol,
    build_graph,
    compute_closure,
    discover_package_files,
    executed_roots,
    plans_for_keep_set,
)
from haircut.packaging import copy_package_support_files, original_package_bytes, tree_bytes
from haircut.parse import CoverageMap, FileCoverage, dump_coverage, load_trace
from haircut.paths import (
    ensure_package_inits,
    infer_output_root,
    is_app_migration_path,
    path_allowed,
    relative_to_root,
    resolve_path,
    top_package_dir,
)
from haircut.slice import slice_source, validate_python


@dataclass
class SliceReport:
    output_dir: Path
    files_written: int = 0
    files_skipped: int = 0
    unresolved: list[str] = field(default_factory=list)
    functions_original: int = 0
    functions_kept: int = 0
    lines_original: int = 0
    lines_kept: int = 0
    written: list[Path] = field(default_factory=list)
    support_files: int = 0
    original_bytes: int = 0
    slim_bytes: int = 0

    @property
    def function_ratio(self) -> float:
        if not self.functions_original:
            return 0.0
        return self.functions_kept / self.functions_original

    @property
    def line_ratio(self) -> float:
        if not self.lines_original:
            return 0.0
        return self.lines_kept / self.lines_original

    @property
    def bytes_ratio(self) -> float:
        if not self.original_bytes:
            return 0.0
        return self.slim_bytes / self.original_bytes

    def summary(self) -> str:
        lines = [
            "CodeHaircut",
            "===========",
            f"Files written:     {self.files_written}",
            f"Files skipped:     {self.files_skipped}",
            f"Functions kept:    {self.functions_kept} / {self.functions_original}"
            + (f" ({self.function_ratio:.1%})" if self.functions_original else ""),
            f"Lines kept:        {self.lines_kept} / {self.lines_original}"
            + (f" ({self.line_ratio:.1%})" if self.lines_original else ""),
        ]
        if self.original_bytes:
            lines.append(
                f"Bytes kept:        {self.slim_bytes} / {self.original_bytes}"
                + f" ({self.bytes_ratio:.1%})"
            )
        if self.support_files:
            lines.append(
                f"Support files:     {self.support_files} (templates, locales, migrations)"
            )
        lines.append(f"Output:            {self.output_dir}")
        if self.unresolved:
            preview = ", ".join(self.unresolved[:5])
            extra = f" (+{len(self.unresolved) - 5} more)" if len(self.unresolved) > 5 else ""
            lines.append(f"Unresolved paths:  {preview}{extra}")
        return "\n".join(lines)


def load_coverage(trace_path: str | Path) -> CoverageMap:
    return load_trace(trace_path)


def slice_trace(
    trace_path: str | Path,
    output: str | Path,
    *,
    source_roots: Sequence[str | Path] | None = None,
    output_root: str | Path | None = None,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
    prune_branches: bool = False,
    require_source: bool = False,
) -> SliceReport:
    """Slice traced files into *output*, preserving package layout."""
    coverage = load_trace(trace_path)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    roots = [Path(root) for root in (source_roots or [])]
    resolved: list[tuple[Path, str, FileCoverage]] = []
    unresolved: list[str] = []

    for raw_path, file_cov in coverage.files.items():
        if not path_allowed(raw_path, include=include, exclude=exclude):
            continue
        path = _resolve(raw_path, roots)
        if path is None:
            unresolved.append(raw_path)
            continue
        if not path_allowed(str(path), include=include, exclude=exclude):
            continue
        resolved.append((path, raw_path, file_cov))

    if require_source and unresolved:
        raise SourceNotFoundError(
            "Could not resolve traced paths to source files: "
            + ", ".join(unresolved[:8])
        )
    if not resolved:
        raise TraceParseError(
            "No traced files could be resolved to source. "
            "Pass --source with the package root (required for truncated Hunter paths)."
        )

    unique_files = _merge_by_path(resolved)
    strip_root = (
        Path(output_root).resolve()
        if output_root
        else infer_output_root([path for path, _ in unique_files])
    )

    package_dirs = []
    seen_pkgs: set[Path] = set()
    for path, _cov in unique_files:
        pkg = top_package_dir(path)
        resolved_pkg = pkg.resolve()
        if resolved_pkg not in seen_pkgs:
            seen_pkgs.add(resolved_pkg)
            package_dirs.append(pkg)

    package_files = [
        path
        for path in discover_package_files(package_dirs)
        if path_allowed(str(path), include=include, exclude=exclude)
    ]
    graph = build_graph(package_files, strip_root)
    coverage_by_path = {path.resolve(): cov for path, cov in unique_files}
    roots = executed_roots(graph, coverage_by_path)
    roots |= _api_root_symbols(graph, coverage.api)
    traced_modules = [
        graph.by_path[path].name
        for path in coverage_by_path
        if path in graph.by_path
    ]
    traced_modules.extend(module for module, _name in coverage.api)
    keep = compute_closure(graph, roots, seed_modules=traced_modules)
    plans = plans_for_keep_set(graph, keep)

    report = SliceReport(output_dir=output_dir, unresolved=unresolved)
    written: list[Path] = []

    emit_paths = set(plans) | {path.resolve() for path, _ in unique_files}
    for path in sorted(emit_paths):
        if is_app_migration_path(path):
            report.files_skipped += 1
            continue
        plan = plans.get(path)
        if plan is None:
            report.files_skipped += 1
            continue
        index = graph.by_path.get(path)
        traced = path in coverage_by_path
        if index is not None and not traced and not _keep_touches_module(keep, index.name):
            report.files_skipped += 1
            continue
        if not plan.keep_linenos:
            if index is not None and index.is_init and plan.keep_import_asnames:
                pass
            elif traced and plan.keep_import_asnames:
                pass
            else:
                report.files_skipped += 1
                continue
        file_cov = coverage_by_path.get(path) or FileCoverage(path=str(path))
        source = path.read_text(encoding="utf-8", errors="replace")
        result = slice_source(
            source,
            file_cov,
            prune_branches=prune_branches,
            filename=str(path),
            plan=plan,
        )
        report.functions_original += result.original_functions
        report.functions_kept += result.kept_functions
        report.lines_original += result.original_lines
        if not result.kept or not result.source.strip():
            report.files_skipped += 1
            continue
        validate_python(result.source, filename=str(path))
        dest = output_dir / relative_to_root(path, strip_root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(result.source, encoding="utf-8")
        written.append(dest)
        report.files_written += 1
        report.lines_kept += result.kept_lines
        report.written.append(dest)

    copied = copy_package_support_files(written, output_dir, strip_root)
    report.support_files = len(copied)
    ensure_package_inits(output_dir, written)
    report.original_bytes = original_package_bytes(written, output_dir, strip_root)
    report.slim_bytes = tree_bytes(output_dir)
    return report


def merge_traces(paths: Sequence[str | Path], output: str | Path) -> CoverageMap:
    """Union coverage from several traces into one compact JSON file."""
    if not paths:
        raise TraceParseError("Pass at least one trace file to merge.")
    combined = CoverageMap()
    for path in paths:
        combined.merge(load_trace(path))
    dest = Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(dump_coverage(combined), encoding="utf-8")
    return combined


def _keep_touches_module(keep, module_name: str) -> bool:
    """True if a kept symbol lives in *module_name* or a submodule."""
    if not module_name:
        return False
    prefix = module_name + "."
    for symbol in keep:
        if symbol.module == module_name or symbol.module.startswith(prefix):
            return True
    return False


def _api_root_symbols(graph, api: list[tuple[str, str]]) -> set[Symbol]:
    roots: set[Symbol] = set()
    for module, name in api:
        if not module:
            continue
        if name in {"", "*"}:
            index = graph.modules.get(module)
            if name == "*" and index is not None:
                for orig, defn in index.defs.items():
                    if not orig.startswith("_"):
                        roots.add(defn.symbol)
            else:
                roots.add(Symbol(module, ""))
            continue
        roots.add(Symbol(module, name))
        resolved = graph.resolve_name(module, name)
        if resolved is not None:
            roots.add(resolved)
        child = f"{module}.{name}"
        if child in graph.modules:
            roots.add(Symbol(child, ""))
    return roots


def _resolve(raw_path: str, roots: Sequence[Path]) -> Path | None:
    direct = Path(raw_path)
    if direct.is_file():
        return direct.resolve()
    if roots:
        return resolve_path(raw_path, roots)
    return resolve_path(raw_path, [Path.cwd()])


def _merge_by_path(
    resolved: list[tuple[Path, str, FileCoverage]],
) -> list[tuple[Path, FileCoverage]]:
    merged: dict[Path, FileCoverage] = {}
    for path, raw_path, file_cov in resolved:
        existing = merged.get(path)
        if existing is None:
            merged[path] = FileCoverage(
                path=str(path),
                lines=set(file_cov.lines),
                call_lines=set(file_cov.call_lines),
                functions=set(file_cov.functions),
            )
        else:
            existing.lines |= file_cov.lines
            existing.call_lines |= file_cov.call_lines
            existing.functions |= file_cov.functions
    return list(merged.items())
