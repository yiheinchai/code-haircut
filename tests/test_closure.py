import ast
import sys
from pathlib import Path

from haircut.api import slice_trace
from haircut.tracer import Tracer

FIXTURES = Path(__file__).parent / "fixtures"


def test_closure_keeps_helpers_and_drops_unused_subsystems(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from biglib.models import Model

    with Tracer(trace, include=["biglib"]):
        assert Model().save("  ok  ") == "ok"

    output = tmp_path / "slim"
    report = slice_trace(trace, output, include=["biglib"])
    assert report.files_written >= 2

    base = (output / "biglib" / "models" / "base.py").read_text(encoding="utf-8")
    ast.parse(base)
    assert "def prepare" in base
    assert "def save" in base
    assert "def unused_helper" not in base
    assert "def delete" not in base

    models_init = (output / "biglib" / "models" / "__init__.py").read_text(encoding="utf-8")
    assert "aggregates" not in models_init
    assert "from .base import Model" in models_init

    assert not (output / "biglib" / "http").exists() or not any(
        (output / "biglib" / "http").rglob("*.py")
    )
    assert not (output / "biglib" / "models" / "aggregates.py").exists()

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "biglib" or name.startswith("biglib."):
                sys.modules.pop(name)
        from biglib.models import Model as SlicedModel

        assert SlicedModel().save("  ok  ") == "ok"
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "biglib" or name.startswith("biglib."):
                sys.modules.pop(name)


def test_closure_keeps_methods_aliased_on_module_instances(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from aliaspkg import main

    with Tracer(trace, include=["aliaspkg"]):
        assert main() == "ran"

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["aliaspkg"])
    source = (output / "aliaspkg" / "registry.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "def run" in source
    assert "def tag_exists" in source
    assert "def unused_method" not in source

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "aliaspkg" or name.startswith("aliaspkg."):
                sys.modules.pop(name)
        from aliaspkg.registry import run, tag_exists

        assert run() == "ran"
        assert tag_exists("ok") is True
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "aliaspkg" or name.startswith("aliaspkg."):
                sys.modules.pop(name)


def test_closure_keeps_imported_names_that_shadow_builtins(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from warnpkg.check import run

    with Tracer(trace, include=["warnpkg"]):
        assert run() == "W001"

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["warnpkg"])
    check = (output / "warnpkg" / "check.py").read_text(encoding="utf-8")
    messages = (output / "warnpkg" / "messages.py").read_text(encoding="utf-8")
    ast.parse(check)
    ast.parse(messages)
    assert "from .messages import Warning" in check
    assert "class Warning" in messages
    assert "class UnusedWarning" not in messages

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "warnpkg" or name.startswith("warnpkg."):
                sys.modules.pop(name)
        from warnpkg.check import run as sliced_run

        assert sliced_run() == "W001"
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "warnpkg" or name.startswith("warnpkg."):
                sys.modules.pop(name)


def test_closure_keeps_property_helpers_on_class(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from proppkg.file import run

    with Tracer(trace, include=["proppkg"]):
        assert run() == "file.txt"

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["proppkg"])
    source = (output / "proppkg" / "file.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "def _get_name" in source
    assert "def _set_name" in source
    assert "name = property" in source
    assert "def unused" not in source

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "proppkg" or name.startswith("proppkg."):
                sys.modules.pop(name)
        from proppkg.file import run as sliced_run

        assert sliced_run() == "file.txt"
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "proppkg" or name.startswith("proppkg."):
                sys.modules.pop(name)


def test_closure_keeps_classes_named_in_dotted_strings(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from dottedpkg.log import configure

    with Tracer(trace, include=["dottedpkg"]):
        assert configure() == "dottedpkg.log.RequireDebugFalse"

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["dottedpkg"])
    source = (output / "dottedpkg" / "log.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "class RequireDebugFalse" in source
    assert "class UnusedHandler" not in source

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "dottedpkg" or name.startswith("dottedpkg."):
                sys.modules.pop(name)
        from dottedpkg.log import RequireDebugFalse, configure as sliced_configure

        assert sliced_configure() == "dottedpkg.log.RequireDebugFalse"
        assert RequireDebugFalse().filter(None) is True
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "dottedpkg" or name.startswith("dottedpkg."):
                sys.modules.pop(name)


def test_closure_keeps_singleton_class_rebound_to_instance(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from singletonpkg.tokens import parse

    with Tracer(trace, include=["singletonpkg"]):
        assert parse().nud(None) is parse()

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["singletonpkg"])
    source = (output / "singletonpkg" / "tokens.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "class EndToken" in source
    assert "EndToken = EndToken()" in source
    assert "class UnusedToken" not in source

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "singletonpkg" or name.startswith("singletonpkg."):
                sys.modules.pop(name)
        from singletonpkg.tokens import parse as sliced_parse

        token = sliced_parse()
        assert token.nud(None) is token
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "singletonpkg" or name.startswith("singletonpkg."):
                sys.modules.pop(name)


def test_closure_keeps_dunder_methods_on_kept_classes(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from dunderpkg.widget import run

    with Tracer(trace, include=["dunderpkg"]):
        assert run() == "rendered"

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["dunderpkg"])
    source = (output / "dunderpkg" / "widget.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "def __str__" in source
    assert "def render" in source
    assert "def open" in source
    assert "def unused" not in source


def test_star_import_only_reexports_kept_local_defs(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from starpkg import Kept

    with Tracer(trace, include=["starpkg"]):
        assert Kept().run() == "ok"

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["starpkg"])
    init = (output / "starpkg" / "__init__.py").read_text(encoding="utf-8")
    ast.parse(init)
    assert "Kept" in init
    assert "BytesIO" not in init
    assert "Unused" not in init
    assert "_private" not in init


def test_submodule_import_keeps_attribute_classes(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from attrpkg.expr import run

    with Tracer(trace, include=["attrpkg"]):
        assert run() == 1

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["attrpkg"])
    source = (output / "attrpkg" / "fields.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "class PositiveIntegerField" in source
    assert "class CharField" in source
    assert "class UnusedField" not in source


def test_closure_keeps_html_safe_str_on_unused_base(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from htmlsafepkg.assets import run

    with Tracer(trace, include=["htmlsafepkg"]):
        assert run() == "label"

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["htmlsafepkg"])
    source = (output / "htmlsafepkg" / "assets.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "@html_safe" in source
    assert "class MediaAsset" in source
    assert "def __str__" in source
    assert "def unused" not in source

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "htmlsafepkg" or name.startswith("htmlsafepkg."):
                sys.modules.pop(name)
        from htmlsafepkg.assets import MediaAsset, Script, run as sliced_run

        assert sliced_run() == "label"
        assert str(MediaAsset("x.js")) == "x.js"
        assert Script.label.__name__ == "label"
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "htmlsafepkg" or name.startswith("htmlsafepkg."):
                sys.modules.pop(name)


def test_closure_keeps_lazy_imports_inside_kept_functions(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURES))
    trace = tmp_path / "trace.json"

    from lazyimp.apps import ready

    with Tracer(trace, include=["lazyimp"]):
        assert ready() == "logged-in"

    output = tmp_path / "slim"
    slice_trace(trace, output, include=["lazyimp"])
    models = (output / "lazyimp" / "models.py").read_text(encoding="utf-8")
    ast.parse(models)
    assert "def update_last_login" in models
    assert "def unused" not in models

    sys.path.insert(0, str(output))
    try:
        for name in list(sys.modules):
            if name == "lazyimp" or name.startswith("lazyimp."):
                sys.modules.pop(name)
        from lazyimp.apps import ready as sliced_ready

        assert sliced_ready() == "logged-in"
    finally:
        sys.path.remove(str(output))
        for name in list(sys.modules):
            if name == "lazyimp" or name.startswith("lazyimp."):
                sys.modules.pop(name)
