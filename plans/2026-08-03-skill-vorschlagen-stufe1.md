# Skill vorschlagen — Ausbaustufe 1 (Einreichen)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eine Person kann auf `stayingclean.github.io/toolbox/skill-vorschlagen.html` anonym einen neuen Skill einreichen; der Vorschlag landet als Issue im öffentlichen Repo `stayingclean/toolbox-vorschlaege`, und ein lokales Skript übernimmt freigegebene Vorschläge in die Excel und baut die Skillsliste neu.

**Architecture:** Statische Formularseite auf GitHub Pages → Cloudflare Worker als Relais (prüft und legt das Issue an) → Issues als Posteingang → lokales Python-Skript `vorschlaege_holen.py` schreibt in `skills_daten.xlsx` und ruft `build.py`. Der Push bleibt manuell. `build.py` erzeugt neu zusätzlich `docs/skill-vorschlagen.html` und `docs/skills-daten.json`; letztere versorgt sowohl das Formular als auch die Prüfung im Worker mit dem aktuellen Bestand.

**Tech Stack:** Python 3.11 + openpyxl (PEP-723-Inline-Metadaten, Aufruf über `uv`), pytest für die Tests, JavaScript (Cloudflare Worker, ESM) mit `node --test`, `gh` CLI, `wrangler` CLI, statisches HTML/CSS/JS ohne Framework.

## Global Constraints

- **Sprache:** Alle sichtbaren Texte, Kommentare und Commit-Meldungen auf Deutsch, Schweizer Schreibweise (`ss` statt `ß`).
- **CSS eingebettet:** Jede Seite in `docs/` trägt ihr CSS im `<style>`-Block, kein externes Stylesheet. Einzige erlaubte Fremdressourcen auf `skill-vorschlagen.html`: die Google-Fonts-Links (wie in `docs/index.html`) und das Turnstile-Skript.
- **Fusszeile:** Jede Seite in `docs/` enthält den Urheber-Credit exakt nach der Vorlage in `CLAUDE.md` (`.footer-credit` + `.footer-avatar`).
- **Generierte Dateien nie von Hand bearbeiten:** `docs/skillsliste.html`, `docs/skill-vorschlagen.html`, `docs/skills-daten.json`. Änderungen gehen in `template.html` bzw. `template-vorschlag.html`.
- **Dateikonvention der Ausgabe:** UTF-8 **mit** BOM, so wie `build.py` es heute schreibt (`b"\xef\xbb\xbf" + html.encode("utf-8")`). Ausnahme: `skills-daten.json` wird als UTF-8 **ohne** BOM geschrieben, sonst scheitert `JSON.parse` im Worker.
- **Anonymität:** Weder IP-Adresse noch Browserkennung dürfen ins Issue, in eine Antwort oder in ein Log gelangen. Für die Ratenbegrenzung nur ein SHA-256-Hashwert mit einer Stunde Gültigkeit.
- **Feldgrenzen (Zeichen, gezählt mit `Array.from(s).length` bzw. `len(s)`):** Emoji 2, Titel 60, Beschreibung 300, Tipp 200, Name 30.
- **Link-Sperre:** Jede Einreichung, die in einem Textfeld `http` enthält (Gross-/Kleinschreibung egal), wird abgelehnt.
- **Ratenbegrenzung:** höchstens 5 Einreichungen pro Stunde und Absender.
- **Repo des Posteingangs:** `stayingclean/toolbox-vorschlaege`, öffentlich, Labels `in Prüfung`, `freigegeben`, `abgelehnt`.
- **Push bleibt manuell.** Kein Schritt in diesem Plan pusht nach `master`.
- **Nicht in dieser Stufe:** Reiter „Bestehenden ergänzen" (Stufe 2), KI-Duplikatprüfung und Kaffeekasse (Stufe 3).

**Testbefehle:**

```bash
uv run --with pytest --with openpyxl pytest tests -v     # Python
node --test worker/                                       # Worker
```

---

### Task 1: Testgerüst und Spalte `Von` in `build.py`

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_build.py`
- Create: `test.bat`
- Modify: `build.py:95-118` (`read_rows`), `build.py:122-235` (`load_data`)

**Interfaces:**
- Consumes: nichts (erste Aufgabe)
- Produces:
  - `build.read_rows(ws, expected_header, optional_header=()) -> list[dict]` — Spalten aus `optional_header` werden gelesen, wenn vorhanden, sonst als `""` geliefert
  - Jeder Skill in `build.load_data()` hat neu den Schlüssel `"von"` (String, leer wenn kein Name)
  - Fixture `mappe` aus `tests/conftest.py`: `mappe(tmp_path, skills_header, skills_rows) -> Path` erzeugt eine gültige Minimal-Excel

- [ ] **Step 1: Testhilfen anlegen**

Datei `tests/conftest.py`:

```python
"""Gemeinsame Testhilfen: Repo-Wurzel importierbar machen + Minimal-Excel bauen."""

import sys
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STUFEN_HEADER = ["Stufe", "Bezeichnung", "Bereich", "Icon", "Intro",
                 "Farbe", "Farbe2", "Hell"]
STUFEN_ROWS = [
    ["Hoch", "Hohe Anspannung", "80-100", "🌶️", "Intro hoch", "#a00", "#c00", "#fee"],
    ["Mittel", "Mittlere Anspannung", "40-79", "🌤️", "Intro mittel", "#0a0", "#0c0", "#efe"],
    ["Tief", "Tiefe Anspannung", "0-39", "🌊", "Intro tief", "#00a", "#00c", "#eef"],
]
KATEGORIEN_HEADER = ["Stufe", "Kategorie", "Icon"]
KATEGORIEN_ROWS = [["Hoch", "Ablenkung", "🎧"]]


@pytest.fixture
def mappe(tmp_path):
    """Erzeugt eine gültige skills_daten.xlsx mit frei wählbarem Skills-Blatt."""

    def bauen(skills_header, skills_rows):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Skills"
        ws.append(skills_header)
        for zeile in skills_rows:
            ws.append(zeile)
        ws2 = wb.create_sheet("Stufen")
        ws2.append(STUFEN_HEADER)
        for zeile in STUFEN_ROWS:
            ws2.append(zeile)
        ws3 = wb.create_sheet("Kategorien")
        ws3.append(KATEGORIEN_HEADER)
        for zeile in KATEGORIEN_ROWS:
            ws3.append(zeile)
        pfad = tmp_path / "skills_daten.xlsx"
        wb.save(pfad)
        return pfad

    return bauen
```

- [ ] **Step 2: Fehlschlagende Tests schreiben**

Datei `tests/test_build.py`:

```python
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
```

- [ ] **Step 3: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: FAIL — `KeyError: 'von'` in den ersten beiden Tests (der dritte ist bereits grün).

- [ ] **Step 4: `read_rows` um optionale Spalten erweitern**

In `build.py` die Funktion `read_rows` ersetzen:

```python
def read_rows(ws, expected_header, optional_header=()):
    """Liest ein Blatt als Liste von dicts {Spaltenname: Wert}.

    Spalten aus `optional_header` werden gelesen, wenn sie vorhanden sind, und
    sonst als leerer String geliefert – so bricht eine ältere Excel nicht.
    Liefert zusätzlich die echte Excel-Zeilennummer für Fehlermeldungen.
    """
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise BuildError(f"Das Blatt '{ws.title}' ist leer.")
    header = [clean(h) for h in rows[0]]
    missing = [h for h in expected_header if h not in header]
    if missing:
        raise BuildError(
            f"Im Blatt '{ws.title}' fehlen die Spalten: {', '.join(missing)}. "
            f"Bitte die Kopfzeile nicht umbenennen."
        )
    alle = list(expected_header) + list(optional_header)
    idx = {name: header.index(name) for name in alle if name in header}
    out = []
    for excel_row, raw in enumerate(rows[1:], start=2):
        record = {name: "" for name in alle}
        record.update(
            {name: clean(raw[i]) if i < len(raw) else "" for name, i in idx.items()}
        )
        if not any(record.values()):
            continue  # komplett leere Zeile überspringen
        record["_row"] = excel_row
        out.append(record)
    return out
```

- [ ] **Step 5: `load_data` liest und liefert `Von`**

In `build.py` in `load_data()` den Aufruf für das Skills-Blatt ändern:

```python
    skill_rows = read_rows(
        get_sheet(wb, "Skills"),
        ["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp"],
        optional_header=["Von"],
    )
```

und im selben Modul beim Aufbau von `skills_by` das neue Feld ergänzen:

```python
        skills_by.setdefault((key, label), []).append(
            {
                "e": rec["Emoji"],
                "t": rec["Titel"],
                "b": rec["Beschreibung"],
                "tip": format_tip(rec["Tipp"]),
                "von": rec["Von"],
            }
        )
