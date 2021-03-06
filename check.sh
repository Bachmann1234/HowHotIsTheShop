#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
poetry run black --check howhot tests
poetry run isort --check howhot tests
poetry run pylint howhot tests
poetry run mypy howhot tests
poetry run pytest tests -v
