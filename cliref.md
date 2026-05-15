# Bring! CLI Reference

This document describes how to use `bring-cli` after it is available on your `PATH`.
It intentionally does not cover installation.

## Command Overview

```bash
bring-cli [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS]
```

Available commands:

| Command | Purpose |
|---|---|
| `lists` | Show all available Bring! shopping lists |
| `show` | Show items in a shopping list |
| `add` | Add one item to a shopping list |
| `add-items` | Add multiple items from a JSON file |
| `remove` | Remove an item completely from a shopping list |
| `check-off` | Mark an item as bought |

## Global Options

These options are available on the top-level command:

| Option | Description |
|---|---|
| `--help` | Show top-level help and exit |
| `--install-completion` | Install shell completion for the current shell |
| `--show-completion` | Print shell completion setup for the current shell |

Example:

```bash
bring-cli --help
bring-cli --show-completion
```

## Configuration

The CLI reads credentials and optional defaults from environment variables.

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

`BRING_EMAIL` and `BRING_PASSWORD` are required for all visible commands.

If a command needs a list reference and no list argument is provided, the CLI uses `BRING_LIST`.
If neither a list argument nor `BRING_LIST` is available, the command exits with an error.

## List References

Commands that accept a list reference can use either:

- A Bring! list UUID.
- A Bring! list name.

List names are resolved by the underlying client logic. If multiple lists have the same name, use the UUID to avoid ambiguity.

## Output Formats

Most commands support:

| Option | Values | Default | Description |
|---|---|---:|---|
| `--output`, `-o` | `text`, `json` | `text` | Select output format |

Text output is intended for humans and uses Rich formatting.
JSON output is intended for scripts and automation.

Example:

```bash
bring-cli lists --output json
bring-cli show "Weekly groceries" -o json
```

Errors in JSON mode are written to stderr as JSON:

```json
{"error": "message", "code": "error"}
```

## `lists`

Show all Bring! shopping lists.

```bash
bring-cli lists [OPTIONS]
```

Options:

| Option | Values | Default | Description |
|---|---|---:|---|
| `--output`, `-o` | `text`, `json` | `text` | Select output format |
| `--help` | n/a | n/a | Show command help |

Examples:

```bash
bring-cli lists
bring-cli lists --output json
```

Text output is a table with UUID, name, and theme.

JSON output is an array of shopping list objects:

```json
[
  {
    "uuid": "list-uuid",
    "name": "Weekly groceries",
    "theme": "blue"
  }
]
```

## `show`

Show items in a shopping list.

```bash
bring-cli show [OPTIONS] [LIST_REF]
```

Arguments:

| Argument | Required | Description |
|---|---:|---|
| `LIST_REF` | No | Shopping list UUID or name. Falls back to `BRING_LIST` when omitted |

Options:

| Option | Values | Default | Description |
|---|---|---:|---|
| `--include-recent` | flag | off | Include recently bought items |
| `--output`, `-o` | `text`, `json` | `text` | Select output format |
| `--help` | n/a | n/a | Show command help |

Examples:

```bash
bring-cli show "Weekly groceries"
bring-cli show "Weekly groceries" --include-recent
bring-cli show --include-recent
bring-cli show "Weekly groceries" --output json
```

When `--include-recent` is not set, only active shopping list items are shown.
When `--include-recent` is set, the output also includes recently bought items.

JSON output shape:

```json
{
  "uuid": "list-uuid",
  "name": "Weekly groceries",
  "purchase": [
    {
      "name": "Milk",
      "specification": "2l"
    }
  ],
  "recently": [
    {
      "name": "Eggs",
      "specification": ""
    }
  ]
}
```

## `add`

Add one item to a shopping list.

```bash
bring-cli add [OPTIONS] [LIST_REF] [ITEM]
```

Arguments:

| Argument | Required | Description |
|---|---:|---|
| `LIST_REF` | Conditional | Shopping list UUID or name. Can be omitted when `BRING_LIST` is set |
| `ITEM` | Yes | Item name |

Options:

| Option | Value | Default | Description |
|---|---|---:|---|
| `--spec`, `-s` | text | empty | Item specification, for example `2l`, `500g`, or `6 pcs` |
| `--output`, `-o` | `text`, `json` | `text` | Select output format |
| `--help` | n/a | n/a | Show command help |

Examples:

```bash
bring-cli add "Weekly groceries" "Milk"
bring-cli add "Weekly groceries" "Milk" --spec "2l"
bring-cli add "Milk" --spec "2l"
bring-cli add "Milk" -s "2l" -o json
```

