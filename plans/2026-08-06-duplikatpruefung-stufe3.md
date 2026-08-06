# Duplikatprüfung mit KI — Ausbaustufe 3, Teil 1

> **Für agentische Umsetzer:** ERFORDERLICHE SUB-SKILL: `superpowers:subagent-driven-development`
> (empfohlen) oder `superpowers:executing-plans`, um diesen Plan Aufgabe für Aufgabe
> umzusetzen. Schritte nutzen Checkbox-Syntax (`- [ ]`) zur Verfolgung.

**Ziel:** `vorschlaege.bat` prüft freigegebene **neue** Skills vor der Übernahme gegen
den bestehenden Bestand und fragt bei einem Verdacht nach, statt stillschweigend eine
Dublette einzutragen.

**Architektur:** Ein neues, eigenständiges Modul `tools/duplikat.py` kapselt alles
zur KI-Prüfung (Schlüssel finden, Prompt laden, Aufruf, Antwort auswerten). Es kennt
weder Excel noch GitHub noch die Konsolenführung. `tools/vorschlaege_holen.py` ruft es
an genau einer Stelle in `main()` auf — nach dem Aussortieren, **vor** dem Schreiben.
Die Prüfung ist eine **Zutat, keine Voraussetzung**: Ohne Schlüssel oder bei einem
Fehler der Schnittstelle läuft die Übernahme unverändert weiter.

**Technik:** Python 3.11+, `anthropic` 0.120.2, pytest.

**Zwei Dinge, die ich vor dem Schreiben dieses Plans am Code geprüft habe — bitte
nicht „verbessern", sie sind so gewollt:**

1. **Importweg.** Es gibt **kein** `tools/__init__.py`, `tools` ist also kein Paket.
   `tests/test_vorschlaege_holen.py` legt `tools/` auf `sys.path` und importiert
   direkt (`import vorschlaege_holen as vh`). Genauso wird `duplikat` importiert:
   `import duplikat` — **nicht** über ein Paket (`from tools import …` schlägt
   fehl, weil `tools` keines ist). In
   `vorschlaege_holen.py` funktioniert derselbe Import, weil Python beim Start
   eines Skripts dessen Ordner an den Anfang von `sys.path` setzt.
2. **Wo `anthropic` deklariert wird.** Gestartet wird über `vorschlaege.bat` →
   `uv run tools/vorschlaege_holen.py`. Bei PEP-723 zählt **nur der Kopf des
   Startskripts**; der Kopf eines importierten Moduls wird ignoriert. `anthropic`
   muss darum in die Abhängigkeiten von **`vorschlaege_holen.py`**. Stünde es nur
   in `duplikat.py`, schlüge der Import genau dann fehl, wenn ein Schlüssel
   hinterlegt ist — also im einzigen Fall, der zählt.
   `duplikat.py` bekommt deshalb **keinen** eigenen PEP-723-Kopf; es ist ein Modul,
   kein Startskript.
   Der Import von `anthropic` bleibt trotzdem **innerhalb** von `client_bauen`:
   Die Testreihe läuft ohne `--with anthropic`, und `duplikat` muss dort
   importierbar sein, ohne dass das Paket vorhanden ist.

## Globale Vorgaben

- **Schweizer Schreibweise, durchgängig `ss` statt Eszett** — auch in Kommentaren,
  Meldungen und Testnamen.
- **Meldungen richten sich an eine Person ohne Technikkenntnisse**, die
  `vorschlaege.bat` doppelklickt. Jede Meldung sagt, **was zu tun ist**.
- **`skills_daten.xlsx` ist das einzige Original.** Die Prüfung darf niemals dazu
  führen, dass geschrieben wird, wo vorher nicht geschrieben worden wäre.
- **Der Schlüssel darf nie in der Ausgabe erscheinen** — nicht gekürzt, nicht maskiert,
  gar nicht. Auch nicht in Fehlermeldungen oder Tracebacks.
- **Kein Netzzugriff in Tests.** Der Client wird injiziert; die Testreihe muss ohne
  Internet und ohne Schlüssel vollständig grün laufen.
