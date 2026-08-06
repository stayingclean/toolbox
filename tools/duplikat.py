"""Duplikatpruefung fuer neue Skill-Vorschlaege (optional, per KI).

Dieses Modul kennt weder Excel noch GitHub noch die Konsolenfuehrung. Es
beantwortet genau eine Frage: „Aehnelt einer dieser neuen Vorschlaege einem
Skill, den es schon gibt?" — und liefert die Treffer zurueck.

Die Pruefung ist eine ZUTAT, keine Voraussetzung: Ohne Schluessel oder bei
einem Fehler der Schnittstelle laeuft die Uebernahme unveraendert weiter.
"""

import json
import os
from pathlib import Path

MODELL = "claude-opus-5"
VARIABLE = "ANTHROPIC_API_KEY"


def _env_datei_lesen(pfad: Path) -> str | None:
    """Sucht den Schluessel in einer .env-Datei. Kein Fremdpaket noetig."""
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        name, _, wert = zeile.partition("=")
        if name.strip() == VARIABLE:
            return wert.strip().strip('"').strip("'") or None
    return None


def schluessel_finden(projekt: Path) -> str | None:
    """Erst die Umgebungsvariable, sonst die .env-Datei. Sonst None.

    None heisst NICHT Fehler: Ohne Schluessel entfaellt die Pruefung
    kommentarlos, und das Uebernahme-Skript laeuft wie sonst auch.
    """
    aus_umgebung = os.environ.get(VARIABLE, "").strip()
    if aus_umgebung:
        return aus_umgebung

    env = projekt / ".env"
    if not env.exists():
        return None

    # Notbremse: Das Uebernahme-Skript schlaegt am Ende woertlich `git add -A`
    # vor. Deckt .gitignore die Datei nicht ab, waere der Schluessel mit einem
    # Befehl oeffentlich — und ein veroeffentlichter Schluessel laesst sich
    # nicht zurueckholen, nur sperren.
    gitignore = projekt / ".gitignore"
    geschuetzt = gitignore.exists() and any(
        zeile.strip() in (".env", ".env*", "*.env")
        for zeile in gitignore.read_text(encoding="utf-8").splitlines()
    )
    if not geschuetzt:
        raise SystemExit(
            "❌ Die Datei .env enthaelt einen Schluessel, ist aber nicht vor Git\n"
            "   geschuetzt.\n\n"
            "   Trage in .gitignore eine Zeile `.env*` ein und starte noch\n"
            "   einmal. Ohne diesen Schutz koennte der Schluessel mit dem\n"
            "   naechsten Commit oeffentlich werden.\n\n"
            "   Es wurde nichts veraendert."
        )

    return _env_datei_lesen(env)
