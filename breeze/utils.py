from collections.abc import Callable, Mapping

# Taken from https://raw.githubusercontent.com/ozgur/python-linkedin/master/linkedin/utils.py


def make_enum(
    enum_type: str = "enum",
    base_classes: tuple[type, ...] | None = None,
    methods: Mapping[str, Callable[..., object]] | None = None,
    **attrs: object,
) -> type:
    """Build a legacy enum class without mutating caller-provided methods.

    Retained for external callers; endpoint constants use a typed StrEnum.
    The dynamic attributes of the returned class require runtime inspection.
    """

    def __init__(instance: object, *args: object, **kwargs: object) -> None:
        raise RuntimeError(f"{enum_type} types cannot be initialized.")

    bases = (*base_classes, object) if base_classes is not None else (object,)
    namespace: dict[str, object] = {
        name: classmethod(method) for name, method in (methods or {}).items()
    }
    namespace.update(attrs)
    namespace["enums"] = attrs.copy()
    namespace["__init__"] = __init__
    return type(enum_type, bases, namespace)
