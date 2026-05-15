# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kontext

`bring` ist ein Python-CLI-Projekt für die [Bring!](https://www.getbring.com/) Einkaufslisten-App.
Es folgt dem Stack aus `../CLAUDE.md`, bleibt aber ein reines CLI-Projekt: Der Root ist als Tool installierbar (`uv tool install .`).
Der CLI-Code ist zusätzlich so gehalten, dass er per `install.sh` in einen Skill-Ordner kopiert und dort über einen Shell-Wrapper gestartet werden kann.

## Projektstruktur

```
bring/                         # Repo-Root
├── pyproject.toml             # Installierbares CLI-Paket + Dev-Tools
├── uv.lock
├── Makefile
├── install.sh
├── tests/
│   ├── test_cli.py
│   └── test_core.py
└── bring/
    ├── pyproject.toml         # Runtime-Deps für kopierten Skill-Code
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── models.py
    ├── output.py
    └── core/
        ├── __init__.py
        └── bring_client.py    # HTTP-Kommunikation mit der Bring-API
```

## Nutzung

```bash
uv tool install .
bring-cli lists
```

Skill-Export:

```bash
./install.sh /path/to/skill/bring
/path/to/skill/bring/bin/bring-cli lists
```

## Konfiguration

Zugangsdaten werden als Umgebungsvariablen übergeben (kein Config-File):

| Variable | Bedeutung |
|---|---|
| `BRING_EMAIL` | Bring-Konto E-Mail |
| `BRING_PASSWORD` | Bring-Konto Passwort |

## Häufige Befehle

```bash
make install      # uv sync + chmod +x bring/bin/bring
make test         # pytest mit Coverage
make lint         # ruff check
make format       # ruff format + ruff check --fix
make typecheck    # mypy bring/scripts
make check        # lint + typecheck + test (CI)
make run ARGS="list --output json"   # CLI direkt aufrufen

# Einzelnen Test ausführen:
uv run pytest tests/test_cli.py::test_list_items -v

# Neue Runtime-Abhängigkeit:
uv add --project bring/scripts <paket>

# Neue Dev-Abhängigkeit:
uv add --dev <paket>
```

## Bring-API

Die Bring-API ist eine inoffizielle REST-API. Authentifizierung via E-Mail/Passwort → Bearer-Token.
Relevante Endpunkte: Login, Einkaufslisten abrufen, Items hinzufügen/entfernen.