- Modellname als Konstante oben im Modul: `MODELL = "claude-opus-5"`.
- Testbefehl (wie `test.bat`):
  `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
  Ausgangsstand: **121 Tests grün**.
- Arbeitsverzeichnis: `C:\workspace\eraschle\.worktrees\formulare-toolbox`,
  Zweig `feature/formulare-toolbox`. **Nicht pushen.** Namentlich committen,
  niemals `git add -A`.

## Entscheidungen des Menschen

- **Schlüssel: beide Wege.** Erst die Umgebungsvariable `ANTHROPIC_API_KEY`, sonst
  eine `.env`-Datei im Projektordner.
- **Bei einem Treffer zwei Tasten:** übernehmen oder überspringen. Die im Entwurf
  erwähnte dritte Option („als Änderung einarbeiten") wird **bewusst nicht** gebaut.

## Dateien

| Datei | Verantwortung |
|---|---|
| `tools/duplikat.py` (neu) | Schlüssel finden, Prompt laden, KI fragen, Treffer liefern. Kennt nichts anderes. |
| `tools/duplikat_prompt.md` (neu) | Der Anweisungstext an die KI. Frei editierbar, ohne Code anzufassen. |
| `.env.example` (neu) | Vorlage, damit niemand raten muss, wie die Datei aussieht. |
| `tests/test_duplikat.py` (neu) | Tests für das Modul, ohne Netz. |
| `tools/vorschlaege_holen.py` | Aufruf an genau einer Stelle in `main()` + Rückfrage. |
| `CLAUDE.md`, `ANLEITUNG.md` | Dokumentation. |

**Wichtige Designentscheidung zum Prompt:** Die Datei enthält **nur die Anweisungen**,
nicht die Daten. Bestand und neue Vorschläge baut der Code als eigene Nachricht
zusammen. Grund: Platzhalter im Text (`{bestand}`) wären eine Stolperfalle — wer die
Datei umformuliert und den Platzhalter versehentlich löscht, bekäme eine Prüfung, die
stillschweigend ohne Daten läuft. So kann die Datei beliebig umgeschrieben werden,
ohne dass etwas bricht.

---

### Task 1: Schlüssel finden — mit Schutz vor dem Veröffentlichen

**Files:**
- Create: `tools/duplikat.py`
- Create: `.env.example`
- Test: `tests/test_duplikat.py`

**Interfaces:**
- Produces: `schluessel_finden(projekt: Path) -> str | None` — liefert den Schlüssel
  oder `None`, wenn keiner hinterlegt ist.
- Produces: `KeinSchluessel` wird **nicht** gebraucht; das Fehlen ist kein Fehler.

**Warum diese Aufgabe zuerst:** Sie enthält die einzige Stelle, an der etwas
Sicherheitsrelevantes passieren kann. Das Übernahme-Skript druckt am Ende wörtlich
`git add -A` — läge eine `.env` mit Schlüssel im Ordner und `.gitignore` deckte sie
nicht mehr ab, wäre der Schlüssel mit einem Befehl öffentlich. Genau davor sichert
diese Aufgabe ab.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

`tests/test_duplikat.py` neu anlegen:

```python
import pytest

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
```

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_duplikat.py -q`
Erwartet: FAIL — `ModuleNotFoundError: No module named 'duplikat'`.

Falls stattdessen `No module named 'tools'` erscheint: In `tools/` fehlt eine
`__init__.py`. Prüfe zuerst, wie `tests/test_vorschlaege_holen.py` sein Modul
importiert, und folge demselben Muster — nicht eigenmächtig ein Paket anlegen.

- [ ] **Schritt 3: Modul mit der Schlüsselsuche anlegen**

`tools/duplikat.py`:

```python
"""Duplikatpruefung fuer neue Skill-Vorschlaege (optional, per KI).

Dieses Modul kennt weder Excel noch GitHub noch die Konsolenfuehrung. Es
beantwortet genau eine Frage: „Aehnelt einer dieser neuen Vorschlaege einem
Skill, den es schon gibt?" — und liefert die Treffer zurueck.

Die Pruefung ist eine ZUTAT, keine Voraussetzung: Ohne Schluessel oder bei
einem Fehler der Schnittstelle laeuft die Uebernahme unveraendert weiter.
"""

import json
import os
from pathlib import Path

MODELL = "claude-opus-5"
VARIABLE = "ANTHROPIC_API_KEY"


def _env_datei_lesen(pfad: Path) -> str | None:
    """Sucht den Schluessel in einer .env-Datei. Kein Fremdpaket noetig."""
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        name, _, wert = zeile.partition("=")
        if name.strip() == VARIABLE:
            return wert.strip().strip('"').strip("'") or None
    return None


def schluessel_finden(projekt: Path) -> str | None:
    """Erst die Umgebungsvariable, sonst die .env-Datei. Sonst None.

    None heisst NICHT Fehler: Ohne Schluessel entfaellt die Pruefung
    kommentarlos, und das Uebernahme-Skript laeuft wie sonst auch.
    """
    aus_umgebung = os.environ.get(VARIABLE, "").strip()
    if aus_umgebung:
        return aus_umgebung

    env = projekt / ".env"
    if not env.exists():
        return None

    # Notbremse: Das Uebernahme-Skript schlaegt am Ende woertlich `git add -A`
    # vor. Deckt .gitignore die Datei nicht ab, waere der Schluessel mit einem
    # Befehl oeffentlich — und ein veroeffentlichter Schluessel laesst sich
    # nicht zurueckholen, nur sperren.
    gitignore = projekt / ".gitignore"
    geschuetzt = gitignore.exists() and any(
        zeile.strip() in (".env", ".env*", "*.env")
        for zeile in gitignore.read_text(encoding="utf-8").splitlines()
    )
    if not geschuetzt:
        raise SystemExit(
            "❌ Die Datei .env enthaelt einen Schluessel, ist aber nicht vor Git\n"
            "   geschuetzt.\n\n"
            "   Trage in .gitignore eine Zeile `.env*` ein und starte noch\n"
            "   einmal. Ohne diesen Schutz koennte der Schluessel mit dem\n"
            "   naechsten Commit oeffentlich werden.\n\n"
            "   Es wurde nichts veraendert."
        )

    return _env_datei_lesen(env)
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_duplikat.py -q`
Erwartet: PASS, 7 Tests.

