import json
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import vorschlaege_holen as vh

BEISPIEL = {
    "art": "neu",
    "stufe": "Hoch",
    "kategorie": "Ablenkung",
    "emoji": "🎧",
    "titel": "Musik hören",
    "beschreibung": "Ein Lied auflegen.",
    "tipp": "Kopfhörer bereitlegen",
    "von": "Max",
}


def issue_text(nutzlast):
    return (
        "| Feld | Wert |\n| --- | --- |\n| Titel | Musik hören |\n\n"
        "<!-- vorschlag\n" + json.dumps(nutzlast, ensure_ascii=False) + "\n-->\n"
    )


def test_parse_body_liest_den_block():
    assert vh.parse_body(issue_text(BEISPIEL)) == BEISPIEL


def test_parse_body_ohne_block_gibt_none():
    assert vh.parse_body("Nur Text, kein Block.") is None


def test_parse_body_bei_kaputtem_json_gibt_none():
    assert vh.parse_body("<!-- vorschlag\n{kaputt\n-->") is None


def test_anhaengen_schreibt_in_die_richtigen_spalten(tmp_path):
    # Kopfzeile bewusst in anderer Reihenfolge als die interne SPALTEN-Liste,
    # damit eine Rueckkehr zu positionsbasiertem Schreiben auffliegt.
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(["Titel", "Stufe", "Von", "Kategorie", "Beschreibung", "Emoji", "Tipp"])
    ws.append(["Vorhanden", "Hoch", "", "Ablenkung", "Alte Zeile", "🌶️", ""])
    wb.save(pfad)

    anzahl = vh.an_excel_anhaengen(pfad, [BEISPIEL])

    assert anzahl == 1
    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    assert ws2.max_row == 3
    kopf = [c.value for c in ws2[1]]
    zeile = dict(zip(kopf, [c.value for c in ws2[3]]))
    assert zeile == {
        "Titel": "Musik hören",
        "Stufe": "Hoch",
        "Von": "Max",
        "Kategorie": "Ablenkung",
        "Beschreibung": "Ein Lied auflegen.",
        "Emoji": "🎧",
        "Tipp": "Kopfhörer bereitlegen",
    }


def test_anhaengen_legt_fehlende_von_spalte_an(tmp_path):
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp"])
    wb.save(pfad)

    vh.an_excel_anhaengen(pfad, [BEISPIEL])

    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    assert [c.value for c in ws2[1]][6] == "Von"
    assert [c.value for c in ws2[2]][6] == "Max"