```

- [ ] **Step 6: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: PASS, 3 Tests.

- [ ] **Step 7: Startdatei für Nicht-Techniker anlegen**

Datei `test.bat`:

```bat
@echo off
cd /d "%~dp0"
uv run --with pytest --with openpyxl pytest tests -v
pause
```

- [ ] **Step 8: Commit**

```bash
git add tests/conftest.py tests/test_build.py test.bat build.py
git commit -m "Spalte Von tolerant einlesen, Testgeruest mit pytest"
```

---

### Task 2: Name im Detail-Dialog anzeigen

**Files:**
- Modify: `template.html:140` (CSS neben `.modal-tip`), `template.html:289-292` (Modal-Rumpf), `template.html:378` (`sObj`), `template.html:405-415` (`openModal`)
- Modify: `tests/test_build.py`

**Interfaces:**
- Consumes: Schlüssel `"von"` je Skill aus Task 1
- Produces: Element `id="m-von"` im Detail-Dialog; `docs/skillsliste.html` enthält es nach dem Build

- [ ] **Step 1: Fehlschlagenden Test schreiben**

An `tests/test_build.py` anhängen:

```python
def test_vorlage_enthaelt_namenszeile():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    assert 'id="m-von"' in vorlage
    assert "modal-von" in vorlage
    assert "s.von" in vorlage
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl pytest tests/test_build.py::test_vorlage_enthaelt_namenszeile -v`
Expected: FAIL — `assert 'id="m-von"' in vorlage`

- [ ] **Step 3: CSS ergänzen**

In `template.html` direkt nach der Zeile mit `.modal-tip{...}` (Zeile 140) einfügen:

```css
.modal-von{margin-top:.9rem;font-size:.78rem;color:var(--muted);font-style:italic}
```

- [ ] **Step 4: Markup ergänzen**

In `template.html` den Modal-Rumpf erweitern:

```html
    <div class="modal-body">
      <p class="modal-desc" id="m-desc"></p>
      <div class="modal-tip" id="m-tip"></div>
      <div class="modal-von" id="m-von" hidden></div>
    </div>
```

- [ ] **Step 5: Wert durchreichen**

In `template.html` in der Kartenschleife das Objekt erweitern:

```javascript
      var sObj={lv:S.level,kid:k.id,klbl:k.label,idx:cardIdx,e:s.e,t:s.t,b:s.b,tip:s.tip,von:s.von};
```

Bei den Modal-Elementen `mVon` ergänzen:

```javascript
var mEmoji=el('m-emoji'), mCat=el('m-cat'), mTitle=el('m-title'), mDesc=el('m-desc'), mTip=el('m-tip'), mVon=el('m-von');
```

und in `openModal(s)` nach der Tipp-Zeile:

```javascript
  if(s.von){ mVon.textContent='Vorgeschlagen von '+s.von; mVon.hidden=false; }
  else { mVon.textContent=''; mVon.hidden=true; }
```

- [ ] **Step 6: Test laufen lassen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: PASS, 4 Tests.

- [ ] **Step 7: Sichtprüfung im Browser**

Run: `build.bat` (Doppelklick oder `uv run build.py`)
Dann `docs/skillsliste.html` im Browser öffnen, einen Skill antippen.
Expected: Dialog sieht aus wie bisher, **keine** Namenszeile (in der Excel steht noch kein Name). Kein Fehler in der Browser-Konsole.

- [ ] **Step 8: Commit**

```bash
git add template.html tests/test_build.py docs/skillsliste.html
git commit -m "Detail-Dialog zeigt Vorgeschlagen von, wenn ein Name hinterlegt ist"
```

---

### Task 3: Spalte `Von` in der Excel und in `seed_excel.py`

**Files:**
- Modify: `tools/seed_excel.py:93` (Kopfzeile), `tools/seed_excel.py:97-107` (Zeilen + Breiten)
- Modify: `skills_daten.xlsx` (einmalig, per Skript)

**Interfaces:**
- Consumes: Schlüssel `"von"` je Skill aus Task 1
- Produces: `skills_daten.xlsx`, Blatt `Skills`, siebte Spalte `Von`

- [ ] **Step 1: `seed_excel.py` um die Spalte erweitern**

In `tools/seed_excel.py` die Kopfzeile ändern:

```python
    ws.append(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp", "Von"])
```

Im Anhänge-Block den Wert ergänzen:

```python
                ws.append(
                    [
                        STUFE_DISPLAY[key],
                        kat["label"],
                        s.get("e", ""),
                        s.get("t", ""),
                        s.get("b", ""),
                        strip_birne(s.get("tip", "")),
                        s.get("von", ""),
                    ]
                )
```

Und die Formatierung auf sieben Spalten setzen:

```python
    style_sheet(ws, 7, [9, 18, 8, 26, 60, 55, 16], emoji_col=3)
```

- [ ] **Step 2: Sicherungskopie der Excel anlegen**

```bash
cp skills_daten.xlsx skills_daten.xlsx.bak
```

Die `.bak`-Datei nicht committen — sie ist die Rückfalloption, falls Schritt 3 die Formatierung beschädigt.

- [ ] **Step 3: Spalte einmalig in die bestehende Excel einfügen**

```bash
uv run --with openpyxl python - <<'PY'
import openpyxl
wb = openpyxl.load_workbook("skills_daten.xlsx")
ws = wb["Skills"]
kopf = [(c.value or "").strip() for c in ws[1]]
if "Von" in kopf:
    print("Spalte 'Von' ist bereits vorhanden – nichts zu tun.")
else:
    spalte = len(kopf) + 1
    ws.cell(row=1, column=spalte, value="Von")
    ws.column_dimensions[openpyxl.utils.get_column_letter(spalte)].width = 16
    wb.save("skills_daten.xlsx")
    print(f"Spalte 'Von' als Spalte {spalte} ergaenzt.")
PY
```

Expected: `Spalte 'Von' als Spalte 7 ergaenzt.`

- [ ] **Step 4: Excel prüfen**

`skills_daten.xlsx` öffnen, Blatt `Skills`.
Expected: Spalte G heisst `Von` und ist leer; alle bisherigen Spalten unverändert, Kopfzeile weiterhin eingefärbt, Filter-Pfeile vorhanden, Dropdown in Spalte A funktioniert.

Falls etwas beschädigt ist: `cp skills_daten.xlsx.bak skills_daten.xlsx` und die Spalte von Hand in Excel ergänzen.

- [ ] **Step 5: Build prüfen**

Run: `uv run build.py`
Expected: `✅ docs/skillsliste.html wurde neu erstellt.` mit unveränderten Zahlen.

Run: `git diff --stat docs/skillsliste.html`
Expected: keine Änderung (alle `von`-Werte sind leer und waren es schon nach Task 2).

- [ ] **Step 6: Probename eintragen und wieder entfernen**

In `skills_daten.xlsx` beim ersten Skill in Spalte `Von` `Testname` eintragen, speichern, `uv run build.py` ausführen, `docs/skillsliste.html` öffnen und den Skill antippen.
Expected: Zeile „Vorgeschlagen von Testname" erscheint unter dem Tipp.

Danach den Eintrag wieder löschen, speichern und `uv run build.py` erneut ausführen.
Expected: `git diff --stat docs/skillsliste.html` meldet keine Änderung.

- [ ] **Step 7: Sicherungskopie löschen und committen**

```bash
rm skills_daten.xlsx.bak
git add tools/seed_excel.py skills_daten.xlsx
git commit -m "Spalte Von in der Excel und im Reset-Skript"
```

---

### Task 4: `docs/skills-daten.json` erzeugen

**Files:**
- Modify: `build.py:31-35` (Konstanten), `build.py:239-251` (`render`), `build.py:254-268` (`main`)
- Modify: `tests/test_build.py`

**Interfaces:**
- Consumes: `build.load_data()` aus Task 1
- Produces:
  - `build.write_daten_json(data) -> None` schreibt `docs/skills-daten.json` (UTF-8 ohne BOM)
  - Die Datei enthält exakt die DATA-Struktur: `{"hoch": {"label", "bereich", "farbe", "farbe2", "hell", "icon", "intro", "kategorien": [{"id", "label", "icon", "skills": [{"e", "t", "b", "tip", "von"}]}]}, "mittel": {...}, "tief": {...}}`

- [ ] **Step 1: Fehlschlagenden Test schreiben**

An `tests/test_build.py` anhängen:

```python
import json


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
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl pytest tests/test_build.py::test_daten_json_wird_geschrieben -v`
Expected: FAIL — `AttributeError: module 'build' has no attribute 'DATEN_JSON'`

- [ ] **Step 3: Konstante und Funktion ergänzen**

In `build.py` bei den Konstanten ergänzen:

```python
DATEN_JSON = ROOT / "docs" / "skills-daten.json"   # Datenstand für Formular + Worker
```

Und nach der Funktion `render` einfügen:

```python
def write_daten_json(data: dict):
    """Schreibt den Datenstand für die Vorschlagsseite und den Worker.

    Bewusst OHNE BOM: JSON.parse im Worker stolpert sonst über das erste Zeichen.
    """
    DATEN_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
    )
