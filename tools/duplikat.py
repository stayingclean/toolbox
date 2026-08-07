"""Duplikatpruefung fuer neue Skill-Vorschlaege (optional, per KI).

Dieses Modul kennt weder Excel noch GitHub noch die Konsolenfuehrung. Es
beantwortet genau eine Frage: „Aehnelt einer dieser neuen Vorschlaege einem
Skill, den es schon gibt?" — und liefert die Treffer zurueck.

Die Pruefung ist eine ZUTAT, keine Voraussetzung: Ohne Schluessel oder bei
einem Fehler der Schnittstelle laeuft die Uebernahme unveraendert weiter.
"""

import json
import os
import subprocess
from pathlib import Path

MODELL = "claude-opus-5"
VARIABLE = "ANTHROPIC_API_KEY"

PROJEKT = Path(__file__).resolve().parent.parent
PROMPT_DATEI = "duplikat_prompt.md"

# Anzeige-Name je Stufenschluessel, damit die KI dieselben Woerter sieht wie
# der Mensch in der Excel.
STUFEN_NAME = {"hoch": "Hoch", "mittel": "Mittel", "tief": "Tief"}

# Rueckfall-Muster, falls Git nicht befragt werden kann (kein Repo, kein Git
# installiert). Ohne Git gibt es aber auch kein `git add -A` -- deshalb darf
# der Rueckfall grosszuegiger sein als eine echte .gitignore-Auswertung.
_RUECKFALL_MUSTER = (".env", ".env*", "*.env", "/.env", "**/.env")


def _von_git_ignoriert(projekt: Path) -> bool | None:
    """Fragt Git direkt, ob `.env` ignoriert wird. None, wenn nicht ermittelbar.

    Nur Git kennt Negationen (`!.env`), Pfadanker (`/.env`) und `**`
    zuverlaessig -- ein Nachbau als Zeichenkettenvergleich uebersieht genau
    die Faelle, die hier sicherheitsrelevant sind (z. B. `.env*` gefolgt von
    `!.env`, was die Datei am Ende doch NICHT schuetzt).
    """
    try:
        ergebnis = subprocess.run(
            ["git", "check-ignore", "--quiet", ".env"],
            cwd=projekt,
            capture_output=True,
        )
    except OSError:
        return None
    if ergebnis.returncode == 0:
        return True
    if ergebnis.returncode == 1:
        return False
    return None  # z. B. kein Git-Repo (Exit-Code 128) -> Rueckfall


def _env_datei_lesen(pfad: Path) -> str | None:
    """Sucht den Schluessel in einer .env-Datei. Kein Fremdpaket noetig."""
    try:
        inhalt = pfad.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Keine Byte-Vorschau in der Meldung durchreichen (koennte
        # Schluesselmaterial zeigen) -- deshalb `from None` statt der
        # verketteten Ausnahme.
        raise SystemExit(
            "❌ Die Datei .env laesst sich nicht als Text lesen (kein\n"
            "   gueltiges UTF-8).\n\n"
            "   Pruefe die Datei von Hand. Es wurde nichts veraendert."
        ) from None
    for zeile in inhalt.splitlines():
        zeile = zeile.strip()
        # `zeile.startswith("#")` ist mit der heutigen Vergleichslogik durch
        # keinen Test einzeln nachweisbar: Nach partition("=") enthaelt der
        # Namensteil einer auskommentierten Zeile das "#" immer noch
        # ("# ANTHROPIC_API_KEY" != "ANTHROPIC_API_KEY"), also kann eine
        # auskommentierte Zuweisung sowieso nie treffen -- mit oder ohne
        # diese Bedingung. Sie bleibt trotzdem stehen: Sie ist die zweite
        # Schutzebene, falls die Vergleichslogik hier spaeter mal
        # nachsichtiger wird (z. B. Gross-/Kleinschreibung ignoriert). Das
        # ist bewusst so und keine Testluecke.
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
    # nicht zurueckholen, nur sperren. Deshalb wird nach Moeglichkeit Git
    # selbst gefragt statt die Regeln nachzubauen (siehe _von_git_ignoriert).
    git_ergebnis = _von_git_ignoriert(projekt)
    if git_ergebnis is not None:
        geschuetzt = git_ergebnis
    else:
        gitignore = projekt / ".gitignore"
        geschuetzt = gitignore.exists() and any(
            zeile.strip() in _RUECKFALL_MUSTER
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


def lade_prompt(projekt: Path) -> str:
    """Liest den Anweisungstext aus tools/duplikat_prompt.md.

    Die Datei enthaelt NUR die Anweisungen, nicht die Daten. Bestand und neue
    Vorschlaege setzt der Code als eigene Nachricht zusammen. So kann die Datei
    frei umformuliert werden, ohne dass ein Platzhalter kaputtgeht.
    """
    pfad = projekt / "tools" / PROMPT_DATEI
    if not pfad.exists():
        raise SystemExit(
            f"❌ Die Datei tools/{PROMPT_DATEI} fehlt.\n\n"
            "   In ihr steht, wonach die Duplikatpruefung suchen soll. Ohne sie\n"
            "   kann nicht geprueft werden. Hol die Datei aus dem Repo zurueck\n"
            "   (git checkout tools/) oder nimm den Schluessel weg, dann\n"
            "   entfaellt die Pruefung.\n\n"
            "   Es wurde nichts veraendert."
        )
    text = pfad.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(
            f"❌ Die Datei tools/{PROMPT_DATEI} ist leer.\n\n"
            "   Ohne Anweisung liefert die Pruefung unbrauchbare Ergebnisse.\n"
            "   Bitte den Text wiederherstellen (git checkout tools/).\n\n"
            "   Es wurde nichts veraendert."
        )
    return text


def bestand_als_text(bestand: dict) -> str:
    """Der vorhandene Bestand als kompakte Zeilenliste.

    Trennzeichen zwischen Titel und Beschreibung ist `|`, nicht der
    Gedankenstrich: 21 von 100 echten Beschreibungen (Feld `b`) enthalten
    selbst einen Gedankenstrich (docs/skills-daten.json), ein Gedankenstrich
    waere also keine eindeutige Grenze. `|` kommt in keinem der Felder
    e/t/b/tip/von/erg im echten Bestand vor -- geprueft gegen
    docs/skills-daten.json (100 Skills, Stand dieser Aenderung).
    """
    zeilen = []
    for schluessel, stufe in bestand.items():
        name = STUFEN_NAME.get(schluessel, schluessel)
        for kategorie in stufe.get("kategorien", []):
            for skill in kategorie.get("skills", []):
                zeilen.append(
                    f"{name} / {kategorie['label']}: {skill['t']} | {skill['b']}"
                )
    return "\n".join(zeilen)
