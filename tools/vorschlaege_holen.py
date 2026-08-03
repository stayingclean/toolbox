# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl"]
# ///
"""
Freigegebene Skill-Vorschläge übernehmen
========================================

Holt aus dem Vorschlags-Repo alle offenen Issues mit dem Label „freigegeben",
hängt sie ans Blatt `Skills` von skills_daten.xlsx an, schliesst die Issues und
ruft anschliessend build.py auf.

Aufruf:  vorschlaege.bat      (oder `uv run tools/vorschlaege_holen.py`)

Der Push bleibt bewusst von Hand — nach dem Lauf zuerst die Skillsliste
anschauen, dann committen und pushen.

Voraussetzung: das GitHub-CLI `gh` ist installiert und angemeldet
(`gh auth status` muss ein angemeldetes Konto zeigen).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "skills_daten.xlsx"
BUILD = ROOT / "build.py"
REPO = "stayingclean/toolbox-vorschlaege"
LABEL = "freigegeben"

SPALTEN = [
    ("Stufe", "stufe"),
    ("Kategorie", "kategorie"),
    ("Emoji", "emoji"),
    ("Titel", "titel"),
    ("Beschreibung", "beschreibung"),
    ("Tipp", "tipp"),
    ("Von", "von"),
]

BLOCK = re.compile(r"<!--\s*vorschlag\s*(\{.*?\})\s*-->", re.DOTALL)


def parse_body(body: str):
    """Liest den maschinenlesbaren Block aus einem Issue-Rumpf.

    Liefert None, wenn kein Block vorhanden ist oder das JSON nicht lesbar ist –
    solche Issues bleiben offen und werden am Ende gemeldet.
    """
    treffer = BLOCK.search(body or "")
    if not treffer:
        return None
    try:
        daten = json.loads(treffer.group(1))
    except json.JSONDecodeError:
        return None
    return daten if isinstance(daten, dict) else None


def hole_issues():
    """Fragt die freigegebenen, offenen Issues über das GitHub-CLI ab."""
    try:
        ergebnis = subprocess.run(
            ["gh", "issue", "list", "--repo", REPO, "--label", LABEL,
             "--state", "open", "--limit", "100", "--json", "number,title,body"],
            capture_output=True, text=True, encoding="utf-8",
        )
    except FileNotFoundError:
        raise SystemExit(
            "❌ Das GitHub-Programm `gh` wurde nicht gefunden.\n\n"
            "   Lade es von https://cli.github.com herunter, installiere es und\n"
            "   melde dich danach einmal mit  gh auth login  an.\n"
            "   Ohne `gh` kann dieses Skript die Vorschlaege nicht abholen."
        )
    if ergebnis.returncode != 0:
        raise SystemExit(
            "❌ Konnte die Vorschläge nicht abrufen:\n"
            + ergebnis.stderr.strip()
            + "\n\nIst `gh` installiert und angemeldet? Prüfe mit: gh auth status"
        )
    return json.loads(ergebnis.stdout or "[]")


def an_excel_anhaengen(pfad: Path, eintraege: list) -> int:
    """Hängt Vorschläge ans Blatt `Skills` an – spaltenweise nach Kopfzeile."""
    if not eintraege:
        return 0
    wb = openpyxl.load_workbook(pfad)
    ws = wb["Skills"]
    kopf = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
    for name, _ in SPALTEN:
        if name not in kopf:
            ws.cell(row=1, column=len(kopf) + 1, value=name)
            kopf.append(name)
    for eintrag in eintraege:
        zeile = [""] * len(kopf)
        for name, schluessel in SPALTEN:
            zeile[kopf.index(name)] = eintrag.get(schluessel, "")
        ws.append(zeile)
    # Filterbereich und Stufen-Dropdown auf die neuen Zeilen ausdehnen, sonst
    # fallen sie heraus und beim Sortieren koennen Werte verrutschen.
    letzte = ws.max_row
    ws.auto_filter.ref = f"A1:{get_column_letter(len(kopf))}{letzte}"
    for pruefung in ws.data_validations.dataValidation:
        if str(pruefung.sqref).startswith("A2:A"):
            pruefung.sqref = f"A2:A{letzte}"
    wb.save(pfad)
    return len(eintraege)


def issue_schliessen(nummer: int):
    subprocess.run(
        ["gh", "issue", "close", str(nummer), "--repo", REPO,
         "--comment", "Übernommen – erscheint mit dem nächsten Build in der Skillsliste."],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )


def main():
    issues = hole_issues()
    if not issues:
        print("Keine freigegebenen Vorschläge offen. Nichts zu tun.")
        return

    uebernehmen, uebersprungen = [], []
    for issue in issues:
        daten = parse_body(issue.get("body", ""))
        if daten is None or daten.get("art") != "neu":
            uebersprungen.append(issue)
            continue
        uebernehmen.append((issue, daten))

    anzahl = an_excel_anhaengen(XLSX, [d for _, d in uebernehmen])
    nicht_geschlossen = []
    for issue, daten in uebernehmen:
        print(f"  + {daten['stufe']} / {daten['kategorie']}: {daten['titel']}")
        try:
            issue_schliessen(issue["number"])
        except Exception:
            nicht_geschlossen.append(issue["number"])

    print(f"\n✅ {anzahl} Vorschlag/Vorschläge in {XLSX.name} übernommen.")

    if nicht_geschlossen:
        nummern = ", ".join(f"#{n}" for n in nicht_geschlossen)
        print(
            f"\n⚠ ACHTUNG: {nummern} konnte(n) nicht geschlossen werden.\n"
            f"   Die Vorschlaege sind bereits in der Excel. Schliesse diese Issues\n"
            f"   von Hand, sonst werden sie beim naechsten Lauf ein zweites Mal\n"
            f"   angehaengt."
        )

    for issue in uebersprungen:
        print(
            f'⚠ Issue #{issue["number"]} „{issue["title"]}" übersprungen '
            f'(kein lesbarer Vorschlagsblock oder andere Art) – bleibt offen.'
        )

    if anzahl:
        print("\nSkillsliste wird neu gebaut …\n")
        subprocess.run([sys.executable, str(BUILD)], check=True)
        print(
            "\nJetzt anschauen: docs/skillsliste.html\n"
            "Wenn es passt:  git add -A && git commit -m \"Neue Skills übernommen\" && git push"
        )


if __name__ == "__main__":
    main()
