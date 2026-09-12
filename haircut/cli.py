"""Command-line interface for CodeHaircut."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from haircut import __version__
from haircut.api import load_coverage, merge_traces, slice_trace
from haircut.errors import HaircutError
from haircut.packaging import apply_slim
from haircut.run import run_target, unwrap_invocation
from haircut.tracer import Tracer


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 1
    try:
        return args.handler(args)
    except HaircutError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="haircut",
        description=(
            "Record how your program uses a library, then rebuild a smaller "
            "copy that contains only the code that actually ran."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    record = sub.add_parser(
        "record",
        help="Run a program and write an execution trace.",
        description=(
            "Run a script or module under a tracer and write coverage. "
            "Interpreter prefixes are stripped, so "
            "`haircut record --include django -- python manage.py test` works."
        ),
    )
    record.add_argument(
        "-o",
        "--output",
        default="trace.json",
        help=(
            "Trace file to write (default: trace.json compact coverage; "
            "use .jsonl for an event log)."
        ),
    )
    _add_filter_args(record)
    record.add_argument(
        "-m",
        dest="module",
        help="Run a module with runpy, like python -m.",
    )
    record.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run, e.g. manage.py test or python manage.py test.",
    )
    record.set_defaults(handler=_cmd_record)

    slice_p = sub.add_parser(
        "slice",
        help="Rebuild a package from a trace, keeping only executed code.",
    )
    slice_p.add_argument("trace", help="Hunter CallPrinter dump or JSONL/JSON trace.")
    _add_slice_output_args(slice_p, default_output="haircutted")
    _add_filter_args(slice_p)
    slice_p.set_defaults(handler=_cmd_slice)

    build = sub.add_parser(
        "build",
        help="Record a run and slice in one step (CI / Docker build).",
        description=(
            "Trace a command, then write a slim package tree. "
            "For Django: `haircut build --django -- manage.py test`."
        ),
    )
    build.add_argument(
        "--django",
        action="store_true",
        help="Include django, default to `manage.py test` if no command is given.",
    )
    build.add_argument(
        "--trace",
        default=".haircut/trace.json",
        help="Where to write the trace (default: .haircut/trace.json).",
    )
    _add_slice_output_args(build, default_output=".haircut/packages")
    _add_filter_args(build)
    build.add_argument(
        "-m",
        dest="module",
        help="Run a module with runpy, like python -m.",
    )
    build.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run, e.g. manage.py test or python manage.py test.",
    )
    build.set_defaults(handler=_cmd_build)

    apply_p = sub.add_parser(
        "apply",
        help="Replace installed packages with a sliced tree (requires --yes).",
    )
    apply_p.add_argument("slim_dir", help="Directory produced by `haircut slice` or `build`.")
    apply_p.add_argument(
        "--yes",
        action="store_true",
        help="Overwrite site-packages. Creates a sibling *.haircut-bak backup.",
    )
    apply_p.set_defaults(handler=_cmd_apply)

    merge = sub.add_parser(
        "merge",
        help="Combine traces from several runs into one coverage file.",
    )
    merge.add_argument("traces", nargs="+", help="Trace files to union.")
    merge.add_argument(
        "-o",
        "--output",
        required=True,
        help="Combined compact coverage JSON to write.",
    )
    merge.set_defaults(handler=_cmd_merge)

    report = sub.add_parser("report", help="Summarize a trace without slicing.")
    report.add_argument("trace", help="Hunter CallPrinter dump or JSONL/JSON trace.")
    report.set_defaults(handler=_cmd_report)

    return parser


def _add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Only include files whose path contains this string. Repeatable.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Skip files whose path contains this string. Repeatable.",
    )


def _add_slice_output_args(parser: argparse.ArgumentParser, *, default_output: str) -> None:
    parser.add_argument(
        "-o",
        "--output",
        default=default_output,
        help=f"Directory to write the sliced package (default: {default_output}).",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Directory to search for original source. Repeatable. "
        "Required for truncated Hunter paths.",
    )
    parser.add_argument(
        "--root",
        help="Path prefix to strip when writing output. Inferred by default.",
    )
    parser.add_argument(
        "--prune-branches",
        action="store_true",
        help="Also drop unexecuted if/else/except bodies inside kept functions.",
    )


def _cmd_record(args: argparse.Namespace) -> int:
    script, module, forwarded = _resolve_run_target(args, default_test=False)
    return _record_run(args.output, args.include, args.exclude, script, module, forwarded)


def _cmd_slice(args: argparse.Namespace) -> int:
    report = slice_trace(
        args.trace,
        args.output,
        source_roots=args.source or None,
        output_root=args.root,
        include=args.include or None,
        exclude=args.exclude or None,
        prune_branches=args.prune_branches,
    )
    print(report.summary())
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    include = list(args.include or [])
    if args.django and not include:
        include = ["django"]
    if not include:
        raise HaircutError("Pass --include PKG (or --django) so the trace stays focused.")
    script, module, forwarded = _resolve_run_target(args, default_test=args.django)
    exit_code = _record_run(args.trace, include, args.exclude, script, module, forwarded)
    if exit_code != 0:
        raise HaircutError(
            f"Recorded command exited with {exit_code}. "
            "Fix the failing run before slicing a production package."
        )
    report = slice_trace(
        args.trace,
        args.output,
        source_roots=args.source or None,
        output_root=args.root,
        include=include,
        exclude=args.exclude or None,
        prune_branches=args.prune_branches,
    )
    print(report.summary())
    print(f"\nReplace the installed package with:\n  haircut apply {args.output} --yes")
    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    results = apply_slim(Path(args.slim_dir), yes=args.yes)
    for name, dest, old, new in results:
        saved = old - new
        print(f"Replaced {name} at {dest}: {old} -> {new} bytes ({saved} saved)")
    return 0


def _cmd_merge(args: argparse.Namespace) -> int:
    coverage = merge_traces(args.traces, args.output)
    print(
        f"Merged {len(args.traces)} traces ({len(coverage.files)} files, "
        f"{coverage.total_lines} lines) into {args.output}"
    )
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    coverage = load_coverage(args.trace)
    files = sorted(coverage.files.values(), key=lambda item: item.path)
    print(f"Files: {len(files)}")
    print(f"Executed lines: {coverage.total_lines}")
    print(f"Call sites: {sum(len(item.call_lines) for item in files)}")
    print()
    for item in files[:50]:
        print(f"  {item.path}: {len(item.lines)} lines, {len(item.functions)} functions")
    if len(files) > 50:
        print(f"  ... {len(files) - 50} more files")
    return 0


def _resolve_run_target(
    args: argparse.Namespace,
    *,
    default_test: bool,
) -> tuple[str | None, str | None, list[str]]:
    command = list(args.command or [])
    if command and command[0] == "--":
        command = command[1:]
    if args.module:
        if command and not str(command[0]).startswith("-"):
            raise HaircutError("Pass a script path or -m MODULE, not both.")
        return unwrap_invocation(None, args.module, command)
    if command:
        return unwrap_invocation(command[0], None, command[1:])
    if default_test:
        manage = Path("manage.py")
        if not manage.is_file():
            raise HaircutError(
                "No manage.py in the current directory. "
                "Pass a command after --, e.g. haircut build --django -- manage.py test"
            )
        return str(manage.resolve()), None, ["test"]
    raise HaircutError("Pass a script path or -m MODULE.")


def _record_run(
    output: str,
    include: Sequence[str],
    exclude: Sequence[str],
    script: str | None,
    module: str | None,
    forwarded: Sequence[str],
) -> int:
    tracer = Tracer(output, include=include, exclude=exclude)
    tracer.start()
    try:
        exit_code = run_target(script, module, forwarded)
    finally:
        tracer.stop()
    print(
        f"Wrote {tracer.events} events across {len(tracer.coverage.files)} files to {output}"
    )
    return exit_code
