#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
uv run ruff format --check howhot tests
uv run ruff check howhot tests
uv run mypy howhot tests
uv run pytest tests -v