```

- [ ] **Step 4: In `main` aufrufen**

In `build.py` in `main()` den `try`-Block erweitern:

```python
    try:
        data = load_data()
        render(data)
        write_daten_json(data)
    except BuildError as exc:
```

und die Erfolgsmeldung ergänzen:

```python
    print(f"✅ {OUTPUT.relative_to(ROOT).as_posix()} wurde neu erstellt.")
    print(f"✅ {DATEN_JSON.relative_to(ROOT).as_posix()} wurde neu erstellt.")
```

- [ ] **Step 5: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: PASS, 5 Tests.

- [ ] **Step 6: Echten Build ausführen**

Run: `uv run build.py`
Expected: beide ✅-Zeilen; `docs/skills-daten.json` existiert und lässt sich im Browser öffnen.

- [ ] **Step 7: Commit**

```bash
git add build.py tests/test_build.py docs/skills-daten.json
git commit -m "build.py erzeugt docs/skills-daten.json für Formular und Worker"
```

---

### Task 5: Prüflogik des Workers (`worker/validate.js`)

**Files:**
- Create: `worker/package.json`
- Create: `worker/validate.js`
- Create: `worker/validate.test.js`

**Interfaces:**
- Consumes: Struktur von `docs/skills-daten.json` aus Task 4
- Produces:
  - `GRENZEN` — Objekt mit den Feldgrenzen
  - `pruefeVorschlag(eingabe, daten) -> {ok: true, wert: {...}} | {ok: false, fehler: "…"}`
    - `eingabe`: `{stufe, kategorie, emoji, titel, beschreibung, tipp, von, falle}` (alle Strings, dürfen fehlen)
    - `daten`: der geparste Inhalt von `skills-daten.json`
    - `wert` bei Erfolg: `{art: "neu", stufe, kategorie, emoji, titel, beschreibung, tipp, von}` — alle Werte getrimmt, `stufe` als Anzeigename (`Hoch`/`Mittel`/`Tief`)

- [ ] **Step 1: ESM-Kennzeichnung anlegen**

Datei `worker/package.json`:

```json
{
  "name": "skill-vorschlag-worker",
  "private": true,
  "type": "module"
}
```

- [ ] **Step 2: Fehlschlagende Tests schreiben**

Datei `worker/validate.test.js`:

```javascript
import test from "node:test";
import assert from "node:assert/strict";
import { pruefeVorschlag } from "./validate.js";

const DATEN = {
  hoch: { kategorien: [{ id: "ablenkung", label: "Ablenkung", skills: [] }] },
  mittel: { kategorien: [] },
  tief: { kategorien: [] },
};

const GUELTIG = {
  stufe: "Hoch",
  kategorie: "Ablenkung",
  emoji: "🎧",
  titel: "Musik hören",
  beschreibung: "Ein Lied auflegen und nur darauf achten.",
  tipp: "Kopfhörer bereitlegen",
  von: "Max",
  falle: "",
};

test("nimmt einen gültigen Vorschlag an", () => {
  const r = pruefeVorschlag(GUELTIG, DATEN);
  assert.equal(r.ok, true);
  assert.equal(r.wert.art, "neu");
  assert.equal(r.wert.titel, "Musik hören");
  assert.equal(r.wert.von, "Max");
});

test("trimmt Leerzeichen", () => {
  const r = pruefeVorschlag({ ...GUELTIG, titel: "  Musik hören  " }, DATEN);
  assert.equal(r.wert.titel, "Musik hören");
});

test("Tipp und Name sind freiwillig", () => {
  const r = pruefeVorschlag({ ...GUELTIG, tipp: "", von: "" }, DATEN);
  assert.equal(r.ok, true);
  assert.equal(r.wert.tipp, "");
  assert.equal(r.wert.von, "");
});

test("lehnt ausgefüllte Falle ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, falle: "bot" }, DATEN);
  assert.equal(r.ok, false);
});

test("lehnt unbekannte Stufe ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, stufe: "Sehr hoch" }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Stufe/);
});

test("lehnt unbekannte Kategorie ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, kategorie: "Erfunden" }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Kategorie/);
});

test("lehnt leeren Titel ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, titel: "   " }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Titel/);
});

test("lehnt zu langen Titel ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, titel: "x".repeat(61) }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Titel/);
});

test("erlaubt genau 60 Zeichen im Titel", () => {
  const r = pruefeVorschlag({ ...GUELTIG, titel: "x".repeat(60) }, DATEN);
  assert.equal(r.ok, true);
});

test("zählt Emoji nach Zeichen, nicht nach Bytes", () => {
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "🎧" }, DATEN);
  assert.equal(r.ok, true);
});

test("lehnt drei Emoji ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "🎧🎧🎧" }, DATEN);
  assert.equal(r.ok, false);
});

test("lehnt Links ab", () => {
  for (const feld of ["titel", "beschreibung", "tipp", "von"]) {
    const r = pruefeVorschlag({ ...GUELTIG, [feld]: "siehe HTTP://spam.example" }, DATEN);
    assert.equal(r.ok, false, `${feld} muss Links ablehnen`);
    assert.match(r.fehler, /Link/);
  }
});

test("verträgt fehlende Felder ohne Absturz", () => {
  const r = pruefeVorschlag({}, DATEN);
  assert.equal(r.ok, false);
});
```

- [ ] **Step 3: Tests laufen lassen, Fehlschlag bestätigen**

Run: `node --test worker/`
Expected: FAIL — `Cannot find module .../worker/validate.js`

- [ ] **Step 4: Prüflogik schreiben**

Datei `worker/validate.js`:

```javascript
/**
 * Reine Prüffunktionen für eingereichte Skill-Vorschläge.
 * Keine Netzwerk- oder Umgebungszugriffe, damit sie mit `node --test` prüfbar sind.
 */

export const GRENZEN = {
  emoji: 2,
  titel: 60,
  beschreibung: 300,
  tipp: 200,
  von: 30,
};

// Anzeigename (Formular) -> Schlüssel in skills-daten.json
const STUFEN = { Hoch: "hoch", Mittel: "mittel", Tief: "tief" };

const TEXTFELDER = ["titel", "beschreibung", "tipp", "von"];

function text(wert) {
  return typeof wert === "string" ? wert.trim() : "";
}

function laenge(wert) {
  return Array.from(wert).length;
}

export function pruefeVorschlag(eingabe, daten) {
  const roh = eingabe && typeof eingabe === "object" ? eingabe : {};

  // Versteckte Falle: für Menschen unsichtbar, Bots füllen sie aus.
  if (text(roh.falle)) {
    return { ok: false, fehler: "Ungültige Einreichung." };
  }

  const stufe = text(roh.stufe);
  const schluessel = STUFEN[stufe];
  if (!schluessel || !daten[schluessel]) {
    return { ok: false, fehler: "Unbekannte Stufe." };
  }

  const kategorie = text(roh.kategorie);
  const bekannt = (daten[schluessel].kategorien || []).some(
    (k) => k.label === kategorie
  );
  if (!bekannt) {
    return { ok: false, fehler: "Unbekannte Kategorie." };
  }

  const wert = {
    art: "neu",
    stufe,
    kategorie,
    emoji: text(roh.emoji),
    titel: text(roh.titel),
    beschreibung: text(roh.beschreibung),
    tipp: text(roh.tipp),
    von: text(roh.von),
  };

  for (const feld of ["emoji", "titel", "beschreibung"]) {
    if (!wert[feld]) {
      return { ok: false, fehler: `Pflichtfeld fehlt: ${feld}.` };
    }
  }

  for (const [feld, grenze] of Object.entries(GRENZEN)) {
    if (laenge(wert[feld]) > grenze) {
      return { ok: false, fehler: `Zu lang: ${feld} (max. ${grenze} Zeichen).` };
    }
  }

  for (const feld of TEXTFELDER) {
    if (wert[feld].toLowerCase().includes("http")) {
      return { ok: false, fehler: "Links sind nicht erlaubt." };
    }
  }

  return { ok: true, wert };
}
```

- [ ] **Step 5: Tests laufen lassen**

Run: `node --test worker/`
Expected: PASS, 13 Tests.

- [ ] **Step 6: Commit**

```bash
git add worker/package.json worker/validate.js worker/validate.test.js
git commit -m "Prueflogik des Workers mit Tests"
```

---

### Task 6: Vorschlags-Repo, Turnstile und Worker in Betrieb nehmen

**Files:**
- Create: `worker/index.js`
- Create: `worker/wrangler.toml`
- Create: `worker/README.md`

**Interfaces:**
- Consumes: `pruefeVorschlag` aus Task 5, `docs/skills-daten.json` aus Task 4
- Produces:
  - Erreichbarer Endpunkt, im Folgenden `WORKER_URL` (Form: `https://skill-vorschlag.<konto>.workers.dev`)
  - Turnstile-Sitekey, im Folgenden `TURNSTILE_SITEKEY`
  - Antwort auf `POST` mit JSON-Rumpf: `200 {"url": "https://github.com/…/issues/1"}` oder `400 {"fehler": "…"}`
  - Issue-Format mit maschinenlesbarem Block:
    ```
    <!-- vorschlag
    {"art":"neu","stufe":"Hoch","kategorie":"Ablenkung","emoji":"🎧","titel":"…","beschreibung":"…","tipp":"…","von":"…"}
    -->
    ```

