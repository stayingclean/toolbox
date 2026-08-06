# Bezugsquellen — Stufe 2: Wächter gegen Linkfäule

> **Für agentische Bearbeitung:** ERFORDERLICHER UNTER-SKILL: `superpowers:subagent-driven-development` (empfohlen) oder `superpowers:executing-plans`, Aufgabe für Aufgabe. Schritte sind als Kästchen (`- [ ]`) geführt.

**Voraussetzung:** Stufe 1 (`plans/2026-08-06-bezugsquellen-stufe1.md`) ist fertig — `docs/skills-daten.json` trägt bei jedem Skill ein Feld `links`.

**Ziel:** Ein wöchentlicher Lauf prüft alle veröffentlichten Bezugsquellen und meldet tote in **einem** Sammel-Issue in `stayingclean/toolbox`.

**Architektur:** Ein eigenständiges Python-Skript ohne Fremdbibliotheken (nur Standardbibliothek — `urllib`, `socket`, `subprocess`), damit der Workflow keine Abhängigkeiten installieren muss. Das Urteil („ist dieser Link tot?") ist eine reine Funktion und getrennt vom Abruf; getestet wird ausschliesslich die reine Seite. Für GitHub wird `gh` verwendet, das auf `ubuntu-latest` bereits vorhanden ist.

**Tech Stack:** Python 3.12 (Standardbibliothek), GitHub Actions, GitHub CLI.

**Zugehöriger Entwurf:** `specs/2026-08-06-bezugsquellen-design.md`

## Global Constraints

- **Nur harte Befunde gelten als tot:** `404`, `410`, Domain existiert nicht mehr (DNS-Fehler). `403`, `429` und **alle** `5xx` werden schweigend übergangen. Grund: Shops sperren automatische Abrufe aus; ein Wächter mit Falschalarm wird ignoriert, und ein ignorierter Wächter täuscht Sicherheit vor.
- **Ein einziges Sammel-Issue**, Titel `Tote Bezugsquellen`, Label `tote-links`, Repo `stayingclean/toolbox`. Bei jedem Lauf wird sein Rumpf ersetzt; ist nichts mehr tot, wird es geschlossen.
- **Kein Netzwerkzugriff in den Tests.** Geprüft werden reine Funktionen; `subprocess.run` und der Abruf werden ersetzt.
- **Keine Fremdbibliotheken** — der Workflow soll ohne Installationsschritt laufen.
- **Höflich abrufen:** eine Sekunde Pause zwischen Abrufen, eigener User-Agent, der das Projekt nennt.
- **Der Lauf schlägt nie fehl, nur weil Links tot sind.** Ein Fehlschlag bedeutet: Das Skript selbst kam nicht durch.
- **Deutsche Bezeichner und Kommentare.**

---

### Task 1: Urteil und Aufbereitung als reine Funktionen

**Files:**
- Create: `tools/links_pruefen.py`
- Test: `tests/test_links_pruefen.py`

**Interfaces:**
- Consumes: `docs/skills-daten.json` in der Gestalt aus Stufe 1 — `daten[stufe]["kategorien"][n]["skills"][m]["links"]` ist eine `list[str]`.
- Produces:
  - `alle_links(daten: dict) -> list[dict]` mit Schlüsseln `stufe`, `kategorie`, `titel`, `url`
  - `urteil(ergebnis: dict) -> tuple[bool, str]` — `ergebnis` hat `status: int|None` und `fehler: str|None`
  - `issue_rumpf(tote: list[dict], stand: str) -> str`
  - `zelle(wert) -> str`

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

`tests/test_links_pruefen.py` neu anlegen:

```python
"""Prueft die reine Seite des Waechters – ohne Netzwerk und ohne gh."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import links_pruefen as lp

DATEN = {
    "hoch": {
        "kategorien": [
            {
                "label": "Ablenkung",
                "skills": [
                    {"t": "Zauberwürfel", "links": ["https://a.ch/x", "https://b.ch/y"]},
                    {"t": "Musik hören", "links": []},
                ],
            }
        ]
    },
    "tief": {"kategorien": []},
}


def test_alle_links_sammelt_mit_herkunft():
    liste = lp.alle_links(DATEN)
    assert len(liste) == 2
    assert liste[0] == {
        "stufe": "hoch",
        "kategorie": "Ablenkung",
        "titel": "Zauberwürfel",
        "url": "https://a.ch/x",
    }


def test_alle_links_vertraegt_einen_datenstand_ohne_links():
    """Eine Fassung von vor Stufe 1 darf den Waechter nicht umwerfen."""
    alt = {"hoch": {"kategorien": [{"label": "A", "skills": [{"t": "X"}]}]}}
    assert lp.alle_links(alt) == []


@pytest.mark.parametrize("status", [404, 410])
def test_404_und_410_gelten_als_tot(status):
    tot, grund = lp.urteil({"status": status, "fehler": None})
    assert tot is True
    assert str(status) in grund


def test_dns_fehler_gilt_als_tot():
    tot, grund = lp.urteil({"status": None, "fehler": "dns"})
    assert tot is True
    assert "Domain" in grund


@pytest.mark.parametrize("status", [200, 301, 403, 429, 500, 502, 503])
def test_alles_andere_gilt_nicht_als_tot(status):
    """Shops sperren Bots aus. Ein Waechter, der auf 403 anspringt, meldet
    dauernd Falschalarm und wird nach drei Wochen ignoriert."""
    tot, _ = lp.urteil({"status": status, "fehler": None})
    assert tot is False


def test_netzfehler_gilt_nicht_als_tot():
    tot, _ = lp.urteil({"status": None, "fehler": "netz"})
    assert tot is False


def test_rumpf_ohne_tote_meldet_das_ausdruecklich():
    rumpf = lp.issue_rumpf([], "12.08.2026")
    assert "Keine toten" in rumpf
    assert "12.08.2026" in rumpf


def test_rumpf_listet_jeden_toten_link_mit_herkunft():
    rumpf = lp.issue_rumpf(
        [
            {"stufe": "hoch", "kategorie": "Ablenkung", "titel": "Zauberwürfel",
             "url": "https://a.ch/x", "grund": "404, Link zeigt ins Leere"},
        ],
        "12.08.2026",
    )
    assert "Zauberwürfel" in rumpf
    assert "https://a.ch/x" in rumpf
    assert "404" in rumpf
    assert "| --- |" in rumpf


def test_senkrechter_strich_zerreisst_die_tabelle_nicht():
    assert lp.zelle("a|b") == "a\\|b"
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest python -m pytest tests/test_links_pruefen.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'links_pruefen'`

- [ ] **Step 3: `tools/links_pruefen.py` anlegen**

```python
# /// script
# requires-python = ">=3.11"
# ///
"""
Waechter gegen Linkfaeule
=========================

Prueft alle Bezugsquellen aus docs/skills-daten.json und traegt tote in ein
einziges Sammel-Issue ein. Laeuft woechentlich ueber
.github/workflows/links-pruefen.yml, laesst sich dort aber auch von Hand
ausloesen.

Aufruf:  uv run tools/links_pruefen.py

Bewusst ohne Fremdbibliotheken: so braucht der Workflow keinen
Installationsschritt.
"""

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATEN_JSON = ROOT / "docs" / "skills-daten.json"

REPO = "stayingclean/toolbox"
TITEL = "Tote Bezugsquellen"
LABEL = "tote-links"

USER_AGENT = (
    "toolbox-linkpruefung (+https://github.com/stayingclean/toolbox)"
)
ZEITLIMIT = 15
PAUSE = 1.0

# Nur diese beiden Antworten sind ein Todesurteil. Alles andere – 403, 429,
# jedes 5xx – wird schweigend uebergangen.
TOT = {
    404: "404, Link zeigt ins Leere",
    410: "410, dauerhaft entfernt",
}


def alle_links(daten: dict) -> list:
    """Alle Bezugsquellen samt Herkunft, in stabiler Reihenfolge."""
    raus = []
    for stufe, inhalt in daten.items():
        for kat in inhalt.get("kategorien", []):
            for skill in kat.get("skills", []):
                for url in skill.get("links", []) or []:
                    raus.append(
                        {
                            "stufe": stufe,
                            "kategorie": kat.get("label", ""),
                            "titel": skill.get("t", ""),
                            "url": url,
                        }
                    )
    return raus


def urteil(ergebnis: dict):
    """Liefert (tot, grund).

    Nur harte Todesurteile zaehlen. Shops sind genau die Seiten, die
    automatische Abrufe aussperren; ein Waechter, der auf 403 anspringt, meldet
    dauernd Falschalarm fuer Links, die im Browser einwandfrei funktionieren –
    und wird nach drei Wochen ignoriert. Ein Waechter, den niemand mehr liest,
    ist schlechter als keiner, weil er Sicherheit vortaeuscht.
    """
    if ergebnis["fehler"] == "dns":
        return True, "Domain gibt es nicht mehr"
    if ergebnis["fehler"]:
        return False, "nicht erreichbar"
    if ergebnis["status"] in TOT:
        return True, TOT[ergebnis["status"]]
    return False, str(ergebnis["status"])


def zelle(wert) -> str:
    """Maskiert einen Wert fuer eine Markdown-Tabellenzelle."""
    return str(wert).replace("|", "\\|").replace("\n", " ")


def issue_rumpf(tote: list, stand: str) -> str:
    if not tote:
        return (
            f"Keine toten Bezugsquellen. Stand {stand}.\n\n"
            f"Dieses Issue wird vom Waechter geschlossen."
        )
    zeilen = [
        f"Stand {stand} — {len(tote)} tote Bezugsquelle(n).",
        "",
        "| Skill | Stufe / Kategorie | Adresse | Befund |",
        "| --- | --- | --- | --- |",
    ]
    for eintrag in tote:
        zeilen.append(
            f"| {zelle(eintrag['titel'])} "
            f"| {zelle(eintrag['stufe'])} / {zelle(eintrag['kategorie'])} "
            f"| {zelle(eintrag['url'])} "
            f"| {zelle(eintrag['grund'])} |"
        )
    zeilen += [
        "",
        "Korrigiert wird in `skills_daten.xlsx` (Spalten `Link1`–`Link3`);",
        "danach `build.bat` ausfuehren, committen und pushen.",
        "",
        "Nur 404, 410 und verschwundene Domains stehen hier. Ein Shop, der",
        "automatische Abrufe aussperrt (403), wird bewusst nicht gemeldet.",
    ]
    return "\n".join(zeilen)
```

- [ ] **Step 4: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest python -m pytest tests/test_links_pruefen.py -q`
Expected: PASS, alle Tests

- [ ] **Step 5: Committen**

```bash
git add tools/links_pruefen.py tests/test_links_pruefen.py
git commit -m "Waechter: Urteil und Aufbereitung als reine Funktionen"
```

---

### Task 2: Abruf und Sammel-Issue

**Files:**
- Modify: `tools/links_pruefen.py`
- Test: `tests/test_links_pruefen.py`

**Interfaces:**
- Consumes: `alle_links`, `urteil`, `issue_rumpf` aus Task 1.
- Produces: `abrufen(url: str) -> dict`, `offenes_issue() -> int|None`, `issue_anlegen(rumpf: str) -> None`, `issue_ersetzen(nummer: int, rumpf: str) -> None`, `issue_schliessen(nummer: int) -> None`, `main() -> None`.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_links_pruefen.py` anhängen:

```python
class Lauf:
    """Ersetzt subprocess.run und merkt sich die Aufrufe."""

    def __init__(self, ausgabe=""):
        self.aufrufe = []
        self.ausgabe = ausgabe

    def __call__(self, befehl, **kwargs):
        self.aufrufe.append(befehl)
        return type("Ergebnis", (), {"stdout": self.ausgabe, "returncode": 0})()


def test_offenes_issue_liest_die_nummer(monkeypatch):
    lauf = Lauf('[{"number": 42}]')
    monkeypatch.setattr(lp.subprocess, "run", lauf)
    assert lp.offenes_issue() == 42


def test_ohne_offenes_issue_kommt_none(monkeypatch):
    monkeypatch.setattr(lp.subprocess, "run", Lauf("[]"))
    assert lp.offenes_issue() is None


def unterbefehle(aufrufe):
    """Die gh-Unterbefehle als Paare, z. B. ('issue', 'create').

    Bewusst als Paar: 'gh label create' enthaelt ebenfalls das Wort 'create',
    eine Suche nach dem blossen Wort wuerde also auch dann zuschlagen, wenn gar
    kein Issue angelegt wurde.
    """
    return {(b[1], b[2]) for b in aufrufe if len(b) > 2}


def waechter_lauf(monkeypatch, tmp_path, lauf, status):
    monkeypatch.setattr(lp.subprocess, "run", lauf)
    monkeypatch.setattr(lp, "abrufen", lambda url: {"status": status, "fehler": None})
    monkeypatch.setattr(lp, "PAUSE", 0)
    pfad = tmp_path / "skills-daten.json"
    pfad.write_text(json.dumps(DATEN), encoding="utf-8")
    monkeypatch.setattr(lp, "DATEN_JSON", pfad)
    lp.main()


def test_kein_totes_und_kein_issue_tut_nichts(monkeypatch, tmp_path):
    """Der haeufigste Fall darf keine Spur hinterlassen – sonst entstuende
    ueber die Jahre eine Issue-Halde."""
    lauf = Lauf("[]")
    waechter_lauf(monkeypatch, tmp_path, lauf, 200)
    befehle = unterbefehle(lauf.aufrufe)
    assert ("issue", "create") not in befehle
    assert ("issue", "close") not in befehle
    assert ("issue", "edit") not in befehle


def test_totes_ohne_issue_legt_eines_an(monkeypatch, tmp_path):
    lauf = Lauf("[]")
    waechter_lauf(monkeypatch, tmp_path, lauf, 404)
    assert ("issue", "create") in unterbefehle(lauf.aufrufe)


def test_totes_mit_offenem_issue_ersetzt_den_rumpf(monkeypatch, tmp_path):
    """Kein zweites Issue: es bleibt bei einem einzigen Sammel-Eintrag."""
    lauf = Lauf('[{"number": 7}]')
    waechter_lauf(monkeypatch, tmp_path, lauf, 404)
    befehle = unterbefehle(lauf.aufrufe)
    assert ("issue", "edit") in befehle
    assert ("issue", "create") not in befehle


def test_nichts_mehr_tot_schliesst_das_offene_issue(monkeypatch, tmp_path):
    lauf = Lauf('[{"number": 7}]')
    waechter_lauf(monkeypatch, tmp_path, lauf, 200)
    assert ("issue", "close") in unterbefehle(lauf.aufrufe)
```

`import json` oben in der Testdatei ergänzen.

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest python -m pytest tests/test_links_pruefen.py -q`
Expected: FAIL — `AttributeError: module 'links_pruefen' has no attribute 'offenes_issue'`

- [ ] **Step 3: Abruf und gh-Aufrufe einbauen**

An `tools/links_pruefen.py` anhängen:

```python
def abrufen(url: str) -> dict:
    """Ruft eine Adresse einmal ab. Wirft nie – das Urteil faellt urteil()."""
    anfrage = urllib.request.Request(
        url, method="GET", headers={"user-agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=ZEITLIMIT) as antwort:
            return {"status": antwort.status, "fehler": None}
    except urllib.error.HTTPError as fehler:
        return {"status": fehler.code, "fehler": None}
    except urllib.error.URLError as fehler:
        # Ein Namensfehler heisst: die Domain gibt es nicht mehr. Das ist der
        # einzige Netzwerkfehler, der als Todesurteil zaehlt.
        if isinstance(fehler.reason, socket.gaierror):
            return {"status": None, "fehler": "dns"}
        return {"status": None, "fehler": "netz"}
    except (OSError, ValueError):
        return {"status": None, "fehler": "netz"}


def gh(*args, **kwargs):
    return subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        **kwargs,
    )


def label_sichern():
    """Legt das Label an, falls es fehlt. --force macht den Aufruf wiederholbar."""
    gh(
        "label", "create", LABEL,
        "--repo", REPO,
        "--description", "Vom Waechter gemeldete tote Bezugsquellen",
        "--color", "d73a4a",
        "--force",
    )


def offenes_issue():
    ergebnis = gh(
        "issue", "list",
        "--repo", REPO,
        "--label", LABEL,
        "--state", "open",
        "--json", "number",
        "--limit", "1",
    )
    liste = json.loads(ergebnis.stdout or "[]")
    return liste[0]["number"] if liste else None


def issue_anlegen(rumpf: str):
    label_sichern()
    gh("issue", "create", "--repo", REPO, "--label", LABEL,
       "--title", TITEL, "--body", rumpf)


def issue_ersetzen(nummer: int, rumpf: str):
    gh("issue", "edit", str(nummer), "--repo", REPO, "--body", rumpf)


def issue_schliessen(nummer: int, rumpf: str):
    gh("issue", "comment", str(nummer), "--repo", REPO, "--body", rumpf)
    gh("issue", "close", str(nummer), "--repo", REPO)


def main():
    daten = json.loads(DATEN_JSON.read_text(encoding="utf-8"))
    links = alle_links(daten)
    print(f"{len(links)} Bezugsquelle(n) zu pruefen.")

    tote = []
    for i, eintrag in enumerate(links):
        if i and PAUSE:
            time.sleep(PAUSE)   # hoeflich bleiben
        tot, grund = urteil(abrufen(eintrag["url"]))
        zeichen = "⚠" if tot else "·"
        print(f"  {zeichen} {eintrag['url']} — {grund}")
        if tot:
            tote.append({**eintrag, "grund": grund})

    stand = date.today().strftime("%d.%m.%Y")
    rumpf = issue_rumpf(tote, stand)
    nummer = offenes_issue()

    if tote and nummer is None:
        issue_anlegen(rumpf)
        print(f"Sammel-Issue angelegt ({len(tote)} tote).")
    elif tote:
        issue_ersetzen(nummer, rumpf)
        print(f"Sammel-Issue #{nummer} aktualisiert ({len(tote)} tote).")
    elif nummer is not None:
        issue_schliessen(nummer, rumpf)
        print(f"Sammel-Issue #{nummer} geschlossen – nichts mehr tot.")
    else:
        print("Nichts tot, kein offenes Issue – nichts zu tun.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest python -m pytest tests/test_links_pruefen.py -q`
Expected: PASS

- [ ] **Step 5: Einen echten Lauf gegen die eigene Seite machen**

Run: `uv run tools/links_pruefen.py`
Expected: Eine Zeile je Bezugsquelle. Solange in `skills_daten.xlsx` noch keine Links stehen, meldet es `0 Bezugsquelle(n) zu pruefen.` und `nichts zu tun`.

> Zum Prüfen des ganzen Wegs vorübergehend eine echte und eine tote Adresse in `skills_daten.xlsx` eintragen, `build.bat` laufen lassen, das Skript starten, das entstandene Issue anschauen — und beides danach wieder zurücknehmen.

- [ ] **Step 6: Committen**

```bash
git add tools/links_pruefen.py tests/test_links_pruefen.py
git commit -m "Waechter: Abruf und Sammel-Issue"
```

---

### Task 3: Workflow und Dokumentation

**Files:**
- Create: `.github/workflows/links-pruefen.yml`
- Modify: `CLAUDE.md`, `ANLEITUNG.md`

**Interfaces:**
- Consumes: `tools/links_pruefen.py` aus Task 2.
- Produces: nichts.

- [ ] **Step 1: Den Workflow anlegen**

`.github/workflows/links-pruefen.yml`:

```yaml
name: Bezugsquellen prüfen

# Montags früh, und jederzeit von Hand über den Knopf "Run workflow".
on:
  schedule:
    - cron: "0 6 * * 1"
  workflow_dispatch:

permissions:
  contents: read
  issues: write

jobs:
  pruefen:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      # Ohne Fremdbibliotheken: das Skript kommt mit der Standardbibliothek
      # aus, darum gibt es hier keinen Installationsschritt.
      - name: Links prüfen
        run: python tools/links_pruefen.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 2: Den Workflow syntaktisch prüfen**

Run: `uv run --with pyyaml python -c "import yaml,pathlib; yaml.safe_load(pathlib.Path('.github/workflows/links-pruefen.yml').read_text(encoding='utf-8')); print('ok')"`
Expected: `ok`

- [ ] **Step 3: `CLAUDE.md` ergänzen**

Nach dem Abschnitt zu den Bezugsquellen einfügen:

```markdown
### Wächter gegen tote Links

`.github/workflows/links-pruefen.yml` prüft montags alle Bezugsquellen aus
`docs/skills-daten.json` (`tools/links_pruefen.py`) und schreibt tote in **ein**
Sammel-Issue in diesem Repo (Titel „Tote Bezugsquellen", Label `tote-links`).
Ist nichts mehr tot, schliesst sich das Issue selbst.

**Gemeldet werden nur `404`, `410` und verschwundene Domains.** `403`, `429` und
alle `5xx` werden schweigend übergangen — Shops sperren automatische Abrufe aus,
und ein Wächter mit Falschalarm wird nach drei Wochen ignoriert. Wer diese
Schwelle senkt, macht den Wächter unbrauchbar, ohne dass etwas fehlschlägt.

Das Skript kommt **ohne Fremdbibliotheken** aus, damit der Workflow keinen
Installationsschritt braucht. Wer eine Abhängigkeit einführt, muss den Workflow
mit ändern.
```

- [ ] **Step 4: `ANLEITUNG.md` ergänzen**

Nach dem Abschnitt „Bezugsquellen" aus Stufe 1 einfügen:

```markdown
### Tote Links werden von selbst gemeldet

Einmal pro Woche prüft der Computer selbständig nach, ob die Bezugsquellen noch
funktionieren. Du musst dafür nichts tun.

Findet er eine tote Adresse, erscheint im Repo unter **Issues** ein Eintrag mit
dem Titel **„Tote Bezugsquellen"** und einer Liste: welcher Skill, welche
Adresse, was daran nicht stimmt. Es bleibt immer bei **einem** solchen Eintrag —
er wird jede Woche neu geschrieben.

So korrigierst du:

1. In `skills_daten.xlsx` die genannte Zeile suchen und in `Link1`–`Link3` die
   Adresse ersetzen oder löschen.
2. `build.bat` doppelklicken.
3. Committen und pushen.

Beim nächsten Lauf verschwindet der Eintrag von selbst. Ist gar nichts mehr
tot, schliesst sich das Issue automatisch.

**Nicht jeder Shop lässt sich prüfen.** Manche Verkaufsseiten blockieren
automatische Zugriffe. Solche Adressen werden bewusst **nicht** gemeldet —
lieber gar keine Meldung als jede Woche ein falscher Alarm.
```

- [ ] **Step 5: Alles laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Expected: PASS

Run: `cd worker && node --test`
Expected: PASS

- [ ] **Step 6: Committen**

```bash
git add .github/workflows/links-pruefen.yml CLAUDE.md ANLEITUNG.md
git commit -m "Waechter: woechentlicher Workflow und Dokumentation"
```

- [ ] **Step 7: Nach dem Push von Hand auslösen**

Auf GitHub unter **Actions → Bezugsquellen prüfen → Run workflow** einmal
starten und das Ergebnis anschauen. Erst dann ist bewiesen, dass Berechtigungen
und `gh`-Zugriff im Workflow stimmen — lokal lief es unter deinem eigenen Konto.
