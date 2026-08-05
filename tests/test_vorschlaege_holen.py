import json
import os
import stat
import subprocess
import sys
import types
from pathlib import Path

import openpyxl
import pytest
from openpyxl.worksheet.datavalidation import DataValidation

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
    # main() schreibt ueber genau eine Funktion – sie muss hier stillgelegt
    # werden, sonst liefe der Test in die echte skills_daten.xlsx.
    monkeypatch.setattr(vh, "in_excel_uebernehmen", lambda pfad, aenderungen, neue: 0)

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
    monkeypatch.setattr(vh, "in_excel_uebernehmen", lambda pfad, aenderungen, neue: 0)

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
    monkeypatch.setattr(vh, "in_excel_uebernehmen", lambda pfad, aenderungen, neue: 0)

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
    monkeypatch.setattr(
        vh, "in_excel_uebernehmen", lambda pfad, aenderungen, neue: len(aenderungen) + len(neue)
    )
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


# ── Ausbaustufe 2: Änderungen an bestehenden Skills ──────────────────────────

AENDERUNG = {
    "art": "aenderung",
    "stufe": "Hoch",
    "kategorie": "Ablenkung",
    "original": "Musik hören",
    "emoji": "🎵",
    "titel": "Musik bewusst hören",
    "beschreibung": "Ein Lied aussuchen und nur darauf achten.",
    "tipp": "Kopfhörer bereitlegen",
    "erg": "Lea",
}

DATEN_MIT_SKILL = {
    "hoch": {"kategorien": [{"id": "ablenkung", "label": "Ablenkung", "skills": [
        {"e": "🎧", "t": "Musik hören", "b": "Ein Lied auflegen.", "tip": "", "von": "Max", "erg": ""}
    ]}]},
    "mittel": {"kategorien": []},
    "tief": {"kategorien": []},
}

KOPF = ["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp", "Von", "Ergaenzt"]


def mappe_mit_skill(tmp_path):
    """Eine Excel mit genau dem Skill, den DATEN_MIT_SKILL beschreibt."""
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(KOPF)
    ws.append(["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.", "", "Max", ""])
    ws.append(["Tief", "Ruhe", "🌊", "Atmen", "Ruhig atmen.", "", "", ""])
    wb.save(pfad)
    return pfad


def test_aenderung_wird_angenommen():
    assert vh.pruefe_eintrag(AENDERUNG, DATEN_MIT_SKILL) is None


def test_aenderung_ohne_original_wird_abgelehnt():
    ohne = {k: v for k, v in AENDERUNG.items() if k != "original"}
    meldung = vh.pruefe_eintrag(ohne, DATEN_MIT_SKILL)
    assert meldung is not None


def test_aenderung_an_verschwundenem_skill_wird_abgelehnt():
    meldung = vh.pruefe_eintrag(dict(AENDERUNG, original="Gibt es nicht"), DATEN_MIT_SKILL)
    assert meldung is not None
    assert "nicht" in meldung.lower()


def test_aenderung_ersetzt_die_zeile(tmp_path):
    pfad = mappe_mit_skill(tmp_path)
    anzahl = vh.in_excel_aendern(pfad, [AENDERUNG])
    assert anzahl == 1
    ws = openpyxl.load_workbook(pfad)["Skills"]
    assert ws.max_row == 3, "es darf keine Zeile dazugekommen sein"
    kopf = [c.value for c in ws[1]]
    zeile = dict(zip(kopf, [c.value for c in ws[2]]))
    assert zeile["Titel"] == "Musik bewusst hören"
    assert zeile["Emoji"] == "🎵"
    assert zeile["Beschreibung"] == "Ein Lied aussuchen und nur darauf achten."
    assert zeile["Tipp"] == "Kopfhörer bereitlegen"
    assert zeile["Von"] == "Max", "der urspruengliche Beitragende bleibt stehen"
    assert zeile["Ergaenzt"] == "Lea"


