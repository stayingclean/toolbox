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
    (tmp_path / ".env").write_text(
        "# Kommentar\nANTHROPIC_API_KEY=sk-test-aus-der-datei\n", encoding="utf-8"
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
