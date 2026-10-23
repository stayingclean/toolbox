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


def test_kommentarbereich_traegt_keine_anpassungsfelder_mehr():
    """Die Anpassung ist eine eigene Tabellenzeile geworden; im
    Aufklappbereich steht nur noch der Kommentar – und der Knopf, der die
    Zeile erzeugt."""
    block = _funktionsblock("makeCommentRow")
    for feld in ("adj-jaehrlich", "adj-monatlich", "adj-ab"):
        assert feld not in block, feld
    assert "adj-add-btn" in block, "der Knopf «Anpassung erfassen» fehlt"


def test_anpassung_ist_eine_eigene_tabellenzeile():
    """Spaltenbuendig zur Position: Datum in der Beschriftungsspalte, die
    Betraege unter den erfassten Betraegen, der Unterschied in Spalte vier."""
    block = _funktionsblock("makeAdjustmentRow")
    for feld in ("adj-jaehrlich", "adj-monatlich", "adj-ab"):
        assert feld in block, feld
    assert 'type="date"' in block or "'date'" in block
    assert "adj-row" in block and "adjFor" in block
    assert "adj-delta" in block, "die vierte Spalte zeigt den Unterschied"


def test_anpassungszeile_traegt_kein_data_row_id():
    """`$('tr[data-row-id=…]')` steht an drei Stellen und nimmt den ersten
    Treffer. Eine zweite Zeile mit derselben Kennung waere ein stiller
    Fehler – die Anpassungszeile heisst darum data-adj-for."""
    block = _funktionsblock("makeAdjustmentRow")
    assert "dataset.rowId" not in block.split("querySelectorAll")[0], \
        "das <tr> der Anpassung darf keine data-row-id tragen"
    assert "dataset.adjFor" in block


def test_zeilen_id_kennt_die_anpassungszeile():
    """Sonst gilt der Wechsel zwischen den Anpassungsfeldern als Verlassen der
    Zeile und das Datum faellt weg (der Fehler aus Commit 5b143b5)."""
    block = _funktionsblock("zeilenIdVon")
    assert "adj-row" in block and "adjFor" in block


def test_zeile_mit_anpassung_bleibt_zugeklappt_markiert():
    text = _seite_text()
    # Die Hauptzeile traegt KEINE Klasse, nur data-row-id und data-group.
    assert re.search(r"tr\[data-row-id\]\.has-adjustment\b", text)
    assert "--color-warning" in text[text.index("tr[data-row-id].has-adjustment"):][:400]


def test_unvollstaendige_anpassung_gibt_es_nicht_mehr():
    """Eine Anpassung ohne Betrag kann nicht mehr entstehen (Sperre am Datumsfeld),
    also steht auch nichts mehr da, das einen solchen Zustand meldet."""
    text = _seite_text()
    for rest in ("adj-unvollstaendig", "data-adj-incomplete", "adjIncomplete", "unvollstaendig", "unvollständig"):
        assert rest not in text, rest


def test_leerer_anpassungseintrag_wird_geloescht():
    text = _seite_text()
    block = text[text.index("function captureFormToActiveVersion"):][:3000]
    assert "delete" in block and "adjustments" in block


def test_unbekannte_zeilen_bleiben_erhalten_leere_huellen_nicht():
    """Beim Speichern: Eintraege fremder Zeilen mit Betrag bleiben; Huellen ohne
    Betrag nicht - auch nicht, wenn nur ein Datum drinsteht (das ist keine
    Anpassung). Bekannte Zeilen kommen nicht von hier (sie folgen den Feldern)."""
    eintraege = {
        "lohn": {"jaehrlich": 1, "monatlich": None, "ab": None},            # bekannt
        "alt_betrag": {"jaehrlich": 0, "monatlich": None, "ab": None},      # 0 ist Inhalt
        "alt_monat": {"jaehrlich": None, "monatlich": 5, "ab": None},
        "alt_datum": {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"},
        "alt_leer": {"jaehrlich": None, "monatlich": None, "ab": None},     # leere Huelle
        "alt_objekt": {},
    }
    ergebnis = kern("unbekannteAnpassungenBehalten", eintraege, ["lohn"])
    assert sorted(ergebnis) == ["alt_betrag", "alt_monat"]
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
    assert "recomputeAll()" in _funktionsblock("handleAdjInputEvent")


# --- Knopf «Anpassungen» in der Kopfleiste ------------------------------------
# Die Gruppierung und die Regel, welche Anpassungen eine neue Version aus einem
# Stand mitnimmt, sind reine Logik und laufen im Treiber. Der Rest hängt am DOM
# und wird als Text der ausgelieferten Datei geprüft.


def gruppen(anpassungen=None, werte=None, heute="2026-10-22"):
    anpassungen = ANPASSUNGEN if anpassungen is None else anpassungen
    staende = kern("stichtagListe", anpassungen, heute)
    return kern("anpassungsGruppen", anpassungen, staende, WERTE if werte is None else werte)


def test_gruppen_in_der_reihenfolge_der_staende_ohne_heute():
    assert [g["key"] for g in gruppen()] == ["2027-01-01", "2027-04-01", "offen"]


def test_zwei_positionen_am_selben_datum_stehen_in_einer_gruppe():
    erste = gruppen()[0]
    assert sorted(e["rowId"] for e in erste["eintraege"]) == ["fitness", "handy"]


def test_eintrag_nennt_alt_neu_und_delta():
    erste = {e["rowId"]: e for e in gruppen()[0]["eintraege"]}
    assert erste["handy"]["altM"] == 60 and erste["handy"]["neuM"] == 0
    assert erste["handy"]["deltaM"] == -60
    assert erste["fitness"]["deltaM"] == -89
    assert erste["handy"]["altY"] == 720 and erste["handy"]["deltaY"] == -720


def test_gruppensumme_ist_die_summe_der_deltas():
    erste = gruppen()[0]
    assert erste["deltaM"] == -149 and erste["deltaY"] == -149 * 12


def test_gruppe_ohne_datum_heisst_offen_und_ist_nie_faellig():
    letzte = gruppen(heute="2099-01-01")[-1]
    assert letzte["key"] == "offen" and letzte["faellig"] is False
    assert [e["rowId"] for e in letzte["eintraege"]] == ["kasse"]


def test_verstrichenes_datum_ist_in_der_gruppe_faellig():
    nach_datum = {g["key"]: g["faellig"] for g in gruppen(heute="2027-02-01")}
    assert nach_datum == {"2027-01-01": True, "2027-04-01": False, "offen": False}


def test_jaehrlicher_istwert_wird_zum_monatlichen_alt():
    werte = {"hausrat.jaehrlich": 600}
    eintrag = gruppen(werte=werte)[1]["eintraege"][0]
    assert eintrag["altY"] == 600 and eintrag["altM"] == 50
    assert eintrag["deltaM"] == 28 - 50


def test_anpassung_ohne_betrag_steht_in_keiner_gruppe():
    nur_datum = {"handy": {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}}
    assert gruppen(nur_datum) == []


def test_neue_version_nimmt_spaetere_und_undatierte_mit():
    rest = kern("anpassungenNachStand", ANPASSUNGEN, "2027-01-01")
    assert sorted(rest) == ["hausrat", "kasse"]
    assert rest["hausrat"] == ANPASSUNGEN["hausrat"]     # unveraendert


def test_neue_version_aus_dem_letzten_datum_behaelt_nur_undatierte():
    assert sorted(kern("anpassungenNachStand", ANPASSUNGEN, "2027-04-01")) == ["kasse"]


def test_neue_version_aus_offen_behaelt_nichts_eingeloestes():
    assert kern("anpassungenNachStand", ANPASSUNGEN, "offen") == {}


def test_neue_version_nimmt_keine_anpassung_ohne_betrag_mit():
    """Ein Datum ohne Betrag ist keine Anpassung. Es wandert nicht in eine neue
    Version, sonst entstünde dort der Zustand, den die Sperre verhindert."""
    mit_huelle = dict(ANPASSUNGEN, strom={"jaehrlich": None, "monatlich": None, "ab": "2026-12-01"})
    for key in ("2026-12-01", "2027-01-01", "2027-04-01", "offen"):
        assert "strom" not in kern("anpassungenNachStand", mit_huelle, key), key


AUSWAHLEN = (
    [],                                   # alles angehakt, wie bisher
    ["handy"],                            # eine von zwei am selben Datum abgewählt
    ["handy", "fitness"],                 # das ganze Datum abgewählt
    ["hausrat", "kasse"],                 # bei «offen»/April: spätere Zeilen
    ["handy", "fitness", "hausrat", "kasse"],   # alles abgewählt
    ["gibt_es_nicht"],                    # eine Zeile, die der Stand nie einlöst
)


def test_eingeloeste_und_mitgenommene_decken_alle_ab():
    """Was in der neuen Version fehlt, steckt in den Werten: keine Anpassung geht
    verloren und keine wird doppelt gezählt - auch mit abgewählten Positionen."""
    for key in ("2027-01-01", "2027-04-01", "offen"):
        for abgewaehlt in AUSWAHLEN:
            rest = kern("anpassungenNachStand", ANPASSUNGEN, key, abgewaehlt)
            neu = kern("werteFuerStand", WERTE, ANPASSUNGEN, key, abgewaehlt)
            for rowId, a in ANPASSUNGEN.items():
                if rowId in rest:
                    assert neu[rowId + ".monatlich"] == WERTE[rowId + ".monatlich"], (key, abgewaehlt, rowId)
                    assert rest[rowId] == a, (key, abgewaehlt, rowId)
                else:
                    assert neu[rowId + ".monatlich"] == a["monatlich"], (key, abgewaehlt, rowId)


def test_jede_anpassung_ist_entweder_eingeloest_oder_geblieben():
    """Die Invariante ohne Umweg über die Werte: loestEin ist die einzige Regel,
    und was sie verneint, bleibt als Anpassung stehen."""
    for key in ("heute", "2027-01-01", "2027-04-01", "offen"):
        for abgewaehlt in AUSWAHLEN:
            rest = kern("anpassungenNachStand", ANPASSUNGEN, key, abgewaehlt)
            for rowId, a in ANPASSUNGEN.items():
                loest = kern("loestEin", a, key, rowId, abgewaehlt)
                assert loest == (rowId not in rest), (key, abgewaehlt, rowId)


def test_nach_stand_laesst_das_original_in_ruhe():
    kern("anpassungenNachStand", ANPASSUNGEN, "offen")
    assert ANPASSUNGEN["handy"]["ab"] == "2027-01-01"


def test_knopf_nennt_die_anzahl():
    text = SEITE.read_text(encoding="utf-8")
    assert 'id="adjustmentsBtn"' in text and 'id="adjustmentsPanel"' in text


def test_knopf_erscheint_nur_mit_anpassungen():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function renderAdjustmentList"):][:4000]
    assert "hidden" in block and "Anpassung" in block


def test_gesprungen_wird_ueber_die_position_nicht_das_datum():
    """Mehrere Positionen koennen auf dasselbe Datum fallen."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function renderAdjustmentList"):][:4000]
    assert "springeZuZeile" in block
    assert re.search(r"springeZuZeile\([^)]*rowId", block)


def test_sprung_zieht_die_klebende_kopfleiste_ab():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function springeZuZeile"):][:800]
    assert "sticky-head" in block or "stickyHead" in block


def test_je_datumsgruppe_ein_versionsknopf():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function renderAdjustmentList"):][:4000]
    assert "Neue Version aus diesem Stand" in block


def test_neue_version_aus_stand_basiert_auf_der_aktiven_version():
    """Ohne Basis gaebe es keinen Vergleich: «Δ vs. Basis» braucht basedOn."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function neueVersionAusStand"):][:2500]
    assert "basedOnId: " in block and "getActiveVersion" in block
    assert "anpassungenNachStand" in block and "werteFuerStand" in block
    assert "bekannteAnpassungen" in block


