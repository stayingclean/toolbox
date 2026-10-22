"""Prüft den Rechenkern aus docs/budgetvorlage.html (Anpassungen und Stichtage).

Der Kern wird nicht nachgebaut, sondern aus der ausgelieferten HTML
herausgeschnitten und in Node ausgeführt (tests/budget_treiber.mjs).
Geprüft wird damit genau der Code, der im Browser läuft.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SEITE = ROOT / "docs" / "budgetvorlage.html"
TREIBER = ROOT / "tests" / "budget_treiber.mjs"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="Node wird gebraucht, um den Rechenkern auszuführen",
)

SCHEMA = {
    "einnahmen": [{"id": "lohn"}],
    "fix": [{"id": "handy"}, {"id": "fitness"}, {"id": "hausrat"},
            {"id": "kasse"}, {"id": "rest"}],
}
WERTE = {
    "lohn.monatlich": 3800, "handy.monatlich": 60, "fitness.monatlich": 89,
    "hausrat.monatlich": 42, "kasse.monatlich": 410, "rest.monatlich": 3319,
}
ANPASSUNGEN = {
    "handy":   {"jaehrlich": None, "monatlich": 0,   "ab": "2027-01-01"},
    "fitness": {"jaehrlich": None, "monatlich": 0,   "ab": "2027-01-01"},
    "hausrat": {"jaehrlich": None, "monatlich": 28,  "ab": "2027-04-01"},
    "kasse":   {"jaehrlich": None, "monatlich": 340, "ab": None},
}


def kern(funktion, *args):
    """Ruft eine Funktion des Rechenkerns in Node auf und gibt das Ergebnis zurück."""
    lauf = subprocess.run(
        ["node", str(TREIBER), str(SEITE), funktion, json.dumps(list(args))],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert lauf.returncode == 0, lauf.stderr
    return json.loads(lauf.stdout)


def test_leer_ist_keine_anpassung():
    assert kern("anpassungBetrag", {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}) is None
    assert kern("anpassungBetrag", None) is None


def test_null_ist_ein_gueltiger_zielbetrag():
    assert kern("anpassungBetrag", {"jaehrlich": None, "monatlich": 0, "ab": None}) == {"jaehrlich": 0, "monatlich": 0}


def test_jaehrlich_gewinnt_sonst_monatlich_mal_zwoelf():
    assert kern("anpassungBetrag", {"jaehrlich": None, "monatlich": 50, "ab": None}) == {"jaehrlich": 600, "monatlich": 50}
    assert kern("anpassungBetrag", {"jaehrlich": 1200, "monatlich": None, "ab": None}) == {"jaehrlich": 1200, "monatlich": 100}


def test_staende_in_reihenfolge_mit_offen_am_schluss():
    liste = kern("stichtagListe", ANPASSUNGEN, "2026-10-22")
    assert [s["key"] for s in liste] == ["heute", "2027-01-01", "2027-04-01", "offen"]


def test_zwei_anpassungen_am_selben_datum_ergeben_einen_stand():
    assert sum(1 for s in kern("stichtagListe", ANPASSUNGEN, "2026-10-22") if s["key"] == "2027-01-01") == 1


def test_offen_fehlt_ohne_undatierte_anpassung():
    nur_datiert = {k: v for k, v in ANPASSUNGEN.items() if v["ab"]}
    assert "offen" not in [s["key"] for s in kern("stichtagListe", nur_datiert, "2026-10-22")]


def test_verstrichenes_datum_ist_faellig_aber_ein_eigener_stand():
    liste = kern("stichtagListe", ANPASSUNGEN, "2027-02-01")
    faellig = {s["key"]: s["faellig"] for s in liste}
    assert faellig == {"heute": False, "2027-01-01": True, "2027-04-01": False, "offen": False}


def test_unlesbares_datum_erzeugt_keinen_stand():
    for kaputt in ("01.01.2027", "", "demnaechst", "2027-13-99"):
        liste = kern("stichtagListe", {"handy": {"jaehrlich": None, "monatlich": 0, "ab": kaputt}}, "2026-10-22")
        assert [s["key"] for s in liste] == ["heute", "offen"]


def test_anpassung_ohne_betrag_zaehlt_nicht_mit():
    liste = kern("stichtagListe", {"handy": {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}}, "2026-10-22")
    assert [s["key"] for s in liste] == ["heute"]


def test_heute_wendet_nichts_an():
    assert kern("werteFuerStand", WERTE, ANPASSUNGEN, "heute") == WERTE


def test_stand_setzt_beide_schluessel():
    neu = kern("werteFuerStand", WERTE, ANPASSUNGEN, "2027-01-01")
    assert neu["handy.monatlich"] == 0 and neu["handy.jaehrlich"] == 0
    assert neu["hausrat.monatlich"] == 42   # spaeteres Datum, noch nicht angewendet
    assert neu["kasse.monatlich"] == 410    # ohne Datum, nur im Stand "offen"


def test_die_vier_differenzen_aus_dem_entwurf():
    ergebnis = {}
    for key in ("heute", "2027-01-01", "2027-04-01", "offen"):
        werte = kern("werteFuerStand", WERTE, ANPASSUNGEN, key)
        ergebnis[key] = round(kern("summen", SCHEMA, werte)["diffM"], 2)
    assert ergebnis == {"heute": -120, "2027-01-01": 29, "2027-04-01": 43, "offen": 113}


def test_werte_fuer_stand_laesst_das_original_in_ruhe():
    kern("werteFuerStand", WERTE, ANPASSUNGEN, "offen")
    assert WERTE["handy.monatlich"] == 60


# --- Datenmodell und Dateiformat v5 ------------------------------------------
# Statische Prüfungen der ausgelieferten Datei (wie in tests/test_plakat.py):
# Das Datenmodell hängt am DOM und lässt sich nicht im Treiber ausführen.


def _seite_text():
    return SEITE.read_text(encoding="utf-8")


def test_dateiformat_ist_fuenf():
    text = _seite_text()
    assert "const FILE_FORMAT_VERSION = 5;" in text
    assert re.search(r"SUPPORTED_VERSIONS = new Set\(\[1, 2, 3, 4, 5\]\)", text)


def test_neue_version_traegt_die_neuen_felder():
    text = _seite_text()
    block = text[text.index("function makeBlankVersion"):][:700]
    assert "adjustments: {}" in block and "privateNote: ''" in block


def test_kein_oder_null_auf_einem_anpassungsbetrag():
    """`|| 0` wuerde aus jeder leeren Anpassung eine Nullsetzung machen."""
    text = _seite_text()
    assert not re.search(
        r"(adjustments|anpassung)\w*\.(jaehrlich|monatlich)\s*\|\|", text, re.I
    )


def test_filter_gegen_unbekannte_zeilen_existiert():
    text = _seite_text()
    assert "function bekannteAnpassungen" in text
    block = text[text.index("function bekannteAnpassungen"):][:500]
    assert "lookupRow" in block or "ROW_INDEX" in block


# --- Die Zeile: Anpassungsfelder, Markierung, Einnahmen aufklappbar -----------


def test_einnahmen_bekommen_den_aufklappbereich():
    text = _seite_text()
    assert re.search(
        r"EXPANDABLE_GROUPS = new Set\(\['einnahmen', \.\.\.AUSGABEN_GROUPS\]\)", text
    )


def test_panel_traegt_drei_anpassungsfelder():
    text = _seite_text()
    block = text[text.index("function makeCommentRow"):][:3000]
    for feld in ("adj-jaehrlich", "adj-monatlich", "adj-ab"):
        assert feld in block, feld
    assert 'type="date"' in block or "type = 'date'" in block


def test_zeile_mit_anpassung_bleibt_zugeklappt_markiert():
    text = _seite_text()
    # Die Hauptzeile traegt KEINE Klasse, nur data-row-id und data-group.
    assert re.search(r"tr\[data-row-id\]\.has-adjustment\b", text)
    assert "--color-warning" in text[text.index("tr[data-row-id].has-adjustment"):][:400]


def test_unvollstaendige_anpassung_wird_angezeigt():
    """Datum ohne Betrag rechnet nicht - die Zeile muss es sagen."""
    assert "adj-unvollstaendig" in _seite_text()


def test_leerer_anpassungseintrag_wird_geloescht():
    text = _seite_text()
    block = text[text.index("function captureFormToActiveVersion"):][:3000]
    assert "delete" in block and "adjustments" in block


def test_unbekannte_zeilen_bleiben_erhalten_leere_huellen_nicht():
    """Beim Speichern: Eintraege fremder Zeilen mit Inhalt bleiben, leere nicht;
    bekannte Zeilen kommen nicht von hier (sie folgen den Feldern)."""
    eintraege = {
        "lohn": {"jaehrlich": 1, "monatlich": None, "ab": None},            # bekannt
        "alt_betrag": {"jaehrlich": 0, "monatlich": None, "ab": None},      # 0 ist Inhalt
        "alt_monat": {"jaehrlich": None, "monatlich": 5, "ab": None},
        "alt_datum": {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"},
        "alt_leer": {"jaehrlich": None, "monatlich": None, "ab": None},     # leere Huelle
        "alt_objekt": {},
    }
    ergebnis = kern("unbekannteAnpassungenBehalten", eintraege, ["lohn"])
    assert sorted(ergebnis) == ["alt_betrag", "alt_datum", "alt_monat"]
    assert ergebnis["alt_betrag"]["jaehrlich"] == 0


def test_capture_nutzt_den_filter_fuer_unbekannte_zeilen():
    text = _seite_text()
    block = text[text.index("function captureFormToActiveVersion"):][:3000]
    assert "unbekannteAnpassungenBehalten(" in block


# --- Die Staende in der Zusammenfassung ----------------------------------------


def test_zusammenfassung_hat_platz_fuer_die_staende():
    text = SEITE.read_text(encoding="utf-8")
    assert 'id="summaryStands"' in text
    assert text.index('id="differenceRow"') < text.index('id="summaryStands"')


def test_staende_haengen_nicht_am_versionsvergleich():
    """Der Vergleich ist bei einer Version ausgeblendet — die Staende nicht."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function recomputeAll"):][:6000]
    assert "isMultiVersion" not in block


