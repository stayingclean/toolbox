import json
import os
import stat
import subprocess
import sys
import types
from pathlib import Path

import openpyxl
import pytest

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


def test_pruefung_nimmt_ein_zusammengesetztes_emoji_an():
    # 🧘‍♀️ ist EIN sichtbares Zeichen (Person + ZWJ + Geschlechtszeichen),
    # aber vier Codepunkte – genau der Fall, den die alte Grenze von 2
    # faelschlich blockiert hat.
    assert vh.pruefe_eintrag({**BEISPIEL, "emoji": "🧘‍♀️"}, BESTAND) is None


def test_pruefung_lehnt_eine_zu_lange_emoji_kette_ab():
    grund = vh.pruefe_eintrag({**BEISPIEL, "emoji": "🎧" * 20}, BESTAND)
    assert grund == "Emoji ist zu lang."


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


def test_anhaengen_meldet_verstaendlich_wenn_datei_gesperrt(tmp_path):
    # Simuliert eine in Excel geoeffnete Datei: schreibgeschuetzt gesetzt,
    # damit wb.save() ein PermissionError wirft, genau wie beim echten Sperren.
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp", "Von"])
    wb.save(pfad)

    os.chmod(pfad, stat.S_IREAD)
    try:
        with pytest.raises(SystemExit) as ausnahme:
            vh.an_excel_anhaengen(pfad, [BEISPIEL])
        meldung = str(ausnahme.value)
        assert "laesst sich nicht speichern" in meldung
        assert "Excel" in meldung
        assert "nichts veraendert" in meldung
    finally:
        os.chmod(pfad, stat.S_IWRITE | stat.S_IREAD)


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


def test_bereinigt_entfernt_randweissraum_der_die_pruefung_besteht():
    # Genau der gemeldete Fall: 60 Zeichen plus zwei Leerzeichen bestehen die
    # Pruefung (die auf der getrimmten Fassung prueft), duerfen aber nicht mit
    # 62 Zeichen in der Excel landen.
    eintrag = {**BEISPIEL, "titel": "x" * 60 + "  "}
    assert vh.pruefe_eintrag(eintrag, BESTAND) is None
    assert vh.bereinigt(eintrag)["titel"] == "x" * 60


def test_bereinigt_trimmt_alle_excel_spalten():
    eintrag = {**BEISPIEL, "beschreibung": "  Ein Lied auflegen.  ", "von": " Max "}
    ergebnis = vh.bereinigt(eintrag)
    assert ergebnis["beschreibung"] == "Ein Lied auflegen."
    assert ergebnis["von"] == "Max"


def freigegebenes_issue(nummer: int, daten: dict = BEISPIEL) -> dict:
    """Baut ein Issue, wie main() es von hole_issues() bekaeme – freigegeben,
    vom Formular-Konto, mit lesbarem Vorschlagsblock."""
    return {
        "number": nummer,
        "title": daten.get("titel", "t"),
        "author": {"login": vh.BOT},
        "labels": [{"name": vh.LABEL}],
        "body": issue_text(daten),
    }


def test_main_laesst_unerwartete_fehler_beim_schliessen_durchschlagen(monkeypatch):
    # except Exception war zu breit: ein Programmierfehler beim Schliessen sah
    # damit aus wie ein gescheiterter Netzaufruf. Nur subprocess.CalledProcessError
    # (der tatsaechliche Fehlerfall von issue_schliessen mit check=True) darf
    # abgefangen werden – alles andere muss durchschlagen.
    monkeypatch.setattr(vh, "hole_issues", lambda: [freigegebenes_issue(1)])
    monkeypatch.setattr(vh, "lade_datenstand", lambda: BESTAND)
    monkeypatch.setattr(vh, "an_excel_anhaengen", lambda pfad, eintraege: 0)

    def schlaegt_unerwartet_fehl(nummer):
        raise RuntimeError("Programmierfehler")

    monkeypatch.setattr(vh, "issue_schliessen", schlaegt_unerwartet_fehl)

    with pytest.raises(RuntimeError):
        vh.main()


def test_main_faengt_calledprocesserror_ab_und_zeigt_keine_widerspruechliche_erfolgszeile(
    monkeypatch, capsys
):
    monkeypatch.setattr(vh, "hole_issues", lambda: [freigegebenes_issue(1)])
    monkeypatch.setattr(vh, "lade_datenstand", lambda: BESTAND)
    # 0 zurueckgeben, um in diesem Test den Skillsliste-Neubau (subprocess) nicht
    # auszuloesen – der Fokus liegt hier auf dem Schliessen-Fehler und der
    # Erfolgszeile, nicht auf build.py.
    monkeypatch.setattr(vh, "an_excel_anhaengen", lambda pfad, eintraege: 0)

    def schlaegt_wie_gh_fehl(nummer):
        raise subprocess.CalledProcessError(1, ["gh"])

    monkeypatch.setattr(vh, "issue_schliessen", schlaegt_wie_gh_fehl)

    vh.main()

    ausgabe = capsys.readouterr().out
    assert "#1" in ausgabe
    assert "konnte(n) nicht geschlossen werden" in ausgabe
    # Bei 0 tatsaechlich uebernommenen Zeilen darf kein gruenes Haekchen mit
    # einer Null erscheinen – widerspruechlich neben der Warnung direkt darunter.
    assert "✅" not in ausgabe


def test_main_gibt_keine_erfolgszeile_bei_null_uebernahmen_aus(monkeypatch, capsys):
    abgelehntes_issue = freigegebenes_issue(1, {**BEISPIEL, "kategorie": "Erfunden"})
    monkeypatch.setattr(vh, "hole_issues", lambda: [abgelehntes_issue])
    monkeypatch.setattr(vh, "lade_datenstand", lambda: BESTAND)
    monkeypatch.setattr(vh, "an_excel_anhaengen", lambda pfad, eintraege: 0)

    vh.main()

    ausgabe = capsys.readouterr().out
    assert "✅" not in ausgabe
    assert "nicht übernommen" in ausgabe


def test_main_verwendet_einzahl_und_mehrzahl_korrekt(monkeypatch, capsys):
    monkeypatch.setattr(vh, "lade_datenstand", lambda: BESTAND)
    monkeypatch.setattr(vh, "issue_schliessen", lambda nummer: None)
    # main() ruft nach einer Uebernahme build.py auf; hier nur die Ausgabe der
    # Erfolgszeile pruefen, ohne einen echten build.py-Lauf auszuloesen.
    monkeypatch.setattr(
        vh.subprocess, "run", lambda *a, **k: types.SimpleNamespace(returncode=0)
    )

    monkeypatch.setattr(vh, "hole_issues", lambda: [freigegebenes_issue(1)])
    monkeypatch.setattr(vh, "an_excel_anhaengen", lambda pfad, eintraege: len(eintraege))
    vh.main()
    einzahl = capsys.readouterr().out
    assert "1 Vorschlag in" in einzahl
    assert "1 Vorschläge" not in einzahl

    monkeypatch.setattr(
        vh, "hole_issues", lambda: [freigegebenes_issue(1), freigegebenes_issue(2)]
    )
    vh.main()
    mehrzahl = capsys.readouterr().out
    assert "2 Vorschläge in" in mehrzahl
