import ast

from haircut.parse import FileCoverage
from haircut.slice import slice_source


def _slice(source: str, lines: set[int], calls: set[int], prune: bool = False):
    cov = FileCoverage(path="mod.py", lines=set(lines), call_lines=set(calls))
    result = slice_source(source, cov, prune_branches=prune, filename="mod.py")
    if result.source:
        ast.parse(result.source)
    return result


def test_drops_unused_top_level_function():
    source = """def used(x):
    return x * 2

def unused(x):
    return x
"""
    result = _slice(source, lines={1, 2}, calls={1})
    assert "def used" in result.source
    assert "def unused" not in result.source


def test_keeps_class_attributes_and_drops_unused_methods():
    source = """class Calculator:
    factor = 3

    def add(self, a, b):
        return a + b + self.factor

    def unused_method(self):
        return 0
"""
    result = _slice(source, lines={4, 5}, calls={4})
    assert "class Calculator" in result.source
    assert "factor = 3" in result.source
    assert "def add" in result.source
    assert "def unused_method" not in result.source


def test_drops_unused_class():
    source = """class Kept:
    def run(self):
        return 1

class Unused:
    def nope(self):
        return 2
"""
    result = _slice(source, lines={2, 3}, calls={2})
    assert "class Kept" in result.source
    assert "class Unused" not in result.source


def test_prune_drops_false_else_branch():
    source = """def used(x):
    if x > 0:
        return x * 2
    else:
        return -x
"""
    result = _slice(source, lines={1, 2, 3}, calls={1}, prune=True)
    assert "return x * 2" in result.source
    assert "return -x" not in result.source
    ast.parse(result.source)


def test_prune_keeps_taken_else_with_pass():
    source = """def used(x):
    if x > 0:
        return x * 2
    else:
        return -x
"""
    result = _slice(source, lines={1, 2, 5}, calls={1}, prune=True)
    assert "pass" in result.source
    assert "return -x" in result.source
    assert "return x * 2" not in result.source


def test_keeps_module_level_constants_and_imports():
    source = """from os.path import join
USED = 2

def used():
    return USED
"""
    result = _slice(source, lines={4, 5}, calls={4})
    assert "from os.path import join" in result.source
    assert "USED = 2" in result.source
    assert "def used" in result.source


def test_empty_when_nothing_executed():
    source = """def unused():
    return 1
"""
    result = _slice(source, lines=set(), calls=set())
    assert result.kept is False
    assert result.source == ""
