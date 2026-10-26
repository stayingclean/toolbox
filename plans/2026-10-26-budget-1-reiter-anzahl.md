# Welle 1 — Anzahl der Anpassungen am Versionsreiter: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jeder Versionsreiter mit Anpassungen trägt eine kleine Zahl; der Tooltip nennt das nächste Datum.

**Architecture:** Eine neue reine Funktion im Rechenkern zählt und fasst zusammen; der Anpassungs-Knopf und die Reiter holen ihre Zahl aus ihr. Die Reiter werden beim Tippen nicht neu gebaut, nur ihre Marke wird nachgeführt.

**Tech Stack:** Vanilla JS und CSS in `docs/budgetvorlage.html`; Tests in Python (`tests/test_budget.py`), der Kern läuft über `tests/budget_treiber.mjs` in Node.

**Spec:** `specs/2026-10-26-budget-ausblick-reiter-spalte-design.md`, Teil 2.

## Global Constraints

- Dateiformat v5 bleibt, kein neues Feld (`FILE_FORMAT_VERSION = 5`).
- Keine Bibliothek, kein CDN; Farben nur über `var(--color-*)`, keine neuen Hex-Werte für Token-Farben.
- Kernfunktionen stehen zwischen `/* == budget-kern:anfang == */` und `/* == budget-kern:ende == */`, auf Einrückung 4 (`^    function name`) — sonst findet der Treiber sie nicht.
- Kommentare im Code auf Deutsch, im Ton der Datei: sie begründen, warum.
- Ein Datum, das heute ist, gilt als eingetreten (`stichtagListe`: `faellig = d <= heuteIso`).
- Tests laufen mit: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
- Voraussetzung: Welle 0 (`plans/2026-10-26-budget-0-ladepruefung.md`) ist auf diesem Branch committed; der Sollwert stammt vom unveränderten Stand.

## Review Focus

1. Eine Version mit Anpassung **ohne Betrag** (nur Datum, aus alter Datei) — keine Marke, Zahl wie Knopf.
2. Anpassungen in **unbekannten Zeilen** (`bekannteAnpassungen` filtert sie) — zählen nicht, wie beim Knopf.
3. **Tippen in einer Anpassungszeile**: die Marke ändert sich sofort, der Fokus bleibt im Feld.
4. **Vorschau offen** und Versionswechsel: Marke stimmt für jede Version, nicht nur die aktive.
5. Ein Datum **gleich heute** zählt als verstrichen, nicht als «nächste».

---

### Task 1: `anpassungsUebersicht` im Rechenkern

**Files:**
- Modify: `docs/budgetvorlage.html` (Kern, direkt nach `stichtagListe`)
- Test: `tests/test_budget.py` (neuer Block am Ende, Überschrift `# --- Welle 1: Zahl am Reiter ---`)

**Interfaces:**
- Produces: `anpassungsUebersicht(adjustments, heuteIso) -> { anzahl: number, naechste: string|null, verstrichen: number, ohneDatum: number }` — `adjustments` ist schon auf bekannte Zeilen gefiltert. Gezählt wird nur, was `anpassungHatBetrag` bejaht. `naechste` = kleinstes `ab` mit `istIsoDatum(ab) && ab > heuteIso`; `verstrichen` = Anzahl mit `ab <= heuteIso`; `ohneDatum` = Anzahl ohne lesbares Datum.
- Produces: `reiterHinweis(uebersicht) -> string` — Text für Tooltip und Screenreader, `''` bei `anzahl === 0`.

- [ ] **Step 1: Failing tests schreiben**

```python
HEUTE = "2026-10-26"

def test_uebersicht_zaehlt_wie_der_knopf():
    u = kern("anpassungsUebersicht", ANPASSUNGEN, HEUTE)
    assert u == {"anzahl": 4, "naechste": "2027-01-01", "verstrichen": 0, "ohneDatum": 1}
    staende = kern("stichtagListe", ANPASSUNGEN, HEUTE)
    gruppen = kern("anpassungsGruppen", ANPASSUNGEN, staende, WERTE)
    assert u["anzahl"] == sum(len(g["eintraege"]) for g in gruppen)

def test_uebersicht_ohne_betrag_zaehlt_nicht():
    u = kern("anpassungsUebersicht",
             {"handy": {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}}, HEUTE)
    assert u["anzahl"] == 0 and u["naechste"] is None

def test_uebersicht_heute_ist_verstrichen():
    a = {"handy": {"jaehrlich": None, "monatlich": 0, "ab": HEUTE},
         "kasse": {"jaehrlich": None, "monatlich": 340, "ab": "2026-10-27"}}
    u = kern("anpassungsUebersicht", a, HEUTE)
    assert u["verstrichen"] == 1 and u["naechste"] == "2026-10-27"

@pytest.mark.parametrize("u, text", [
    ({"anzahl": 3, "naechste": "2026-12-01", "verstrichen": 0, "ohneDatum": 1},
     "3 Anpassungen, nächste ab 01.12.2026, 1 ohne Datum"),
    ({"anzahl": 2, "naechste": None, "verstrichen": 2, "ohneDatum": 0},
     "2 Anpassungen, alle Daten verstrichen"),
    ({"anzahl": 1, "naechste": None, "verstrichen": 0, "ohneDatum": 1},
     "1 Anpassung, ohne Datum"),
    ({"anzahl": 0, "naechste": None, "verstrichen": 0, "ohneDatum": 0}, ""),
])
def test_reiter_hinweis(u, text):
    assert kern("reiterHinweis", u) == text
```

