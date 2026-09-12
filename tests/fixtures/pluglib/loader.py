from importlib import import_module


def load(name: str):
    module = import_module(name)
    return module.Command()
