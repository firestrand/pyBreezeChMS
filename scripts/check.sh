#!/usr/bin/env bash
set -euo pipefail
uv sync --locked --group dev
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked ty check
uv run --locked pytest --cov=breeze --cov=samples --cov-report=term-missing tests samples/easytithe/tests
uv run --locked pip-audit --skip-editable
uv build --no-sources
uv build --project samples/easytithe --no-sources
