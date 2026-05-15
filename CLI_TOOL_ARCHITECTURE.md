# CLI/Tool Project Architecture

This document describes a reusable architecture for Python CLI projects that need to work in two modes:

1. As a normal installable CLI tool, for example with `uv tool install .`.
2. As copied CLI code inside a skill project, started through a shell wrapper.

The pattern is based on this repository, but the names can be adapted for other tools.

## Goals

- Keep the repository a normal Python CLI project.
- Make the CLI installable from source, sdist, or wheel.
- Keep runtime code copyable into another project without depending on the original package name.
- Keep CLI parsing, output rendering, data models, and business logic separated.
- Keep development tooling in the repository root.

## Project Layout

Use this layout for a project named `my-cli` with a Python package named `my_cli`:

```text
my-cli/
|-- pyproject.toml
|-- uv.lock
|-- Makefile
|-- install.sh
|-- README.md
|-- tests/
|   |-- __init__.py
|   `-- test_cli.py
`-- my_cli/
    |-- pyproject.toml
    |-- __init__.py
    |-- __main__.py
    |-- cli.py
    |-- models.py
    |-- output.py
    `-- core/
        |-- __init__.py
        `-- client.py
```

The root is the installable CLI project. The package directory contains all runtime code and a secondary `pyproject.toml` used after the code is copied into a skill layout.

## Runtime Modes

### Tool Mode

Install from the repository root:

```bash
uv tool install .
my-cli --help
```

The root `pyproject.toml` defines the package, build backend, and console script.

### Wheel Mode

Build a wheel:

```bash
uv build
```

Install the wheel as a persistent tool:

```bash
uv tool install dist/my_cli-0.1.0-py3-none-any.whl
my-cli --help
```

Run directly from the wheel without a persistent installation:

```bash
uv tool run --from dist/my_cli-0.1.0-py3-none-any.whl my-cli --help
```

`uvx` is equivalent to `uv tool run`:

```bash
uvx --from dist/my_cli-0.1.0-py3-none-any.whl my-cli --help
```

### Skill Mode

In skill mode, `install.sh` copies the package directory into another project as `scripts/` and generates a shell wrapper:

```text
target-skill/
|-- bin/
|   `-- my-cli
`-- scripts/
    |-- pyproject.toml
    |-- __main__.py
    |-- cli.py
    |-- models.py
    |-- output.py
    `-- core/
```

The copied code is started with:

```bash
target-skill/bin/my-cli --help
```

The wrapper runs:

```bash
uv run --project "$CLI_DIR" --directory "$(dirname "$CLI_DIR")" python -m scripts "$@"
```

This is why internal package imports must be relative. After copying, the package name changes from `my_cli` to `scripts`.

## Root `pyproject.toml`

The root `pyproject.toml` is the source of truth for the installable tool and development tools:

```toml
[project]
name = "my-cli"
version = "0.1.0"
description = "CLI for ..."
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "rich>=13.7",
    "pydantic>=2.7",
]

[project.scripts]
my-cli = "my_cli.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["my_cli"]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "mypy>=1.10",
]
```

Use `[project.scripts]` only in the root project. That is what makes the CLI installable as a tool.

## Package `pyproject.toml`

The package-level `pyproject.toml` exists for skill mode. It defines runtime dependencies, but it is not an installable package:

```toml
[project]
name = "my-cli"
version = "0.1.0"
description = "Runtime dependencies for the my-cli skill wrapper"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "rich>=13.7",
    "pydantic>=2.7",
]

[tool.uv]
package = false
```

Do not define `[project.scripts]` or `[build-system]` here. In skill mode, the shell wrapper is the entrypoint and `uv` only needs runtime dependencies.

## Shell Wrapper Export

Use an `install.sh` script to copy the package directory and generate the wrapper:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <target-skill-dir>" >&2
    exit 2
fi

TARGET="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/my_cli"

mkdir -p "$TARGET/bin" "$TARGET/scripts"
rsync -a \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "$SRC/" "$TARGET/scripts/"

cat > "$TARGET/bin/my-cli" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)"

unset VIRTUAL_ENV CONDA_PREFIX CONDA_DEFAULT_ENV
exec uv run --project "$CLI_DIR" --directory "$(dirname "$CLI_DIR")" python -m scripts "$@"
EOF

chmod +x "$TARGET/bin/my-cli"
```

