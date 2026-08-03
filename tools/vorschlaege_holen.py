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
DATEN_JSON = ROOT / "docs" / "skills-daten.json"
REPO = "stayingclean/skills-suggestions"
LABEL = "freigegeben"

# Nur Issues von diesem Konto werden uebernommen. Der Worker legt sie unter dem
# Token dieses Kontos an; von Hand eroeffnete Issues sind nie geprueft worden.
BOT = "eraschle"

# Muessen zu den Grenzen in worker/validate.js passen.
GRENZEN = {
    "emoji": 2,
    "titel": 60,
    "beschreibung": 300,
    "tipp": 200,
    "von": 30,
}
FELDNAMEN = {
    "emoji": "Emoji",
    "titel": "Titel",
    "beschreibung": "Beschreibung",
    "tipp": "Tipp",
    "von": "Name",
}
PFLICHT = ["stufe", "kategorie", "emoji", "titel", "beschreibung"]
TEXTFELDER = ["titel", "beschreibung", "tipp", "von"]
# Anzeigename -> Schluessel in docs/skills-daten.json
STUFEN = {"Hoch": "hoch", "Mittel": "mittel", "Tief": "tief"}

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

    Liefert None, wenn kein Block vorhanden ist, das JSON nicht lesbar ist oder
    MEHR ALS EIN Block gefunden wird. Der letzte Fall ist der Abwehrschritt gegen
    einen gefaelschten Block, den jemand in ein Freitextfeld geschrieben hat –
    solche Issues bleiben offen und werden gemeldet.
    """
    treffer = BLOCK.findall(body or "")
    if len(treffer) != 1:
        return None
    try:
        daten = json.loads(treffer[0])
    except json.JSONDecodeError:
        return None
    return daten if isinstance(daten, dict) else None


def pruefe_eintrag(eintrag: dict, daten: dict):
    """Prueft einen Vorschlag gegen den aktuellen Datenbestand.

    Liefert None, wenn alles stimmt, sonst eine verstaendliche Meldung.
    Der Worker prueft dasselbe – hier geht es um Issues, die nicht ueber das
    Formular kamen, und um Vorschlaege, deren Kategorie inzwischen weg ist.
    """
    for schluessel in PFLICHT:
        wert = eintrag.get(schluessel)
        if not isinstance(wert, str) or not wert.strip():
            name = FELDNAMEN.get(schluessel, schluessel.capitalize())
            return f"Pflichtfeld fehlt oder ist leer: {name}."

    # Tipp und Von duerfen fehlen und gelten dann als leer.
    felder = {s: str(eintrag.get(s) or "").strip() for s in GRENZEN}
    felder.update({s: str(eintrag.get(s) or "").strip() for s in ("stufe", "kategorie")})

    for schluessel, grenze in GRENZEN.items():
        if len(felder[schluessel]) > grenze:
            return (
                f"Zu lang: {FELDNAMEN[schluessel]} "
                f"({len(felder[schluessel])} statt hoechstens {grenze} Zeichen)."
            )

    for schluessel in TEXTFELDER:
        if "http" in felder[schluessel].lower():
            return "Links sind nicht erlaubt."

    for schluessel in TEXTFELDER + ["emoji"]:
        wert = felder[schluessel]
        if "<!--" in wert or "-->" in wert:
            return "Kommentarzeichen sind nicht erlaubt."
        if "<" in wert or ">" in wert:
            return "Spitze Klammern sind nicht erlaubt."

    stufe = felder["stufe"]
    if stufe not in STUFEN:
        return f"Unbekannte Stufe: '{stufe}' (erlaubt sind Hoch, Mittel, Tief)."

    stufen_daten = daten.get(STUFEN[stufe]) or {}
    kategorien = [k.get("label") for k in stufen_daten.get("kategorien", [])]
    if felder["kategorie"] not in kategorien:
        return (
            f"Unbekannte Kategorie: '{felder['kategorie']}' "
            f"gibt es in der Stufe '{stufe}' nicht (mehr)."
        )

    return None


def lade_datenstand() -> dict:
    """Liest docs/skills-daten.json – den Stand, gegen den geprueft wird."""
    if not DATEN_JSON.exists():
        raise SystemExit(
            f"❌ {DATEN_JSON.name} fehlt.\n\n"
            "   Ohne diese Datei laesst sich nicht pruefen, welche Stufen und\n"
            "   Kategorien es gibt. Bitte zuerst build.bat ausfuehren."
        )
    try:
        return json.loads(DATEN_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(
            f"❌ {DATEN_JSON.name} ist nicht lesbar.\n\n"
            "   Bitte zuerst build.bat ausfuehren."
        )


def hole_issues():
    """Fragt alle offenen Issues über das GitHub-CLI ab (ungefiltert).

    Der serverseitige Label-Filter von GitHub (`--label`) ist nicht sofort
    aktuell: ein frisch gesetztes Label taucht dort erst nach einigen Sekunden
    auf. Darum werden hier alle offenen Issues samt Labels geholt und das
    Filtern nach `hat_label()` in Python erledigt.
    """
    try:
        ergebnis = subprocess.run(
            ["gh", "issue", "list", "--repo", REPO,
             "--state", "open", "--limit", "100",
             "--json", "number,title,body,author,labels"],
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


def hat_label(issue: dict, name: str) -> bool:
    """Prueft das Label in Python statt ueber den Server.

    Der serverseitige Label-Filter von GitHub ist nicht sofort aktuell: ein
    frisch gesetztes Label taucht dort erst nach einigen Sekunden auf. Wer
    freigibt und sofort startet, bekaeme sonst faelschlich „nichts zu tun".
    """
    return any(l.get("name") == name for l in issue.get("labels", []))


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
    alle_offenen = hole_issues()
    issues = [i for i in alle_offenen if hat_label(i, LABEL)]
    if not issues:
        print("Keine freigegebenen Vorschläge offen. Nichts zu tun.")
        if alle_offenen:
            print(f"({len(alle_offenen)} Vorschlaege warten noch auf deine Freigabe.)")
        return

    bestand = lade_datenstand()

    uebernehmen, uebersprungen, abgelehnt = [], [], []
    for issue in issues:
        # Herkunft zuerst: das Repo ist oeffentlich, jede Person mit GitHub-Konto
        # kann dort ein Issue eroeffnen – solche Rumpfe hat nie jemand geprueft.
        konto = (issue.get("author") or {}).get("login", "")
        if konto != BOT:
            abgelehnt.append(
                (issue, f"stammt von '{konto or 'unbekannt'}', nicht vom Formular")
            )
            continue
        daten = parse_body(issue.get("body", ""))
        if daten is None or daten.get("art") != "neu":
            uebersprungen.append(issue)
            continue
        # Erst pruefen, dann anhaengen: ein Abbruch nach dem Speichern wuerde
        # beim naechsten Lauf Dubletten erzeugen (Excel geschrieben, Issue offen).
        grund = pruefe_eintrag(daten, bestand)
        if grund:
            abgelehnt.append((issue, grund))
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

    for issue, grund in abgelehnt:
        print(
            f'⚠ Issue #{issue["number"]} „{issue["title"]}" nicht übernommen: '
            f"{grund} – bleibt offen."
        )

    if anzahl:
        print("\nSkillsliste wird neu gebaut …\n")
        ergebnis = subprocess.run([sys.executable, str(BUILD)], check=False)
        if ergebnis.returncode != 0:
            print(
                "\n⚠ ACHTUNG: Der Neubau der Skillsliste ist gescheitert.\n"
                "   Was zu korrigieren ist, steht in der Meldung weiter oben.\n"
                f"   Die Vorschlaege stehen bereits in {XLSX.name} – nach der\n"
                "   Korrektur genuegt ein Doppelklick auf build.bat, ein erneuter\n"
                "   Lauf von vorschlaege.bat ist nicht noetig."
            )
            return
        print(
            "\nJetzt anschauen: docs/skillsliste.html\n"
            "Wenn es passt:  git add -A && git commit -m \"Neue Skills übernommen\" && git push"
        )


if __name__ == "__main__":
    main()
