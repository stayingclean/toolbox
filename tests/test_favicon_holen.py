"""Prueft die reine Seite des Favicon-Helfers - ohne Netzwerk."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import favicon_holen as fh


def test_zielpfad_entfernt_www():
    assert fh.zielpfad("www.coop.ch").name == "coop.ch.png"
    assert fh.zielpfad("coop.ch").name == "coop.ch.png"


def test_adressen_beginnen_mit_dem_standardort():
    adressen = fh.symbol_adressen("coop.ch", "")
    assert adressen[0] == "https://coop.ch/favicon.ico"


def test_adressen_lesen_die_link_angabe_der_seite():
    html = '<link rel="apple-touch-icon" href="/static/icon-180.png">'
    adressen = fh.symbol_adressen("coop.ch", html)
    assert "https://coop.ch/static/icon-180.png" in adressen


def test_absolute_angabe_bleibt_absolut():
    html = '<link rel="icon" href="https://cdn.coop.ch/i.png">'
    assert "https://cdn.coop.ch/i.png" in fh.symbol_adressen("coop.ch", html)


def test_ohne_domain_beendet_sich_das_skript_verstaendlich(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["favicon_holen.py"])
    with pytest.raises(SystemExit):
        fh.main()
    assert "Domain" in capsys.readouterr().out
