import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import duplikat


def test_umgebungsvariable_wird_gefunden(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-aus-der-umgebung")
    assert duplikat.schluessel_finden(tmp_path) == "sk-test-aus-der-umgebung"


def test_auskommentierte_zuweisung_gewinnt_nicht(tmp_path, monkeypatch):
    """Eine auskommentierte Zuweisung darf die echte Zeile nicht verdraengen.

    Prueft NICHT den `startswith("#")`-Zweig einzeln -- das kann kein
    ausgabebasierter Test, siehe Kommentar in `_env_datei_lesen`. Geprueft
    wird nur das Ergebnis: Steht vor der echten Zuweisung eine Zeile, die wie
    eine auskommentierte Zuweisung aussieht, gewinnt trotzdem der echte Wert.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / ".gitignore").write_text(".env*\n", encoding="utf-8")
    (tmp_path / ".env").write_text(
        "# ANTHROPIC_API_KEY=sk-auskommentiert\n"
        "ANTHROPIC_API_KEY=sk-test-aus-der-datei\n",
        encoding="utf-8",
    )
    assert duplikat.schluessel_finden(tmp_path) == "sk-test-aus-der-datei"


def test_umgebungsvariable_hat_vorrang(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-umgebung")
    (tmp_path / ".gitignore").write_text(".env*\n", encoding="utf-8")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-datei\n", encoding="utf-8")
    assert duplikat.schluessel_finden(tmp_path) == "sk-umgebung"


def test_anfuehrungszeichen_und_leerzeichen_werden_entfernt(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / ".gitignore").write_text(".env*\n", encoding="utf-8")
    (tmp_path / ".env").write_text(
        '  ANTHROPIC_API_KEY = "sk-in-anfuehrungszeichen"  \n', encoding="utf-8"
    )
    assert duplikat.schluessel_finden(tmp_path) == "sk-in-anfuehrungszeichen"


def test_ohne_alles_kein_schluessel(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert duplikat.schluessel_finden(tmp_path) is None


def test_env_ohne_gitignore_schutz_haelt_an(tmp_path, monkeypatch):
    """Sonst wuerde `git add -A` den Schluessel veroeffentlichen."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-ungeschuetzt\n", encoding="utf-8")
    with pytest.raises(SystemExit) as ausnahme:
        duplikat.schluessel_finden(tmp_path)
    meldung = str(ausnahme.value)
    assert ".gitignore" in meldung
    assert "sk-ungeschuetzt" not in meldung, "der Schluessel darf nie in der Meldung stehen"


def test_env_ohne_gitignore_datei_haelt_ebenfalls_an(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-ungeschuetzt\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        duplikat.schluessel_finden(tmp_path)


def test_env_mit_git_negation_haelt_an(tmp_path, monkeypatch):
    """`.gitignore` mit `.env*` UND `!.env` schuetzt die Datei in Wirklichkeit NICHT.

    Ein reiner Zeichenkettenvergleich der .gitignore-Zeilen sieht die Negation
    nicht -- nur Git selbst kennt sie. In einem echten Repo muss deshalb trotz
    vorhandener Zeile `.env*` angehalten werden.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(".env*\n!.env\n", encoding="utf-8")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-ungeschuetzt\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        duplikat.schluessel_finden(tmp_path)


def test_env_in_echtem_git_repo_wird_erkannt(tmp_path, monkeypatch):
    """Bestaetigt den Git-Pfad auch fuer den normalen (geschuetzten) Fall."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(".env*\n", encoding="utf-8")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-aus-git-repo\n", encoding="utf-8")
    assert duplikat.schluessel_finden(tmp_path) == "sk-aus-git-repo"


