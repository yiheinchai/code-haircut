# CodeHaircut

Slice a Python package down to the code your program actually executes.

Large libraries ship every edge case. Most programs use a sliver of that surface.
CodeHaircut records a real run, then rebuilds a copy of the package that keeps
only the functions, methods, and (optionally) branches that ran.

The result is valid Python in the original package layout. It is meant for:

- **Reading** the internals that matter for your use case, without the long tail
- **Extracting** a smaller copy of a library when the remaining import graph is simple

It is not a drop-in minifier for something like Django. Complex packages have
import-time side effects and cross-module wiring that a coverage slice will not
fully reconstruct. Use the output as a map of what ran, and as a working subset
when the library is small enough.

## Install

```bash
pip install -e .
```

Requires Python 3.9+.

## Workflow

### 1. Record a run

Trace only the package you care about:

```bash
haircut record -o trace.jsonl --include shop -- examples/app.py
```

Or from Python:

```python
from haircut import Tracer

with Tracer("trace.jsonl", include=["django"]):
    run_app()
```

`haircut record` also accepts `-m package` like `python -m`.

Existing [Python Hunter](https://github.com/ionelmc/python-hunter) CallPrinter
dumps still work. Save the printer output to a file and pass it to `slice`.
Hunter paths are often truncated (`[...]django/db/models/query.py`); pass
`--source` so those suffixes can be matched against real files.

```bash
PYTHONHUNTER='Q(module_startswith=["django"])' python manage.py runserver --noreload --nothreading
haircut slice execution_trace.txt -o slim --source /path/to/django --include django
```

### 2. Slice

```bash
haircut slice trace.jsonl -o slim --include shop
```

JSONL traces from `haircut record` contain absolute paths, so `--source` is
optional. Hunter text traces need `--source`.

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
haircut report trace.jsonl
```

`slice` also prints a summary: files written, functions kept, lines kept.

## What is kept

For each traced source file:

- **Functions and methods** stay if they were called (or any body line ran)
- **Unused functions, methods, and classes** are removed
- **Modules that never ran** are not copied
- **Module-level** imports, constants, and class attributes stay — they run at
  import time and traces often start after that
- **Package `__init__.py` files** are created so the sliced tree still imports

The slicer edits original source by line range. It does not rebuild function
signatures from tracer pretty-printing, so output stays syntactically valid.

## Library API

```python
from haircut import Tracer, slice_trace

with Tracer("trace.jsonl", include=["mypkg"]):
    do_work()

report = slice_trace("trace.jsonl", "slim", include=["mypkg"], prune_branches=True)
print(report.summary())
```

## Demo

```bash
haircut record -o /tmp/shop.jsonl --include shop -- examples/app.py
haircut slice /tmp/shop.jsonl -o /tmp/shop-slim --source examples --include shop --prune-branches
```

`examples/shop` includes catalog lookup, payments, refunds, coupons, and a
warehouse. The demo app only looks up a SKU and charges a card. The sliced copy
drops `Warehouse`, `refund`, `apply_coupon`, and the unused catalog methods.

## Limitations

- Tracing uses `sys.settrace` and is slow. Narrow `--include` to the package
  you want to cut.
- Import-time code that ran before the tracer started will not appear. Start
  the tracer before importing the target package, or accept that untraced
  helpers may be missing.
- Sliced Django (and similar frameworks) will not boot as a replacement
  install. The output is a readable subset of the code that ran.
- Comments attached to deleted functions disappear with those functions.
  `--prune-branches` rewrites control flow and can leave `pass` placeholders.