- [ ] **Schritt 5: `.env.example` anlegen**

```
# Kopiere diese Datei zu ".env" und trage deinen Schluessel ein.
# Die Datei .env wird von Git ignoriert und gehoert NICHT ins Repo.
#
# Schluessel erstellen: https://console.anthropic.com/settings/keys
#
# Alternativ (empfohlen, liegt dann ausserhalb des Projektordners):
#   setx ANTHROPIC_API_KEY "sk-ant-..."
# Danach ein NEUES Fenster oeffnen, damit die Variable wirkt.

ANTHROPIC_API_KEY=
```

- [ ] **Schritt 6: Nachweisen, dass `.env` wirklich ignoriert wird**

```bash
printf 'ANTHROPIC_API_KEY=sk-nur-ein-test\n' > .env
git status --porcelain --untracked-files=all | grep -c '\.env$'
```
Erwartet: `0` — die Datei taucht nicht auf. **Danach wieder löschen:** `rm .env`
Erscheint sie doch, ist die `.gitignore`-Regel kaputt. Dann anhalten und melden,
nicht weiterbauen.

- [ ] **Schritt 7: Commit**

```bash
git add tools/duplikat.py tests/test_duplikat.py .env.example
git commit -m "Schluesselsuche fuer die Duplikatpruefung"
```

---

### Task 2: Prompt aus einer Datei laden

**Files:**
- Create: `tools/duplikat_prompt.md`
- Modify: `tools/duplikat.py`
- Test: `tests/test_duplikat.py`

**Interfaces:**
- Consumes: nichts aus Task 1 ausser dem Modul selbst.
- Produces: `lade_prompt(projekt: Path) -> str` — der Anweisungstext.
- Produces: `bestand_als_text(bestand: dict) -> str` — der vorhandene Bestand,
  kompakt als Zeilen `Stufe / Kategorie: Titel — Beschreibung`.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

An `tests/test_duplikat.py` anhängen:

```python
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
    assert "Hoch / Ablenkung: Musik hören — Ein Lied auflegen." in text
    assert "Tief / Ruhe: Atmen — Ruhig atmen." in text
    assert "Mittel" not in text, "leere Stufen erzeugen keine Zeilen"


def test_echte_prompt_datei_existiert_und_ist_gefuellt():
    """Die mitgelieferte Datei muss im Repo liegen, sonst laeuft nichts."""
    text = duplikat.lade_prompt(duplikat.PROJEKT)
    assert len(text) > 200
```

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_duplikat.py -q`
Erwartet: FAIL — `AttributeError: module 'duplikat' has no attribute 'lade_prompt'`.

- [ ] **Schritt 3: Prompt-Datei anlegen**

`tools/duplikat_prompt.md`:

```markdown
Du hilfst beim Pflegen einer Skills-Liste fuer Menschen in der Suchtbehandlung.
Ein Skill ist eine kurze, konkrete Handlung, die in einer Krise hilft.

Du bekommst zwei Listen:

1. **Vorhanden** — die Skills, die es bereits gibt.
2. **Neu** — eingereichte Vorschlaege, die uebernommen werden sollen.

Deine Aufgabe: Finde heraus, welche neuen Vorschlaege einen bereits vorhandenen
Skill nur wiederholen.

Als Dublette gilt ein Vorschlag, der **dieselbe Handlung** beschreibt — auch mit
anderen Worten. „Musik bewusst hoeren" und „Lieblingslied auflegen" sind
dieselbe Handlung.

**Keine** Dublette ist:

