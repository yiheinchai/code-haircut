# CodeHaircut

Slice a Python package down to the code your program actually executes.

Large libraries ship every edge case. Most programs use a sliver of that surface.
CodeHaircut records a real run — your tests, your management command, your
WSGI load — then rebuilds a copy of the package that keeps only the functions,
methods, helpers, re-exports, templates, locales, and migrations that run needed.

The result is valid Python in the original package layout. On a Django polls
app (models, templates, the test client, `migrate` via `TestCase`), unused
admin, GIS, and unused backends are omitted. The same `manage.py test` still
passes against the sliced tree, and the install is substantially smaller.

That is the production use case: add CodeHaircut as a **build step**, record
the suite you already trust, replace site-packages Django, and ship the slim
copy.

## Install

```bash
pip install -e ".[dev]"
```

Requires Python 3.9+. `sys.monitoring` is used automatically on 3.12+ so large
libraries stay practical to trace.

## Production workflow (Django)

Record the tests that represent production behavior, slice Django, then swap
the install. Interpreter prefixes are stripped, so the command you already run
works unchanged.

```bash
# from your Django project (the directory that contains manage.py)
haircut build --django -- python manage.py test
haircut apply .haircut/packages --yes
```

`haircut build --django`:

1. Traces only `django` (override with `--include` if you also cut another package)
2. Defaults to `manage.py test` when you pass no command
3. Writes compact coverage to `.haircut/trace.json`
4. Emits the slim tree to `.haircut/packages`
5. Copies package data (`templates/`, `locale/`, `static/`) and **copies app
   migrations intact** (`django.contrib.auth.migrations`, …). Slicing those
   files would break `migrate` / `TestCase`.

`haircut apply --yes` overwrites the installed package and leaves a sibling
`*.haircut-bak` backup.

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt code-haircut
COPY . /app
RUN haircut build --django -- python manage.py test \
 && haircut apply .haircut/packages --yes \
 && rm -rf .haircut
EXPOSE 8000
CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000"]
```

A complete example lives at `examples/pollsite/` (models, views, templates,
migrations, tests). Build it from the repository root:

```bash
docker build -f examples/pollsite/Dockerfile .
```

Or without Docker:

```bash
pip install -e ".[dev]"
cd examples/pollsite
haircut build --django -- python manage.py test
PYTHONPATH=.haircut/packages python manage.py test
```

### CI

Keep the full Django install in CI so the suite is the source of truth. Use
the sliced copy only when building the image you deploy:

```yaml
- run: pip install -e ".[dev]"
- run: python examples/pollsite/manage.py test
- run: |
    haircut build --django -o /tmp/slim -- python examples/pollsite/manage.py test
    # optional: PYTHONPATH=/tmp/slim python examples/pollsite/manage.py test
```

Merge traces when one job cannot cover every entrypoint:

```bash
haircut record -o orm.json --include django -- python manage.py test polls
haircut record -o http.json --include django -- python manage.py test polls.tests.PollsTests
haircut merge orm.json http.json -o combined.json
haircut slice combined.json -o slim --include django
```

## What is kept

- **Functions and methods** that were called
- **Public names your app imported** from the library (`from django.urls
  import path`, `models.CharField`, …), even when Django itself never
  called them
- **Helpers, bases, and re-exports** they still need (even if those helpers
  were not themselves the API you called)
- **Package data**: templates, locales, static files, and other non-`.py`
  sidecars next to kept modules
- **App migrations**, copied verbatim so `migrate` / `TestCase` keep working
- **Unused functions, methods, classes, and subsystems** (admin, GIS, unused
  backends, …) are removed
- **Package `__init__.py` files** are rewritten so they only import names the
  remaining code uses

The slicer edits original source by line range. It does not rebuild function
signatures from tracer pretty-printing, so output stays syntactically valid.
`slice` / `build` print files kept, lines kept, and **bytes kept** against the
original package.

## Library API

```python
from haircut import Tracer, slice_trace, merge_traces, apply_slim

with Tracer("trace.json", include=["django"]):
    run_app()

report = slice_trace("trace.json", "slim", include=["django"])
print(report.summary())
```

## Demos

Shop catalog (small library):

```bash
haircut record -o /tmp/shop.json --include shop -- examples/app.py
haircut slice /tmp/shop.json -o /tmp/shop-slim --source examples --include shop --prune-branches
```

Django ORM (ContentType smoke test):

```bash
haircut record -o /tmp/django.json --include django -- tests/fixtures/django_workload.py
haircut slice /tmp/django.json -o /tmp/django-slim --include django
PYTHONPATH=/tmp/django-slim python tests/fixtures/django_workload.py
```

Django application (polls site, the production shape):

```bash
cd examples/pollsite
haircut build --django -- python manage.py test
PYTHONPATH=.haircut/packages python manage.py test
```

## Commands

| Command | Purpose |
| --- | --- |
| `haircut record` | Trace a command (`python manage.py test` is fine) |
| `haircut slice` | Rebuild a package from a trace |
| `haircut build` | Record + slice (use `--django` in a project) |
| `haircut apply` | Replace the installed package (`--yes` required) |
| `haircut merge` | Union several traces |
| `haircut report` | Summarize a trace without slicing |

Useful flags:

| Flag | Meaning |
| --- | --- |
| `--django` | `build` only: include `django`, default command `manage.py test` |
| `--source DIR` | Search here for original source (repeatable) |
| `--include TEXT` | Only include files whose path contains this string |
| `--exclude TEXT` | Skip matching files |
| `--prune-branches` | Also drop `if`/`else`/`except` bodies that never ran |
| `--root DIR` | Prefix to strip when writing output (inferred by default) |

Without `--prune-branches`, a kept function is copied in full. That preserves
comments and unexecuted fallbacks, and the result is more likely to still run
for nearby inputs. With `--prune-branches`, unread branches disappear so the
file shows only the path you took.

Existing [Python Hunter](https://github.com/ionelmc/python-hunter) CallPrinter
dumps still work. Hunter paths are often truncated (`[...]django/db/models/query.py`);
pass `--source` so those suffixes can be matched against real files.

## Limitations

- Narrow `--include` to the package you want to cut. Tracing the whole process
  is slow even with `sys.monitoring`.
- Import-time code that ran before the tracer started will not appear. Record
  the program from process start (`haircut record -- script.py`).
- Dynamic dispatch that never ran (an unused model field, an uncalled signal)
  is not kept. A sliced Django is a replacement for the *traced* use case, not
  a general Django install. Trace every entrypoint you deploy (tests, plus a
  management command or WSGI ping if those paths differ).
- Comments attached to deleted functions disappear with those functions.
  `--prune-branches` rewrites control flow and can leave `pass` placeholders.
- `haircut apply` replaces site-packages. Use it in an image build or a
  dedicated venv, not on a shared developer install you still need intact.
