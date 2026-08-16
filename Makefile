.PHONY: run test lint format-check check

run:
	uv run run_polling.py

test:
	uv run pytest

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

check: lint format-check
	uv run pyright
	uv run pytest