- [ ] **Step 2: Laufen lassen, Fehlschlag sehen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests/test_budget.py -q -k "uebersicht or reiter_hinweis"`
Expected: FAIL, «Unbekannte Funktion des Rechenkerns: anpassungsUebersicht»

- [ ] **Step 3: Beide Funktionen im Kern schreiben**

Datum über `datumAnzeige`. Regel für den Text: `"<n> Anpassung(en)"`, dann `", nächste ab <datum>"` wenn `naechste`, sonst `", alle Daten verstrichen"` wenn `verstrichen > 0`; dann bei `ohneDatum > 0`: `", <k> ohne Datum"` — ausser wenn es **nur** Vorschläge sind (`ohneDatum === anzahl`), dann `", ohne Datum"`.

- [ ] **Step 4: Tests grün**

Run: wie Step 2. Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Kern: Uebersicht der Anpassungen einer Version fuer den Reiter"
```

### Task 2: Marke am Reiter, Knopf aus derselben Quelle

**Files:**
- Modify: `docs/budgetvorlage.html` — `renderVersionTabs`, `renderAdjustmentList`, CSS bei `.version-tab`
- Test: `tests/test_budget.py`

**Interfaces:**
- Consumes: `anpassungsUebersicht`, `reiterHinweis` (Task 1); `bekannteAnpassungen`, `heuteIso` (bestehend).
- Produces: `reiterMarkeSetzen(tab, version)` (DOM, ausserhalb des Kerns) — setzt/entfernt `span.version-tab-anzahl` (Zahl, `aria-hidden="true"`), `tab.title` und `aria-label`. `reiterMarkenAktualisieren()` — ruft sie für jeden `.version-tab` mit seiner Version auf.

- [ ] **Step 1: Failing statische Tests**

```python
def test_reiter_bekommt_die_marke():
    block = _funktionsblock("renderVersionTabs")
    assert "reiterMarkeSetzen(tab, v)" in block

def test_knopf_und_reiter_zaehlen_aus_einer_quelle():
    assert "anpassungsUebersicht(" in _funktionsblock("renderAdjustmentList")
    assert "anpassungsUebersicht(" in _funktionsblock("reiterMarkeSetzen")

def test_marke_lebt_ohne_neubau_der_reiter():
    # Nach jeder Rechnung nachgeführt; ein Neubau würfe den Fokus weg.
    rechnen = _funktionsblock("recomputeAll")
    assert "reiterMarkenAktualisieren()" in rechnen
    assert "renderVersionTabs()" not in rechnen

def test_marke_ist_fuer_screenreader_verborgen():
    block = _funktionsblock("reiterMarkeSetzen")
    assert "version-tab-anzahl" in block and "aria-hidden" in block
    assert "aria-label" in block
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `... python -m pytest tests/test_budget.py -q -k "reiter or marke or quelle"`
Expected: FAIL

- [ ] **Step 3: Umsetzen**

- `reiterMarkeSetzen(tab, version)`: `uebersicht = anpassungsUebersicht(bekannteAnpassungen(version.adjustments), heuteIso())`. Bei `anzahl === 0` keine Marke, Titel wie bisher (`Zu „<name>" wechseln (Doppelklick zum Umbenennen)`), `aria-label` entfernen. Sonst Marke mit der Zahl, Titel `Zu „<name>" wechseln · <reiterHinweis> (Doppelklick zum Umbenennen)`, `aria-label` = `<name>, <reiterHinweis>`.
- In `renderVersionTabs` nach `tab.textContent = v.name` aufrufen.
- `renderAdjustmentList`: `anzahl` aus `anpassungsUebersicht(anpassungen, heuteIso()).anzahl` statt aus der Summe der Gruppen.
- `recomputeAll` ruft am Ende `reiterMarkenAktualisieren()`. Das genügt fürs Tippen: `handleAdjInputEvent` schreibt `active.adjustments[rowId]` vor seinem `recomputeAll()`.
- CSS `.version-tab-anzahl`: kleine runde Marke, `background: var(--color-primary)`, weisse Schrift, `font-size: .7rem`, `margin-left: .4rem`, `font-variant-numeric: tabular-nums`. Im aktiven Reiter lesbar (Kontrast prüfen).

- [ ] **Step 4: Alle Tests grün**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Expected: alles grün.

- [ ] **Step 5: Im Browser ansehen**

`docs/budgetvorlage.html` im eingebauten Browser öffnen (`preview_start` mit `url` `file:///…/docs/budgetvorlage.html`). Zwei Versionen anlegen, in einer drei Anpassungen eintragen (eine mit Datum 01.12.2026, eine ohne). Prüfen: Marke «3» nur an dieser Version; Tooltip-Text; Marke springt beim Tippen eines Betrags in einer neuen Anpassungszeile von 3 auf 4, ohne dass der Fokus das Feld verlässt; nach Leeren wieder 3. Screenshot.

- [ ] **Step 6: Ladeprüfung** — `tests/budget_ladepruefung.js` wie dort beschrieben ausführen; Ergebnis muss `tests/fixtures/budget/erwartet.json` gleichen (Welle 0). Die v5-Datei zeigt dabei die Marke an der zweiten Version — Screenshot.

- [ ] **Step 7: Commit**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Versionsreiter zeigen die Zahl ihrer Anpassungen"
```
