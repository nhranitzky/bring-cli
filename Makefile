
.PHONY: help install sync test lint format typecheck check build clean run

help:  ## Verfügbare Targets anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

install:  ## Dependencies installieren
	uv sync

sync:  ## Deps aktualisieren
	uv sync

test:  ## Tests mit Coverage
	uv run pytest tests/ --cov=bring --cov-report=term-missing

lint:  ## Ruff linting
	uv run ruff check bring tests

format:  ## Formatieren und auto-fix
	uv run ruff format bring tests
	uv run ruff check --fix bring tests

typecheck:  ## mypy type checking
	uv run mypy bring

check: lint typecheck test  ## Alle Checks (CI)

build:  ## Wheel und sdist bauen
	uv build

clean:  ## Build-Artefakte löschen
	rm -rf dist/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +

run:  ## CLI starten: make run ARGS="lists --output json"
	uv run bring-cli $(ARGS)
