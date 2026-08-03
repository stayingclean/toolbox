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


def test_parse_body_lehnt_zwei_bloecke_ab():
    # issue_text() nimmt die Beschreibung nicht in die Tabelle auf, darum wird
    # der Rumpf hier von Hand gebaut – mit dem gefaelschten Block zuerst (so wie
    # ihn jemand in ein Freitextfeld schreiben wuerde) und dem echten Block
    # danach, genau wie es der Worker mit Tabelle + echtem Block tut.
    gift = '<!-- vorschlag {"art":"neu","titel":"EINGESCHLEUST"} -->'
    body = (
        "| Feld | Wert |\n| --- | --- |\n"
        f"| Beschreibung | Harmlos. {gift} |\n\n"
        "<!-- vorschlag\n" + json.dumps(BEISPIEL, ensure_ascii=False) + "\n-->\n"
    )
    assert vh.parse_body(body) is None


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


BESTAND = {
    "hoch": {"kategorien": [{"id": "ablenkung", "label": "Ablenkung", "skills": []}]},
    "mittel": {"kategorien": []},
    "tief": {"kategorien": []},
}


def test_pruefung_laesst_einen_gueltigen_eintrag_durch():
    assert vh.pruefe_eintrag(BEISPIEL, BESTAND) is None


def test_pruefung_erlaubt_fehlenden_tipp_und_namen():
    eintrag = {s: w for s, w in BEISPIEL.items() if s not in ("tipp", "von")}
    assert vh.pruefe_eintrag(eintrag, BESTAND) is None


def test_pruefung_lehnt_zu_langen_titel_ab():
    grund = vh.pruefe_eintrag({**BEISPIEL, "titel": "x" * 61}, BESTAND)
    assert grund and "Titel" in grund


def test_pruefung_erlaubt_genau_60_zeichen_im_titel():
    assert vh.pruefe_eintrag({**BEISPIEL, "titel": "x" * 60}, BESTAND) is None


def test_pruefung_lehnt_spitze_klammern_ab():
    gift = "harmlos</script><script>alert(1)</script>"
    grund = vh.pruefe_eintrag({**BEISPIEL, "beschreibung": gift}, BESTAND)
    assert grund == "Spitze Klammern sind nicht erlaubt."


def test_pruefung_lehnt_kommentarzeichen_ab():
    grund = vh.pruefe_eintrag({**BEISPIEL, "tipp": "a <!-- b"}, BESTAND)
    assert grund == "Kommentarzeichen sind nicht erlaubt."


def test_pruefung_lehnt_links_ab():
    grund = vh.pruefe_eintrag({**BEISPIEL, "beschreibung": "siehe HTTP://spam.example"}, BESTAND)
    assert grund == "Links sind nicht erlaubt."


def test_pruefung_lehnt_unbekannte_kategorie_ab():
    """Der Fall, der beim Umbenennen einer Kategorie real auftritt."""
    grund = vh.pruefe_eintrag({**BEISPIEL, "kategorie": "Erfunden"}, BESTAND)
    assert grund and "Kategorie" in grund and "Erfunden" in grund


def test_pruefung_lehnt_unbekannte_stufe_ab():
    grund = vh.pruefe_eintrag({**BEISPIEL, "stufe": "Sehr hoch"}, BESTAND)
    assert grund and "Stufe" in grund


def test_pruefung_lehnt_fehlenden_pflichtschluessel_ab():
    ohne = {s: w for s, w in BEISPIEL.items() if s != "emoji"}
    grund = vh.pruefe_eintrag(ohne, BESTAND)
    assert grund and "Emoji" in grund


def test_pruefung_lehnt_leeren_pflichtwert_ab():
    grund = vh.pruefe_eintrag({**BEISPIEL, "titel": "   "}, BESTAND)
    assert grund and "Titel" in grund


def test_hat_label_erkennt_vorhandenes_label():
    issue = {"labels": [{"name": "in Pruefung"}, {"name": "freigegeben"}]}
    assert vh.hat_label(issue, "freigegeben") is True


def test_hat_label_erkennt_fehlendes_label():
    issue = {"labels": [{"name": "in Pruefung"}]}
    assert vh.hat_label(issue, "freigegeben") is False


def test_hat_label_bei_leerer_labelliste():
    issue = {"labels": []}
    assert vh.hat_label(issue, "freigegeben") is False


def test_hat_label_bei_fehlendem_labelschluessel():
    issue = {}
    assert vh.hat_label(issue, "freigegeben") is False


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