def test_aenderung_ohne_passende_zeile_meldet_es(tmp_path):
    pfad = mappe_mit_skill(tmp_path)
    try:
        vh.in_excel_aendern(pfad, [dict(AENDERUNG, original="Gibt es nicht")])
    except vh.ZeileNichtGefunden as fehler:
        assert "Gibt es nicht" in str(fehler)
    else:
        raise AssertionError("ZeileNichtGefunden erwartet")


def test_aenderung_erhaelt_filter_und_dropdown(tmp_path):
    # Beim Ersetzen einer Zeile darf weder der Filterbereich noch das
    # Stufen-Dropdown verlorengehen – beides sieht man der Datei nicht an,
    # es faellt erst auf, wenn jemand in Excel sortiert.
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(KOPF)
    ws.append(["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.", "", "Max", ""])
    ws.append(["Tief", "Ruhe", "🌊", "Atmen", "Ruhig atmen.", "", "", ""])
    ws.auto_filter.ref = "A1:H3"
    pruefung = DataValidation(type="list", formula1='"Hoch,Mittel,Tief"', allow_blank=True)
    ws.add_data_validation(pruefung)
    pruefung.add("A2:A3")
    wb.save(pfad)

    vh.in_excel_aendern(pfad, [AENDERUNG])

    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    assert ws2.auto_filter.ref == "A1:H3"
    bereiche = [str(p.sqref) for p in ws2.data_validations.dataValidation]
    assert bereiche == ["A2:A3"]


def test_aenderung_zieht_den_filter_ueber_eine_neu_angelegte_spalte(tmp_path):
    # Aeltere Mappen haben die Spalte `Ergaenzt` noch nicht. Sie wird angelegt –
    # dann muss der Filter sie auch abdecken, sonst faellt sie beim Sortieren
    # heraus und die Werte verrutschen gegenueber den uebrigen Spalten.
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(KOPF[:-1])
    ws.append(["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.", "", "Max"])
    ws.append(["Tief", "Ruhe", "🌊", "Atmen", "Ruhig atmen.", "", ""])
    ws.auto_filter.ref = "A1:G3"
    pruefung = DataValidation(type="list", formula1='"Hoch,Mittel,Tief"', allow_blank=True)
    ws.add_data_validation(pruefung)
    pruefung.add("A2:A3")
    wb.save(pfad)

    vh.in_excel_aendern(pfad, [AENDERUNG])

    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    assert [c.value for c in ws2[1]][7] == "Ergaenzt"
    assert [c.value for c in ws2[2]][7] == "Lea"
    assert ws2.auto_filter.ref == "A1:H3"
    assert [str(p.sqref) for p in ws2.data_validations.dataValidation] == ["A2:A3"]


def test_aenderung_bei_doppeltem_titel_aendert_nichts(tmp_path):
    # Stufe + Kategorie + Titel sind der Schluessel. Kommt er zweimal vor, waere
    # jede Wahl geraten – dann lieber gar nichts schreiben und nachfragen.
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(KOPF)
    ws.append(["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.", "", "Max", ""])
    ws.append(["Hoch", "Ablenkung", "🎼", "Musik hören", "Etwas anderes.", "", "Ida", ""])
    wb.save(pfad)

    with pytest.raises(vh.ZeileMehrdeutig) as ausnahme:
        vh.in_excel_aendern(pfad, [AENDERUNG])
    assert "Musik hören" in str(ausnahme.value)

    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    assert [c.value for c in ws2[2]][2] == "🎧", "keine Zeile darf angefasst worden sein"
    assert [c.value for c in ws2[3]][2] == "🎼"


def test_aenderung_meldet_fehlende_schluesselspalte(tmp_path):
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(["Stufe", "Kategorie", "Emoji", "Beschreibung", "Tipp", "Von"])
    ws.append(["Hoch", "Ablenkung", "🎧", "Ein Lied auflegen.", "", "Max"])
    wb.save(pfad)

    with pytest.raises(SystemExit) as ausnahme:
        vh.in_excel_aendern(pfad, [AENDERUNG])
    meldung = str(ausnahme.value)
    assert "Titel" in meldung
    assert "Kopfzeile" in meldung


