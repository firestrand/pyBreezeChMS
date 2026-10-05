"""Private, bounded operator artifacts; publish complete files without overwrite."""

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

from .breeze import JsonValue, _json_value
from .errors import BreezeResponseError
from .importing import ImportValidationError


@contextmanager
def private_output(path: Path | str) -> Iterator[IO[str]]:
    """Write beside the destination and link only after a successful full write."""
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        try:
            yield stream.file
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
            os.link(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)


def write_json(path: Path | str, payload: JsonValue) -> None:
    with private_output(path) as stream:
        json.dump(payload, stream, ensure_ascii=False, allow_nan=False, sort_keys=True)
        stream.write("\n")


def read_json(path: Path | str, max_bytes: int = 64 * 1024 * 1024) -> JsonValue:
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        raise ImportValidationError("Artifact byte limit must be a positive integer.")

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ImportValidationError("Repeated field in operator JSON artifact.")
            result[key] = value
        return result

    with Path(path).open("rb") as stream:
        content = stream.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ImportValidationError("Operator artifact exceeds its size limit.")
    try:
        return _json_value(json.loads(content, object_pairs_hook=unique_object))
    except (ValueError, UnicodeDecodeError, RecursionError, BreezeResponseError) as error:
        raise ImportValidationError("Invalid operator JSON artifact.") from error


def object_value(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ImportValidationError("Expected an object in operator configuration.")
    return value


def string(value: JsonValue) -> str:
    if not isinstance(value, str):
        raise ImportValidationError("Expected text in operator configuration.")
    return value


def integer(value: JsonValue) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ImportValidationError("Expected an integer in operator configuration.")
    return value


def boolean(value: JsonValue) -> bool:
    if not isinstance(value, bool):
        raise ImportValidationError("Expected a boolean in operator configuration.")
    return value