The wrapper unsets active virtual environment variables to keep the skill runtime isolated from the invoking process.

## Module Responsibilities

`cli.py` owns the Typer app, command definitions, argument parsing, environment lookup, and calls into the core layer.

`__main__.py` allows module execution:

```python
from .cli import main

if __name__ == "__main__":
    main()
```

`models.py` defines Pydantic models used as the output contract between the core layer, JSON output, text output, and tests.

`output.py` owns all rendering. Commands should call `render(...)` or `render_error(...)` instead of formatting tables or JSON directly.

`core/` owns API clients, filesystem operations, parsing, persistence, or other domain behavior. The core layer should not import Typer.

## Import Rules

Use relative imports inside the package:

```python
from .output import OutputFormat, render
from .core.client import ClientError, fetch_items
from ..models import Item
```

Avoid absolute internal imports:

```python
from my_cli.output import render
```

Absolute internal imports work in installed tool mode, but fail after the package is copied to `scripts/` for skill mode.

## Configuration Pattern

Prefer environment variables for secrets and defaults:

```python
TOKEN = os.environ.get("MY_CLI_TOKEN", "")
DEFAULT_PROJECT = os.environ.get("MY_CLI_PROJECT", "")
```

Fail early with a clear error when required values are missing. Explicit CLI arguments and options should take precedence over environment defaults.

## Output Contract

Every command should support text and JSON output:

```bash
my-cli command --output text
my-cli command --output json
```

Text output is for humans. JSON output is for automation and should be stable.

For write commands, return compact action results:

```json
{"status": "ok", "item": "Milk", "list": "Weekly groceries"}
```

For errors in JSON mode, write structured JSON to stderr and exit non-zero:

```json
{"error": "Missing required environment variable", "code": "error"}
```

## Testing Strategy

Use `typer.testing.CliRunner` for CLI tests and mock the core layer.

Test at least:

- Commands succeed in text mode.
- Commands succeed in JSON mode.
- Required environment variables are enforced.
- Optional environment defaults are honored.
- Invalid user input exits non-zero.
- Core exceptions become user-facing errors.

## Build and Release Flow

Local verification:

```bash
make check
uv build
```

Install from source:

```bash
uv tool install .
```

Install from wheel:

```bash
uv tool install dist/my_cli-0.1.0-py3-none-any.whl
```

Run from wheel:

```bash
uv tool run --from dist/my_cli-0.1.0-py3-none-any.whl my-cli --help
```

Export to skill:

```bash
./install.sh /path/to/skill/my-cli
/path/to/skill/my-cli/bin/my-cli --help
```

## Checklist for New Projects

- Choose CLI command name, for example `my-cli`.
- Choose Python package name, for example `my_cli`.
- Put installable package metadata in the root `pyproject.toml`.
- Add `[project.scripts]` in the root only.
- Add a package-level `pyproject.toml` with `[tool.uv] package = false`.
- Implement all internal imports as relative imports.
- Keep Typer code in `cli.py`.
- Keep Pydantic output models in `models.py`.
- Keep rendering in `output.py`.
- Keep domain/API logic in `core/`.
- Add `__main__.py` that calls `main()`.
- Add `install.sh` to copy the package to `scripts/` and generate `bin/<command>`.
- Add CLI tests with mocked core functions.
- Verify `uv tool install .`.
- Verify `uv build`.
- Verify `uv tool install dist/*.whl`.
- Verify `uv tool run --from dist/*.whl <command> --help`.
- Verify exported skill wrapper starts successfully.

## Design Tradeoffs

This architecture duplicates runtime dependency metadata in two `pyproject.toml` files:

- Root `pyproject.toml` makes the CLI installable and buildable.
- Package-level `pyproject.toml` lets copied skill code create its own runtime environment.

That duplication is acceptable because it keeps both runtime modes simple. When dependencies change, update both files in the same commit.

The package directory is copied as `scripts/` in skill mode. Internal imports must be relative, but the wrapper does not need editable installs, `PYTHONPATH`, or project-specific package names.

The shell wrapper depends on `uv` being available at runtime. This gives reproducible dependency setup with very little wrapper logic.