def test_aenderung_meldet_verstaendlich_wenn_datei_gesperrt(tmp_path):
    # Gleiche Behandlung wie beim Anhaengen: eine in Excel geoeffnete Datei darf
    # keinen Absturz erzeugen, sondern muss sagen, was zu tun ist.
    pfad = mappe_mit_skill(tmp_path)
    os.chmod(pfad, stat.S_IREAD)
    try:
        with pytest.raises(SystemExit) as ausnahme:
            vh.in_excel_aendern(pfad, [AENDERUNG])
        meldung = str(ausnahme.value)
        assert "laesst sich nicht speichern" in meldung
        assert "Excel" in meldung
        assert "nichts veraendert" in meldung
    finally:
        os.chmod(pfad, stat.S_IWRITE | stat.S_IREAD)


NEUER_SKILL = {**BEISPIEL, "titel": "Spazieren gehen", "emoji": "🚶"}


def test_main_uebergibt_beide_arten_in_einem_schreibvorgang(monkeypatch, capsys):
    # Ein einziger Schreibvorgang fuer den ganzen Lauf: er gelingt oder er
    # scheitert – es gibt kein „halb uebernommen".
    aufrufe = []
    monkeypatch.setattr(vh, "hole_issues", lambda: [
        freigegebenes_issue(1, NEUER_SKILL),
        freigegebenes_issue(2, AENDERUNG),
    ])
    monkeypatch.setattr(vh, "lade_datenstand", lambda: DATEN_MIT_SKILL)
    monkeypatch.setattr(vh, "issue_schliessen", lambda nummer: None)
    monkeypatch.setattr(
        vh.subprocess, "run", lambda *a, **k: types.SimpleNamespace(returncode=0)
    )

    def uebernehmen(pfad, aenderungen, neue):
        aufrufe.append(
            ([e["titel"] for e in aenderungen], [e["titel"] for e in neue])
        )
        return len(aenderungen) + len(neue)

    monkeypatch.setattr(vh, "in_excel_uebernehmen", uebernehmen)

    vh.main()

    assert aufrufe == [(["Musik bewusst hören"], ["Spazieren gehen"])]
    ausgabe = capsys.readouterr().out
    assert "~ Hoch / Ablenkung: Musik bewusst hören" in ausgabe
    assert "+ Hoch / Ablenkung: Spazieren gehen" in ausgabe
    assert "2 Vorschläge" in ausgabe


def test_main_schliesst_kein_issue_wenn_eine_aenderung_nicht_zuzuordnen_ist(monkeypatch):
    # Geschriebene Excel bei offenen Issues waere der Dublettenfall. Bricht der
    # Schreibvorgang ab, darf deshalb auch kein Issue geschlossen werden.
    monkeypatch.setattr(vh, "hole_issues", lambda: [
        freigegebenes_issue(1, NEUER_SKILL),
        freigegebenes_issue(2, AENDERUNG),
    ])
    monkeypatch.setattr(vh, "lade_datenstand", lambda: DATEN_MIT_SKILL)
    geschlossen = []
    monkeypatch.setattr(vh, "issue_schliessen", lambda nummer: geschlossen.append(nummer))

    def uebernehmen(pfad, aenderungen, neue):
        raise vh.ZeileNichtGefunden("'Musik hören' in Hoch / Ablenkung")

    monkeypatch.setattr(vh, "in_excel_uebernehmen", uebernehmen)

    with pytest.raises(SystemExit) as ausnahme:
        vh.main()

    meldung = str(ausnahme.value)
    assert "Musik hören" in meldung
    assert "build.bat" in meldung, "die haeufigste Ursache muss genannt sein"
    assert "nichts veraendert" in meldung
    assert "freigegeben" in meldung
    assert geschlossen == [], "kein Issue darf geschlossen worden sein"