def test_panel_schliesst_bei_klick_ausserhalb_und_escape():
    text = SEITE.read_text(encoding="utf-8")
    assert "function closeAdjustmentsPanel" in text
    ende = text[text.index("function init"):]
    assert "adjustmentsPanel" in ende and "Escape" in ende


def test_kopfleiste_traegt_den_knopf_neben_den_reitern():
    text = SEITE.read_text(encoding="utf-8")
    bar = text[text.index('id="versionBar"'):text.index("/sticky-head")]
    assert bar.index('id="versionTabs"') < bar.index('id="adjustmentsBtn"')


# --- Vorschau: Schreibsperre, Stand-Leiste, Uebersicht ------------------------
# Die Vorschau stellt GERECHNETE Werte ins Formular. Schreibt irgendetwas sie
# zurueck in die Version, sind die erfassten Zahlen der Person weg. Darum stehen
# die Tests zur Sperre zuerst. Sie haengt am DOM und laeuft nicht im Treiber;
# geprueft wird darum der Text der ausgelieferten Datei - fuer die Sperre ist
# genau die Stelle im Code die Zusicherung.


def _funktionsblock(name):
    """Der Rumpf einer Funktion: von ihrem Kopf bis zur naechsten auf gleicher
    Einrueckung. Genauer als ein Fenster fester Laenge, das in die naechste
    Funktion hineinlaeuft."""
    text = _seite_text()
    ab = text.index("function " + name)
    weiter = text.find("\n    function ", ab + 1)
    return text[ab:weiter if weiter > 0 else len(text)]


def test_vorschau_schreibt_nicht_zurueck():
    """Sonst ersetzt der naechste Aufruf die erfassten Werte durch gerechnete."""
    text = SEITE.read_text(encoding="utf-8")
    ab = text.index("function captureFormToActiveVersion")
    assert "if (state.previewStand) return;" in text[ab:ab + 500], \
        "die Sperre fehlt am Anfang von captureFormToActiveVersion"


