#!/usr/bin/env bash
set -euo pipefail
uv sync --locked --group dev --extra operator
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked ty check
uv run --locked pytest --cov=breeze --cov-report=term-missing tests
uv run --locked pip-audit --skip-editable
uv build --no-sources
