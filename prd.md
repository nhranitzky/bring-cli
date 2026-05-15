# Bring! CLI

CLI für die [Bring!](https://www.getbring.com/) Einkaufslisten-App, basierend auf dem `bring-api` Python-Paket.
Dieses Projekt ist ein reines CLI-Projekt und direkt als Tool installierbar:

```bash
uv tool install .
bring-cli lists
```

Der CLI-Code kann zusätzlich in ein Skill-Projekt kopiert werden:

```bash
./install.sh /path/to/skill/bring
/path/to/skill/bring/bin/bring-cli lists
```

## Kommandos

| Kommando | Argumente | Optionen |
|---|---|---|
| `lists` | — | `--output` |
| `show <list>` | List-Ref (ID oder Name) | `--output`, `--include-recent` |
| `add <list> <item>` | List-Ref, Item-Name | `--output`, `--spec "2l"` |
| `add-items <list> <file>` | List-Ref, Pfad zur JSON-Datei | `--output` |
| `remove <list> <item>` | List-Ref, Item-Name | `--output` |
| `check-off <list> <item>` | List-Ref, Item-Name | `--output` |

## Entscheidungen

**Listen-Adressierung:** `<list>` akzeptiert UUID oder Name (case-insensitive). Bei Mehrdeutigkeit (mehrere Listen mit gleichem Namen) → Fehler mit Hinweis, die ID zu verwenden.

**Default-Liste:** Wenn `<list>` weggelassen wird, fällt die CLI auf die Umgebungsvariable `BRING_LIST` zurück. Ist diese nicht gesetzt, Fehler.

**`show` Inhalt:** Zeigt standardmäßig nur aktive Items (`purchase`). Mit `--include-recent` werden zusätzlich abgehakte Items (`recently`) in einer separaten Sektion angezeigt.

**`check-off` vs. `remove`:** `check-off` markiert ein Item als kürzlich gekauft (bleibt in `recently`). `remove` löscht es vollständig aus der Liste.

**Erfolgs-Output** (`add`, `remove`, `check-off`): Kurze Bestätigung als Text, bei `--output json` als `{"status": "ok", "item": "...", "list": "..."}`.

**Async:** `bring-api` ist async — jedes Command nutzt `asyncio.run()`.

**Bulk-Import JSON-Format:**
```json
[
  {"name": "Milch", "specification": "2l"},
  {"name": "Butter"},
  {"name": "Eier", "specification": "6 Stück"}
]
```
`specification` ist optional.

## Konfiguration (Umgebungsvariablen)

| Variable | Pflicht | Bedeutung |
|---|---|---|
| `BRING_EMAIL` | ✅ | Bring-Konto E-Mail |
| `BRING_PASSWORD` | ✅ | Bring-Konto Passwort |
| `BRING_LIST` | ❌ | Standard-Einkaufsliste (ID oder Name) |