def test_vorschau_ist_kein_versionsreiter():
    """In derselben tablist behauptete sie, die aktive Version sei inaktiv."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index('id="previewBtn"')-400:text.index('id="previewBtn"')+400]
    assert 'role="tab"' not in block


def test_vorschau_sperrt_die_eingabefelder():
    """`.disabled = ` steht schon viermal in der Datei — hier zaehlt nur,
    dass die Sperre an `previewStand` haengt."""
    text = SEITE.read_text(encoding="utf-8")
    ab = text.index("function enterPreview")
    block = text[ab:ab + 1500]
    assert re.search(r"\.disabled = (true|Boolean\(|!!)", block)
    assert "previewStand" in block


def test_speichern_laeuft_in_der_vorschau_normal_weiter():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function serialize"):][:900]
    assert "previewStand" not in block, "serialize darf nicht auf die Vorschau reagieren"


def test_vorschau_erfasst_einmal_bevor_sie_sperrt():
    """Sonst waeren die zuletzt getippten Werte beim Verlassen verloren:
    captureFormToActiveVersion muss laufen, SOLANGE previewStand noch null ist."""
    block = _funktionsblock("enterPreview")
    assert block.index("captureFormToActiveVersion()") < block.index("state.previewStand ="), \
        "enterPreview setzt die Sperre, bevor es erfasst hat"


def test_vorschau_sperrt_betraege_und_anpassungen():
    block = _funktionsblock("enterPreview")
    assert "amount-input" in block and "adj-input" in block


def test_vorschau_sagt_dass_hier_nichts_erfasst_wird():
    text = _seite_text()
    leiste = text[text.index('id="previewBar"'):]
    leiste = leiste[:leiste.index("</div>", leiste.index('id="previewLeaveBtn"'))]
    assert "nichts erfasst" in leiste


def test_vorschau_hat_drei_wege_hinaus():
    """Ein Zustand, aus dem man nicht sichtbar herauskommt, waere das Schlimmste."""
    text = _seite_text()
    assert "function leavePreview" in text
    # der Vorschau-Knopf selbst und Escape haengen in init
    ende = text[text.index("function init"):]
    assert "previewBtn" in ende and "leavePreview" in ende and "Escape" in ende
    # ein Versionsreiter: switchVersion ruft leavePreview als Erstes
    sw = _funktionsblock("switchVersion")
    assert sw.index("leavePreview()") < sw.index("captureFormToActiveVersion()")


def test_vorschau_stellt_die_felder_wieder_frei():
    block = _funktionsblock("leavePreview")
    assert re.search(r"\.disabled = false", block)
    assert "state.previewStand = null" in block
    assert "hydrateFormFromActiveVersion()" in block


def test_vorschau_knopf_erscheint_nur_mit_anpassungen():
    block = _funktionsblock("renderAdjustmentList")
    assert re.search(r"previewBtn'\)[\s\S]{0,400}?hidden", block)


def test_stand_leiste_nur_in_der_vorschau():
    assert 'id="previewBar"' in _seite_text()
    block = _funktionsblock("renderPreviewBar")
    assert re.search(r"hidden = !state\.previewStand", block)


def test_heute_in_der_stand_leiste_verlaesst_die_vorschau_nicht():
    """«heute» ist das gesperrte Abbild der Version, kein Ausgang."""
    block = _funktionsblock("renderPreviewBar")
    assert "enterPreview(" in block and "leavePreview(" not in block


def test_uebersicht_behaelt_das_gate_auf_zwei_versionen():
    """Die Staende kommen dazu, wo die Uebersicht ohnehin sichtbar ist."""
    block = _funktionsblock("renderVersionsOverview")
    assert "if (!isMultiVersion())" in block and "section.hidden = true;" in block


def test_uebersicht_setzt_die_staende_ab():
    block = _funktionsblock("renderVersionsOverview")
    assert "overview-stand-row" in block
    text = _seite_text()
    assert ".overview-stand-row" in text[:text.index("function renderVersionsOverview")], \
        "zur abgesetzten Zeile fehlt das CSS"


def test_vorschau_rechnet_aus_der_version_nicht_aus_dem_formular():
    """Im Formular stehen in der Vorschau schon gerechnete Werte. Wer von dort
    weiterrechnet, zeigt in der Anpassungsliste den Zielbetrag als Istwert und
    in den Stand-Zeilen ein Delta von 0."""
    vorschau = _funktionsblock("fuelleVorschau")
    assert "active.values" in vorschau and "werteFuerStand(" in vorschau
    assert "formWerte" not in vorschau
    rechnen = _funktionsblock("recomputeAll")
    assert re.search(r"state\.previewStand[^\n]*active\.values", rechnen), \
        "recomputeAll muss in der Vorschau aus der Version rechnen"


def test_vorschau_oeffnet_den_ersten_stand_nach_heute():
    staende = kern("stichtagListe", ANPASSUNGEN, "2026-10-22")
    assert kern("ersterVorschauStand", staende) == "2027-01-01"


def test_vorschau_ohne_stichtag_zeigt_heute():
    """Ohne Anpassung mit Betrag gibt es nur «heute» — und keinen Knopf."""
    assert kern("ersterVorschauStand", kern("stichtagListe", {}, "2026-10-22")) == "heute"
    assert kern("ersterVorschauStand", []) == "heute"


def test_offen_ist_der_erste_stand_wenn_kein_datum_gesetzt_ist():
    nur_offen = {"kasse": ANPASSUNGEN["kasse"]}
    staende = kern("stichtagListe", nur_offen, "2026-10-22")
    assert kern("ersterVorschauStand", staende) == "offen"


def test_uebersicht_zeigt_je_stand_das_delta_zur_version():
    """Die abgesetzten Zeilen rechnen aus den erfassten Werten der Version:
    Differenz des Stands minus Differenz der Version — die Spalte «Δ vs. Basis»."""
    jetzt = kern("summen", SCHEMA, WERTE)["diffY"]
    deltas = {}
    for key in ("2027-01-01", "2027-04-01", "offen"):
        werte = kern("werteFuerStand", WERTE, ANPASSUNGEN, key)
        deltas[key] = round(kern("summen", SCHEMA, werte)["diffY"] - jetzt, 2)
    assert deltas == {"2027-01-01": 149 * 12, "2027-04-01": 163 * 12, "offen": 233 * 12}


def test_eingabe_handler_schreiben_in_der_vorschau_nicht_in_die_version():
    """Die Sperre sitzt in captureFormToActiveVersion. Ein Handler, der direkt
    in die aktive Version schreibt, geht daran vorbei — heute unerreichbar
    (die Felder sind in der Vorschau `disabled` und feuern keine Events), aber
    das haengt an einem Attribut, das eine andere Funktion setzt. Kommentare
    sind bewusst ausgenommen: sie werden nicht gerechnet und duerfen durch."""
    text = _seite_text()
    geprueft = []
    for treffer in re.finditer(r"function (handle\w+)\(", text):
        name = treffer.group(1)
        block = _funktionsblock(name)
        if not re.search(r"active\.(values|adjustments)\s*(\[|=)", block):
            continue
        geprueft.append(name)
        assert "if (state.previewStand) return;" in block, \
            f"{name} schreibt in die Version, ohne die Vorschau-Sperre"
    assert "handleAdjInputEvent" in geprueft, \
        "der bekannte Schreibweg wurde nicht mehr gefunden — pruefe den Suchausdruck"


def test_nur_die_reiter_stehen_in_der_tablist():
    """Eine tablist mit Nicht-Reiter-Kindern ist ungueltiges ARIA; Screenreader
    duerfen solche Kinder in der Reiter-Navigation ueberspringen — und einer von
    ihnen ist der Weg aus dem gesperrten Formular hinaus."""
    text = _seite_text()
    bar = text[text.index('id="versionBar"'):text.index("/sticky-head")]
    for knopf in ('id="addVersionBtn"', 'id="adjustmentsBtn"', 'id="previewBtn"'):
        assert knopf in bar, knopf
    # Die Rolle haengt an der Reiterliste, nicht an der ganzen Leiste.
    assert re.search(r'id="versionTabs"[^>]*role="tablist"', text)
    kopf = text[text.index('id="versionBar"'):text.index('id="versionTabs"')]
    assert "tablist" not in kopf, "die Leiste selbst darf keine tablist sein"


# ---------------------------------------------------------------------------
# Private Notiz, Druck und Hinweistexte (Task 7)
#
# «Privat» heisst hier: wird nicht mitgedruckt, ausser das Haekchen ist gesetzt.
# Es heisst NICHT: steht nicht in der Datei. Das ist ausdruecklich so entschieden.
# Geschuetzt ist der versehentliche Ausdruck, nicht die Weitergabe der Datei.
# ---------------------------------------------------------------------------


def _druck_css():
    """Der @media-print-Block, vom Kopf bis zum naechsten Abschnittskommentar."""
    text = _seite_text()
    ab = text.index("@media print {")
    return text[ab:text.index("Version bar", ab)]


def test_private_notiz_druckt_nur_mit_haekchen():
    text = _seite_text()
    # Nur das Tag selbst pruefen: ein Fenster um die ID erwischte das
    # «checked» der Nachbar-Checkbox «Kommentare drucken».
    tag = re.search(r'<input[^>]*id="chkPrintPrivateNote"[^>]*>', text)
    assert tag, "die Checkbox fehlt"
    assert not re.search(r"\bchecked\b", tag.group(0)), \
        "die private Notiz darf nicht vorgewaehlt mitdrucken"
    assert "body.print-private-note" in text
    # «Kommentare drucken» behaelt seine Voreinstellung.
    assert re.search(r'<input[^>]*id="chkPrintComments"[^>]*\bchecked\b[^>]*>', text)


def test_private_notiz_ist_im_druck_sonst_unsichtbar():
    css = _druck_css()
    regel = re.search(r"#privateNoteBox\s*\{[^}]*display:\s*none", css)
    assert regel, "ohne Haekchen muss die Notiz im Druck weg sein"
    gezeigt = css.index("body.print-private-note")
    assert gezeigt > css.index("#privateNoteBox"), \
        "die Regel mit Haekchen muss nach der verbergenden stehen"


def test_private_notiz_steht_in_der_datei():
    """Ausdruecklich so entschieden — geschuetzt ist der Druck, nicht die Datei."""
    block = _funktionsblock("serialize")
    assert "privateNote" in block


def test_private_notiz_gehoert_zur_version_und_laeuft_durch_die_sperre():
    """Gefuellt aus der aktiven Version, zurueckgeschrieben in
    captureFormToActiveVersion — also hinter der Vorschau-Sperre, ohne zweite."""
    capture = _funktionsblock("captureFormToActiveVersion")
    assert "privateNote" in capture
    assert capture.index("privateNote") > capture.index("if (state.previewStand) return;")
    assert "privateNote" in _funktionsblock("hydrateFormFromActiveVersion")
    assert "privateNote" in _funktionsblock("resetAll")
    # Keine zweite Sperre fuer die Notiz: die eine am Kopf von capture genuegt.
    assert capture.count("state.previewStand") == 1


def test_private_notiz_ist_in_der_vorschau_gesperrt():
    """Capture schreibt dort nicht zurueck; ein offenes Feld verschluckte Tipparbeit."""
    assert "privateNote" in _funktionsblock("enterPreview")
    assert "privateNote" in _funktionsblock("leavePreview")


def test_private_notiz_verspricht_nicht_mehr_als_der_druck():
    text = _seite_text()
    box = text[text.index('id="privateNoteBox"'):][:1500]
    assert "nicht mitgedruckt" in box
    assert "Datei" in box, "der Hinweis muss sagen, dass die Notiz in der Datei steht"
    assert "verschl" not in box.lower() and "geheim" not in box.lower()


def test_private_notiz_hat_einen_druckblock_der_mitwaechst():
    """Eine Textarea waechst im Druck nicht mit; wie beim Kommentar druckt ein Block."""
    css = _druck_css()
    assert re.search(r"#privateNote\s*\{[^}]*display:\s*none", css)
    block = re.search(r"addEventListener\('beforeprint'.*?\n        \}\);", _seite_text(), re.S).group(0)
    assert "privateNote" in block


def test_gerechneter_stand_wird_im_ausdruck_gekennzeichnet():
    text = _seite_text()
    assert 'id="printStandMarker"' in text
    assert "gerechnet, nicht erfasst" in text


def test_genau_eine_kennzeichnung_im_ausdruck():
    """Task 6 brachte schon einen Hinweis nur fuer den Druck. Zwei davon
    stuenden doppelt auf dem Blatt."""
    text = _seite_text()
    assert text.count('id="printStandMarker"') == 1
    assert "preview-print-note" not in text, "der alte Hinweis darf nicht uebrig bleiben"


def test_kennzeichnung_steht_im_blattkopf_und_nur_im_druck():
    text = _seite_text()
    kopf = text[text.index('<header class="header">'):text.index("</header>")]
    assert 'id="printStandMarker"' in kopf
    css = _druck_css()
    assert re.search(r"body\.mode-preview\s+#printStandMarker", css)
    # Am Bildschirm sagt es die Stand-Leiste: ausserhalb des Druck-Blocks verborgen.
    ausserhalb = text.replace(css, "")
    assert re.search(r"#printStandMarker\s*\{[^}]*display:\s*none", ausserhalb)


def test_kennzeichnung_nennt_das_datum():
    assert kern("standKennzeichnung", "2027-01-01") == "Stand ab 01.01.2027 — gerechnet, nicht erfasst"


def test_kennzeichnung_fuer_offen():
    assert kern("standKennzeichnung", "offen") == "Stand mit allen Vorschlägen — gerechnet, nicht erfasst"


def test_heute_wird_nicht_gekennzeichnet():
    """«heute» zeigt die erfassten Werte; ein «gerechnet» darauf wäre falsch."""
    assert kern("standKennzeichnung", "heute") == ""
    assert kern("standKennzeichnung", None) == ""


def test_kennzeichnung_wird_beim_zeichnen_der_leiste_gesetzt():
    block = _funktionsblock("renderPreviewBar")
    assert "printStandMarker" in block and "standKennzeichnung" in block


def test_druckmarkierung_kennt_nur_noch_kommentare():
    """Anpassungen drucken nie mehr (Punkt 1): der beforeprint-Handler markiert
    deshalb keine Zeile mehr als «hat eine Anpassung»."""
    text = _seite_text()
    block = re.search(r"addEventListener\('beforeprint'.*?\n        \}\);", text, re.S).group(0)
    assert "has-comment" in block
    assert "has-adjustment" not in block, "die Anpassung druckt nicht mehr mit"
    assert "readAdjustmentFromDom" not in block


def test_vorschau_bietet_keine_neue_anpassung_an():
    """In der Vorschau sind alle Anpassungsfelder gesperrt; der Knopf boete
    eine Zeile an, in die sich nichts schreiben laesst."""
    text = _seite_text()
    assert re.search(r"body\.mode-preview\s+\.adj-add-btn\s*\{[^}]*display:\s*none", text)


def test_anpassungszeile_druckt_nie():
    """Der Ausdruck vom 22.10.2026 zeigte die Anpassung als leeres Formular auf
    dem Blatt («Neu jaehrlich», «Gilt ab», bei leerem Datum sogar
    «tt.mm.jjjj»). Sie bietet nur eine Moeglichkeit zum Erfassen und gehoert
    nicht auf Papier — auch nicht mit dem Haekchen «Kommentare drucken»."""
    css = _druck_css()
    assert re.search(r"\.adj-row\s*\{[^}]*display:\s*none", css)
    assert re.search(r"\.adj-add-btn\s*\{[^}]*display:\s*none", css), \
        "sonst druckt der Knopf «Anpassung erfassen» im Kommentarkasten mit"
    assert not re.search(r"\.adj-(row|add-btn)\s*\{[^}]*display:\s*(block|table|inline)", css), \
        "keine Regel darf die Anpassung im Druck wieder einblenden"
    assert "print-comments" not in css[css.index(".adj-row"):css.index(".adj-row") + 400]
    assert "adj-input" not in css, "die Druckfarben der Anpassungsfelder sind ueberfluessig"
    assert "adj-block" not in _seite_text(), "der alte Block im Aufklappbereich ist weg"


def test_zeile_mit_anpassung_druckt_nie_markiert():
    """Die Markierung erklaerte eine Anpassung, die nun gar nicht mehr druckt —
    eine hervorgehobene Zeile ohne Erklaerung bliebe auf dem Blatt zurueck."""
    css = _druck_css()
    assert re.search(r"tr\[data-row-id\]\.has-adjustment\s*>\s*td\s*\{[^}]*background:\s*transparent", css)
    assert not re.search(r"body\.print-comments[^{]*\.has-adjustment", css), \
        "auch mit dem Haekchen bleibt die Zeile unmarkiert"


def test_zeile_mit_anpassung_ohne_kommentar_zeigt_keinen_leeren_kommentarkasten():
    css = _druck_css()
    assert re.search(r"\.expander-row:not\(\.has-comment\)[^{]*\.comment-print[^{]*\{[^}]*display:\s*none", css)


def test_stand_zeilen_der_zusammenfassung_drucken_mit():
    css = _druck_css()
    assert "stand-row" not in css, "keine Druckregel darf die Stand-Zeilen verbergen"
    assert 'id="differenceRow"' in _seite_text()


def test_infobox_verweist_nicht_mehr_nur_auf_versionen():
    text = _seite_text()
    assert "modellieren Sie über <strong>weitere Budget-Versionen</strong>" not in text
    box = text[text.index('<div class="info-box">'):][:2500]
    assert "direkt in der Zeile" in box, "Anpassungen stehen jetzt in der Zeile"
    assert "grundsätzlich anderen Haushalt" in box, "Versionen sind fuer den anderen Haushalt da"


# --- Schlussrunde: Hinweis zum Stand, Jahresbeträge, Tastatur ----------------

def test_summen_rechnet_mit_jahresbetraegen():
    """Steuern, Versicherung und Rückstellungen werden jährlich erfasst. Alle
    anderen Kerntests nutzen *.monatlich; hier läuft der zweite Zweig von
    y || (m*12) und m || (y/12). Von Hand gerechnet:
    heute      Einnahmen 4000*12 = 48000; Ausgaben 2400 + 1200 = 3600
               -> diffY 44400, diffM 3700 (Ausgaben 200 + 100 im Monat)
    ab 1.1.27  Steuern auf 3000 jährlich (250 im Monat) -> Ausgaben 4200
               -> diffY 43800, diffM 4000 - (250 + 100) = 3650
    offen      dazu Versicherung auf 80 monatlich (960 im Jahr) -> Ausgaben 3960
               -> diffY 44040, diffM 4000 - (250 + 80) = 3670"""
    schema = {
        "einnahmen": [{"id": "lohn"}],
        "fix": [{"id": "steuern"}, {"id": "versicherung"}],
    }
    werte = {"lohn.monatlich": 4000, "steuern.jaehrlich": 2400, "versicherung.jaehrlich": 1200}
    anpassungen = {
        "steuern": {"jaehrlich": 3000, "monatlich": None, "ab": "2027-01-01"},
        "versicherung": {"jaehrlich": None, "monatlich": 80, "ab": None},
    }

    def rechne(key):
        s = kern("summen", schema, kern("werteFuerStand", werte, anpassungen, key))
        return {k: round(s[k], 2) for k in ("einnahmenY", "ausgabenY", "ausgabenM", "diffY", "diffM")}

    assert rechne("heute") == {"einnahmenY": 48000, "ausgabenY": 3600, "ausgabenM": 300,
                               "diffY": 44400, "diffM": 3700}
    assert rechne("2027-01-01") == {"einnahmenY": 48000, "ausgabenY": 4200, "ausgabenM": 350,
                                    "diffY": 43800, "diffM": 3650}
    assert rechne("offen") == {"einnahmenY": 48000, "ausgabenY": 3960, "ausgabenM": 330,
                               "diffY": 44040, "diffM": 3670}


def test_hinweis_fuer_offen_stimmt_mit_dem_was_stehen_bleibt():
    """Bei «offen» bleibt (ohne Abwahl) nichts stehen, auch keine Hülle ohne
    Betrag: eine Hülle gibt es nicht mehr."""
    mit_leerer = dict(ANPASSUNGEN, leer={"jaehrlich": None, "monatlich": None, "ab": "2028-01-01"})
    assert kern("anpassungenNachStand", mit_leerer, "offen") == {}
    assert set(kern("anpassungenNachStand", mit_leerer, "2027-01-01")) == {"hausrat", "kasse"}


def test_name_der_neuen_version_sagt_vorschlaege_wie_der_rest():
    assert kern("neueVersionName", "offen") == "Stand mit allen Vorschlägen"
    assert kern("neueVersionName", "2027-04-01") == "Stand ab 01.04.2027"
    assert "Stand mit allen Anpassungen" not in _seite_text()


def test_neue_version_aus_stand_nimmt_den_namen_aus_dem_kern_und_hat_keinen_festen_hinweis():
    block = _funktionsblock("neueVersionAusStand")
    assert "neueVersionName(standKey)" in block
    assert "neueVersionHinweis" not in _seite_text()
    assert "newVersionHinweis" not in _seite_text(), "der feste Hinweissatz entfällt, die Liste zeigt es"
    assert "Später fällige" not in _seite_text()
    assert "bleibt keine stehen" not in _seite_text()


def test_neue_version_aus_stand_nutzt_die_regel_des_kerns_fuer_unbekannte_zeilen():
    block = _funktionsblock("neueVersionAusStand")
    assert "unbekannteAnpassungenBehalten(alle, Object.keys(ROW_INDEX))" in block
    assert "typeof alle" not in block
    assert "{ ...unbekannt[id] }" in block, "die Einträge dürfen nicht mit der Quellversion geteilt werden"


def test_private_notiz_platzhalter_verspricht_keine_vertraulichkeit():
    text = _seite_text()
    tag = text[text.index('<textarea id="privateNote"'):].split(">", 1)[0]
    assert "nur für mich" not in tag


def test_sprung_zur_zeile_setzt_den_fokus_auf_den_aufklapper():
    block = _funktionsblock("springeZuZeile")
    assert "closeAdjustmentsPanel();" in block
    assert re.search(r"row-expander\[data-row-id=\"\$\{rowId\}\"\]", block)
    assert ".focus({ preventScroll: true })" in block


def test_escape_schliesst_panel_und_vorschau_nicht_zugleich():
    text = _seite_text()
    ab = text.index("// Nur wenn kein Dialog offen ist")
    handler = text[ab:text.index("leavePreview();", ab)]
    assert "if (!$('#adjustmentsPanel').hidden) return;" in handler


# --- Eine Anpassung ohne Betrag gibt es nicht ----------------------------------

def test_nur_ein_betrag_macht_einen_eintrag_aus():
    leer = {"jaehrlich": None, "monatlich": None}
    assert kern("anpassungHatBetrag", dict(leer, ab="2027-01-01")) is False   # Datum allein
    assert kern("anpassungHatBetrag", dict(leer, ab=None)) is False
    assert kern("anpassungHatBetrag", None) is False
    assert kern("anpassungHatBetrag", {}) is False
    assert kern("anpassungHatBetrag", dict(leer, monatlich=5, ab=None)) is True
    assert kern("anpassungHatBetrag", dict(leer, jaehrlich=60, ab="2027-01-01")) is True


def test_null_ist_ein_betrag_und_macht_einen_eintrag_aus():
    """Das Gründungsbeispiel: «Abo gekündigt, kostet ab 01.01. nichts mehr»."""
    assert kern("anpassungHatBetrag", {"jaehrlich": None, "monatlich": 0, "ab": "2027-01-01"}) is True
    assert kern("anpassungHatBetrag", {"jaehrlich": 0, "monatlich": None, "ab": None}) is True


def test_hinweis_im_dialog_bleibt_gedaempft():
    """«.modal p» hat ein Element mehr im Selektor und schlug «.modal-hint» —
    der Satz unter der Einloese-Liste stand in Fliesstextfarbe da."""
    text = _seite_text()
    assert re.search(r"\.modal\s+\.modal-hint\s*\{", text)


def test_dialog_rechnet_mit_der_sichtbaren_fensterhoehe():
    """100vh ist auf Mobilgeraeten hoeher als das sichtbare Fenster, solange
    die Adressleiste eingeblendet ist."""
    text = _seite_text()
    assert "calc(100dvh" in text
    assert not re.search(r"max-height:\s*calc\(100vh", text)


def test_unterschied_zum_erfassten_wert():
    """Die vierte Spalte der Anpassungszeile: Zielbetrag minus erfasster
    Jahreswert. Ohne Anpassung steht dort nichts (null)."""
    leer = {"jaehrlich": None, "monatlich": None, "ab": None}
    assert kern("anpassungUnterschied", dict(leer, jaehrlich=1212), 2052) == -840
    assert kern("anpassungUnterschied", dict(leer, monatlich=101), 2052) == -840
    assert kern("anpassungUnterschied", dict(leer, jaehrlich=0), 1200) == -1200
    assert kern("anpassungUnterschied", dict(leer, jaehrlich=500), 0) == 500
    assert kern("anpassungUnterschied", leer, 2052) is None
    assert kern("anpassungUnterschied", None, 2052) is None
    assert kern("anpassungUnterschied", dict(leer, jaehrlich=600), None) == 600


def test_wirkung_haengt_an_der_gruppe():
    """Bei einer Ausgabe ist weniger gut, bei einer Einnahme mehr. Ohne diese
    Unterscheidung stuende «+1'200.00» beim Lohn in Rot da — die Seite saegte
    dem Benutzer das Gegenteil dessen, was er erreicht hat."""
    assert kern("anpassungWirkung", -840, False) == "gut"       # Ausgabe sinkt
    assert kern("anpassungWirkung", 500, False) == "schlecht"   # Ausgabe steigt
    assert kern("anpassungWirkung", 1200, True) == "gut"        # Einnahme steigt
    assert kern("anpassungWirkung", -300, True) == "schlecht"   # Einnahme sinkt
    assert kern("anpassungWirkung", 0, False) == ""
    assert kern("anpassungWirkung", None, False) == ""


def test_unmoegliches_datum_gilt_nicht_als_datum():
    """`Date.parse` nimmt den 31. Februar an und rechnet ihn still auf den
    3. Maerz um — das ergaebe einen Stand mit unsinniger Ueberschrift. Ueber
    <input type="date"> ist so etwas nicht zu erzeugen, aus einer von Hand
    geschriebenen Datei schon."""
    assert kern("istIsoDatum", "2027-01-01") is True
    assert kern("istIsoDatum", "2027-02-28") is True
    assert kern("istIsoDatum", "2028-02-29") is True     # Schaltjahr
    assert kern("istIsoDatum", "2027-02-29") is False    # kein Schaltjahr
    assert kern("istIsoDatum", "2027-02-31") is False
    assert kern("istIsoDatum", "2026-13-01") is False
    assert kern("istIsoDatum", "01.01.2027") is False
    assert kern("istIsoDatum", None) is False


def test_eingabe_ohne_betrag_ergibt_keinen_eintrag():
    """Beide Beträge geleert: das Datum fällt mit, der Eintrag verschwindet."""
    assert kern("anpassungEintrag", {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}) is None
    assert kern("anpassungEintrag", {"jaehrlich": None, "monatlich": None, "ab": None}) is None
    assert kern("anpassungEintrag", {"jaehrlich": None, "monatlich": None, "ab": ""}) is None


def test_eingabe_mit_betrag_behaelt_alles_und_die_null_bleibt_null():
    assert kern("anpassungEintrag", {"jaehrlich": None, "monatlich": 0, "ab": "2027-01-01"}) == \
        {"jaehrlich": None, "monatlich": 0, "ab": "2027-01-01"}
    assert kern("anpassungEintrag", {"jaehrlich": 0, "monatlich": 0, "ab": ""}) == \
        {"jaehrlich": 0, "monatlich": 0, "ab": None}
    assert kern("anpassungEintrag", {"jaehrlich": 600, "monatlich": 50, "ab": None}) == \
        {"jaehrlich": 600, "monatlich": 50, "ab": None}


def test_datumsfeld_ist_gesperrt_genau_wenn_kein_betrag_da_ist():
    """Die Sperre und der Eintrag teilen eine Regel: gesperrt heisst, es gäbe
    ohnehin keinen Eintrag."""
    for j, m in ((None, None), (None, 0), (0, None), (12, None), (None, 1)):
        roh = {"jaehrlich": j, "monatlich": m, "ab": "2027-01-01"}
        assert kern("anpassungDatumGesperrt", roh) is (kern("anpassungEintrag", roh) is None), (j, m)
    assert kern("anpassungDatumGesperrt", {"jaehrlich": None, "monatlich": None, "ab": None}) is True
    assert kern("anpassungDatumGesperrt", {"jaehrlich": None, "monatlich": 0, "ab": None}) is False
    assert kern("anpassungDatumGesperrt", None) is True


def test_bereinigen_wirft_datum_ohne_betrag_raus_und_laesst_die_null_stehen():
    alt = {
        "handy": {"jaehrlich": None, "monatlich": 0, "ab": "2027-01-01"},        # 0: bleibt
        "strom": {"jaehrlich": None, "monatlich": None, "ab": "2027-03-01"},     # nur Datum
        "miete": {"jaehrlich": None, "monatlich": None, "ab": None},             # leere Hülle
        "fremd": {"jaehrlich": None, "monatlich": None, "ab": "2027-05-01"},     # Zeile unbekannt
        "kasse": {"jaehrlich": None, "monatlich": 340, "ab": None},
    }
    erg = kern("anpassungenBereinigen", alt, ["handy", "strom", "miete", "kasse"])
    assert sorted(erg["behalten"]) == ["handy", "kasse"]
    assert erg["behalten"]["handy"]["monatlich"] == 0
    assert erg["verworfen"] == 3
    # Sichtbar war nur, was auf einer bekannten Zeile ein lesbares Datum trug.
    assert erg["sichtbar"] == 1


def test_bereinigen_ohne_etwas_zu_verwerfen_meldet_nichts():
    erg = kern("anpassungenBereinigen", ANPASSUNGEN, ["handy", "fitness", "hausrat", "kasse"])
    assert sorted(erg["behalten"]) == sorted(ANPASSUNGEN)
    assert erg["verworfen"] == 0 and erg["sichtbar"] == 0
    assert kern("anpassungenBereinigen", None, []) == {"behalten": {}, "verworfen": 0, "sichtbar": 0}


def test_bereinigen_ungelesenes_datum_war_nicht_sichtbar():
    """Ein Feld vom Typ date zeigt keinen Text, der kein Datum ist."""
    erg = kern("anpassungenBereinigen",
               {"handy": {"jaehrlich": None, "monatlich": None, "ab": "demnächst"}}, ["handy"])
    assert erg["verworfen"] == 1 and erg["sichtbar"] == 0


def test_rechnung_und_gruppen_kennen_huellen_ohne_betrag_weiterhin_nicht():
    """Der Kern bleibt auch gegen handgeschriebene Dateien dicht (Datum ohne
    Betrag), selbst wenn das Laden solche Einträge vorher entfernt."""
    nur_datum = {"handy": {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}}
    assert [s["key"] for s in kern("stichtagListe", nur_datum, "2026-10-22")] == ["heute"]
    assert kern("werteFuerStand", WERTE, nur_datum, "2027-01-01") == WERTE


def test_laden_bereinigt_und_sagt_es():
    """hydrate führt die Bereinigung aus; wer beim Öffnen etwas verliert, das
    er sehen konnte, erfährt es (der Hinweis hängt am Öffnen, nicht an hydrate:
    der Erfolgshinweis dort würde ihn sonst überschreiben)."""
    block = _funktionsblock("hydrate(payload)")
    assert "anpassungenBereinigen(" in block
    assert "Object.keys(ROW_INDEX)" in block
    for oeffnen in ("openFile", "fallbackOpen"):
        assert "ladeHinweis(" in _funktionsblock(oeffnen), oeffnen


def test_laden_laesst_die_datei_unveraendert():
    """Beim Öffnen wird nichts zurückgeschrieben: die Bereinigung gilt im
    Speicher, die Datei auf der Platte ändert erst ein späteres Speichern."""
    assert "markDirty" not in _funktionsblock("hydrate(payload)")


def test_datumsfeld_startet_gesperrt_und_hat_eine_erklaerung():
    text = _seite_text()
    block = _funktionsblock("makeAdjustmentRow")
    assert re.search(r'class="adj-input adj-ab"[^>]*\bdisabled\b', block)
    assert "adj-datum-hinweis" in block, "eine kurze Zeile sagt, warum das Feld zu ist"
    assert ".adj-input:disabled" in text, "ein gesperrtes Feld muss gesperrt aussehen"


def test_sperre_haengt_am_betrag_und_nicht_an_einer_zweiten_regel():
    block = _funktionsblock("refreshExpanderUI")
    assert "anpassungDatumGesperrt(" in block
    assert "state.previewStand" in block, "in der Vorschau bleibt alles zu, auch mit Betrag"


def test_korrigieren_eines_betrags_verliert_das_datum_nicht():
    """Der Ablauf: 0 mit Datum -> die 0 löschen (Feld nicht verlassen) -> 50
    tippen. Dazwischen ist kein Betrag da, aber das ist kein gespeicherter
    Zustand, sondern ein Zwischenschritt beim Tippen; das Datum steht noch."""
    d = "2027-01-01"
    mit_null = {"jaehrlich": None, "monatlich": 0, "ab": d}
    geleert = {"jaehrlich": None, "monatlich": None, "ab": d}        # Datumsfeld unberührt
    neu_50 = {"jaehrlich": None, "monatlich": 50, "ab": d}
    assert kern("anpassungEintrag", mit_null)["ab"] == d
    assert kern("anpassungEintrag", geleert) is None                  # nichts wird gespeichert
    assert kern("datumNachVerlassen", geleert, True) == d             # Fokus bleibt in der Zeile
    assert kern("anpassungEintrag", neu_50) == {"jaehrlich": None, "monatlich": 50, "ab": d}
    assert kern("datumNachVerlassen", neu_50, False) == d


def test_betrag_geleert_und_zeile_verlassen_verwirft_datum_und_eintrag():
    """Das Gegenstück: kommt kein Betrag mehr, fällt das Datum mit."""
    geleert = {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}
    assert kern("datumNachVerlassen", geleert, False) == ""
    assert kern("anpassungEintrag", dict(geleert, ab="")) is None
    # Ohne Datum gibt es nichts zu verwerfen.
    assert kern("datumNachVerlassen", dict(geleert, ab=""), False) == ""
    assert kern("datumNachVerlassen", None, False) == ""


def test_null_bleibt_beim_verlassen_ein_betrag():
    mit_null = {"jaehrlich": None, "monatlich": 0, "ab": "2027-01-01"}
    assert kern("datumNachVerlassen", mit_null, False) == "2027-01-01"


def _ohne_kommentare(quelltext):
    return "\n".join(z for z in quelltext.splitlines() if not z.strip().startswith("//"))


def test_zeile_umfasst_den_ganzen_aufklappbereich():
    """Ziel des Fokuswechsels liegt in derselben Zeile (Kommentarfeld, Pfeil, Betrag
    der Hauptzeile): das Datum bleibt. Eine andere Zeile oder gar keine: es fällt."""
    assert kern("bleibtInDerZeile", "miete", "miete") is True
    assert kern("bleibtInDerZeile", "strom", "miete") is False
    assert kern("bleibtInDerZeile", None, "miete") is False
    assert kern("bleibtInDerZeile", "", "miete") is False


def _blur(**kw):
    standard = dict(
        roh={"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"},
        rowId="miete", zielRowId=None, fensterHatFokus=True, vorschau=False,
    )
    standard.update(kw)
    return kern("anpassungDatumNachBlur", standard)


def test_blur_ohne_betrag_aus_der_zeile_heraus_leert_das_datum():
    assert _blur() == ""                                    # ins Leere
    assert _blur(zielRowId="strom") == ""                   # andere Zeile


def test_blur_innerhalb_der_zeile_laesst_das_datum_stehen():
    assert _blur(zielRowId="miete") == "2027-01-01"         # Kommentarfeld/Pfeil/anderes Betragsfeld


def test_blur_mit_betrag_laesst_das_datum_stehen():
    roh = {"jaehrlich": None, "monatlich": 0, "ab": "2027-01-01"}
    assert _blur(roh=roh) == "2027-01-01"


def test_blur_in_der_vorschau_fasst_nichts_an():
    assert _blur(vorschau=True) is None


def test_blur_beim_fensterwechsel_fasst_nichts_an():
    assert _blur(fensterHatFokus=False) is None


def test_blur_ohne_zeilenfelder_fasst_nichts_an():
    assert _blur(roh=None) is None
    assert kern("anpassungDatumNachBlur", None) is None


def test_hinweis_nennt_den_stehengebliebenen_wert():
    """Steht noch ein Datum im gesperrten Feld, darf daneben nicht «setzen Sie es
    erst» stehen. Offen: kein Hinweis."""
    assert kern("anpassungDatumHinweis", False, True) == ""
    assert kern("anpassungDatumHinweis", False, False) == ""
    leer = kern("anpassungDatumHinweis", True, False)
    steht = kern("anpassungDatumHinweis", True, True)
    assert leer and steht and leer != steht
    assert "gilt" in steht and "Betrag" in steht
    assert "setzen" in leer


def test_tippen_fasst_das_datumsfeld_nicht_an():
    """Beim Tippen bleibt das Datum stehen; das Verwerfen gehört in den blur-Handler.
    Geprüft wird jede Schreibweise, mit der das Feld angesprochen werden könnte."""
    code = _ohne_kommentare(_funktionsblock("handleAdjInputEvent"))
    assert not re.search(r"""[.'"\-]ab\b""", code), "kein Zugriff auf das Datumsfeld (.ab, 'ab', adj-ab, data-adj=\"ab\")"
    assert "datumNachVerlassen" not in code and "anpassungDatumNachBlur" not in code
    assert "readAdjustmentFromDom(rowId)" in code     # Eintrag folgt den Feldern, ohne Betrag null


def test_blur_handler_ist_nur_verdrahtung():
    """Die Entscheidung liegt im Kern (getestet); der Handler liest und schreibt nur."""
    verlassen = _funktionsblock("handleAdjInputBlur")
    assert "anpassungDatumNachBlur(" in verlassen
    assert "zeilenIdVon(ereignis && ereignis.relatedTarget)" in verlassen
    assert "document.hasFocus()" in verlassen and "state.previewStand" in verlassen
    assert "(e) => handleAdjInputBlur(input, e)" in _seite_text()


def test_zeilenid_kennt_hauptzeile_und_aufklappbereich():
    block = _funktionsblock("zeilenIdVon")
    assert "'.expander-row'" in block and "expanderFor" in block
    assert "tr[data-row-id]" in block


def test_vorschau_steht_fest_bevor_die_felder_zugehen():
    """Ein gesperrtes Feld mit Fokus feuert blur; dessen Handler schaut auf
    state.previewStand und muss es dann schon gesetzt finden."""
    block = _funktionsblock("enterPreview")
    gesetzt = block.index("state.previewStand = standKey")
    assert gesetzt < block.index("$$('.adj-input').forEach((input) => { input.disabled = true; })")
    assert gesetzt < block.index("$$('input.amount-input').forEach((input) => { input.disabled = true; })")
    assert block.index("captureFormToActiveVersion()") < gesetzt, "erfasst wird, solange die Sperre noch offen ist"


def test_kommentar_ueber_capture_sagt_nicht_mehr_datum_allein_sei_ein_eintrag():
    text = _seite_text()
    assert "Ohne Betrag UND ohne Datum" not in text


def test_ohne_betrag_wird_nichts_gespeichert_auch_wenn_ein_datum_im_feld_steht():
    """Das Datum im Feld ist ein Entwurf; gespeichert wird nur, was anpassungEintrag liefert."""
    assert "anpassungEintrag(" in _funktionsblock("readAdjustmentFromDom")
    assert "readAdjustmentFromDom(rowId)" in _funktionsblock("captureFormToActiveVersion")


def test_anpassungsfunktionen_kennen_kein_oder_null():
    """null ist leer, 0 ist ein Wert. Kein `|| 0` in den Funktionen, die
    Anpassungsfelder lesen oder bewerten."""
    for name in ("anpassungEintrag", "anpassungHatBetrag", "anpassungDatumGesperrt",
                 "anpassungenBereinigen", "datumNachVerlassen", "readAdjustmentFromDom",
                 "readAdjustmentFieldsFromDom", "parseAnpassungsFeld", "anpassungDatumNachBlur",
                 "bleibtInDerZeile", "anpassungDatumHinweis", "zeilenIdVon",
                 "handleAdjInputEvent", "handleAdjInputBlur"):
        assert "|| 0" not in _funktionsblock(name), name


# --- Dialog «Neue Version aus Stand»: welche Positionen kommen mit ------------
# Die Auswahl entscheidet sich im Moment des Drückens und wird nirgends
# gespeichert. Die Logik ist rein und liegt im Kern; der Dialog selbst hängt
# am DOM und wird als Text geprüft.


def test_abgewaehlte_position_bleibt_mit_ihrem_datum_stehen():
    rest = kern("anpassungenNachStand", ANPASSUNGEN, "2027-01-01", ["handy"])
    assert sorted(rest) == ["handy", "hausrat", "kasse"]
    assert rest["handy"] == ANPASSUNGEN["handy"], "mit Betrag 0 und Datum, nichts verloren"
    assert rest["handy"]["ab"] == "2027-01-01"


def test_abgewaehlte_position_behaelt_ihren_alten_wert():
    neu = kern("werteFuerStand", WERTE, ANPASSUNGEN, "2027-01-01", ["handy"])
    assert neu["handy.monatlich"] == 60 and "handy.jaehrlich" not in neu
    assert neu["fitness.monatlich"] == 0, "die angehakte wird eingelöst, auch auf 0"


def test_ohne_auswahl_wie_bisher():
    for key in ("heute", "2027-01-01", "offen"):
        assert kern("werteFuerStand", WERTE, ANPASSUNGEN, key, None) == kern("werteFuerStand", WERTE, ANPASSUNGEN, key)
        assert kern("anpassungenNachStand", ANPASSUNGEN, key, None) == kern("anpassungenNachStand", ANPASSUNGEN, key)
        assert kern("anpassungenNachStand", ANPASSUNGEN, key, []) == kern("anpassungenNachStand", ANPASSUNGEN, key)


def test_alles_abgewaehlt_ist_eine_kopie_mit_allen_anpassungen():
    alle = ["handy", "fitness", "hausrat", "kasse"]
    assert kern("werteFuerStand", WERTE, ANPASSUNGEN, "offen", alle) == WERTE
    assert kern("anpassungenNachStand", ANPASSUNGEN, "offen", alle) == ANPASSUNGEN


def test_abwahl_aendert_loest_ein_nur_fuer_die_genannte_zeile():
    a = ANPASSUNGEN["handy"]
    assert kern("loestEin", a, "2027-01-01", "handy", []) is True
    assert kern("loestEin", a, "2027-01-01", "handy", ["fitness"]) is True
    assert kern("loestEin", a, "2027-01-01", "handy", ["handy"]) is False
    assert kern("loestEin", a, "2027-01-01") is True, "ohne die neuen Parameter wie bisher"
    assert kern("loestEin", a, "heute", "handy", []) is False


def test_abwahl_aendert_die_eingaben_nicht():
    kern("anpassungenNachStand", ANPASSUNGEN, "offen", ["handy"])
    assert ANPASSUNGEN["handy"]["ab"] == "2027-01-01"


def eintraege(key, anpassungen=None, werte=None):
    anpassungen = ANPASSUNGEN if anpassungen is None else anpassungen
    staende = kern("stichtagListe", anpassungen, "2026-10-22")
    return kern("einloesbareEintraege", anpassungen, staende, WERTE if werte is None else werte, key)


def test_dialog_listet_alles_was_der_stand_einloest():
    """Die Liste im Dialog ist dieselbe Menge, die loestEin bejaht - kumulativ:
    der Stand vom April löst auch die Anpassungen vom Januar ein."""
    assert sorted(e["rowId"] for e in eintraege("2027-01-01")) == ["fitness", "handy"]
    assert sorted(e["rowId"] for e in eintraege("2027-04-01")) == ["fitness", "handy", "hausrat"]
    assert sorted(e["rowId"] for e in eintraege("offen")) == ["fitness", "handy", "hausrat", "kasse"]
    for key in ("2027-01-01", "2027-04-01", "offen"):
        erwartet = sorted(r for r, a in ANPASSUNGEN.items() if kern("loestEin", a, key))
        assert sorted(e["rowId"] for e in eintraege(key)) == erwartet


def test_dialogeintrag_nennt_alt_neu_und_datum():
    e = {x["rowId"]: x for x in eintraege("2027-04-01")}
    assert e["handy"]["altM"] == 60 and e["handy"]["neuM"] == 0 and e["handy"]["deltaM"] == -60
    assert e["hausrat"]["neuM"] == 28 and e["hausrat"]["ab"] == "2027-04-01"
    assert e["handy"]["ab"] == "2027-01-01", "bei einem kumulativen Stand sieht man, von wann die Zeile ist"
    assert {x["rowId"]: x["ab"] for x in eintraege("offen")}["kasse"] is None


def test_dialog_listet_nichts_fuer_heute_und_unbekannte_staende():
    assert eintraege("heute") == []
    assert eintraege("2030-01-01") == []


def test_dialog_listet_keine_huelle_ohne_betrag():
    mit_huelle = dict(ANPASSUNGEN, strom={"jaehrlich": None, "monatlich": None, "ab": "2026-12-01"})
    for key in ("2027-04-01", "offen"):
        assert "strom" not in [e["rowId"] for e in eintraege(key, mit_huelle)]


def test_dialog_listet_die_null_als_zielbetrag():
    e = {x["rowId"]: x for x in eintraege("2027-01-01")}
    assert e["handy"]["neuM"] == 0 and e["handy"]["neuY"] == 0


def test_auswahltext_zaehlt_mit():
    def t(n, g):
        return kern("neueVersionAuswahlText", n, g)
    assert t(3, 3) == "Alle 3 Positionen werden eingerechnet."
    assert t(1, 1) == "Die Position wird eingerechnet."
    assert t(2, 3) == "2 von 3 Positionen werden eingerechnet, 1 bleibt als Anpassung stehen."
    assert t(1, 4) == "1 von 4 Positionen wird eingerechnet, 3 bleiben als Anpassung stehen."
    assert t(0, 1) == "Die Position wird nicht eingerechnet, sie bleibt als Anpassung stehen."
    assert t(0, 3).startswith("Keine Position wird eingerechnet")
    assert "Kopie" in t(0, 3), "die leere Auswahl sagt, was dabei herauskommt"


def test_dialog_hat_checkboxen_standardmaessig_gesetzt_und_nur_fuer_den_stand():
    block = _funktionsblock("openNewVersionModal")
    assert "vorgabe.eintraege" in block, "die Liste kommt nur mit der Vorgabe des Stands"
    assert "abgewaehlt" in block and "!b.checked" in block
    liste = _funktionsblock("fuelleEinloesenListe")
    assert "type = 'checkbox'" in liste
    assert re.search(r"\.checked\s*=\s*true", liste), "alle Häkchen beginnen gesetzt"
    assert "neueVersionAuswahlText" in liste
    assert "abschnitt.hidden = zeilen.length === 0" in liste, "ohne Stand bleibt der Abschnitt zu"
    assert "localStorage" not in block + liste


def test_dialog_gibt_die_abgewaehlten_an_beide_kernfunktionen_weiter():
    block = _funktionsblock("neueVersionAusStand")
    assert "einloesbareEintraege(" in block
    assert re.search(r"werteFuerStand\(.*abgewaehlt\)", block)
    assert re.search(r"anpassungenNachStand\(.*abgewaehlt\)", block)


def test_auswahl_hat_keinen_zustand_ausserhalb_des_dialogs():
    """Die Entscheidung gehört in den Moment des Drückens: nichts in state, nichts
    in der Version, keine Häkchen neben den Zeilen im Formular."""
    text = _seite_text()
    block = _funktionsblock("neueVersionAusStand")
    assert "state." not in block
    liste = text[text.index("function renderAdjustmentList"):][:5000]
    assert "abgewaehlt" not in liste and "checkbox" not in liste
    kern_text = re.sub(r"//.*", "", text[text.index("budget-kern:anfang"):text.index("budget-kern:ende")])
    assert not re.search(r"\bstate\b|\bSCHEMA\b|\bdocument\b|\$\(", kern_text), "der Kern bleibt frei von state, SCHEMA und DOM"


def test_liste_im_dialog_scrollt_und_ist_per_tastatur_erreichbar():
    text = _seite_text()
    assert re.search(r"\.einloesen-liste\s*\{[^}]*max-height", text)
    assert re.search(r"\.einloesen-liste\s*\{[^}]*overflow-y:\s*auto", text)
    assert '<fieldset class="modal-field" id="newVersionEinloesen"' in text
    assert "<legend" in text[text.index('id="newVersionEinloesen"'):][:300]