**Hinweis:** Dieser Task enthält Schritte, die nur die kontoführende Person ausführen kann (GitHub-Repo, Cloudflare-Konto, Secrets). Die Zugangsdaten dürfen **nicht** ins Repo.

- [ ] **Step 1: Vorschlags-Repo anlegen**

```bash
gh repo create stayingclean/toolbox-vorschlaege --public \
  --description "Posteingang für Skill-Vorschläge aus der Toolbox"
gh label create "in Prüfung" --repo stayingclean/toolbox-vorschlaege --color FBCA04 --description "Wird gerade angeschaut"
gh label create "freigegeben" --repo stayingclean/toolbox-vorschlaege --color 0E8A16 --description "Kommt in die Skillsliste"
gh label create "abgelehnt"   --repo stayingclean/toolbox-vorschlaege --color B60205 --description "Wird nicht übernommen"
```

Expected: Repo erreichbar unter `https://github.com/stayingclean/toolbox-vorschlaege`, drei Labels angelegt.

- [ ] **Step 2: GitHub-Token für den Worker erzeugen**

Im Browser: GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → *Generate new token*.

- Name: `toolbox-vorschlag-worker`
- Resource owner: `stayingclean`
- Repository access: *Only select repositories* → `toolbox-vorschlaege`
- Permissions → Repository permissions → **Issues: Read and write** (sonst nichts)
- Ablauf: 1 Jahr, Erinnerung notieren

Den Token einmalig kopieren. Er wird in Step 6 als Secret gesetzt und danach nirgends gespeichert.

- [ ] **Step 3: Turnstile-Schlüsselpaar erzeugen**

Im Browser: Cloudflare Dashboard → Turnstile → *Add widget*.

- Name: `toolbox-skill-vorschlag`
- Hostnames: `stayingclean.github.io`
- Widget Mode: *Managed*

Ergebnis: **Sitekey** (öffentlich, kommt in Task 7 in die Seite) und **Secret Key** (kommt in Step 6 in den Worker).

- [ ] **Step 4: Worker-Code schreiben**

Datei `worker/index.js`:

```javascript
/**
 * Nimmt Skill-Vorschläge vom Formular entgegen und legt daraus ein Issue an.
 *
 * Bewusst NICHT gespeichert oder protokolliert: IP-Adresse und Browserkennung.
 * Die IP wird ausschliesslich als Hashwert für die Ratenbegrenzung verwendet
 * und verfällt nach einer Stunde.
 */

import { pruefeVorschlag } from "./validate.js";

const HERKUNFT = "https://stayingclean.github.io";
const MAX_PRO_STUNDE = 5;

function antwort(rumpf, status = 200) {
  return new Response(JSON.stringify(rumpf), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": HERKUNFT,
      "access-control-allow-headers": "content-type",
      "access-control-allow-methods": "POST, OPTIONS",
    },
  });
}

async function hashe(text) {
  const roh = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text)
  );
  return [...new Uint8Array(roh)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function turnstileGeprueft(token, secret, ip) {
  if (!token) return false;
  const formular = new FormData();
  formular.append("secret", secret);
  formular.append("response", token);
  if (ip) formular.append("remoteip", ip);
  const res = await fetch(
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
    { method: "POST", body: formular }
  );
  const ergebnis = await res.json();
  return ergebnis.success === true;
}

function issueRumpf(w) {
  const zeilen = [
    "| Feld | Wert |",
    "| --- | --- |",
    `| Stufe | ${w.stufe} |`,
    `| Kategorie | ${w.kategorie} |`,
    `| Emoji | ${w.emoji} |`,
    `| Titel | ${w.titel} |`,
    `| Beschreibung | ${w.beschreibung} |`,
    `| Tipp | ${w.tipp || "—"} |`,
    `| Name | ${w.von || "— (anonym)"} |`,
  ];
  return (
    zeilen.join("\n") +
    "\n\n<!-- vorschlag\n" +
    JSON.stringify(w) +
    "\n-->\n"
  );
}

export default {
  async fetch(anfrage, umgebung) {
    if (anfrage.method === "OPTIONS") {
      // 204 darf keinen Rumpf haben – sonst wirft die Workers-Laufzeit.
      return new Response(null, {
        status: 204,
        headers: {
          "access-control-allow-origin": HERKUNFT,
          "access-control-allow-headers": "content-type",
          "access-control-allow-methods": "POST, OPTIONS",
          "access-control-max-age": "86400",
        },
      });
    }
    if (anfrage.method !== "POST") {
      return antwort({ fehler: "Nur POST." }, 405);
    }

    const ip = anfrage.headers.get("CF-Connecting-IP") || "";

    // Ratenbegrenzung: Hashwert der IP, Ablauf nach einer Stunde.
    const schluessel = "rate:" + (await hashe(ip + umgebung.RATE_SALT));
    const bisher = Number((await umgebung.RATE.get(schluessel)) || 0);
    if (bisher >= MAX_PRO_STUNDE) {
      return antwort(
        { fehler: "Zu viele Einreichungen. Bitte in einer Stunde erneut." },
        429
      );
    }

    let eingabe;
    try {
      eingabe = await anfrage.json();
    } catch {
      return antwort({ fehler: "Ungültige Anfrage." }, 400);
    }

    if (
      !(await turnstileGeprueft(eingabe.turnstile, umgebung.TURNSTILE_SECRET, ip))
    ) {
      return antwort({ fehler: "Sicherheitsprüfung fehlgeschlagen." }, 400);
    }

    const datenRes = await fetch(umgebung.DATEN_URL, {
      cf: { cacheTtl: 300, cacheEverything: true },
    });
    if (!datenRes.ok) {
      return antwort({ fehler: "Datenstand nicht erreichbar." }, 503);
    }
    const daten = await datenRes.json();

    const geprueft = pruefeVorschlag(eingabe, daten);
    if (!geprueft.ok) {
      return antwort({ fehler: geprueft.fehler }, 400);
    }

    const issueRes = await fetch(
      `https://api.github.com/repos/${umgebung.REPO}/issues`,
      {
        method: "POST",
        headers: {
          authorization: `Bearer ${umgebung.GITHUB_TOKEN}`,
          accept: "application/vnd.github+json",
          "content-type": "application/json",
          "user-agent": "toolbox-skill-vorschlag",
        },
        body: JSON.stringify({
          title: geprueft.wert.titel,
          body: issueRumpf(geprueft.wert),
        }),
      }
    );
    if (!issueRes.ok) {
      return antwort({ fehler: "Konnte den Vorschlag nicht ablegen." }, 502);
    }
    const issue = await issueRes.json();

    await umgebung.RATE.put(schluessel, String(bisher + 1), {
      expirationTtl: 3600,
    });

    return antwort({ url: issue.html_url });
  },
};
```

- [ ] **Step 5: Konfiguration anlegen**

Datei `worker/wrangler.toml` (die `id` wird in Step 6 eingesetzt):

```toml
name = "skill-vorschlag"
main = "index.js"
compatibility_date = "2026-01-01"

[vars]
REPO = "stayingclean/toolbox-vorschlaege"
DATEN_URL = "https://stayingclean.github.io/toolbox/skills-daten.json"

[[kv_namespaces]]
binding = "RATE"
id = "HIER_DIE_ID_AUS_SCHRITT_6"
```

- [ ] **Step 6: KV-Speicher und Secrets einrichten**

```bash
cd worker
npx wrangler login
npx wrangler kv namespace create RATE
```

Die ausgegebene `id` in `wrangler.toml` bei `[[kv_namespaces]]` eintragen.

```bash
npx wrangler secret put GITHUB_TOKEN       # Token aus Step 2 einfügen
npx wrangler secret put TURNSTILE_SECRET   # Secret Key aus Step 3 einfügen
npx wrangler secret put RATE_SALT          # eine beliebige lange Zufallszeichenfolge
```

Zufallszeichenfolge erzeugen, falls keine zur Hand:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

- [ ] **Step 7: Veröffentlichen**

```bash
npx wrangler deploy
```

Expected: Ausgabe endet mit der Adresse, z. B. `https://skill-vorschlag.erichraschle.workers.dev`. Diese Adresse notieren — sie ist `WORKER_URL` für Task 7.

