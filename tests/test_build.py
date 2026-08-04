import json
import re

import build

SKILLS_HEADER = ["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp"]
SKILLS_ROW = ["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen", "Kopfhörer"]


def test_von_wird_gelesen_wenn_spalte_vorhanden(mappe, monkeypatch):
    pfad = mappe(SKILLS_HEADER + ["Von"], [SKILLS_ROW + ["Max"]])
    monkeypatch.setattr(build, "XLSX", pfad)
    daten = build.load_data()
    assert daten["hoch"]["kategorien"][0]["skills"][0]["von"] == "Max"


def test_von_ist_leer_wenn_spalte_fehlt(mappe, monkeypatch):
    pfad = mappe(SKILLS_HEADER, [SKILLS_ROW])
    monkeypatch.setattr(build, "XLSX", pfad)
    daten = build.load_data()
    assert daten["hoch"]["kategorien"][0]["skills"][0]["von"] == ""


def test_pflichtspalte_fehlt_bricht_ab(mappe, monkeypatch):
    pfad = mappe(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung"], [SKILLS_ROW[:5]])
    monkeypatch.setattr(build, "XLSX", pfad)
    try:
        build.load_data()
    except build.BuildError as fehler:
        assert "Tipp" in str(fehler)
    else:
        raise AssertionError("BuildError erwartet")


def test_vorlage_enthaelt_namenszeile():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    assert 'id="m-von"' in vorlage
    assert "modal-von" in vorlage

    # Nicht nur "s.von"/"s.erg" irgendwo suchen (koennte ein Kommentar sein),
    # sondern den zusammenhaengenden Anzeige-Block aus openModal pruefen: er
    # muss die Namenszeile bei vorhandenem "von" und/oder "erg" zusammensetzen
    # UND bei beiden fehlend wieder verstecken/leeren (sonst bliebe der Name
    # eines fruehreren Skills stehen).
    treffer = re.search(r"var teile=\[\];.*?else\s*\{.*?\}", vorlage, re.DOTALL)
    assert treffer, "Anzeige-Block fuer s.von/s.erg in openModal nicht gefunden"
    block = re.sub(r"\s+", " ", treffer.group(0)).strip()
    assert block == (
        "var teile=[]; if(s.von){ teile.push('Vorgeschlagen von '+s.von); } "
        "if(s.erg){ teile.push('ergänzt von '+s.erg); } "
        "if(teile.length){ mVon.textContent=teile.join(' · '); mVon.hidden=false; } "
        "else { mVon.textContent=''; mVon.hidden=true; }"
    )


def test_daten_json_wird_geschrieben(mappe, monkeypatch, tmp_path):
    pfad = mappe(SKILLS_HEADER + ["Von"], [SKILLS_ROW + ["Max"]])
    ziel = tmp_path / "skills-daten.json"
    monkeypatch.setattr(build, "XLSX", pfad)
    monkeypatch.setattr(build, "DATEN_JSON", ziel)

    build.write_daten_json(build.load_data())

    roh = ziel.read_bytes()
    assert not roh.startswith(b"\xef\xbb\xbf"), "JSON darf kein BOM haben"
    daten = json.loads(roh.decode("utf-8"))
    assert set(daten) == {"hoch", "mittel", "tief"}
    skill = daten["hoch"]["kategorien"][0]["skills"][0]
    assert skill["t"] == "Musik hören"
    assert skill["von"] == "Max"


def test_vorschlagsseite_wird_erzeugt(mappe, monkeypatch, tmp_path):
    pfad = mappe(SKILLS_HEADER + ["Von"], [SKILLS_ROW + ["Max"]])
    ziel = tmp_path / "skill-vorschlagen.html"
    monkeypatch.setattr(build, "XLSX", pfad)
    monkeypatch.setattr(build, "OUTPUT_VORSCHLAG", ziel)

    build.render_vorschlag(build.load_data())

    roh = ziel.read_bytes()
    assert roh.startswith(b"\xef\xbb\xbf")
    html = roh.decode("utf-8-sig")
    assert "var DATEN = {" in html
    assert "Ablenkung" in html
    assert "/*__BUILD_DATA__*/" not in html


def test_script_block_kann_nicht_verlassen_werden(mappe, monkeypatch, tmp_path):
    """Ein </script> im Freitext darf das Skriptelement nicht beenden."""
    gift = "</script><script>alert(1)</script>"
    zeile = SKILLS_ROW[:4] + [gift, "Kopfhörer"]
    pfad = mappe(SKILLS_HEADER, [zeile])
    ziel = tmp_path / "skillsliste.html"
    monkeypatch.setattr(build, "XLSX", pfad)
    monkeypatch.setattr(build, "OUTPUT", ziel)

    build.render(build.load_data())

    html = ziel.read_bytes().decode("utf-8-sig")
    assert gift not in html, "die Zeichenfolge darf nicht wörtlich im Erzeugnis stehen"
    assert "\\u003c/script\\u003e" in html
    assert "<script>alert(1)" not in html

    # Der Wert selbst bleibt unverändert – der Browser (bzw. json.loads) setzt
    # die Escapes beim Parsen zurück.
    # Die Datenzeile ist eine einzige Zeile: bis zum Zeilenende lesen, ohne ";".
    roh = html.split("var DATA = ", 1)[1].split("\n", 1)[0].rstrip().rstrip(";")
    wieder = json.loads(roh)
    assert wieder["hoch"]["kategorien"][0]["skills"][0]["b"] == gift


def test_daten_json_endet_mit_zeilenumbruch(mappe, monkeypatch, tmp_path):
    """Feste Zeilenenden, sonst gibt es plattformabhängige Scheinunterschiede."""
    pfad = mappe(SKILLS_HEADER, [SKILLS_ROW])
    ziel = tmp_path / "skills-daten.json"
    monkeypatch.setattr(build, "XLSX", pfad)
    monkeypatch.setattr(build, "DATEN_JSON", ziel)

    build.write_daten_json(build.load_data())

    roh = ziel.read_bytes()
    assert roh.endswith(b"\n")
    assert b"\r\n" not in roh


def test_vorschlagsvorlage_hat_pflichtbestandteile():
    vorlage = build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")
    for baustein in ['name="falle"', "cf-turnstile", "footer-credit", "WORKER_URL"]:
        assert baustein in vorlage, baustein


def test_vorschlagsvorlage_hat_keine_platzhalter_mehr():
    """Fängt ab, dass die Seite mit unersetzter Worker-Adresse veröffentlicht wird."""
    vorlage = build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")
    for platzhalter in ("WORKER_URL_HIER_EINSETZEN", "TURNSTILE_SITEKEY_HIER_EINSETZEN"):
        assert platzhalter not in vorlage, platzhalter
    assert "https://" in vorlage.split('var WORKER_URL = "')[1][:60]


def test_vorschlagsvorlage_setzt_die_turnstile_aktion():
    """Ohne data-action lehnt der Worker jede Einreichung ab."""
    vorlage = build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")
    assert 'data-action="skill-vorschlag"' in vorlage


def test_vorschlagsvorlage_emojifeld_hat_kein_maxlength_und_bietet_auswahl():
    """maxlength="2" zaehlt UTF-16-Einheiten und blockiert zusammengesetzte
    Emoji (z. B. 🧘‍♀️) stumm. Stattdessen muss die Vorlage eine eingebettete
    Emoji-Auswahl anbieten (kein Nachladen, keine fremde Bibliothek)."""
    vorlage = build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")
    emoji_feld = re.search(r'<input[^>]*id="emoji"[^>]*>', vorlage)
    assert emoji_feld, "Emoji-Eingabefeld nicht gefunden"
    assert "maxlength" not in emoji_feld.group(0)
    assert "Intl.Segmenter" in vorlage
    assert "Schon verwendet" in vorlage


def test_vorschlagsvorlage_emoji_pruefung_hat_notbremse_und_rueckfallweg():
    """Die Client-Pruefung muss dieselbe 16-Codepunkt-Notbremse haben wie
    worker/validate.js – sonst weist der Worker eine sehr lange, aber als EIN
    Graphem zaehlende ZWJ-Kette ab, obwohl das Formular sie durchliess (die
    Person sieht dann eine unerklaerliche Meldung nach dem Absenden). Fehlt
    Intl.Segmenter (aeltere Firefox-Fassungen), darf das Absenden nicht mit
    einem unbehandelten Fehler abbrechen."""
    vorlage = build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")
    assert "EMOJI_CODEPUNKT_GRENZE" in vorlage
    assert "typeof Intl.Segmenter" in vorlage
    assert "Array.from(wert).length" in vorlage


def test_vorschlagsvorlage_themengruppen_stehen_vor_schon_verwendet():
    """'Schon verwendet' kann viele Eintraege haben und darf die kuratierten
    Themengruppen darum nicht unter die Scroll-Kante schieben."""
    vorlage = build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")
    erste_themengruppe = vorlage.index("Körper & Bewegung")
    schon_verwendet_literal = vorlage.index("'Schon verwendet'")
    assert erste_themengruppe < schon_verwendet_literal


def test_erg_wird_gelesen_wenn_spalte_vorhanden(mappe, monkeypatch):
    pfad = mappe(SKILLS_HEADER + ["Von", "Ergaenzt"], [SKILLS_ROW + ["Max", "Lea"]])
    monkeypatch.setattr(build, "XLSX", pfad)
    daten = build.load_data()
    skill = daten["hoch"]["kategorien"][0]["skills"][0]
    assert skill["von"] == "Max"
    assert skill["erg"] == "Lea"


def test_erg_ist_leer_wenn_spalte_fehlt(mappe, monkeypatch):
    pfad = mappe(SKILLS_HEADER, [SKILLS_ROW])
    monkeypatch.setattr(build, "XLSX", pfad)
    skill = build.load_data()["hoch"]["kategorien"][0]["skills"][0]
    assert skill["erg"] == ""


def test_vorlage_nennt_beide_beitragenden():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    assert 'id="m-von"' in vorlage
    assert "s.erg" in vorlage
    assert "ergänzt von" in vorlage