def test_ohne_git_greift_der_rueckfallweg(tmp_path, monkeypatch):
    """Ist Git nicht aufrufbar (z. B. nicht installiert), greift der
    Zeichenkettenvergleich als Rueckfall -- ohne echten Eingriff ins System.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def kein_git(*args, **kwargs):
        raise FileNotFoundError("git nicht gefunden")

    monkeypatch.setattr(duplikat.subprocess, "run", kein_git)
    (tmp_path / ".gitignore").write_text(".env*\n", encoding="utf-8")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-ohne-git\n", encoding="utf-8")
    assert duplikat.schluessel_finden(tmp_path) == "sk-ohne-git"


def test_ohne_git_und_ohne_schutz_haelt_der_rueckfallweg_ebenfalls_an(tmp_path, monkeypatch):
    """Derselbe Rueckfallweg muss auch den ungeschuetzten Fall erkennen."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def kein_git(*args, **kwargs):
        raise FileNotFoundError("git nicht gefunden")

    monkeypatch.setattr(duplikat.subprocess, "run", kein_git)
    (tmp_path / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-ungeschuetzt\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        duplikat.schluessel_finden(tmp_path)


def test_env_mit_ungueltigem_utf8_haelt_verstaendlich_an(tmp_path, monkeypatch):
    """Kaputte/binaere .env: verstaendliche Meldung statt rohem Traceback.

    Ein roher UnicodeDecodeError zeigt in seiner Meldung eine Byte-Vorschau
    der Datei -- ein unwahrscheinlicher, aber unnoetiger Weg, auf dem
    Schluesselmaterial in der Konsole landen koennte.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / ".gitignore").write_text(".env*\n", encoding="utf-8")
    (tmp_path / ".env").write_bytes(b"ANTHROPIC_API_KEY=\xff\xfe kaputt")
    with pytest.raises(SystemExit) as ausnahme:
        duplikat.schluessel_finden(tmp_path)
    meldung = str(ausnahme.value)
    assert "UTF-8" in meldung
    assert "\\xff" not in meldung


BESTAND = {
    "hoch": {"kategorien": [{"label": "Ablenkung", "skills": [
        {"e": "🎧", "t": "Musik hören", "b": "Ein Lied auflegen.", "tip": "", "von": "", "erg": ""},
    ]}]},
    "mittel": {"kategorien": []},
    "tief": {"kategorien": [{"label": "Ruhe", "skills": [
        {"e": "🌊", "t": "Atmen", "b": "Ruhig atmen.", "tip": "", "von": "", "erg": ""},
    ]}]},
}


def test_prompt_wird_aus_der_datei_gelesen(tmp_path):
    ordner = tmp_path / "tools"
    ordner.mkdir()
    (ordner / "duplikat_prompt.md").write_text("Sei streng.", encoding="utf-8")
    assert duplikat.lade_prompt(tmp_path) == "Sei streng."


def test_fehlende_prompt_datei_meldet_sich_verstaendlich(tmp_path):
    with pytest.raises(SystemExit) as ausnahme:
        duplikat.lade_prompt(tmp_path)
    meldung = str(ausnahme.value)
    assert "duplikat_prompt.md" in meldung
    assert "fehlt" in meldung.lower()


def test_leere_prompt_datei_meldet_sich(tmp_path):
    """Eine leere Datei ergaebe eine Pruefung ohne Anweisung – das faellt sonst
    erst an unbrauchbaren Antworten auf."""
    ordner = tmp_path / "tools"
    ordner.mkdir()
    (ordner / "duplikat_prompt.md").write_text("   \n\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        duplikat.lade_prompt(tmp_path)


def test_bestand_wird_kompakt_aufbereitet():
    text = duplikat.bestand_als_text(BESTAND)
    assert "Hoch / Ablenkung: Musik hören | Ein Lied auflegen." in text
    assert "Tief / Ruhe: Atmen | Ruhig atmen." in text
    assert "Mittel" not in text, "leere Stufen erzeugen keine Zeilen"


def test_bestand_zeile_bleibt_eindeutig_bei_gedankenstrich_in_beschreibung():
    """21 von 100 echten Beschreibungen enthalten selbst einen Gedankenstrich.

    Ein Gedankenstrich als Trenner zwischen Titel und Beschreibung waere dann
    nicht mehr eindeutig. Das Trennzeichen `|` kommt in keinem der echten
    Felder vor (siehe docs/skills-daten.json)."""
    bestand = {
        "hoch": {"kategorien": [{"label": "Achtsamkeit", "skills": [
            {
                "e": "🍽️",
                "t": "Achtsames Essen üben",
                "b": "Bewusst essen — jeden Bissen schmecken.",
                "tip": "",
                "von": "",
                "erg": "",
            },
        ]}]},
        "mittel": {"kategorien": []},
        "tief": {"kategorien": []},
    }
    text = duplikat.bestand_als_text(bestand)
    assert (
        "Hoch / Achtsamkeit: Achtsames Essen üben | Bewusst essen — jeden Bissen schmecken."
        in text
    )


def test_echte_prompt_datei_existiert_und_ist_gefuellt():
    """Die mitgelieferte Datei muss im Repo liegen, sonst laeuft nichts."""
    text = duplikat.lade_prompt(duplikat.PROJEKT)
    assert len(text) > 200


NEUE = [
    {"stufe": "Hoch", "kategorie": "Ablenkung", "titel": "Lieblingslied auflegen",
     "beschreibung": "Ein Lied aussuchen und hoeren."},
]


class FakeAntwort:
    def __init__(self, nutzlast):
        block = type("Block", (), {"parsed_output": nutzlast, "text": json.dumps(nutzlast)})
        self.content = [block()]


class FakeClient:
    """Ersetzt den echten Client – die Tests duerfen nie ins Netz."""

    def __init__(self, nutzlast=None, fehler=None):
        self.nutzlast = nutzlast if nutzlast is not None else {"treffer": []}
        self.fehler = fehler
        self.gesehen = {}
        aussen = self

        class Messages:
            def create(self, **kwargs):
                aussen.gesehen = kwargs
                if aussen.fehler:
                    raise aussen.fehler
                return FakeAntwort(aussen.nutzlast)

        self.messages = Messages()


def test_treffer_wird_durchgereicht():
    client = FakeClient({"treffer": [{
        "titel": "Lieblingslied auflegen", "aehnlich_zu": "Musik hören",
        "stufe": "Hoch", "kategorie": "Ablenkung",
        "begruendung": "Beide beschreiben gezieltes Musikhoeren.",
    }]})
    treffer = duplikat.pruefe_duplikate(NEUE, BESTAND, client)
    assert len(treffer) == 1
    assert treffer[0]["aehnlich_zu"] == "Musik hören"


def test_ohne_treffer_leere_liste():
    assert duplikat.pruefe_duplikate(NEUE, BESTAND, FakeClient()) == []


def test_ohne_neue_vorschlaege_wird_gar_nicht_gefragt():
    client = FakeClient()
    assert duplikat.pruefe_duplikate([], BESTAND, client) == []
    assert client.gesehen == {}, "ohne Vorschlaege darf kein Aufruf erfolgen"


def test_anfrage_enthaelt_prompt_bestand_und_neue():
    client = FakeClient()
    duplikat.pruefe_duplikate(NEUE, BESTAND, client)
    assert client.gesehen["model"] == duplikat.MODELL
    assert "Dublette" in client.gesehen["system"]
    inhalt = client.gesehen["messages"][0]["content"]
    assert "Musik hören" in inhalt, "der Bestand fehlt in der Anfrage"
    assert "Lieblingslied auflegen" in inhalt, "der neue Vorschlag fehlt"
    schema = client.gesehen["output_config"]["format"]
    assert schema["type"] == "json_schema"
    assert "treffer" in schema["schema"]["properties"]


def test_fehler_der_schnittstelle_haelt_den_lauf_nicht_an(capsys):
    """Eine optionale Zutat darf den Hauptweg niemals blockieren."""
    client = FakeClient(fehler=RuntimeError("Netz weg"))
    assert duplikat.pruefe_duplikate(NEUE, BESTAND, client) == []
    ausgabe = capsys.readouterr().out
    assert "Duplikatpruefung" in ausgabe
    assert "uebersprungen" in ausgabe.lower() or "übersprungen" in ausgabe.lower()


def test_unerwartete_antwort_haelt_den_lauf_nicht_an():
    """Kommt etwas anderes zurueck als erwartet, wird nicht geraten."""
    assert duplikat.pruefe_duplikate(NEUE, BESTAND, FakeClient({"quatsch": 1})) == []


def test_treffer_ohne_pflichtfelder_werden_verworfen():
    client = FakeClient({"treffer": [{"titel": "Lieblingslied auflegen"}]})
    assert duplikat.pruefe_duplikate(NEUE, BESTAND, client) == []