- [ ] **Step 8: Endpunkt prüfen**

Ohne Turnstile-Token muss abgelehnt werden:

```bash
curl -s -X POST "<WORKER_URL>" \
  -H "content-type: application/json" \
  -d '{"stufe":"Hoch","kategorie":"Ablenkung","emoji":"🎧","titel":"Test","beschreibung":"Test"}'
```

Expected: `{"fehler":"Sicherheitsprüfung fehlgeschlagen."}`

Falsche Methode:

```bash
curl -s "<WORKER_URL>"
```

Expected: `{"fehler":"Nur POST."}`

Damit ist bestätigt, dass der Worker läuft und ohne gültige Sicherheitsprüfung nichts anlegt. Der vollständige Durchlauf mit echtem Token folgt in Task 10.

- [ ] **Step 9: Kurzanleitung für später schreiben**

Datei `worker/README.md`:

```markdown
# Worker: Skill-Vorschläge entgegennehmen

Nimmt das Formular `docs/skill-vorschlagen.html` entgegen, prüft die Eingaben
und legt daraus ein Issue in `stayingclean/toolbox-vorschlaege` an.

## Erneut veröffentlichen

    cd worker
    npx wrangler deploy

## Secrets (nur einmalig bzw. bei Ablauf)

| Secret | Woher |
| --- | --- |
| `GITHUB_TOKEN` | GitHub → Fine-grained token, nur `toolbox-vorschlaege`, Issues: Read and write |
| `TURNSTILE_SECRET` | Cloudflare → Turnstile → Widget `toolbox-skill-vorschlag` |
| `RATE_SALT` | beliebige Zufallszeichenfolge, `python -c "import secrets; print(secrets.token_hex(32))"` |

Setzen mit `npx wrangler secret put <NAME>`.

## Notbremse

Bei Missbrauch: im Repo `toolbox-vorschlaege` unter Settings die Issues
abschalten. Der Worker antwortet dann mit einem Fehler, die Formularseite
zeigt die Fehlermeldung an. Die Toolbox selbst ist nicht betroffen.

## Prüflogik

Die reinen Prüffunktionen stehen in `validate.js` und werden mit
`node --test worker/` geprüft. Sie kennen die gültigen Stufen und Kategorien
nicht selbst, sondern lesen sie aus `docs/skills-daten.json` — diese Datei
erzeugt `build.py` bei jedem Build mit.
```

- [ ] **Step 10: Commit**

```bash
git add worker/index.js worker/wrangler.toml worker/README.md
git commit -m "Cloudflare Worker nimmt Vorschlaege entgegen und legt Issues an"
```

---

### Task 7: Formularseite

**Files:**
- Create: `template-vorschlag.html`
- Modify: `build.py` (Konstanten, `render`, `main`)
- Modify: `tests/test_build.py`

**Interfaces:**
- Consumes: `WORKER_URL` und `TURNSTILE_SITEKEY` aus Task 6; `docs/skills-daten.json` aus Task 4
- Produces:
  - `build.render_vorschlag(data) -> None` erzeugt `docs/skill-vorschlagen.html`
  - Die Seite sendet an `WORKER_URL` ein JSON-Objekt mit den Feldern `stufe, kategorie, emoji, titel, beschreibung, tipp, von, falle, turnstile`

- [ ] **Step 1: Fehlschlagende Tests schreiben**

An `tests/test_build.py` anhängen:

