"""Tests für tools/anleitung_aufgaben.py: Aufgaben aus ki-tasks in SEITEN und aufgaben.html."""

import sys

import pytest

from conftest import ROOT

sys.path.insert(0, str(ROOT / "tools"))

import anleitung_aufgaben as aa  # noqa: E402

JS = """var SEITEN = [
  { gruppe: 'Aufgaben', seiten: [
    { href: 'aufgaben.html', titel: 'Übersicht' },
    /* AUFGABEN-ANFANG */
    { href: 'alt.html', titel: 'Alt' }
    /* AUFGABEN-ENDE */
  ]}
];
"""

UEBERSICHT = """<div class="grid">
  <!-- AUFGABEN-KARTEN -->
  <div class="card">alt</div>
  <!-- /AUFGABEN-KARTEN -->
</div>
"""


def seite(titel, lead):
    return f'<header><h1>{titel}</h1>\n<p class="lead">{lead}</p></header>'


@pytest.fixture
def repos(tmp_path):
    """ki-tasks mit zwei Aufgaben und ein Zielordner wie nach dem cp im Deploy."""
    ki = tmp_path / "ki-tasks"
    ziel = tmp_path / "ziel"
    (ki / "anleitung").mkdir(parents=True)
    ziel.mkdir()

    def aufgabe(name, titel, lead, reihenfolge=None, mit_seite=True):
        (ki / "aufgaben" / name).mkdir(parents=True)
        info = f"titel: {titel} lang\ngruppe: X\nkurz: k\n"
        if reihenfolge is not None:
            info += f"reihenfolge: {reihenfolge}\n"
        (ki / "aufgaben" / name / "INFO.md").write_text(info, encoding="utf-8")
        if mit_seite:
            (ki / "anleitung" / f"{name}.html").write_text(seite(titel, lead), encoding="utf-8")

    aufgabe("zebra", "Zebra zähmen", "Erst das.", reihenfolge=10)
    aufgabe("affe", "Affe & Co", "Dann <em>das</em>.", reihenfolge=20)
    (ki / "anleitung" / "aufgaben.html").write_text(UEBERSICHT, encoding="utf-8")
    (ziel / "anleitung.js").write_text(JS, encoding="utf-8")
    (ziel / "aufgaben.html").write_text(UEBERSICHT, encoding="utf-8")
    return ki, ziel, aufgabe


def test_seiten_nach_reihenfolge_mit_h1_als_titel(repos):
    ki, ziel, _ = repos
    aa.einsetzen(ki, ziel)
    js = (ziel / "anleitung.js").read_text(encoding="utf-8")
    assert "alt.html" not in js
    assert js.index("zebra.html") < js.index("affe.html")
    assert "titel: 'Affe & Co' }" in js
    # Übersicht bleibt stehen, der letzte Eintrag hat kein Komma
    assert "{ href: 'aufgaben.html', titel: 'Übersicht' }," in js
    assert "titel: 'Affe & Co' }\n    /* AUFGABEN-ENDE */" in js


def test_karten_aus_h1_und_lead(repos):
    ki, ziel, _ = repos
    aa.einsetzen(ki, ziel)
    html = (ziel / "aufgaben.html").read_text(encoding="utf-8")
    assert '<div class="card">alt</div>' not in html
    assert '<h3><a href="zebra.html">Zebra zähmen</a></h3>' in html
    assert "<p>Dann das.</p>" in html
    assert "Affe &amp; Co" in html


def test_zweimal_laufen_ergibt_dasselbe(repos):
    ki, ziel, _ = repos
    aa.einsetzen(ki, ziel)
    erst = (ziel / "anleitung.js").read_text(encoding="utf-8")
    aa.einsetzen(ki, ziel)
    assert (ziel / "anleitung.js").read_text(encoding="utf-8") == erst


def test_ohne_reihenfolge_ans_ende(repos):
    ki, ziel, aufgabe = repos
    aufgabe("baer", "Bär", "B.")
    aa.einsetzen(ki, ziel)
    js = (ziel / "anleitung.js").read_text(encoding="utf-8")
    assert js.index("affe.html") < js.index("baer.html")


def test_aufgabe_ohne_seite_wird_gemeldet_nicht_verlinkt(repos):
    ki, ziel, aufgabe = repos
    aufgabe("neu", "Neu", "N.", mit_seite=False)
    _, meldungen = aa.einsetzen(ki, ziel)
    assert "neu.html" not in (ziel / "anleitung.js").read_text(encoding="utf-8")
    assert any("anleitung/neu.html" in z for z in meldungen)


def test_seite_ohne_navigation_bricht_ab(repos):
    ki, ziel, _ = repos
    (ki / "anleitung" / "verwaist.html").write_text(seite("V", "v"), encoding="utf-8")
    with pytest.raises(aa.KonventionFehler, match="verwaist.html"):
        aa.einsetzen(ki, ziel)


def test_fehlender_marker_bricht_ab(repos):
    ki, ziel, _ = repos
    (ziel / "anleitung.js").write_text("var SEITEN = [];", encoding="utf-8")
    with pytest.raises(aa.KonventionFehler, match="Marker"):
        aa.einsetzen(ki, ziel)


def test_seite_ohne_lead_bricht_ab(repos):
    ki, ziel, _ = repos
    (ki / "anleitung" / "affe.html").write_text("<h1>Affe</h1>", encoding="utf-8")
    with pytest.raises(aa.KonventionFehler, match="affe.html"):
        aa.einsetzen(ki, ziel)


def test_echte_anleitung_js_hat_die_marker():
    js = (ROOT / "docs" / "claude-anleitung" / "anleitung.js").read_text(encoding="utf-8")
    assert js.count(aa.JS_ANFANG) == 1
    assert js.count(aa.JS_ENDE) == 1


def test_uebersicht_ohne_marker_bleibt_stehen(repos):
    ki, ziel, _ = repos
    (ziel / "aufgaben.html").write_text("<p>von Hand</p>", encoding="utf-8")
    _, meldungen = aa.einsetzen(ki, ziel)
    assert (ziel / "aufgaben.html").read_text(encoding="utf-8") == "<p>von Hand</p>"
    assert any("ohne Marker" in z for z in meldungen)
