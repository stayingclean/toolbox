import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import duplikat


def test_umgebungsvariable_wird_gefunden(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-aus-der-umgebung")
    assert duplikat.schluessel_finden(tmp_path) == "sk-test-aus-der-umgebung"


def test_env_datei_wird_gelesen_wenn_variable_fehlt(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / ".gitignore").write_text(".env*\n", encoding="utf-8")
    # Die Kommentarzeile sieht wie eine echte Zuweisung aus (inkl. "="),
    # damit der Test tatsaechlich beweist, dass Kommentare uebersprungen
    # werden -- ein blosses "# Kommentar" ohne "=" wuerde schon von der
    # vorherigen Bedingung aussortiert und den Kommentar-Zweig nie pruefen.
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
