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
