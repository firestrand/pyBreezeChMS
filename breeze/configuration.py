"""Explicit local dotenv loading, with no execution/interpolation or secret output."""

import io
import os
import stat
from pathlib import Path

from .importing import ImportValidationError


def breeze_credentials(path: Path | str | None = None) -> tuple[str, str]:
    environment = dict(os.environ)
    path = None if path is None else Path(path)
    if path is not None and path.exists():
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            info = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_mode & 0o077
                or hasattr(os, "getuid")
                and info.st_uid != os.getuid()
            ):
                raise ImportValidationError("Credential file must be a private owned regular file.")
            content = stream.read(65537)
        if len(content) > 65536:
            raise ImportValidationError("Credential file exceeds its bound.")
        try:
            from dotenv import dotenv_values
        except ImportError as error:
            raise ImportValidationError("Install the operator extra for dotenv support.") from error
        values = dotenv_values(stream=io.StringIO(content.decode("utf-8")), interpolate=False)
        for key in ("BREEZE_URL", "BREEZE_API_KEY"):
            value = values.get(key)
            if key not in environment and value is not None:
                environment[key] = value
    url, key = environment.get("BREEZE_URL", ""), environment.get("BREEZE_API_KEY", "")
    if not url or not key:
        raise ImportValidationError("Populate BREEZE_URL and BREEZE_API_KEY.")
    return url, key
