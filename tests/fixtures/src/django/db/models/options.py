"""Fake package used to resolve truncated Hunter paths."""


def swapped(self):
    if self.swappable:
        return "other"
    return None