ZWEITE_AENDERUNG = {
    "art": "aenderung",
    "stufe": "Tief",
    "kategorie": "Ruhe",
    "original": "Atmen",
    "emoji": "💨",
    "titel": "Langsam atmen",
    "beschreibung": "Viermal ein, viermal aus.",
    "tipp": "",
    "erg": "Ida",
}


def inhalt(pfad):
    """Alle Zellen des Blattes `Skills` – zum Vergleich vorher/nachher."""
    ws = openpyxl.load_workbook(pfad)["Skills"]
    return [[c.value for c in zeile] for zeile in ws.iter_rows()]


def test_uebernahme_schreibt_nichts_wenn_eine_aenderung_nicht_passt(tmp_path):
    # Die wichtigste Eigenschaft: gespeichert wird erst, wenn ALLES zugeordnet
    # ist. Zwei zuordenbare Aenderungen, eine nicht zuordenbare und ein neuer
    # Skill – danach darf in der Datei nichts davon stehen, auch nicht die
    # beiden Aenderungen, die fuer sich genommen gepasst haetten.
    pfad = mappe_mit_skill(tmp_path)
    vorher = inhalt(pfad)

    with pytest.raises(vh.ZeileNichtGefunden):
        vh.in_excel_uebernehmen(
            pfad,
            [AENDERUNG, ZWEITE_AENDERUNG, dict(AENDERUNG, original="Gibt es nicht")],
            [NEUER_SKILL],
        )

    assert inhalt(pfad) == vorher, "die Datei muss unveraendert geblieben sein"


def test_uebernahme_schreibt_nichts_wenn_die_datei_gesperrt_ist(tmp_path):
    # Ein einziger Speichervorgang fuer Aenderungen UND neue Zeilen: scheitert
    # er, ist die Zusage „Es wurde nichts veraendert" in jedem Fall wahr.
    pfad = mappe_mit_skill(tmp_path)
    vorher = inhalt(pfad)
    os.chmod(pfad, stat.S_IREAD)
    try:
        with pytest.raises(SystemExit) as ausnahme:
            vh.in_excel_uebernehmen(pfad, [AENDERUNG], [NEUER_SKILL])
        assert "nichts veraendert" in str(ausnahme.value)
    finally:
        os.chmod(pfad, stat.S_IWRITE | stat.S_IREAD)

    assert inhalt(pfad) == vorher, "die Datei muss unveraendert geblieben sein"


def test_aenderung_ohne_urspruenglichen_titel_trifft_keine_leere_zeile(tmp_path):
    # Ein leerer urspruenglicher Titel wuerde sonst auf eine Zeile mit leerer
    # Titelzelle passen und die falsche Zeile ueberschreiben. pruefe_eintrag
    # faengt das ab – die Sperre gehoert trotzdem direkt vor das Schreiben.
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(KOPF)
    ws.append(["Hoch", "Ablenkung", "🎧", "", "Zeile ohne Titel.", "", "Max", ""])
    wb.save(pfad)
    vorher = inhalt(pfad)

    with pytest.raises(vh.ZeileNichtGefunden):
        vh.in_excel_aendern(pfad, [dict(AENDERUNG, original="")])

    assert inhalt(pfad) == vorher


def test_aenderung_greift_nicht_auf_eine_im_selben_lauf_neue_zeile(tmp_path):
    # Aenderungen werden VOR den neuen Zeilen eingearbeitet: eine Aenderung darf
    # sich nie auf einen Skill beziehen, den derselbe Lauf erst anlegt.
    pfad = mappe_mit_skill(tmp_path)
    vorher = inhalt(pfad)

    with pytest.raises(vh.ZeileNichtGefunden):
        vh.in_excel_uebernehmen(
            pfad, [dict(AENDERUNG, original="Spazieren gehen")], [NEUER_SKILL]
        )

    assert inhalt(pfad) == vorher
