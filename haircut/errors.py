"""Public exceptions."""


class HaircutError(Exception):
    """Base error for the haircut CLI and API."""


class TraceParseError(HaircutError):
    """The execution trace could not be parsed."""


class SourceNotFoundError(HaircutError):
    """A traced file could not be resolved to source on disk."""
