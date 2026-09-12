"""AST-guided source slicing: keep executed code, drop the rest."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Sequence

from haircut.parse import FileCoverage
from haircut.graph import FilePlan

_BLANK_RE = re.compile(r"\n{3,}")


@dataclass
class FileSliceResult:
    source: str
    kept: bool
    original_functions: int
    kept_functions: int
    original_lines: int
    kept_lines: int


@dataclass
class _Mask:
    n: int
    keep: list[bool]
    replacements: dict[int, str] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    @classmethod
    def from_source(cls, source: str) -> "_Mask":
        lines = source.splitlines(keepends=True)
        if source and not source.endswith("\n"):
            # splitlines(keepends=True) keeps content; treat uniformly later
            pass
        n = len(lines)
        return cls(n=n, keep=[True] * (n + 1), lines=lines)

    def drop(self, start: int | None, end: int | None) -> None:
        if start is None:
            return
        last = end if end is not None else start
        for index in range(start, last + 1):
            if 1 <= index <= self.n:
                self.keep[index] = False
                self.replacements.pop(index, None)

    def put_pass(self, lineno: int) -> None:
        if not (1 <= lineno <= self.n):
            return
        indent = _leading_ws(self.lines[lineno - 1])
        newline = "\n" if self.lines[lineno - 1].endswith("\n") else ""
        self.keep[lineno] = True
        self.replacements[lineno] = f"{indent}pass{newline}"

    def render(self) -> str:
        out: list[str] = []
        for index, line in enumerate(self.lines, start=1):
            if index in self.replacements:
                out.append(self.replacements[index])
            elif self.keep[index]:
                out.append(line)
        text = "".join(out)
        text = _BLANK_RE.sub("\n\n", text)
        return text.strip() + ("\n" if text.strip() else "")


def slice_source(
    source: str,
    coverage: FileCoverage,
    *,
    prune_branches: bool = False,
    filename: str = "<unknown>",
    plan: FilePlan | None = None,
) -> FileSliceResult:
    """Return a valid-Python subset of *source* using *coverage*."""
    original_lines = len(source.splitlines()) or (1 if source else 0)
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return FileSliceResult(
            source=source,
            kept=True,
            original_functions=0,
            kept_functions=0,
            original_lines=original_lines,
            kept_lines=original_lines,
        )

    original_functions = _count_functions(tree)
    mask = _Mask.from_source(source)
    kept_functions = 0
    extra_classes = _same_file_base_closure(tree, coverage, plan)
    support_names = _kept_class_support_names(tree, coverage, plan, extra_classes)

    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _keep_function(stmt, coverage, plan) or stmt.name in support_names:
                kept_functions += 1
                if prune_branches and _function_executed(stmt, coverage):
                    _prune_function(stmt, coverage, mask)
            else:
                start, end = _span(stmt)
                mask.drop(start, end)
        elif isinstance(stmt, ast.ClassDef):
            kept_in_class = _slice_class(
                stmt, coverage, mask, prune_branches, plan, extra_classes
            )
            kept_functions += kept_in_class
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)) and plan is not None:
            _apply_import_plan(stmt, plan, mask, source, extra_asnames=support_names)
        elif plan is not None and _is_dunder_all(stmt):
            _rewrite_dunder_all(stmt, plan, mask)

    text = mask.render()
    if not text.strip():
        return FileSliceResult(
            source="",
            kept=False,
            original_functions=original_functions,
            kept_functions=0,
            original_lines=original_lines,
            kept_lines=0,
        )

    kept_functions = max(kept_functions, 0)
    kept_lines = len(text.splitlines())
    return FileSliceResult(
        source=text,
        kept=True,
        original_functions=original_functions,
        kept_functions=min(kept_functions, original_functions),
        original_lines=original_lines,
        kept_lines=kept_lines,
    )


def _keep_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    coverage: FileCoverage,
    plan: FilePlan | None,
) -> bool:
    if plan is not None:
        start, _ = _span(node)
        return node.lineno in plan.keep_linenos or start in plan.keep_linenos
    return _function_executed(node, coverage)


def _is_protocol_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__") and len(name) > 4


def _same_file_base_closure(
    tree: ast.Module,
    coverage: FileCoverage,
    plan: FilePlan | None,
) -> set[str]:
    classes = [stmt for stmt in tree.body if isinstance(stmt, ast.ClassDef)]
    by_name = {cls.name: cls for cls in classes}
    kept: set[str] = set()
    for cls in classes:
        if plan is not None and cls.lineno in plan.keep_linenos:
            kept.add(cls.name)
            continue
        if any(
            _keep_function(stmt, coverage, plan)
            for stmt in cls.body
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            kept.add(cls.name)
    changed = True
    while changed:
        changed = False
        for name in list(kept):
            cls = by_name.get(name)
            if cls is None:
                continue
            for base in cls.bases:
                if isinstance(base, ast.Name) and base.id in by_name and base.id not in kept:
                    kept.add(base.id)
                    changed = True
    return kept


def _class_is_kept(
    node: ast.ClassDef,
    coverage: FileCoverage,
    plan: FilePlan | None,
    extra_classes: set[str],
) -> bool:
    if node.name in extra_classes:
        return True
    if plan is not None and node.lineno in plan.keep_linenos:
        return True
    return any(
        _keep_function(stmt, coverage, plan)
        for stmt in node.body
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def _expr_root_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        names.add(node.value.id)
    elif isinstance(node, ast.Call):
        names.update(_expr_root_names(node.func))
        for arg in node.args:
            names.update(_expr_root_names(arg))
        for keyword in node.keywords:
            if keyword.value is not None:
                names.update(_expr_root_names(keyword.value))
    return names


def _kept_class_support_names(
    tree: ast.Module,
    coverage: FileCoverage,
    plan: FilePlan | None,
    extra_classes: set[str],
) -> set[str]:
    names: set[str] = set()
    for stmt in tree.body:
        if not isinstance(stmt, ast.ClassDef):
            continue
        if not _class_is_kept(stmt, coverage, plan, extra_classes):
            continue
        for deco in stmt.decorator_list:
            names.update(_expr_root_names(deco))
        for base in stmt.bases:
            names.update(_expr_root_names(base))
        for keyword in stmt.keywords:
            if keyword.value is not None:
                names.update(_expr_root_names(keyword.value))
    return names


def _slice_class(
    node: ast.ClassDef,
    coverage: FileCoverage,
    mask: _Mask,
    prune_branches: bool,
    plan: FilePlan | None = None,
    extra_classes: set[str] | None = None,
) -> int:
    force = (plan is not None and node.lineno in plan.keep_linenos) or (
        extra_classes is not None and node.name in extra_classes
    )
    kept_names = {
        stmt.name
        for stmt in node.body
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
        and _keep_function(stmt, coverage, plan)
    }
    will_keep = bool(kept_names) or force
    if will_keep:
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_protocol_dunder(
                stmt.name
            ):
                kept_names.add(stmt.name)
    kept_methods = 0
    for stmt in node.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _keep_function(stmt, coverage, plan) or stmt.name in kept_names:
                kept_methods += 1
                if prune_branches and _function_executed(stmt, coverage):
                    _prune_function(stmt, coverage, mask)
            else:
                start, end = _span(stmt)
                mask.drop(start, end)
        elif isinstance(stmt, ast.ClassDef):
            kept_methods += _slice_class(
                stmt, coverage, mask, prune_branches, plan, extra_classes
            )
    if kept_methods == 0 and not force:
        mask.drop(*_span(node))
        return 0
    if kept_methods == 0 and force:
        remaining = [
            stmt
            for stmt in node.body
            if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        if not remaining and node.body:
            mask.put_pass(node.body[0].lineno)
        return 1
    return kept_methods


def _function_executed(node: ast.FunctionDef | ast.AsyncFunctionDef, coverage: FileCoverage) -> bool:
    end = node.end_lineno or node.lineno
    if coverage.call_lines & set(range(node.lineno, end + 1)):
        return True
    if not node.body:
        return False
    body_start = node.body[0].lineno
    return bool(coverage.lines & set(range(body_start, end + 1)))


def _prune_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    coverage: FileCoverage,
    mask: _Mask,
) -> int:
    body = list(node.body)
    if body and _is_docstring(body[0]):
        body = body[1:]
    _prune_stmts(body, coverage, mask)
    return 0


def _prune_stmts(
    stmts: Sequence[ast.stmt],
    coverage: FileCoverage,
    mask: _Mask,
) -> bool:
    kept_any = False
    for stmt in stmts:
        if _keep_stmt(stmt, coverage, mask):
            kept_any = True
        else:
            start, end = _span(stmt) if isinstance(
                stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) else (stmt.lineno, stmt.end_lineno)
            mask.drop(start, end)
    return kept_any


def _keep_stmt(stmt: ast.stmt, coverage: FileCoverage, mask: _Mask) -> bool:
    if _is_docstring(stmt):
        return True

    if isinstance(stmt, ast.If):
        body_kept = _prune_stmts(stmt.body, coverage, mask)
        else_kept = _prune_stmts(stmt.orelse, coverage, mask) if stmt.orelse else False
        if body_kept and else_kept:
            return True
        if body_kept:
            _drop_after_body(stmt, mask)
            return True
        if else_kept:
            _ensure_pass(stmt.body, mask)
            return True
        return False

    if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
        body_kept = _prune_stmts(stmt.body, coverage, mask)
        else_kept = _prune_stmts(stmt.orelse, coverage, mask) if stmt.orelse else False
        header_hit = _header_covered(stmt, stmt.body, coverage)
        if not (body_kept or else_kept or header_hit):
            return False
        if not body_kept:
            _ensure_pass(stmt.body, mask)
        if not else_kept:
            _drop_after_body(stmt, mask)
        return True

    if isinstance(stmt, (ast.With, ast.AsyncWith)):
        body_kept = _prune_stmts(stmt.body, coverage, mask)
        if not (body_kept or _header_covered(stmt, stmt.body, coverage)):
            return False
        if not body_kept:
            _ensure_pass(stmt.body, mask)
        return True

    if isinstance(stmt, ast.Try):
        if not _overlaps(stmt, coverage.lines):
            return False
        body_kept = _prune_stmts(stmt.body, coverage, mask)
        if not body_kept:
            _ensure_pass(stmt.body, mask)
        for handler in stmt.handlers:
            handler_kept = _prune_stmts(handler.body, coverage, mask)
            if not handler_kept:
                _ensure_pass(handler.body, mask)
        if stmt.orelse:
            else_kept = _prune_stmts(stmt.orelse, coverage, mask)
            if not else_kept:
                _drop_try_else(stmt, mask)
        if stmt.finalbody:
            final_kept = _prune_stmts(stmt.finalbody, coverage, mask)
            if not final_kept:
                _ensure_pass(stmt.finalbody, mask)
        return True

    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if _function_executed(stmt, coverage):
            _prune_function(stmt, coverage, mask)
            return True
        return False

    if isinstance(stmt, ast.ClassDef):
        return _slice_class(stmt, coverage, mask, prune_branches=True, plan=None) > 0

    if hasattr(ast, "Match") and isinstance(stmt, ast.Match):
        return _keep_match(stmt, coverage, mask)

    return _overlaps(stmt, coverage.lines)


def _keep_match(stmt: ast.AST, coverage: FileCoverage, mask: _Mask) -> bool:
    cases = getattr(stmt, "cases", [])
    kept_any = False
    for case in cases:
        body_kept = _prune_stmts(case.body, coverage, mask)
        if body_kept or _overlaps(case, coverage.lines):
            kept_any = True
            if not body_kept:
                _ensure_pass(case.body, mask)
        else:
            mask.drop(case.pattern.lineno, case.body[-1].end_lineno if case.body else case.pattern.lineno)
    return kept_any or _overlaps(stmt, coverage.lines)


def _drop_after_body(stmt: ast.stmt, mask: _Mask) -> None:
    orelse = getattr(stmt, "orelse", None)
    if not orelse:
        return
    body = getattr(stmt, "body", None)
    if not body:
        mask.drop(orelse[0].lineno, stmt.end_lineno)
        return
    start = (body[-1].end_lineno or body[-1].lineno) + 1
    mask.drop(start, stmt.end_lineno)


def _drop_try_else(stmt: ast.Try, mask: _Mask) -> None:
    if not stmt.orelse:
        return
    start = (stmt.body[-1].end_lineno or stmt.body[-1].lineno) + 1
    if stmt.handlers:
        start = (stmt.handlers[-1].end_lineno or start)
        start += 1
    end = stmt.orelse[-1].end_lineno or stmt.orelse[-1].lineno
    if stmt.finalbody:
        end = (stmt.orelse[-1].end_lineno or end)
    mask.drop(start, end)


def _ensure_pass(body: Sequence[ast.stmt], mask: _Mask) -> None:
    if not body:
        return
    first = body[0]
    if first.end_lineno and first.end_lineno > first.lineno:
        mask.drop(first.lineno + 1, first.end_lineno)
    mask.put_pass(first.lineno)


def _header_covered(
    stmt: ast.stmt,
    body: Sequence[ast.stmt],
    coverage: FileCoverage,
) -> bool:
    start = stmt.lineno
    end = (body[0].lineno - 1) if body else (stmt.end_lineno or stmt.lineno)
    if end < start:
        end = start
    return bool(coverage.lines & set(range(start, end + 1)))


def _overlaps(node: ast.AST, lines: set[int]) -> bool:
    lineno = getattr(node, "lineno", None)
    if lineno is None:
        return False
    end = getattr(node, "end_lineno", None) or lineno
    return bool(lines & set(range(lineno, end + 1)))


def _is_docstring(stmt: ast.stmt) -> bool:
    if not isinstance(stmt, ast.Expr):
        return False
    value = stmt.value
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return True
    return False


def _count_functions(node: ast.AST) -> int:
    total = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += 1
    return total


def _span(node: ast.AST) -> tuple[int, int]:
    start = getattr(node, "lineno", 1)
    for deco in getattr(node, "decorator_list", ()) or ():
        lineno = getattr(deco, "lineno", None)
        if lineno:
            start = min(start, lineno)
    return start, getattr(node, "end_lineno", None) or start


def _leading_ws(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def _is_dunder_all(stmt: ast.stmt) -> bool:
    if not isinstance(stmt, ast.Assign):
        return False
    return any(isinstance(target, ast.Name) and target.id == "__all__" for target in stmt.targets)


def _rewrite_dunder_all(stmt: ast.Assign, plan: FilePlan, mask: _Mask) -> None:
    names = [
        value.value
        for value in ast.walk(stmt)
        if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value in plan.keep_names
    ]
    indent = _leading_ws(mask.lines[stmt.lineno - 1])
    newline = "\n" if mask.lines[stmt.lineno - 1].endswith("\n") else ""
    mask.drop(stmt.lineno, stmt.end_lineno)
    rendered = ", ".join(repr(name) for name in names)
    mask.replacements[stmt.lineno] = f"{indent}__all__ = [{rendered}]{newline}"


def validate_python(source: str, filename: str = "<sliced>") -> None:
    ast.parse(source, filename=filename)


def _apply_import_plan(
    stmt: ast.Import | ast.ImportFrom,
    plan: FilePlan,
    mask: _Mask,
    source: str,
    extra_asnames: set[str] | None = None,
) -> None:
    needed = plan.keep_import_asnames | (extra_asnames or set())
    if (
        stmt.lineno in plan.drop_import_linenos
        and stmt.lineno not in plan.star_names
        and not _import_provides(stmt, needed)
    ):
        mask.drop(stmt.lineno, stmt.end_lineno)
        return
    if stmt.lineno in plan.star_names and isinstance(stmt, ast.ImportFrom):
        names = plan.star_names[stmt.lineno]
        indent = _leading_ws(mask.lines[stmt.lineno - 1])
        module = stmt.module or ""
        dots = "." * stmt.level
        newline = "\n" if mask.lines[stmt.lineno - 1].endswith("\n") else ""
        mask.drop(stmt.lineno, stmt.end_lineno)
        mask.put_pass(stmt.lineno)
        mask.replacements[stmt.lineno] = (
            f"{indent}from {dots}{module} import {', '.join(names)}{newline}"
        )
        return
    if isinstance(stmt, ast.ImportFrom) and stmt.names and needed:
        kept = [
            alias
            for alias in stmt.names
            if (alias.asname or alias.name) in needed
        ]
        if not kept:
            mask.drop(stmt.lineno, stmt.end_lineno)
            return
        if len(kept) == len(stmt.names):
            return
        indent = _leading_ws(mask.lines[stmt.lineno - 1])
        module = stmt.module or ""
        dots = "." * stmt.level
        parts = []
        for alias in kept:
            if alias.asname:
                parts.append(f"{alias.name} as {alias.asname}")
            else:
                parts.append(alias.name)
        newline = "\n" if mask.lines[stmt.lineno - 1].endswith("\n") else ""
        mask.drop(stmt.lineno, stmt.end_lineno)
        mask.replacements[stmt.lineno] = (
            f"{indent}from {dots}{module} import {', '.join(parts)}{newline}"
        )


def _import_provides(stmt: ast.Import | ast.ImportFrom, needed: set[str]) -> bool:
    return any((alias.asname or alias.name.split(".")[0]) in needed for alias in stmt.names)
