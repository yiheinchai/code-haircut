from haircut.errors import HaircutError
from haircut.run import unwrap_invocation
import pytest


def test_unwrap_python_manage_py():
    script, module, forwarded = unwrap_invocation(
        "python", None, ["manage.py", "test"]
    )
    assert script == "manage.py"
    assert module is None
    assert forwarded == ["test"]


def test_unwrap_python_dash_m_pytest():
    script, module, forwarded = unwrap_invocation(
        "python3", None, ["-m", "pytest", "-q"]
    )
    assert script is None
    assert module == "pytest"
    assert forwarded == ["-q"]


def test_unwrap_interpreter_flags_before_script():
    script, module, forwarded = unwrap_invocation(
        "python", None, ["-u", "-B", "manage.py", "test", "polls"]
    )
    assert script == "manage.py"
    assert forwarded == ["test", "polls"]


def test_unwrap_sys_executable(monkeypatch):
    import sys

    script, module, forwarded = unwrap_invocation(
        sys.executable, None, ["app.py", "--flag"]
    )
    assert script == "app.py"
    assert forwarded == ["--flag"]


def test_unwrap_plain_script_unchanged():
    script, module, forwarded = unwrap_invocation("manage.py", None, ["test"])
    assert script == "manage.py"
    assert forwarded == ["test"]


def test_unwrap_module_flag_passthrough():
    script, module, forwarded = unwrap_invocation(None, "pytest", ["-q"])
    assert script is None
    assert module == "pytest"
    assert forwarded == ["-q"]


def test_unwrap_python_c_rejected():
    with pytest.raises(HaircutError, match="python -c"):
        unwrap_invocation("python", None, ["-c", "print(1)"])