When `BRING_LIST` is set, a single positional argument is treated as `ITEM`.
For example:

```bash
BRING_LIST="Weekly groceries" bring-cli add "Milk"
```

JSON output shape:

```json
{
  "status": "ok",
  "item": "Milk",
  "list": "Weekly groceries"
}
```

## `add-items`

Add multiple items to a shopping list from a JSON file.

```bash
bring-cli add-items [OPTIONS] [LIST_REF] [FILE]
```

Arguments:

| Argument | Required | Description |
|---|---:|---|
| `LIST_REF` | No | Shopping list UUID or name. Falls back to `BRING_LIST` when omitted |
| `FILE` | Yes | Path to a JSON file containing items |

Options:

| Option | Values | Default | Description |
|---|---|---:|---|
| `--output`, `-o` | `text`, `json` | `text` | Select output format |
| `--help` | n/a | n/a | Show command help |

Input file format:

```json
[
  {
    "name": "Milk",
    "specification": "2l"
  },
  {
    "name": "Butter"
  },
  "Eggs"
]
```

Object entries must include `name`.
`specification` is optional and defaults to an empty string.
String entries are treated as item names with an empty specification.

Examples:

```bash
bring-cli add-items "Weekly groceries" items.json
bring-cli add-items "Weekly groceries" items.json --output json
```

Important: although the command can fall back to `BRING_LIST` for the list reference, the current positional interface is easiest to use with an explicit list argument:

```bash
bring-cli add-items "$BRING_LIST" items.json
```

JSON output shape:

```json
{
  "status": "ok",
  "item": "Milk, Butter, Eggs",
  "list": "Weekly groceries"
}
```

## `remove`

Remove an item completely from a shopping list.

```bash
bring-cli remove [OPTIONS] [LIST_REF] [ITEM]
```

Arguments:

| Argument | Required | Description |
|---|---:|---|
| `LIST_REF` | Conditional | Shopping list UUID or name. Can be omitted when `BRING_LIST` is set |
| `ITEM` | Yes | Item name |

Options:

| Option | Values | Default | Description |
|---|---|---:|---|
| `--output`, `-o` | `text`, `json` | `text` | Select output format |
| `--help` | n/a | n/a | Show command help |

Examples:

```bash
bring-cli remove "Weekly groceries" "Milk"
bring-cli remove "Milk"
bring-cli remove "Milk" --output json
```

When `BRING_LIST` is set, a single positional argument is treated as `ITEM`.

JSON output shape:

```json
{
  "status": "ok",
  "item": "Milk",
  "list": "Weekly groceries"
}
```

## `check-off`

Mark an item as bought.

```bash
bring-cli check-off [OPTIONS] [LIST_REF] [ITEM]
```

Arguments:

| Argument | Required | Description |
|---|---:|---|
| `LIST_REF` | Conditional | Shopping list UUID or name. Can be omitted when `BRING_LIST` is set |
| `ITEM` | Yes | Item name |

Options:

| Option | Values | Default | Description |
|---|---|---:|---|
| `--output`, `-o` | `text`, `json` | `text` | Select output format |
| `--help` | n/a | n/a | Show command help |

Examples:

```bash
bring-cli check-off "Weekly groceries" "Milk"
bring-cli check-off "Milk"
bring-cli check-off "Milk" --output json
```

When `BRING_LIST` is set, a single positional argument is treated as `ITEM`.

JSON output shape:

```json
{
  "status": "ok",
  "item": "Milk",
  "list": "Weekly groceries"
}
```

## `remove` vs. `check-off`

Use `remove` when the item should be deleted from the list completely.

Use `check-off` when the item should be marked as bought. In Bring!, this moves the item into the recently bought area instead of deleting it.

## Exit Behavior

Successful commands exit with status code `0`.

User input errors and Bring! API errors exit with a non-zero status code.

Common error cases:

- `BRING_EMAIL` or `BRING_PASSWORD` is missing.
- No list argument is provided and `BRING_LIST` is not set.
- An item command is called without an item name.
- `add-items` is called with a missing file.
- `add-items` receives invalid JSON.
- The Bring! API rejects authentication or a request.

## Automation Notes

For scripts, prefer JSON output:

```bash
bring-cli lists --output json
bring-cli show "Weekly groceries" --output json
bring-cli add "Weekly groceries" "Milk" --spec "2l" --output json
```

Use explicit list UUIDs in automation when possible. UUIDs avoid ambiguity if multiple lists have similar or identical names.
