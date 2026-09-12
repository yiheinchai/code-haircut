def html_safe(klass):
    if "__html__" in klass.__dict__:
        raise ValueError(
            f"can't apply @html_safe to {klass.__name__} because it defines __html__()."
        )
    if "__str__" not in klass.__dict__:
        raise ValueError(
            f"can't apply @html_safe to {klass.__name__} because it doesn't "
            "define __str__()."
        )
    return klass


@html_safe
class MediaAsset:
    element_template = "{path}"

    def __init__(self, path):
        self._path = path

    def __eq__(self, other):
        return type(self) is type(other) and self._path == getattr(other, "_path", None)

    def __hash__(self):
        return hash(self._path)

    def __str__(self):
        return self.element_template.format(path=self._path)

    def __repr__(self):
        return f"{type(self).__qualname__}({self._path!r})"

    def unused(self):
        return "nope"


class Script(MediaAsset):
    def label(self):
        return "js"


def run() -> str:
    return Script.label.__name__