```python
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
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: FAIL — `AttributeError: module 'build' has no attribute 'OUTPUT_VORSCHLAG'`

- [ ] **Step 3: Vorlage schreiben**

Datei `template-vorschlag.html` — vor dem Speichern die beiden Grossbuchstaben-Platzhalter durch die Werte aus Task 6 ersetzen: `WORKER_URL_HIER_EINSETZEN` und `TURNSTILE_SITEKEY_HIER_EINSETZEN`.

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Skill vorschlagen – Toolbox</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg:#FAF8F5; --card:#FFFFFF; --border:#E8E4DF; --text:#1C1C1C;
      --muted:#7A7268; --accent:#008080; --accent-dark:#006666; --accent-tint:#E6F2F2;
      --font-display:'Playfair Display',Georgia,serif;
      --font-body:'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    }
    *{box-sizing:border-box}
    body{margin:0;font-family:var(--font-body);background:var(--bg);color:var(--text);line-height:1.5;-webkit-font-smoothing:antialiased}
    body::before{content:'';position:fixed;inset:0;z-index:-1;pointer-events:none;
      background:radial-gradient(ellipse 80% 55% at 50% 0%,var(--accent-tint) 0%,transparent 68%);
      opacity:.3;animation:breathe 7s ease-in-out infinite}
    @keyframes breathe{0%,100%{opacity:.22;transform:scaleY(1)}50%{opacity:.40;transform:scaleY(1.05)}}
    .wrap{max-width:680px;margin:0 auto;padding:48px 20px 64px}
    h1{font-family:var(--font-display);font-size:2rem;font-weight:600;margin:0 0 8px;letter-spacing:-.01em;color:var(--accent-dark)}
    .sub{color:var(--muted);margin:0 0 8px;font-size:1rem}
    .zurueck{display:inline-block;margin-bottom:24px;color:var(--accent);text-decoration:none;font-size:.88rem}
    .zurueck:hover{text-decoration:underline}
    form{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:24px}
    .feld{margin-bottom:18px}
    label{display:block;font-weight:600;font-size:.9rem;margin-bottom:4px}
    .hinweis{color:var(--muted);font-size:.8rem;margin:0 0 6px}
    input[type=text],textarea,select{
      width:100%;padding:10px 12px;font-family:inherit;font-size:1rem;color:var(--text);
      background:var(--bg);border:1px solid var(--border);border-radius:10px}
    input[type=text]:focus,textarea:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
    textarea{resize:vertical;min-height:88px}
    .falle{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
    button{font-family:inherit;font-size:1rem;font-weight:600;padding:12px 22px;border:0;border-radius:10px;
      background:var(--accent);color:#fff;cursor:pointer;transition:background .15s ease}
    button:hover{background:var(--accent-dark)}
    button[disabled]{opacity:.55;cursor:progress}
    .fehler{margin-top:14px;color:#B60205;font-size:.9rem}
    .danke{background:var(--card);border:1px solid var(--accent);border-radius:14px;padding:24px}
    .danke h2{font-family:var(--font-display);margin:0 0 8px;color:var(--accent-dark)}
    .link-box{display:flex;gap:8px;align-items:center;margin:14px 0;flex-wrap:wrap}
    .link-box a{color:var(--accent);word-break:break-all}
    .link-box button{padding:8px 14px;font-size:.85rem}
    .status-liste{color:var(--muted);font-size:.85rem;padding-left:1.2em;margin:12px 0 0}
    footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--border);color:var(--muted);font-size:.82rem}
    .footer-credit{display:inline-flex;align-items:center;gap:8px;margin-top:12px;color:var(--muted);text-decoration:none;transition:color .15s ease}
    .footer-credit:hover{color:var(--accent)}
    .footer-avatar{width:28px;height:28px;border-radius:50%;border:1px solid var(--border);object-fit:cover;display:block}
  </style>
</head>
<body>
  <div class="wrap">
    <a class="zurueck" href="index.html">← Zur Übersicht</a>
    <h1>Skill vorschlagen</h1>
    <p class="sub">Du kennst einen Skill, der in der Liste fehlt? Trag ihn hier ein — ohne Konto, ohne Anmeldung.</p>
    <p class="hinweis">Wir speichern nichts über dich: keine Adresse, keine Kennung. Dein Vorschlag wird angeschaut und, wenn er passt, in die Skillsliste aufgenommen.</p>

    <form id="formular" novalidate>
      <div class="feld">
        <label for="stufe">Anspannungsstufe</label>
        <p class="hinweis">Bei welcher Anspannung hilft dieser Skill?</p>
        <select id="stufe" required></select>
      </div>

      <div class="feld">
        <label for="kategorie">Kategorie</label>
        <select id="kategorie" required></select>
      </div>

      <div class="feld">
        <label for="emoji">Symbol</label>
        <p class="hinweis">Ein einzelnes Emoji, z. B. 🎧</p>
        <input type="text" id="emoji" maxlength="2" required>
      </div>

      <div class="feld">
        <label for="titel">Titel</label>
        <p class="hinweis">Kurz und konkret, höchstens 60 Zeichen.</p>
        <input type="text" id="titel" maxlength="60" required>
      </div>

      <div class="feld">
        <label for="beschreibung">Beschreibung</label>
        <p class="hinweis">Was macht man genau? Höchstens 300 Zeichen.</p>
        <textarea id="beschreibung" maxlength="300" required></textarea>
      </div>

      <div class="feld">
        <label for="tipp">Tipp <span class="hinweis" style="display:inline">(freiwillig)</span></label>
        <p class="hinweis">Ein praktischer Hinweis, höchstens 200 Zeichen.</p>
        <textarea id="tipp" maxlength="200"></textarea>
      </div>

      <div class="feld">
        <label for="von">Dein Name <span class="hinweis" style="display:inline">(freiwillig)</span></label>
        <p class="hinweis"><strong>Achtung:</strong> Der Name erscheint öffentlich und dauerhaft auf der Skillsliste. Vorname oder Spitzname genügt. Lass das Feld leer, wenn du anonym bleiben willst.</p>
        <input type="text" id="von" maxlength="30">
      </div>

      <input class="falle" type="text" name="falle" id="falle" tabindex="-1" autocomplete="off" aria-hidden="true">

      <div class="cf-turnstile" data-sitekey="TURNSTILE_SITEKEY_HIER_EINSETZEN"></div>

      <button type="submit" id="senden">Vorschlag absenden</button>
      <div class="fehler" id="fehler" hidden></div>
    </form>

    <div class="danke" id="danke" hidden>
      <h2>Danke!</h2>
      <p>Dein Vorschlag ist angekommen. Wir können dich nicht benachrichtigen — merk dir diesen Link, dort siehst du den Stand:</p>
      <div class="link-box">
        <a id="issue-link" href="#" target="_blank" rel="noopener"></a>
        <button type="button" id="kopieren">Link kopieren</button>
      </div>
      <ul class="status-liste">
        <li><strong>ohne Kennzeichnung</strong> — eingegangen, noch nicht angeschaut</li>
        <li><strong>in Prüfung</strong> — wird gerade angeschaut</li>
        <li><strong>freigegeben</strong> — kommt in die Skillsliste</li>
        <li><strong>abgelehnt</strong> — wird nicht übernommen, mit Begründung</li>
      </ul>
    </div>

    <footer>
      <div>Gehostet via GitHub Pages unter <code>stayingclean.github.io/toolbox/</code></div>
      <a class="footer-credit" href="https://github.com/stayingclean" target="_blank" rel="noopener">
        <img class="footer-avatar" src="https://github.com/stayingclean.png?size=80" alt="stayingclean" loading="lazy" width="28" height="28">
        <span>Erstellt von stayingclean</span>
      </a>
    </footer>
  </div>

<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
<script>
var DATEN = /*__BUILD_DATA__*/{};
var WORKER_URL = "WORKER_URL_HIER_EINSETZEN";
var STUFEN = [["hoch","Hoch"],["mittel","Mittel"],["tief","Tief"]];

function el(id){ return document.getElementById(id); }

/* Stufen-Auswahl aus dem Datenstand füllen */
STUFEN.forEach(function(paar){
  var o=document.createElement('option');
  o.value=paar[1];
  o.textContent=paar[1]+' – '+(DATEN[paar[0]]?DATEN[paar[0]].label:paar[1]);
  el('stufe').appendChild(o);
});

/* Kategorien hängen von der gewählten Stufe ab */
function kategorienFuellen(){
  var schluessel=STUFEN.filter(function(p){return p[1]===el('stufe').value;})[0][0];
  var liste=(DATEN[schluessel]&&DATEN[schluessel].kategorien)||[];
  el('kategorie').innerHTML='';
  liste.forEach(function(k){
    var o=document.createElement('option');
    o.value=k.label;
    o.textContent=(k.icon?k.icon+' ':'')+k.label;
    el('kategorie').appendChild(o);
  });
}
el('stufe').addEventListener('change', kategorienFuellen);
kategorienFuellen();

el('formular').addEventListener('submit', async function(ereignis){
  ereignis.preventDefault();
  el('fehler').hidden=true;

  var pflicht=['emoji','titel','beschreibung'];
  for(var i=0;i<pflicht.length;i++){
    if(!el(pflicht[i]).value.trim()){
      el('fehler').textContent='Bitte Emoji, Titel und Beschreibung ausfüllen.';
      el('fehler').hidden=false;
      el(pflicht[i]).focus();
      return;
    }
  }

  var token=(document.querySelector('[name="cf-turnstile-response"]')||{}).value||'';
  if(!token){
    el('fehler').textContent='Bitte warte kurz, bis die Sicherheitsprüfung fertig ist, und versuch es dann erneut.';
    el('fehler').hidden=false;
    return;
  }

  el('senden').disabled=true;
  el('senden').textContent='Wird gesendet …';

  try{
    var antwort=await fetch(WORKER_URL,{
      method:'POST',
      headers:{'content-type':'application/json'},
      body:JSON.stringify({
        stufe:el('stufe').value,
        kategorie:el('kategorie').value,
        emoji:el('emoji').value,
        titel:el('titel').value,
        beschreibung:el('beschreibung').value,
        tipp:el('tipp').value,
        von:el('von').value,
        falle:el('falle').value,
        turnstile:token
      })
    });
    var ergebnis=await antwort.json();
    if(!antwort.ok){ throw new Error(ergebnis.fehler||'Unbekannter Fehler'); }
    el('issue-link').href=ergebnis.url;
    el('issue-link').textContent=ergebnis.url;
    el('formular').hidden=true;
    el('danke').hidden=false;
    window.scrollTo(0,0);
  }catch(fehler){
    el('fehler').textContent='Das hat nicht geklappt: '+fehler.message+' Bitte versuch es später noch einmal.';
    el('fehler').hidden=false;
    if(window.turnstile){ window.turnstile.reset(); }
  }finally{
    el('senden').disabled=false;
    el('senden').textContent='Vorschlag absenden';
  }
});

el('kopieren').addEventListener('click', function(){
  navigator.clipboard.writeText(el('issue-link').href).then(function(){
    el('kopieren').textContent='Kopiert ✓';
    setTimeout(function(){ el('kopieren').textContent='Link kopieren'; },2000);
  });
});
</script>
</body>
</html>
```

- [ ] **Step 4: `build.py` erweitern**

Bei den Konstanten ergänzen:

```python
TEMPLATE_VORSCHLAG = ROOT / "template-vorschlag.html"
OUTPUT_VORSCHLAG = ROOT / "docs" / "skill-vorschlagen.html"
PLACEHOLDER_VORSCHLAG = "var DATEN = /*__BUILD_DATA__*/{};"
```

Die Funktion `render` durch einen gemeinsamen Kern und zwei Aufrufer ersetzen:

```python
def _render(template_path, output_path, placeholder, ersatz, data: dict):
    if not template_path.exists():
        raise BuildError(f"Vorlage nicht gefunden: {template_path.name}")
    template = template_path.read_bytes().decode("utf-8-sig")  # evtl. BOM entfernen
    if placeholder not in template:
        raise BuildError(
            f"Platzhalter nicht in {template_path.name} gefunden. "
            f"Die Vorlage muss '{placeholder}' enthalten."
        )
    payload = json.dumps(data, ensure_ascii=False, separators=(", ", ": "))
    html = template.replace(placeholder, ersatz % payload, 1)
    # gleiche Datei-Konvention wie das Original: UTF-8 mit BOM
    output_path.write_bytes(b"\xef\xbb\xbf" + html.encode("utf-8"))


def render(data: dict):
    _render(TEMPLATE, OUTPUT, PLACEHOLDER, "var DATA = %s;", data)


def render_vorschlag(data: dict):
    _render(
        TEMPLATE_VORSCHLAG,
        OUTPUT_VORSCHLAG,
        PLACEHOLDER_VORSCHLAG,
        "var DATEN = %s;",
        data,
    )
```

In `main()` den Aufruf ergänzen:

```python
    try:
        data = load_data()
        render(data)
        render_vorschlag(data)
        write_daten_json(data)
    except BuildError as exc:
```

und die Erfolgsmeldung:

```python
    print(f"✅ {OUTPUT_VORSCHLAG.relative_to(ROOT).as_posix()} wurde neu erstellt.")
```

- [ ] **Step 5: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: PASS, 8 Tests.

- [ ] **Step 6: Bauen und im Browser prüfen**

Run: `uv run build.py`
Expected: drei ✅-Zeilen.