def test_staende_kommen_aus_dem_kern():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function recomputeAll"):][:6000]
    for fn in ("stichtagListe", "werteFuerStand", "summen"):
        assert fn in block, fn


def test_jede_leseseite_filtert_unbekannte_zeilen():
    """Eine Anpassung auf einer rowId, die das Schema nicht kennt, darf
    weder gerechnet noch angezeigt werden."""
    text = SEITE.read_text(encoding="utf-8")
    for name in ("stichtagListe", "werteFuerStand"):
        # Die Definition im Kern ausnehmen, nur Aufrufstellen pruefen.
        for treffer in re.finditer(r"(?<!function )\b" + name + r"\(", text):
            umfeld = text[max(0, treffer.start() - 300):treffer.end() + 300]
            assert "bekannteAnpassungen" in umfeld, f"ungefiltert bei {name}"


def test_heute_wird_nur_an_einer_stelle_gelesen():
    """Wer heute fuer die Faelligkeit braucht, geht durch heuteIso()."""
    text = SEITE.read_text(encoding="utf-8")
    assert text.count("function heuteIso(") == 1
    block = text[text.index("function heuteIso("):][:400]
    assert "new Date()" in block
    assert len(re.findall(r"new Date\(\)(?!\.toISOString)", text)) == 1


def test_eingabe_in_anpassungsfeld_rechnet_die_zusammenfassung_neu():
    """Die Anpassungsfelder aendern nur die Version, nicht die Betragsfelder:
    ohne eigenen Aufruf bliebe die Zusammenfassung stehen."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function handleAdjInputEvent"):][:1500]
    assert "recomputeAll()" in block
