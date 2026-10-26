# Welle 0 — Ladeprüfung alter Dateien und Sollwert: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Beispieldateien der Formate v1–v5 und ein Prüfskript, das sie über den echten Ladeweg der Seite öffnet und wieder speichert; der Sollwert stammt vom unveränderten Stand.

**Architecture:** Das Skript läuft im eingebauten Browser in der ausgelieferten Seite (`javascript_tool`) und ersetzt nur die Datei-Dialoge des Browsers durch Attrappen — die Seite selbst bekommt keinen Prüf-Haken. Eine lokale Auslieferung per `python -m http.server` macht die Beispieldateien per `fetch` erreichbar.

**Tech Stack:** JSON-Beispieldateien, ein JavaScript-Prüfskript, Python-Tests (`pytest`), eingebauter Browser.

**Spec:** `specs/2026-10-26-budget-ausblick-reiter-spalte-design.md`, Teil 4.

## Global Constraints

- **`docs/budgetvorlage.html` wird in dieser Welle nicht verändert.** Der Sollwert muss vom heutigen Stand stammen.
- Beispieldateien enthalten nur fiktive Zahlen und Texte (keine echten Personendaten; das Repo ist öffentlich).
- Format-Kennung `"format": "budgetvorlage"` (`APP_NAME`).
- Zeilen-IDs aus dem `SCHEMA` der Seite (z. B. `netto_einkommen_p1`, `miete`, `heiz_nebenkosten`); eine bewusst unbekannte Zeile heisst `gibt_es_nicht`.
- Tests: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`

## Review Focus

1. **Zufällige IDs** (`genVersionId`) und `savedAt` dürfen den Vergleich nicht kippen — normalisieren.
2. **v3-Kommentare** landen bei «Nach Reduktion», nicht bei «Original» — der Sollwert muss das zeigen.
3. **v5-Eintrag nur mit Datum** fällt beim Laden weg und erscheint nicht im Gespeicherten; die unbekannte Zeile bleibt erhalten.
4. **Speichern nach dem Öffnen** läuft über `state.fileHandle` (die Attrappe aus dem Öffnen) — sie muss `createWritable` können.
5. **Toasts und `beforeunload`** dürfen den Ablauf nicht blockieren.

---

### Task 1: Beispieldateien v1–v5 und ihre Python-Tests

**Files:**
- Create: `tests/fixtures/budget/v1.json` … `v5.json`
- Test: `tests/test_budget.py`, Block `# --- Alte Dateien ---`

**Interfaces:**
- Produces: die fünf Dateien; Inhalt:
  - **v1**: `version: 1`, `data.values` mit `"<id>.jaehrlich"`/`"<id>.monatlich"` für mindestens eine Einnahme und vier Ausgaben, keine Reduktion.
  - **v2**: wie v1, dazu zwei Schlüssel `"<id>.reduktion"` (Jahresbetrag).
  - **v3**: wie v1, dazu `"<id>.reduktion_jaehrlich"` und `"<id>.reduktion_monatlich"`, und `data.comments` mit zwei Texten.
  - **v4**: `data.versions` mit zwei Versionen (zweite `basedOn` erste), `comments`, `activeVersionId` = zweite.
  - **v5**: wie v4, plus `adjustments` in der zweiten Version: eine datiert in der Zukunft (`2027-04-01`), eine verstrichen (`2026-01-01`), eine ohne Datum, eine **nur Datum ohne Betrag** in einer bekannten Zeile, eine in `gibt_es_nicht`; `privateNote` mit fiktivem Text.

- [ ] **Step 1: Failing Tests**

```python
FIXTURES = ROOT / "tests" / "fixtures" / "budget"

@pytest.mark.parametrize("v", [1, 2, 3, 4, 5])
def test_beispieldatei_ist_gueltig(v):
    d = json.loads((FIXTURES / f"v{v}.json").read_text(encoding="utf-8"))
    assert d["format"] == "budgetvorlage" and d["version"] == v
    if v >= 4:
        assert isinstance(d["data"]["versions"], list) and len(d["data"]["versions"]) == 2
    else:
        assert isinstance(d["data"]["values"], dict)

def test_format_und_unterstuetzte_versionen_bleiben():
    text = _seite_text()
    assert "const FILE_FORMAT_VERSION = 5;" in text
    assert "SUPPORTED_VERSIONS = new Set([1, 2, 3, 4, 5])" in text

def test_v5_beispiel_deckt_die_sonderfaelle():
    d = json.loads((FIXTURES / "v5.json").read_text(encoding="utf-8"))
    a = d["data"]["versions"][1]["adjustments"]
    assert "gibt_es_nicht" in a
    assert any(e.get("ab") is None for e in a.values())
    assert any(e.get("jaehrlich") is None and e.get("monatlich") is None and e.get("ab") for e in a.values())
```

- [ ] **Step 2: Fehlschlag sehen** — `... python -m pytest tests/test_budget.py -q -k "beispiel or unterstuetzte"` → FAIL (Dateien fehlen)