`docs/skill-vorschlagen.html` im Browser öffnen (Doppelklick genügt).
Expected:
- Stufen-Auswahl enthält Hoch/Mittel/Tief mit den Bezeichnungen aus der Excel
- Kategorie-Auswahl ändert sich, wenn die Stufe gewechselt wird
- Turnstile-Kästchen erscheint (bei lokalem Öffnen kann es fehlschlagen, das ist erwartet — die Domain ist nicht freigegeben)
- Keine Fehler in der Browser-Konsole ausser der Turnstile-Domainmeldung

- [ ] **Step 7: Commit**

```bash
git add template-vorschlag.html build.py tests/test_build.py docs/skill-vorschlagen.html
git commit -m "Formularseite zum Einreichen neuer Skills"
```

---

### Task 8: Freigegebene Vorschläge übernehmen

**Files:**
- Create: `tools/vorschlaege_holen.py`
- Create: `vorschlaege.bat`
- Create: `tests/test_vorschlaege_holen.py`

**Interfaces:**
- Consumes: Issue-Format aus Task 6, Excel-Spalte `Von` aus Task 3
- Produces:
  - `parse_body(body: str) -> dict | None` — liest den `<!-- vorschlag … -->`-Block; `None`, wenn keiner vorhanden oder das JSON kaputt ist
  - `an_excel_anhaengen(pfad: Path, eintraege: list[dict]) -> int` — hängt Zeilen ans Blatt `Skills` an, spaltenweise nach Kopfzeile zugeordnet; legt die Spalte `Von` an, falls sie fehlt; gibt die Anzahl angehängter Zeilen zurück

- [ ] **Step 1: Fehlschlagende Tests schreiben**

Datei `tests/test_vorschlaege_holen.py`:

```python
import json
import sys
from pathlib import Path

import openpyxl

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


def test_anhaengen_schreibt_in_die_richtigen_spalten(tmp_path):
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp", "Von"])
    ws.append(["Hoch", "Ablenkung", "🌶️", "Vorhanden", "Alte Zeile", "", ""])
    wb.save(pfad)

    anzahl = vh.an_excel_anhaengen(pfad, [BEISPIEL])

    assert anzahl == 1
    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    assert ws2.max_row == 3
    assert [c.value for c in ws2[3]] == [
        "Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.",
        "Kopfhörer bereitlegen", "Max",
    ]


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
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl pytest tests/test_vorschlaege_holen.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vorschlaege_holen'`

- [ ] **Step 3: Skript schreiben**