- dieselbe Sinnesart, aber eine andere Handlung („Chilischote essen" gegen
  „Wasabi essen" — beides scharf, aber verschiedene Mittel),
- eine deutlich andere Ausfuehrung derselben Idee („kalt duschen" gegen
  „Eiswuerfel in die Hand nehmen"),
- derselbe Skill in einer anderen Stufe oder Kategorie — das kann bewusst so
  sein.

Melde nur Faelle, bei denen du dir sicher bist. Ein uebersehener Doppeleintrag
ist leicht zu korrigieren; ein faelschlich zurueckgehaltener Vorschlag kostet
eine Person ihren Beitrag. **Im Zweifel: kein Treffer.**

Begruende jeden Treffer in einem kurzen Satz, der die gemeinsame Handlung nennt.
```

- [ ] **Schritt 4: Lade- und Aufbereitungsfunktion ergänzen**

In `tools/duplikat.py` bei den Konstanten ergänzen:

```python
PROJEKT = Path(__file__).resolve().parent.parent
PROMPT_DATEI = "duplikat_prompt.md"

# Anzeige-Name je Stufenschluessel, damit die KI dieselben Woerter sieht wie
# der Mensch in der Excel.
STUFEN_NAME = {"hoch": "Hoch", "mittel": "Mittel", "tief": "Tief"}
```

und diese Funktionen:

```python
def lade_prompt(projekt: Path) -> str:
    """Liest den Anweisungstext aus tools/duplikat_prompt.md.

    Die Datei enthaelt NUR die Anweisungen, nicht die Daten. Bestand und neue
    Vorschlaege setzt der Code als eigene Nachricht zusammen. So kann die Datei
    frei umformuliert werden, ohne dass ein Platzhalter kaputtgeht.
    """
    pfad = projekt / "tools" / PROMPT_DATEI
    if not pfad.exists():
        raise SystemExit(
            f"❌ Die Datei tools/{PROMPT_DATEI} fehlt.\n\n"
            "   In ihr steht, wonach die Duplikatpruefung suchen soll. Ohne sie\n"
            "   kann nicht geprueft werden. Hol die Datei aus dem Repo zurueck\n"
            "   (git checkout tools/) oder nimm den Schluessel weg, dann\n"
            "   entfaellt die Pruefung.\n\n"
            "   Es wurde nichts veraendert."
        )
    text = pfad.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(
            f"❌ Die Datei tools/{PROMPT_DATEI} ist leer.\n\n"
            "   Ohne Anweisung liefert die Pruefung unbrauchbare Ergebnisse.\n"
            "   Bitte den Text wiederherstellen (git checkout tools/).\n\n"
            "   Es wurde nichts veraendert."
        )
    return text


def bestand_als_text(bestand: dict) -> str:
    """Der vorhandene Bestand als kompakte Zeilenliste."""
    zeilen = []
    for schluessel, stufe in bestand.items():
        name = STUFEN_NAME.get(schluessel, schluessel)
        for kategorie in stufe.get("kategorien", []):
            for skill in kategorie.get("skills", []):
                zeilen.append(
                    f"{name} / {kategorie['label']}: {skill['t']} — {skill['b']}"
                )
    return "\n".join(zeilen)
```

- [ ] **Schritt 5: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_duplikat.py -q`
Erwartet: PASS, 12 Tests.

- [ ] **Schritt 6: Commit**

```bash
git add tools/duplikat.py tools/duplikat_prompt.md tests/test_duplikat.py
git commit -m "Prompt kommt aus einer Datei, Bestand kompakt aufbereitet"
```

---

### Task 3: Der Aufruf an die KI

**Files:**
- Modify: `tools/duplikat.py`
- Test: `tests/test_duplikat.py`

**Interfaces:**
- Consumes: `schluessel_finden`, `lade_prompt`, `bestand_als_text`, `MODELL`.
- Produces: `pruefe_duplikate(neue: list[dict], bestand: dict, client) -> list[dict]`
  Jeder Treffer ist ein dict mit den Schlüsseln `titel`, `aehnlich_zu`, `stufe`,
  `kategorie`, `begruendung` — alle `str`.
  `neue` sind die Vorschlagsdicts aus `vorschlaege_holen.bereinigt()`, also mit
  den Schlüsseln `stufe`, `kategorie`, `titel`, `beschreibung`.
- Produces: `client_bauen(schluessel: str)` — kapselt den Import von `anthropic`,
  damit das Paket nur geladen wird, wenn tatsächlich geprüft wird.

**Der wichtigste Punkt dieser Aufgabe:** Ein Fehler der Schnittstelle — kein Netz,
Kontingent aufgebraucht, ungültiger Schlüssel, unerwartete Antwort — darf die
Übernahme **niemals** anhalten. Er wird gemeldet, und der Lauf geht ohne Prüfung
weiter. Alles andere hiesse, dass eine optionale Zutat den Hauptweg blockiert.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

An `tests/test_duplikat.py` anhängen:

```python
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
```

Ganz oben in der Testdatei ergänzen: `import json`

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_duplikat.py -q`
Erwartet: FAIL — `AttributeError: module 'duplikat' has no attribute 'pruefe_duplikate'`.

- [ ] **Schritt 3: Aufruf umsetzen**

In `tools/duplikat.py` ergänzen:

```python
# Festes Antwortschema: So kann die Antwort nicht als Fliesstext zurueckkommen,
# den wir dann raten muessten.
SCHEMA = {
    "type": "object",
    "properties": {
        "treffer": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "titel": {"type": "string"},
                    "aehnlich_zu": {"type": "string"},
                    "stufe": {"type": "string"},
                    "kategorie": {"type": "string"},
                    "begruendung": {"type": "string"},
                },
                "required": ["titel", "aehnlich_zu", "stufe", "kategorie", "begruendung"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["treffer"],
    "additionalProperties": False,
}

PFLICHTFELDER = ("titel", "aehnlich_zu", "stufe", "kategorie", "begruendung")


def client_bauen(schluessel: str):
    """Baut den Anthropic-Client. Der Import steht absichtlich hier drin:

    Ohne Schluessel wird die Funktion nie gerufen, und dann muss das Paket
    `anthropic` auch nicht installiert sein.
    """
    import anthropic

    return anthropic.Anthropic(api_key=schluessel)


def _anfrage_text(neue: list, bestand: dict) -> str:
    zeilen = ["## Vorhanden", bestand_als_text(bestand), "", "## Neu"]
    for v in neue:
        zeilen.append(
            f"{v['stufe']} / {v['kategorie']}: {v['titel']} — {v['beschreibung']}"
        )
    return "\n".join(zeilen)


def pruefe_duplikate(neue: list, bestand: dict, client) -> list:
    """Fragt die KI, welche neuen Vorschlaege es schon gibt.

    Liefert IMMER eine Liste. Geht etwas schief, ist sie leer und der Lauf geht
    ohne Pruefung weiter — die Pruefung ist eine Zutat, keine Voraussetzung.
    """
    if not neue:
        return []

    try:
        antwort = client.messages.create(
            model=MODELL,
            max_tokens=2000,
            system=lade_prompt(PROJEKT),
            messages=[{"role": "user", "content": _anfrage_text(neue, bestand)}],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        )
    except SystemExit:
        raise  # fehlende/leere Prompt-Datei: die Meldung soll durchschlagen
    except Exception as fehler:
        print(
            f"\n⚠ Die Duplikatpruefung wurde uebersprungen: {type(fehler).__name__}.\n"
            "   Die Uebernahme laeuft normal weiter – sie haengt nicht daran.\n"
            "   Meist ist das Internet weg oder der Schluessel nicht mehr gueltig."
        )
        return []

    block = antwort.content[0]
    nutzlast = getattr(block, "parsed_output", None)
    if nutzlast is None:
        try:
            nutzlast = json.loads(block.text)
        except (AttributeError, ValueError):
            return []

    roh = nutzlast.get("treffer") if isinstance(nutzlast, dict) else None
    if not isinstance(roh, list):
        return []

    # Nur vollstaendige Treffer: ein halber Treffer wuerde beim Nachfragen eine
    # luecken hafte Zeile ergeben, die niemand einordnen kann.
    return [
        t for t in roh
        if isinstance(t, dict) and all(str(t.get(f, "")).strip() for f in PFLICHTFELDER)
    ]
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_duplikat.py -q`
Erwartet: PASS, 19 Tests.

- [ ] **Schritt 5: Gegenprobe, dass die Tests etwas prüfen**

Baue nacheinander diese drei Mutationen ein, lass die Tests laufen und **stelle
danach den Ausgangszustand wieder her**:

| Mutation | Erwartung |
|---|---|
| `except Exception` entfernen (Fehler durchschlagen lassen) | mindestens 1 Test rot |
| `if not neue: return []` entfernen | mindestens 1 Test rot |
| Filter auf `PFLICHTFELDER` entfernen | mindestens 1 Test rot |

Bleibt eine grün, ist der zugehörige Test wertlos — melde es, statt es zu übergehen.

- [ ] **Schritt 6: Commit**

```bash
git add tools/duplikat.py tests/test_duplikat.py
git commit -m "KI-Aufruf mit festem Antwortschema"
```

---

### Task 4: Einbau ins Übernahme-Skript mit Rückfrage

**Files:**
- Modify: `tools/vorschlaege_holen.py`
- Test: `tests/test_vorschlaege_holen.py`

**Interfaces:**
- Consumes: `duplikat.schluessel_finden(PROJEKT)`, `duplikat.client_bauen(schluessel)`,
  `duplikat.pruefe_duplikate(neue, bestand, client)`.
- Produces: `nachfragen(treffer: list, uebernehmen: list, eingabe=input) -> list`
  Liefert die Liste der Issue-Nummern, die **übersprungen** werden sollen.

**Wo genau:** In `main()` **nach** der Zeile
`neue = [d for _, d in uebernehmen if d.get("art") != "aenderung"]`
und **vor** dem `try:`-Block mit `in_excel_uebernehmen`.

**Warum dort:** Vorher stünde nicht fest, welche Vorschläge überhaupt in Frage
kommen. Nachher wäre bereits geschrieben — und dann käme die Rückfrage zu spät.

**Nur neue Skills werden geprüft.** Eine Änderung zeigt über Stufe, Kategorie und
Originaltitel auf einen bestimmten vorhandenen Skill; „ähnelt einem vorhandenen
Skill" ist dort keine sinnvolle Frage.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

An `tests/test_vorschlaege_holen.py` anhängen:

```python
TREFFER = [{
    "titel": "Lieblingslied auflegen", "aehnlich_zu": "Musik hören",
    "stufe": "Hoch", "kategorie": "Ablenkung",
    "begruendung": "Beide beschreiben gezieltes Musikhoeren.",
}]


def uebernehmen_liste():
    return [({"number": 7}, {"art": "neu", "stufe": "Hoch", "kategorie": "Ablenkung",
                             "titel": "Lieblingslied auflegen"})]


def test_nachfrage_uebernehmen_laesst_den_vorschlag_drin(capsys):
    offen = vh.nachfragen(TREFFER, uebernehmen_liste(), eingabe=lambda _: "ü")
    assert offen == []
    ausgabe = capsys.readouterr().out
    assert "Musik hören" in ausgabe
    assert "Beide beschreiben" in ausgabe, "die Begruendung muss sichtbar sein"


def test_nachfrage_weiter_nimmt_den_vorschlag_heraus():
    assert vh.nachfragen(TREFFER, uebernehmen_liste(), eingabe=lambda _: "w") == [7]


def test_nachfrage_akzeptiert_grossschreibung_und_leerzeichen():
    assert vh.nachfragen(TREFFER, uebernehmen_liste(), eingabe=lambda _: " W ") == [7]


def test_nachfrage_fragt_erneut_bei_unsinniger_eingabe():
    antworten = iter(["x", "", "w"])
    assert vh.nachfragen(TREFFER, uebernehmen_liste(),
                         eingabe=lambda _: next(antworten)) == [7]


def test_nachfrage_ohne_tastatur_ueberspringt_sicherheitshalber():
    """Laeuft das Skript ohne Eingabemoeglichkeit, wird NICHT stillschweigend
    uebernommen – lieber bleibt das Issue offen."""
    def keine_tastatur(_):
        raise EOFError

    assert vh.nachfragen(TREFFER, uebernehmen_liste(), eingabe=keine_tastatur) == [7]


def test_treffer_ohne_passendes_issue_wird_ignoriert():
    """Nennt die KI einen Titel, den es hier gar nicht gibt, darf nichts passieren."""
    fremd = [dict(TREFFER[0], titel="Gibt es nicht")]
    assert vh.nachfragen(fremd, uebernehmen_liste(), eingabe=lambda _: "w") == []
```

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_vorschlaege_holen.py -k nachfrage -q`
Erwartet: FAIL — `AttributeError: module 'vorschlaege_holen' has no attribute 'nachfragen'`.

- [ ] **Schritt 3: `nachfragen` umsetzen**

In `tools/vorschlaege_holen.py` vor `main()` ergänzen:

```python
def nachfragen(treffer: list, uebernehmen: list, eingabe=input) -> list:
    """Fragt je Treffer nach und liefert die Nummern der Issues, die
    uebersprungen werden sollen.

    Uebersprungen heisst: nicht eintragen, Issue bleibt offen. Es geht dabei
    nichts verloren – der naechste Lauf bietet den Vorschlag wieder an.
    """
    nach_titel = {d["titel"]: i["number"] for i, d in uebernehmen}
    ueberspringen = []
    for t in treffer:
        nummer = nach_titel.get(t["titel"])
        if nummer is None:
            continue  # kein passender Vorschlag – nichts zu fragen
        print(
            f'\n⚠ „{t["titel"]}" aehnelt „{t["aehnlich_zu"]}" '
            f'({t["stufe"]} / {t["kategorie"]})\n'
            f'   Begruendung: {t["begruendung"]}'
        )
        while True:
            try:
                wahl = eingabe("   [ü]bernehmen  [w]eiter (ueberspringen)  ? ")
            except EOFError:
                # Kein Mensch am Bildschirm: nicht raten, lieber offen lassen.
                print("   Keine Eingabe moeglich – wird uebersprungen.")
                ueberspringen.append(nummer)
                break
            wahl = wahl.strip().lower()
            if wahl in ("ü", "u", "ue"):
                break
            if wahl == "w":
                ueberspringen.append(nummer)
                break
            print("   Bitte ü oder w eingeben.")
    return ueberspringen
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_vorschlaege_holen.py -k nachfrage -q`
Erwartet: PASS, 6 Tests.

- [ ] **Schritt 5: `anthropic` in die Abhängigkeiten des Startskripts eintragen**

Im PEP-723-Kopf von `tools/vorschlaege_holen.py` (die ersten vier Zeilen):

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl", "anthropic"]
# ///
```

**Das ist nicht optional.** `vorschlaege.bat` startet `uv run tools/vorschlaege_holen.py`;
bei PEP-723 zählt allein der Kopf des Startskripts. Ohne diese Zeile scheitert
`client_bauen` mit `ModuleNotFoundError` — und zwar genau dann, wenn ein Schlüssel
hinterlegt ist, also im einzigen Fall, in dem die Prüfung überhaupt läuft.

Gegenprobe nach dem Eintragen:

```bash
uv run tools/vorschlaege_holen.py
```
Erwartet: läuft durch wie vorher (`uv` installiert `anthropic` einmalig nach).

- [ ] **Schritt 6: In `main()` einhängen**

Oben bei den Importen ergänzen:

```python
import duplikat
```

Falls `tools/vorschlaege_holen.py` nicht als Paketmodul läuft, nimm denselben
Importweg, den die Datei schon für andere eigene Module nutzt — **prüfe das, statt
zu raten**, und melde es, wenn keiner existiert.

In `main()` nach der Zeile `neue = [d for _, d in uebernehmen if ...]` einfügen:

```python
    # Optionale Duplikatpruefung. Ohne Schluessel entfaellt sie kommentarlos;
    # scheitert sie, laeuft die Uebernahme unveraendert weiter.
    schluessel = duplikat.schluessel_finden(PROJEKT)
    if schluessel and neue:
        print("\nPruefe die neuen Vorschlaege auf Dubletten …")
        treffer = duplikat.pruefe_duplikate(
            neue, bestand, duplikat.client_bauen(schluessel)
        )
        raus = nachfragen(treffer, uebernehmen)
        if raus:
            uebernehmen = [(i, d) for i, d in uebernehmen if i["number"] not in raus]
            aenderungen = [d for _, d in uebernehmen if d.get("art") == "aenderung"]
            neue = [d for _, d in uebernehmen if d.get("art") != "aenderung"]
            uebersprungen.extend(
                i for i in issues if i["number"] in raus
            )
```

Ausserdem oben bei den Pfadkonstanten ergänzen (prüfe zuerst, ob es schon eine
gleichwertige Konstante gibt — dann diese verwenden):

```python
PROJEKT = Path(__file__).resolve().parent.parent
```

- [ ] **Schritt 7: Volle Testreihe**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
Erwartet: PASS, **146** Tests (121 + 19 aus Tasks 1–3 + 6 aus dieser Aufgabe).

Weicht die Zahl ab, zähle nach und melde die tatsächliche — die Zahl ist eine
Erwartung aus dem Plan, kein Gesetz.

- [ ] **Schritt 8: Leerlauf gegen das echte Repo**

Run: `uv run tools/vorschlaege_holen.py`
Erwartet: „Keine freigegebenen Vorschläge offen. Nichts zu tun." — unverändert wie
vorher, denn ohne Schlüssel und ohne offene Issues ändert sich nichts.

- [ ] **Schritt 9: Commit**

```bash
git add tools/vorschlaege_holen.py tests/test_vorschlaege_holen.py
git commit -m "Duplikatpruefung ins Uebernahme-Skript einhaengen"
```

---

### Task 5: Dokumentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `ANLEITUNG.md`
- Modify: `specs/2026-08-03-skill-vorschlagen-design.md`

- [ ] **Schritt 1: `ANLEITUNG.md`**

Im Abschnitt „Vorschläge von anderen übernehmen" ergänzen — in der Sprache des
Menschen, ohne Funktionsnamen:

```markdown
### Dubletten-Warnung (nur wenn eingerichtet)

Wenn ein Anthropic-Schlüssel hinterlegt ist, schaut das Programm vor dem
Übernehmen nach, ob ein neuer Vorschlag einen Skill wiederholt, den es schon
gibt. Ist das der Fall, fragt es nach:

```
⚠ „Lieblingslied auflegen" aehnelt „Musik hören" (Hoch / Ablenkung)
   Begruendung: Beide beschreiben gezieltes Musikhoeren.
   [ü]bernehmen  [w]eiter (ueberspringen)  ?
```

- **ü** — trotzdem eintragen. Die Einschätzung war daneben.
- **w** — nicht eintragen. Der Vorschlag bleibt offen und kommt beim nächsten
  Lauf wieder. Es geht nichts verloren.

**Ohne Schlüssel entfällt dieser Schritt komplett**, und das Programm läuft wie
gewohnt. Du musst nichts einrichten, wenn du das nicht möchtest.

**Einrichten:** Einen Schlüssel auf console.anthropic.com erstellen und dann
entweder einmalig im Terminal `setx ANTHROPIC_API_KEY "sk-ant-..."` ausführen
(danach ein neues Fenster öffnen), oder die Datei `.env.example` zu `.env`
kopieren und den Schlüssel dort eintragen. Ein Durchgang kostet einige Rappen.
```

- [ ] **Schritt 2: `CLAUDE.md`**

Im Abschnitt „Skill-Vorschläge von aussen" ergänzen:

```markdown
**Duplikatprüfung (optional, `tools/duplikat.py`):** Läuft nur, wenn ein
Schlüssel gefunden wird — erst `ANTHROPIC_API_KEY`, sonst eine `.env` im
Projektordner. Geprüft werden **nur neue** Skills, nicht Änderungen (eine
Änderung zeigt bereits auf einen bestimmten Skill). Der Anweisungstext steht in
`tools/duplikat_prompt.md` und enthält **nur Anweisungen, keine Daten** — die
setzt der Code zusammen, damit kein Platzhalter kaputtgehen kann.

Zwei Eigenschaften, die jeder Umbau erhalten muss:

1. **Die Prüfung ist eine Zutat, keine Voraussetzung.** Ohne Schlüssel, ohne
   Netz oder bei einer unerwarteten Antwort läuft die Übernahme unverändert
   weiter. Sie darf den Hauptweg nie blockieren.
2. **Liegt eine `.env` im Ordner, die `.gitignore` nicht abdeckt, hält das
   Programm an.** Das Skript schlägt am Ende `git add -A` vor; ohne diese
   Sperre wäre der Schlüssel mit einem Befehl öffentlich.
```

- [ ] **Schritt 3: Spezifikation nachziehen**

In `specs/2026-08-03-skill-vorschlagen-design.md` im Abschnitt „Ausbaustufen"
Punkt 3 aufteilen: Duplikatprüfung als **umgesetzt** kennzeichnen, die Kaffeeseite
(`docs/unterstuetzen.html`) bleibt offen. Ausserdem im Abschnitt
„Duplikatprüfung mit KI" festhalten, dass die dritte Option („als Änderung
einarbeiten") bewusst **nicht** gebaut wurde und dass der Prompt aus einer Datei
kommt.

- [ ] **Schritt 4: Prüfen und committen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
Erwartet: unverändert grün (Dokumentation ändert nichts am Verhalten).

```bash
git add CLAUDE.md ANLEITUNG.md specs/2026-08-03-skill-vorschlagen-design.md
git commit -m "Duplikatpruefung dokumentieren"
```

---

### Task 6: Echter Durchlauf — braucht den Menschen

Diese Aufgabe kann **kein Agent** erledigen: Sie braucht einen echten Schlüssel und
eine echte Einreichung. Der Umsetzer bereitet sie vor und übergibt.

- [ ] **Schritt 1: Anleitung für den Menschen zusammenstellen**

Schreibe eine kurze Schritt-für-Schritt-Liste:

1. Schlüssel auf `console.anthropic.com/settings/keys` erstellen.
2. Hinterlegen — entweder `setx ANTHROPIC_API_KEY "sk-ant-..."` und ein **neues**
   Fenster öffnen, oder `.env.example` zu `.env` kopieren und eintragen.
3. Über das Formular einen Skill einreichen, der einem vorhandenen **absichtlich
   ähnelt** (z. B. „Lieblingslied auflegen", wenn es „Musik hören" gibt).
4. Dem Issue das Label `freigegeben` geben.
5. `vorschlaege.bat` doppelklicken → die Rückfrage muss erscheinen.
6. Einmal **w** drücken: Der Vorschlag darf **nicht** in der Excel landen und das
   Issue muss offen bleiben.
7. Erneut starten und **ü** drücken: Jetzt muss er übernommen werden.

- [ ] **Schritt 2: Zusichern, dass der Schlüssel nirgends auftaucht**

```bash
git status --porcelain --untracked-files=all
```
Erwartet: keine `.env` in der Liste.

- [ ] **Schritt 3: Übergeben**

Ergebnis berichten und ausdrücklich sagen, was **nicht** geprüft werden konnte.

---

## Selbstprüfung des Plans

**Abdeckung gegen den Entwurf** (`specs/2026-08-03-skill-vorschlagen-design.md`,
Abschnitt „Duplikatprüfung mit KI"):

| Anforderung | Aufgabe |
|---|---|
| Läuft nur bei gesetztem Schlüssel, sonst kommentarlos entfallen | 1, 4 |
| Modell als Konstante oben im Skript | 3 |
| Offizielles `anthropic`-Paket, Antwort per `output_config.format` | 3 |
| Festes JSON-Schema (Treffer, ähnlicher Titel, Begründung) | 3 |
| Rückfrage je Fall | 4 |
| Prompt aus einer Datei (Wunsch des Menschen, über den Entwurf hinaus) | 2 |
| Schlüssel per Umgebungsvariable **oder** `.env` (Entscheidung) | 1 |

**Bewusst nicht umgesetzt:** die dritte Option „als Änderung einarbeiten" — vom
Menschen ausdrücklich zurückgestellt. Im Entwurf ist sie beschrieben; Task 5,
Schritt 3 hält fest, dass sie offen bleibt.

**Namensabgleich:** `schluessel_finden`, `lade_prompt`, `bestand_als_text`,
`client_bauen`, `pruefe_duplikate`, `nachfragen`, `MODELL`, `PROJEKT`, `SCHEMA`,
`PFLICHTFELDER`, `STUFEN_NAME` — in Tasks 1–4 durchgängig gleich geschrieben.

**Offene Annahme, die der Umsetzer prüfen muss:** Wie `tests/` das Modul `tools/`
importiert (`import duplikat` gegen direkten Import). Task 1, Schritt 2
und Task 4, Schritt 5 sagen ausdrücklich, dass dem bestehenden Muster zu folgen und
nicht eigenmächtig ein Paket anzulegen ist.