- [ ] **Step 3: Dateien schreiben** — Beträge so wählen, dass jährlich = monatlich × 12 nicht überall gilt (eine Zeile nur mit Monatswert, eine nur mit Jahreswert), damit auch die Regel `y || m*12` geprüft wird.

- [ ] **Step 4: Tests grün** — Run wie Step 2 → PASS

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/budget tests/test_budget.py
git commit -m "Beispieldateien der Formate v1 bis v5 fuer die Ladepruefung"
```

### Task 2: Prüfskript, lokale Auslieferung, Sollwert

**Files:**
- Create: `tests/budget_ladepruefung.js` — wird im Browser ausgeführt, nicht von Node.
- Create (lokal, nicht im Repo — `.claude/` ist ignoriert): `.claude/launch.json` mit Eintrag `toolbox-statisch`: `runtimeExecutable` `uv`, `runtimeArgs` `["run", "python", "-m", "http.server", "8765"]`, `port` 8765.
- Create: `tests/fixtures/budget/erwartet.json`
- Test: `tests/test_budget.py`

**Interfaces:**
- Produces: `budget_ladepruefung.js` ist ein Ausdruck, dessen Wert ein Promise ist: `await (async () => { … })()` → `{ "v1": { versionen: [{ name, einnahmenY, ausgabenY, diffY, diffM }], gespeichert: <data aus dem Gespeicherten, normalisiert> }, …, "v5": … }`. Normalisieren: `savedAt` weg; jede Versions-`id` durch ihren Index ersetzen (`"#0"`, `"#1"`), ebenso `basedOn` und `activeVersionId`; `createdAt` weg (Legacy setzt `savedAt` oder jetzt).
- Ablauf je Datei: `fetch('/tests/fixtures/budget/vN.json')` → Text; `window.showOpenFilePicker = async () => [handle]` mit `handle.getFile()` (liefert `new File([text], 'vN.json')`) und `handle.createWritable()` (sammelt `write`-Argumente, `close` löst auf); Klick auf `#btnOpen`; warten, bis `#versionTabs` die erwartete Zahl Reiter trägt; je Reiter klicken und `[data-summary][data-period]` der Zusammenfassung lesen (Text → Zahl, Tausendertrennzeichen `'` entfernen); dann Klick auf `#btnSave` und warten, bis die Attrappe geschrieben hat; JSON parsen, normalisieren.
- Produces: `erwartet.json` = Ausgabe des Skripts auf dem **unveränderten** Stand, 2 Leerzeichen eingerückt, Schlüssel sortiert.

- [ ] **Step 1: Failing Test**

```python
def test_sollwert_deckt_jede_beispieldatei():
    soll = json.loads((FIXTURES / "erwartet.json").read_text(encoding="utf-8"))
    assert sorted(soll) == ["v1", "v2", "v3", "v4", "v5"]
    assert [v["name"] for v in soll["v2"]["versionen"]] == ["Original", "Nach Reduktion"]
    assert [v["name"] for v in soll["v1"]["versionen"]] == ["Hauptversion"]
    v5 = soll["v5"]["gespeichert"]["versions"][1]["adjustments"]
    assert "gibt_es_nicht" in v5                       # unbekannte Zeile bleibt
    assert all(e.get("jaehrlich") is not None or e.get("monatlich") is not None
               for k, e in v5.items() if k != "gibt_es_nicht")   # nur-Datum fiel weg
```

- [ ] **Step 2: Fehlschlag sehen** — `... -k sollwert` → FAIL (Datei fehlt)

- [ ] **Step 3: Skript schreiben und Sollwert aufnehmen**

`preview_start` `{name: "toolbox-statisch"}`, dann `navigate` zu `http://localhost:8765/docs/budgetvorlage.html`. Inhalt von `tests/budget_ladepruefung.js` per `javascript_tool` ausführen. Ergebnis als `erwartet.json` speichern. Ein zweiter Lauf nach Neuladen muss dasselbe liefern (Stabilität der Normalisierung) — sonst nachbessern, bevor der Sollwert gilt. Prüfen, dass die Konsole (`read_console_messages`) ausser dem erwarteten Hinweis zur verworfenen Anpassung nichts meldet.

- [ ] **Step 4: Tests grün** — volle Suite → grün

- [ ] **Step 5: Anleitung für spätere Wellen**

Am Kopf von `tests/budget_ladepruefung.js` in einem Kommentar: wozu, wie ausführen (die drei Schritte aus Step 3), und «das Ergebnis muss `tests/fixtures/budget/erwartet.json` gleichen; ändert eine Welle gewollt etwas am Gespeicherten, ist das ein Entscheid und kein Nachführen».

- [ ] **Step 6: Commit**

```bash
git add tests/budget_ladepruefung.js tests/fixtures/budget/erwartet.json tests/test_budget.py
git commit -m "Ladepruefung im Browser: alte Dateien oeffnen, Summen und Gespeichertes als Sollwert"
```
