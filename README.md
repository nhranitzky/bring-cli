# Bring! CLI

A small Python CLI for the [Bring!](https://www.getbring.com/) shopping list app.
It is built on top of the unofficial `bring-api` Python package.

The project is primarily a standalone CLI that can be installed with `uv tool install`.
The same CLI code can also be copied into a Codex/Claude-style skill project and run there through a generated shell wrapper.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- A Bring! account

## Installation

Install the CLI as a uv tool from the project root:

```bash
uv tool install .
bring-cli --help
```

Build a wheel:

```bash
uv build
```

Install the CLI from the built wheel:

```bash
uv tool install dist/bring_cli-0.1.0-py3-none-any.whl
bring-cli --help
```

Run the CLI directly from the wheel without installing it as a persistent tool:

```bash
uv tool run --from dist/bring_cli-0.1.0-py3-none-any.whl bring-cli --help
```

`uvx` is equivalent to `uv tool run`:

```bash
uvx --from dist/bring_cli-0.1.0-py3-none-any.whl bring-cli lists
```

Uninstall the CLI:

```bash
uv tool uninstall bring-cli
```

For local development without a tool installation:

```bash
uv sync
uv run bring-cli --help
```

## Configuration

Credentials are provided through environment variables. No config file is required.

| Variable | Required | Description |
|---|---:|---|
| `BRING_EMAIL` | Yes | Bring! account email address |
| `BRING_PASSWORD` | Yes | Bring! account password |
| `BRING_LIST` | No | Default shopping list ID or name |

Example:

```bash
export BRING_EMAIL="you@example.com"
export BRING_PASSWORD="your-password"
export BRING_LIST="Weekly groceries"
```

`BRING_LIST` lets item commands omit the list argument:

```bash
bring-cli add "Milk" --spec "2l"
bring-cli remove "Milk"
bring-cli check-off "Milk"
```

Without `BRING_LIST`, pass the list explicitly:

```bash
bring-cli add "Weekly groceries" "Milk" --spec "2l"
```

## Commands

| Command | Arguments | Options | Description |
|---|---|---|---|
| `lists` | none | `--output`, `-o` | Show all shopping lists |
| `show` | `[list]` | `--include-recent`, `--output`, `-o` | Show items in a shopping list |
| `add` | `[list] <item>` | `--spec`, `-s`, `--output`, `-o` | Add an item |
| `add-items` | `<list> <file>` | `--output`, `-o` | Add multiple items from a JSON file |
| `remove` | `[list] <item>` | `--output`, `-o` | Remove an item completely |
| `check-off` | `[list] <item>` | `--output`, `-o` | Mark an item as bought |

List references can be either Bring! list IDs or list names. List name matching is case-insensitive.

## Examples

Show available lists:

```bash
bring-cli lists
```

Show the active items in a list:

```bash
bring-cli show "Weekly groceries"
```

Include recently bought items:

```bash
bring-cli show "Weekly groceries" --include-recent
```

Add, remove, and check off items:

```bash
bring-cli add "Weekly groceries" "Milk" --spec "2l"
bring-cli remove "Weekly groceries" "Milk"
bring-cli check-off "Weekly groceries" "Milk"
```

Use JSON output:

```bash
bring-cli lists --output json
bring-cli show "Weekly groceries" -o json
```

## Bulk Import

`add-items` reads a JSON array. Each entry can be either an object with a `name` and optional `specification`, or a plain string.

```json
[
  {"name": "Milk", "specification": "2l"},
  {"name": "Butter"},
  "Eggs"
]
```

Run the import:

```bash
bring-cli add-items "Weekly groceries" items.json
```

## Skill Export

This repository stays a normal CLI project. To copy the CLI code into a skill project, run:

```bash
./copy-to-skill.sh /path/to/skill/bring
```

The script creates this target layout:

```text
/path/to/skill/bring/
├── bin/
│   └── bring-cli
└── scripts/
    ├── pyproject.toml
    ├── __main__.py
    ├── cli.py
    ├── models.py
    ├── output.py
    └── core/
```

The generated wrapper can be called from the skill:

```bash
/path/to/skill/bring/bin/bring-cli lists
```

The wrapper uses `uv run --project scripts` and starts the copied package with `python -m scripts`.

## Development

Common commands:

```bash
make install
make test
make lint
make typecheck
make check
make build
make run ARGS="lists --output json"
```

Equivalent direct commands:

```bash
uv run pytest tests/
uv run ruff check bring tests
uv run mypy bring
uv build
```

## License

MIT

## AI Usage

This project was developed with AI assistance and human review/testing.
