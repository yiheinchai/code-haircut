# CodeHaircut

Slice a Python package down to the code your program actually executes.

Large libraries ship every edge case. Most programs use a sliver of that surface.
CodeHaircut records a real run, then rebuilds a copy of the package that keeps
only the functions, methods, helpers, and re-exports required for that run.

The result is valid Python in the original package layout. On a Django
ContentType create/get, that is typically about a fifth of the install: unused
backends, admin, GIS, and uncalled APIs are omitted, and the same script still
runs against the sliced tree.

## Install

```bash
pip install -e .
```

Requires Python 3.9+. `sys.monitoring` is used automatically on 3.12+ so large
libraries stay practical to trace.

## Workflow

### 1. Record a run

Trace only the package you care about. Start the tracer *before* the library is
imported. Compact `trace.json` stores unique file/line sets; use `.jsonl` only
if you need the per-event log.

```bash
haircut record -o trace.json --include django -- myapp.py
```

Or from Python:

```python
from haircut import Tracer

with Tracer("trace.json", include=["django"]):
    run_app()
```

`haircut record` also accepts `-m package` like `python -m`.

Existing [Python Hunter](https://github.com/ionelmc/python-hunter) CallPrinter
dumps still work. Hunter paths are often truncated (`[...]django/db/models/query.py`);
pass `--source` so those suffixes can be matched against real files.

```bash
PYTHONHUNTER='Q(module_startswith=["django"])' python manage.py runserver --noreload --nothreading
haircut slice execution_trace.txt -o slim --source /path/to/django --include django
```

### 2. Slice

```bash
haircut slice trace.json -o slim --include django
```

JSON traces from `haircut record` contain absolute paths, so `--source` is
optional. Hunter text traces need `--source`.

The slicer then takes the **static closure** of what ran: helpers called by
kept methods, base classes, and package re-exports. Modules that were imported
only because an `__init__.py` pulled them in, and never used, are dropped and
those imports are rewritten.

Useful flags:

| Flag | Meaning |
| --- | --- |
| `--source DIR` | Search here for original source (repeatable) |
| `--include TEXT` | Only slice files whose path contains this string |
| `--exclude TEXT` | Skip matching files |
| `--prune-branches` | Also drop `if`/`else`/`except` bodies that never ran |
| `--root DIR` | Prefix to strip when writing output (inferred by default) |

Without `--prune-branches`, a kept function is copied in full. That preserves
comments and unexecuted fallbacks, and the result is more likely to still run
for nearby inputs. With `--prune-branches`, unread branches disappear so the
file shows only the path you took.

### 3. Inspect

```bash
haircut report trace.json
```

`slice` also prints a summary: files written, functions kept, lines kept.

Put the output directory on `PYTHONPATH` *ahead* of the original install to
run the same program against the sliced package.

## What is kept

- **Functions and methods** that were called
- **Helpers, bases, and re-exports** they still need (even if those helpers
  were not themselves the API you called)
- **Unused functions, methods, classes, and subsystems** (admin, GIS, unused
  backends, …) are removed
- **Package `__init__.py` files** are rewritten so they only import names the
  remaining code uses

The slicer edits original source by line range. It does not rebuild function
signatures from tracer pretty-printing, so output stays syntactically valid.

## Library API

```python
from haircut import Tracer, slice_trace

with Tracer("trace.json", include=["django"]):
    do_work()

report = slice_trace("trace.json", "slim", include=["django"])
print(report.summary())
```

## Demos

Shop catalog (small library):

```bash
haircut record -o /tmp/shop.json --include shop -- examples/app.py
haircut slice /tmp/shop.json -o /tmp/shop-slim --source examples --include shop --prune-branches
```

Django ORM (large library):

```bash
haircut record -o /tmp/django.json --include django -- tests/fixtures/django_workload.py
haircut slice /tmp/django.json -o /tmp/django-slim --include django
PYTHONPATH=/tmp/django-slim python tests/fixtures/django_workload.py
```

## Limitations

- Narrow `--include` to the package you want to cut. Tracing the whole process
  is slow even with `sys.monitoring`.
- Import-time code that ran before the tracer started will not appear. Record
  the program from process start (`haircut record -- script.py`).
- Dynamic dispatch that never ran (an unused model field, an uncalled signal)
  is not kept. A sliced Django is a replacement for the *traced* use case, not
  a general Django install.
- Comments attached to deleted functions disappear with those functions.
  `--prune-branches` rewrites control flow and can leave `pass` placeholders.
