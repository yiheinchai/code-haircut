"""Command-line interface for CodeHaircut."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path
from typing import Sequence

from haircut import __version__
from haircut.api import load_coverage, slice_trace
from haircut.errors import HaircutError
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
        description="Run a script or module under a tracer and write JSONL coverage.",
    )
    record.add_argument(
        "-o",
        "--output",
        default="trace.json",
        help="Trace file to write (default: trace.json compact coverage; use .jsonl for an event log).",
    )
    record.add_argument(
        "--include",
        action="append",
        default=[],
        help="Only record files whose path contains this string. Repeatable.",
    )
    record.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Skip files whose path contains this string. Repeatable.",
    )
    record.add_argument(
        "-m",
        dest="module",
        help="Run a module with runpy, like python -m.",
    )
    record.add_argument(
        "script",
        nargs="?",
        help="Python script to run.",
    )
    record.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the script or module.",
    )
    record.set_defaults(handler=_cmd_record)

    slice_p = sub.add_parser(
        "slice",
        help="Rebuild a package from a trace, keeping only executed code.",
    )
    slice_p.add_argument("trace", help="Hunter CallPrinter dump or JSONL trace.")
    slice_p.add_argument(
        "-o",
        "--output",
        default="haircutted",
        help="Directory to write the sliced package (default: haircutted).",
    )
    slice_p.add_argument(
        "--source",
        action="append",
        default=[],
        help="Directory to search for original source. Repeatable. "
        "Required for truncated Hunter paths.",
    )
    slice_p.add_argument(
        "--root",
        help="Path prefix to strip when writing output. Inferred by default.",
    )
    slice_p.add_argument(
        "--include",
        action="append",
        default=[],
        help="Only slice files whose path contains this string. Repeatable.",
    )
    slice_p.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Skip files whose path contains this string. Repeatable.",
    )
    slice_p.add_argument(
        "--prune-branches",
        action="store_true",
        help="Also drop unexecuted if/else/except bodies inside kept functions.",
    )
    slice_p.set_defaults(handler=_cmd_slice)

    report = sub.add_parser("report", help="Summarize a trace without slicing.")
    report.add_argument("trace", help="Hunter CallPrinter dump or JSONL trace.")
    report.set_defaults(handler=_cmd_report)

    return parser


def _cmd_record(args: argparse.Namespace) -> int:
    if bool(args.module) == bool(args.script):
        raise HaircutError("Pass a script path or -m MODULE, not both or neither.")
    forwarded = list(args.script_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    tracer = Tracer(args.output, include=args.include, exclude=args.exclude)
    exit_code = 0
    tracer.start()
    try:
        if args.module:
            sys.argv = [args.module, *forwarded]
            runpy.run_module(args.module, run_name="__main__", alter_sys=True)
        else:
            script = Path(args.script).resolve()
            if not script.is_file():
                raise HaircutError(f"Script not found: {args.script}")
            sys.argv = [str(script), *forwarded]
            sys.path.insert(0, str(script.parent))
            runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        if exc.code is None:
            exit_code = 0
        elif isinstance(exc.code, int):
            exit_code = exc.code
        else:
            exit_code = 1
    finally:
        tracer.stop()

    print(f"Wrote {tracer.events} events across {len(tracer.coverage)} files to {args.output}")
    return exit_code


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
