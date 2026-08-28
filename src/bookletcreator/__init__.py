"""bookletcreator package."""

__all__ = ["convert_booklet", "run"]


def __getattr__(name: str):
    if name in __all__:
        from .cli import convert_booklet, run

        return {"convert_booklet": convert_booklet, "run": run}[name]
    raise AttributeError(f"module 'bookletcreator' has no attribute {name!r}")