Datei `tools/vorschlaege_holen.py`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl"]
# ///
"""
Freigegebene Skill-Vorschläge übernehmen
========================================

Holt aus dem Vorschlags-Repo alle offenen Issues mit dem Label „freigegeben",
hängt sie ans Blatt `Skills` von skills_daten.xlsx an, schliesst die Issues und
ruft anschliessend build.py auf.

Aufruf:  vorschlaege.bat      (oder `uv run tools/vorschlaege_holen.py`)

Der Push bleibt bewusst von Hand — nach dem Lauf zuerst die Skillsliste
anschauen, dann committen und pushen.

Voraussetzung: das GitHub-CLI `gh` ist installiert und angemeldet
(`gh auth status` muss ein angemeldetes Konto zeigen).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "skills_daten.xlsx"
BUILD = ROOT / "build.py"
REPO = "stayingclean/toolbox-vorschlaege"
LABEL = "freigegeben"

SPALTEN = [
    ("Stufe", "stufe"),
    ("Kategorie", "kategorie"),
    ("Emoji", "emoji"),
    ("Titel", "titel"),
    ("Beschreibung", "beschreibung"),
    ("Tipp", "tipp"),
    ("Von", "von"),
]

BLOCK = re.compile(r"<!--\s*vorschlag\s*(\{.*?\})\s*-->", re.DOTALL)


def parse_body(body: str):
    """Liest den maschinenlesbaren Block aus einem Issue-Rumpf.

    Liefert None, wenn kein Block vorhanden ist oder das JSON nicht lesbar ist –
    solche Issues bleiben offen und werden am Ende gemeldet.
    """
    treffer = BLOCK.search(body or "")
    if not treffer:
        return None
    try:
        daten = json.loads(treffer.group(1))
    except json.JSONDecodeError:
        return None
    return daten if isinstance(daten, dict) else None


def hole_issues():
    """Fragt die freigegebenen, offenen Issues über das GitHub-CLI ab."""
    ergebnis = subprocess.run(
        ["gh", "issue", "list", "--repo", REPO, "--label", LABEL,
         "--state", "open", "--limit", "100", "--json", "number,title,body"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if ergebnis.returncode != 0:
        raise SystemExit(
            "❌ Konnte die Vorschläge nicht abrufen:\n"
            + ergebnis.stderr.strip()
            + "\n\nIst `gh` installiert und angemeldet? Prüfe mit: gh auth status"
        )
    return json.loads(ergebnis.stdout or "[]")


def an_excel_anhaengen(pfad: Path, eintraege: list) -> int:
    """Hängt Vorschläge ans Blatt `Skills` an – spaltenweise nach Kopfzeile."""
    if not eintraege:
        return 0
    wb = openpyxl.load_workbook(pfad)
    ws = wb["Skills"]
    kopf = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
    for name, _ in SPALTEN:
        if name not in kopf:
            ws.cell(row=1, column=len(kopf) + 1, value=name)
            kopf.append(name)
    for eintrag in eintraege:
        zeile = [""] * len(kopf)
        for name, schluessel in SPALTEN:
            zeile[kopf.index(name)] = eintrag.get(schluessel, "")
        ws.append(zeile)
    wb.save(pfad)
    return len(eintraege)


def issue_schliessen(nummer: int):
    subprocess.run(
        ["gh", "issue", "close", str(nummer), "--repo", REPO,
         "--comment", "Übernommen – erscheint mit dem nächsten Build in der Skillsliste."],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )


def main():
    issues = hole_issues()
    if not issues:
        print("Keine freigegebenen Vorschläge offen. Nichts zu tun.")
        return

    uebernehmen, uebersprungen = [], []
    for issue in issues:
        daten = parse_body(issue.get("body", ""))
        if daten is None or daten.get("art") != "neu":
            uebersprungen.append(issue)
            continue
        uebernehmen.append((issue, daten))

    anzahl = an_excel_anhaengen(XLSX, [d for _, d in uebernehmen])
    for issue, daten in uebernehmen:
        print(f"  + {daten['stufe']} / {daten['kategorie']}: {daten['titel']}")
        issue_schliessen(issue["number"])

    print(f"\n✅ {anzahl} Vorschlag/Vorschläge in {XLSX.name} übernommen.")

    for issue in uebersprungen:
        print(
            f'⚠ Issue #{issue["number"]} „{issue["title"]}" übersprungen '
            f'(kein lesbarer Vorschlagsblock oder andere Art) – bleibt offen.'
        )

    if anzahl:
        print("\nSkillsliste wird neu gebaut …\n")
        subprocess.run([sys.executable, str(BUILD)], check=True)
        print(
            "\nJetzt anschauen: docs/skillsliste.html\n"
            "Wenn es passt:  git add -A && git commit -m \"Neue Skills übernommen\" && git push"
        )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: PASS, 13 Tests.

- [ ] **Step 5: Startdatei anlegen**

Datei `vorschlaege.bat`:

```bat
@echo off
cd /d "%~dp0"
uv run tools/vorschlaege_holen.py
pause
```

- [ ] **Step 6: Leerlauf prüfen**

Run: `uv run tools/vorschlaege_holen.py`
Expected: `Keine freigegebenen Vorschläge offen. Nichts zu tun.` (im Vorschlags-Repo liegt noch nichts.)

- [ ] **Step 7: Commit**

```bash
git add tools/vorschlaege_holen.py vorschlaege.bat tests/test_vorschlaege_holen.py
git commit -m "Freigegebene Vorschlaege in die Excel uebernehmen"
```

---

### Task 9: Karte in der Übersicht und Dokumentation

**Files:**
- Modify: `docs/index.html:133-146` (Gruppe „Werkzeuge")
- Modify: `CLAUDE.md`
- Modify: `ANLEITUNG.md`

**Interfaces:**
- Consumes: `docs/skill-vorschlagen.html` aus Task 7, `vorschlaege.bat` aus Task 8
- Produces: keine Schnittstelle für spätere Tasks

- [ ] **Step 1: Karte in der Übersicht ergänzen**

In `docs/index.html` in der Gruppe „Werkzeuge" nach der Flyer-Karte einfügen:

```html
        <a class="card" href="skill-vorschlagen.html">
          <span class="name">Skill vorschlagen</span>
          <span class="meta">Eigenen Skill für die Liste einreichen – ohne Konto</span>
        </a>
```

- [ ] **Step 2: Sichtprüfung**

`docs/index.html` im Browser öffnen.
Expected: vier Karten in „Werkzeuge", die neue Karte führt auf das Formular.

- [ ] **Step 3: `CLAUDE.md` erweitern**

Im Abschnitt „Aufbau" nach der Zeile zu `asrs-v1-1.html` ergänzen:

```markdown
- `docs/skill-vorschlagen.html` = Formular zum Einreichen neuer Skills (generiert).
- `docs/skills-daten.json` = Datenstand für Formular und Worker (generiert).
```

Nach dem Abschnitt „Skillsliste pflegen" einen neuen Abschnitt einfügen:

```markdown
## Skill-Vorschläge von aussen

Besucher können über `docs/skill-vorschlagen.html` anonym neue Skills einreichen.
Der Weg: Formular → Cloudflare Worker (`worker/`) → Issue in
`stayingclean/toolbox-vorschlaege`.

**Freigeben und übernehmen:**

1. Im Vorschlags-Repo das Issue anschauen und Label `freigegeben` setzen
   (oder `abgelehnt` mit einer kurzen Begründung als Kommentar).
2. **`vorschlaege.bat`** doppelklicken → übernimmt alle freigegebenen Vorschläge
   in `skills_daten.xlsx`, schliesst die Issues und baut die Skillsliste neu.
3. Ergebnis anschauen, dann committen und pushen. **Nichts geht ohne Push online.**

Die Formularseite ist generiert (`template-vorschlag.html` + `build.py`) — nicht
direkt bearbeiten. Sie ist die einzige Seite in `docs/`, die Internet braucht
(Spam-Schutz und Absenden); das CSS bleibt trotzdem eingebettet.

Der Worker liegt in `worker/`, wird aber **nicht** veröffentlicht. Details und
Notbremse: `worker/README.md`.
```

- [ ] **Step 4: `ANLEITUNG.md` erweitern**

Am Ende einen Abschnitt in derselben, für Nicht-Techniker gedachten Tonlage ergänzen:

```markdown
## Vorschläge von anderen übernehmen

Auf der Website gibt es die Seite „Skill vorschlagen". Wer dort etwas einträgt,
landet als Eintrag in einer Liste, die nur du freigeben kannst.

1. **Anschauen:** Öffne https://github.com/stayingclean/toolbox-vorschlaege/issues
   (auf dem Handy geht die GitHub-App). Jeder Eintrag ist ein Vorschlag.
2. **Entscheiden:** Rechts unter „Labels" wählst du
   - `freigegeben` → soll in die Skillsliste
   - `abgelehnt` → nicht übernehmen (schreib kurz dazu, warum)
   - `in Prüfung` → du schaust es dir später nochmal an
3. **Übernehmen:** Doppelklick auf **`vorschlaege.bat`**. Das Fenster zeigt, was
   übernommen wurde, und baut die Skillsliste neu.
4. **Veröffentlichen:** Schau `docs/skillsliste.html` an. Wenn es passt, wie
   gewohnt committen und pushen. Vorher ist online nichts verändert.

Wenn im Fenster steht „Keine freigegebenen Vorschläge offen", hast du gerade
nichts freigegeben — dann ist alles in Ordnung.
```

- [ ] **Step 5: Commit**

```bash
git add docs/index.html CLAUDE.md ANLEITUNG.md
git commit -m "Karte fuer das Vorschlagsformular und Dokumentation"
```

---

### Task 10: Durchlauf von Ende zu Ende

**Files:**
- Keine neuen Dateien; ggf. Korrekturen an `template-vorschlag.html`, `worker/index.js`, `tools/vorschlaege_holen.py`

**Interfaces:**
- Consumes: alles aus Task 1–9
- Produces: bestätigte Funktionsfähigkeit; keine Schnittstelle

- [ ] **Step 1: Aktuellen Stand veröffentlichen**

**Wichtig:** `.github/workflows/deploy.yml` löst nur bei einem Push auf `master`
aus. Solange die Arbeit auf einem Feature-Zweig liegt, ist online nichts
sichtbar — und der Worker scheitert an „Datenstand nicht erreichbar", weil
`skills-daten.json` noch nicht veröffentlicht ist. Also zuerst nach `master`
bringen:

```bash
git checkout master
git merge --no-ff feature/formulare-toolbox
git push
```

Warten, bis die GitHub-Action durch ist (`gh run watch`), dann prüfen:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://stayingclean.github.io/toolbox/skills-daten.json
curl -s -o /dev/null -w '%{http_code}\n' https://stayingclean.github.io/toolbox/skill-vorschlagen.html
```

Expected: zweimal `200`. Der Worker kann `skills-daten.json` erst jetzt lesen — vorher wäre jede Einreichung an „Datenstand nicht erreichbar" gescheitert.

- [ ] **Step 2: Echten Vorschlag absenden**

`https://stayingclean.github.io/toolbox/skill-vorschlagen.html` im Browser öffnen, ausfüllen:

- Stufe: Hoch, Kategorie: (eine beliebige)
- Emoji: `🧪`, Titel: `Testeintrag bitte löschen`
- Beschreibung: `Test des Einreichwegs.`
- Tipp: leer lassen, Name: `Testname`

Absenden.
Expected: Dankesmeldung mit Link; der Link öffnet ein Issue im Vorschlags-Repo.

- [ ] **Step 3: Anonymität und Format prüfen**

```bash
gh issue view 1 --repo stayingclean/toolbox-vorschlaege
```

Expected:
- Tabelle mit den eingegebenen Werten
- `<!-- vorschlag … -->`-Block mit gültigem JSON, `"art":"neu"`, `"von":"Testname"`
- **keine** IP-Adresse, **keine** Browserkennung irgendwo im Text

- [ ] **Step 4: Abwehr prüfen**

Auf der Seite ein zweites Mal absenden, diesmal mit `http://spam.example` in der Beschreibung.
Expected: rote Meldung „Links sind nicht erlaubt.", kein neues Issue.

Ratenbegrenzung: sechs gültige Einreichungen kurz hintereinander.
Expected: ab der sechsten die Meldung „Zu viele Einreichungen. Bitte in einer Stunde erneut."

Die dabei entstandenen Test-Issues anschliessend löschen:

```bash
gh issue delete <nummer> --repo stayingclean/toolbox-vorschlaege --yes
```

- [ ] **Step 5: Freigeben und übernehmen**

```bash
gh issue edit 1 --repo stayingclean/toolbox-vorschlaege --add-label "freigegeben"
uv run tools/vorschlaege_holen.py
```

Expected:
- Ausgabe listet den übernommenen Vorschlag
- `✅ 1 Vorschlag/Vorschläge in skills_daten.xlsx übernommen.`
- Skillsliste wird neu gebaut, drei ✅-Zeilen
- Issue #1 ist geschlossen mit Kommentar

- [ ] **Step 6: Ergebnis prüfen**

`docs/skillsliste.html` im Browser öffnen, den Skill „Testeintrag bitte löschen" antippen.
Expected: Dialog zeigt Beschreibung und darunter „Vorgeschlagen von Testname".

- [ ] **Step 7: Testeintrag entfernen**

In `skills_daten.xlsx` die Testzeile löschen, speichern.

Run: `uv run build.py`
Expected: die Zeile ist aus `docs/skillsliste.html` verschwunden.

- [ ] **Step 8: Alle Tests laufen lassen**

```bash
uv run --with pytest --with openpyxl pytest tests -v
node --test worker/
```

Expected: beide grün.

- [ ] **Step 9: Abschluss committen und veröffentlichen**

```bash
git add -A
git commit -m "Durchlauf von Ende zu Ende geprueft"
git push
```

- [ ] **Step 10: Abnahme gegen die Spezifikation**

Die Liste „Prüfen vor Abschluss" in `specs/2026-08-03-skill-vorschlagen-design.md` durchgehen, soweit sie Stufe 1 betrifft:

- [ ] Formular auf Handy und Rechner bedienbar, Kategorie-Auswahl filtert korrekt
- [ ] Worker lehnt ab: fehlendes Turnstile-Token, ausgefüllte Falle, Link im Text, zu lange Felder, unbekannte Kategorie, sechste Einreichung innert einer Stunde
- [ ] Issue enthält weder IP noch Browserkennung; die Dankesmeldung zeigt den Link
- [ ] `vorschlaege.bat` übernimmt mehrere Vorschläge in einem Durchgang, schliesst die Issues und erzeugt eine korrekte Skillsliste
- [ ] Bestehende Excel ohne Spalte `Von` baut weiterhin fehlerfrei (durch `test_von_ist_leer_wenn_spalte_fehlt` abgedeckt)
- [ ] Detail-Dialog zeigt die Namenszeile nur bei vorhandenem Namen

Offene Punkte notieren; alles, was Reiter „Bestehenden ergänzen", Duplikatprüfung, Kaffeekasse oder Fusszeilen-Link betrifft, gehört zu Stufe 2 bzw. 3 und bleibt hier offen.
