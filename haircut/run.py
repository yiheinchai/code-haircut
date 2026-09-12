"""Run a user program in-process so the tracer sees the real import graph."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path
from typing import Sequence

from haircut.errors import HaircutError

_INTERPRETER_NAMES = {
    "python",
    "python3",
    "python.exe",
    "py",
    "pypy",
    "pypy3",
}
_FLAGS_WITH_VALUE = {"-m", "-c", "-W", "-X", "--check-hash-based-pycs"}


def looks_like_interpreter(script: str) -> bool:
    name = Path(script).name.lower()
    if name in _INTERPRETER_NAMES:
        return True
    if script == sys.executable:
        return True
    if name.startswith("python"):
        rest = name[len("python") :]
        return not rest or set(rest) <= set("0123456789.-")
    return False


def should_unwrap_interpreter(script: str) -> bool:
    if not looks_like_interpreter(script):
        return False
    path = Path(script)
    if path.is_file() and path.suffix == ".py":
        return False
    return True


def strip_interpreter_flags(args: Sequence[str]) -> list[str]:
    """Drop CPython flags so ``python -u manage.py test`` still finds the script."""
    args = list(args)
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--":
            return args[index + 1 :]
        if item in ("-m", "-c"):
            return args[index:]
        if item.startswith("-") and item != "-":
            flag = item.split("=", 1)[0]
            takes_value = item in _FLAGS_WITH_VALUE or flag in {"-W", "-X"}
            if takes_value and "=" not in item:
                index += 2
            else:
                index += 1
            continue
        return args[index:]
    return []


def unwrap_invocation(
    script: str | None,
    module: str | None,
    forwarded: Sequence[str],
) -> tuple[str | None, str | None, list[str]]:
    """Normalize ``python manage.py test`` / ``python -m pytest`` to an in-process target."""
    forwarded = list(forwarded)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    if module:
        if script:
            raise HaircutError("Pass a script path or -m MODULE, not both.")
        return None, module, forwarded
    if not script:
        raise HaircutError("Pass a script path or -m MODULE.")
    if not should_unwrap_interpreter(script):
        return script, None, forwarded
    rest = strip_interpreter_flags(forwarded)
    if rest and rest[0] == "-m":
        if len(rest) < 2:
            raise HaircutError("python -m requires a module name.")
        return None, rest[1], rest[2:]
    if rest and rest[0] == "-c":
        raise HaircutError("python -c is not supported; pass a script or -m MODULE.")
    if not rest:
        raise HaircutError(
            "Pass a script after the interpreter, e.g. python manage.py test"
        )
    return rest[0], None, rest[1:]


def run_target(script: str | None, module: str | None, forwarded: Sequence[str]) -> int:
    """Execute *script* or *module* with runpy. Returns the process-style exit code."""
    forwarded = list(forwarded)
    try:
        if module:
            sys.argv = [module, *forwarded]
            runpy.run_module(module, run_name="__main__", alter_sys=True)
        elif script:
            path = Path(script)
            if not path.is_file():
                raise HaircutError(f"Script not found: {script}")
            resolved = str(path.resolve())
            sys.argv = [resolved, *forwarded]
            sys.path.insert(0, str(path.resolve().parent))
            runpy.run_path(resolved, run_name="__main__")
        else:
            raise HaircutError("Pass a script path or -m MODULE.")
    except SystemExit as exc:
        if exc.code is None:
            return 0
        if isinstance(exc.code, int):
            return exc.code
        return 1
    return 0
