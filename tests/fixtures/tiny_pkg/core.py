from .util import double

USED_CONSTANT = 2


def used(x):
    """Scale a positive number."""
    if x > 0:
        return double(x) * USED_CONSTANT
    else:
        return -x


def unused(x):
    return x + 99


class Calculator:
    factor = 3

    def add(self, a, b):
        return a + b + self.factor

    def unused_method(self):
        return 0


class UnusedClass:
    def nope(self):
        return 1
