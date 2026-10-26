# Welle 2 — Punkt 10: Die Spalte «Total / Jahr» fällt weg: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Budget-Tabellen haben nur noch drei Spalten in der Folge Position, Monatlich, Jährlich; der Unterschied der Anpassungszeile steht hinter dem Datum.

**Architecture:** Reiner Rückbau in Markup, Zeilenaufbau, `recomputeAll` und CSS. Die Rechnung (`rowTotal`, `anpassungUnterschied`) bleibt, nur ihre Anzeige wandert. Kein Kern-Code ändert sich ausser einem Kommentar.

**Tech Stack:** Vanilla JS, CSS inkl. `@media print` in `docs/budgetvorlage.html`; statische Tests in `tests/test_budget.py`.

**Spec:** `specs/2026-10-26-budget-ausblick-reiter-spalte-design.md`, Teil 3.

## Global Constraints

- Dateiformat v5 bleibt; die Spalte war gerechnet, nichts davon steht in der Datei.
- Gilt für Erfassung **und** Druck.
- Der Unterschied bleibt der **Jahresbetrag** aus `anpassungUnterschied` und trägt die Einheit selbst: `(+600.00 / Jahr)`.
- Spaltenfolge danach überall, wo das Paar steht: **Monatlich vor Jährlich** — Budget-Tabellen, Anpassungszeile, Zwischensummen, «Total Fixkosten», Zusammenfassung samt Stand-Zeilen. Tabellen der Auswertung bleiben.
- Keine Änderung an `serialize`, `hydrate`, `isValidPayload` und der Migration.
- Farben nur über `var(--color-*)`.
- Tests: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
- Voraussetzung: Welle 1 (`plans/2026-10-26-budget-1-reiter-anzahl.md`) ist auf diesem Branch committed.

## Review Focus

1. **Schmales Fenster (375 px)**: Anpassungszeile mit Datum **und** Unterschied bricht sauber um, kein seitlicher Überlauf neu dazugekommen.
2. **Kommentarzeile** spannt über genau drei Spalten (sonst eine Phantomspalte in jeder Tabelle).
3. **Vorschau offen**: die gesperrte Anpassungszeile zeigt den Unterschied weiterhin an derselben Stelle.
4. **Druck** mit «Kommentare drucken»: Anpassungszeile druckt Datum und Unterschied auf einer Zeile, Zwischensummen bleiben als solche erkennbar.
5. **Unterschied 0** (neuer Betrag = erfasster) zeigt wie bisher nichts Farbiges; leerer Betrag zeigt gar nichts, auch keine leeren Klammern.

---

### Task 1: Spalte aus Tabellen, Zeilen und Rechnung entfernen

**Files:**
- Modify: `docs/budgetvorlage.html` — alle `<th>Total / Jahr</th>` (13 Stück) und `<th scope="col">Total / Jahr</th>`; die `td.total-cell` in «Total Fixkosten»; Zeilenaufbau (die Funktion mit `totalSpan.dataset.rowTotal`), Zwischensummenzeile (`data-subtotal="${groupId}" data-period="total"`), `recomputeAll` (Zeilen, die `data-row-total`, `[data-period="total"]` bei Subtotal und Grand-Total füllen); Kommentarzeile `td.colSpan = 4` → `3`.
- Test: `tests/test_budget.py`

**Interfaces:**
- Consumes: nichts Neues.
- Produces: Tabellen mit drei Zellen je Zeile; `.total-cell` und `.total-display` haben in `.budget-table` keine Verwendung mehr (CSS-Aufräumen in Task 2).

- [ ] **Step 1: Failing Tests**

```python
def test_keine_spalte_total_jahr_mehr():
    text = _seite_text()
    assert "Total / Jahr" not in text
    assert 'data-period="total"' not in text
    assert "data-row-total" not in text and "dataset.rowTotal" not in text

def test_kommentarzeile_spannt_drei_spalten():
    text = _seite_text()
    assert "td.colSpan = 3;" in text and "td.colSpan = 4;" not in text

def test_rowtotal_rechnet_weiter_den_unterschied():
    # Die Anzeige ist weg, die Rechnung nicht: der Unterschied braucht den Jahreswert.
    assert "anpassungUnterschied(" in _funktionsblock("recomputeAll")
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `... python -m pytest tests/test_budget.py -q -k "total_jahr or drei_spalten or rowtotal"`
Expected: FAIL

- [ ] **Step 3: Entfernen**

Jede Fundstelle aus der Dateiliste. Danach `grep -n "total-cell\|total-display\|Total / Jahr" docs/budgetvorlage.html` und jeden verbleibenden Treffer begründen oder in Task 2 erledigen. `rowTotal` als Variable behalten, solange `anpassungUnterschied` sie braucht.

- [ ] **Step 4: Tests grün**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q` — Expected: grün. (`test_anpassungsfelder_stehen_neben_dem_datum` prüft nur CSS und bleibt bis Task 2 grün; die Anpassungszeile behält in Task 1 noch ihre vierte Zelle.)

- [ ] **Step 5: Commit**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Punkt 10: Spalte Total / Jahr aus Tabellen und Rechnung entfernt"
```

### Task 2: Anpassungszeile mit drei Zellen, Unterschied hinter dem Datum, Breiten und Druck

**Files:**
- Modify: `docs/budgetvorlage.html` — `makeAdjustmentRow` (die `deltaTd` fällt weg, `span.adj-delta` kommt in `.adj-label-content` hinter `.adj-ab-feld`); die Stelle in `recomputeAll`, die `span[data-adj-delta]` füllt; CSS: `.budget-table tbody tr.adj-row > td.total-cell`, `.input-cell`/`.total-cell`-Breiten (Bildschirm und `max-width`-Block mit `label-cell: 40%`), `.subtotal-row .total-display`, Druckregeln `.total-display`; Texte: `title` der Anpassungsfelder («Rechts steht der Unterschied.» → «Der Unterschied pro Jahr steht hinter dem Datum.»), Hilfetext («rechts der Unterschied zum erfassten Wert» → «hinter dem Datum der Unterschied pro Jahr»), Kommentar über `anpassungUnterschied` («die vierte Spalte der Anpassungszeile» → «steht hinter dem Datum der Anpassungszeile»).
- Test: `tests/test_budget.py` — in `test_anpassungsfelder_stehen_neben_dem_datum` die letzte Prüfung (`td\.total-cell \{[^}]*padding-top:\s*0\.6rem`) streichen; der Rest des Tests (Zeile oben ausgerichtet) gilt weiter.

**Interfaces:**
- Consumes: Task 1.
- Produces: `.adj-delta` lebt in `.adj-label-content`; Text `(<deltaAnzeige-Jahr> / Jahr)` oder leer.

- [ ] **Step 1: Failing Tests**

```python
def test_anpassungszeile_hat_drei_zellen():
    block = _funktionsblock("makeAdjustmentRow")
    assert "deltaTd" not in block
    assert "adj-delta" in block   # lebt jetzt in der ersten Zelle

def test_unterschied_traegt_die_einheit():
    # Gefüllt wird in recomputeAll; ohne Spaltenkopf muss die Zahl die Einheit selbst tragen.
    assert "/ Jahr)" in _funktionsblock("recomputeAll")

def test_keine_alten_texte_ueber_rechts():
    text = _seite_text()
    assert "Rechts steht der Unterschied" not in text
    assert "rechts der Unterschied zum erfassten Wert" not in text
    assert "die vierte Spalte der Anpassungszeile" not in text
```

Die gestrichene Prüfung galt der Polsterung einer Zelle, die es nicht mehr gibt — im Commit so sagen. Steht der Unterschied in der ersten Zelle zu hoch oder zu tief neben dem Datumsfeld, dort ausrichten, nicht über eine neue Zelle.

- [ ] **Step 2: Fehlschlag sehen**

Run: `... python -m pytest tests/test_budget.py -q -k "drei_zellen or einheit or alten_texte"` — Expected: FAIL

- [ ] **Step 3: Umsetzen**

- Unterschied: Text `(${deltaAnzeige(unterschied)} / Jahr)` bei Zahl ≠ null, sonst leer; Klassen `ist-gut`/`ist-schlecht` wie bisher über `anpassungWirkung`. Bei Unterschied 0: Text `(0.00 / Jahr)` ohne Farbklasse — wie heute die Zahl ohne Farbe.
- Breiten: `.input-cell` auf `24%` (Bildschirm); im `max-width`-Block Label `46%`, Betragsspalten `27%`. Auf 375 px und 1280 px ansehen und nachstellen, wenn ein Betrag abgeschnitten wird.
- Zwischensumme: beide Zahlen `.computed`, fett, keine Marke (Spec: «mein Vorschlag: nein»). `.subtotal-row .total-display` und `.total-cell`/`.total-display`-Regeln löschen, wenn nach Task 1 kein Element sie mehr trägt (`grep`).
- Druck: `.adj-delta` in der Druckregel bei Zeile ~2923 bleibt, wirkt jetzt in der ersten Zelle; prüfen, dass `.adj-label-content` im Druck nicht umbricht, wo es auf dem Schirm einzeilig ist.

- [ ] **Step 4: Alle Tests grün**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q` — Expected: alles grün.

- [ ] **Step 5: Im Browser ansehen**

`docs/budgetvorlage.html` im eingebauten Browser, Breite 1280 und `resize_window` `mobile` (375). Eine Anpassung mit Datum und Betrag eintragen; prüfen: drei Spalten überall, Unterschied hinter dem Datum, grün/rot richtig (Ausgabe günstiger = grün), Kommentarzeile volle Breite, kein seitlicher Überlauf der Seite (`document.documentElement.scrollWidth <= innerWidth` per `javascript_tool`; ist er schon vorher da gewesen, im Bericht so nennen). Druckansicht: `@media print` per `javascript_tool` auf `all` umschreiben wie in früheren Prüfungen (`plans/2026-10-22-budget-offene-arbeiten.md`, «Der echte Ausdruck») und ansehen. Screenshots beider Breiten.

- [ ] **Step 6: Commit**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Punkt 10: Unterschied steht hinter dem Datum, drei Spalten auch im Druck"
```

### Task 3: «Monatlich» vor «Jährlich»

**Files:**
- Modify: `docs/budgetvorlage.html` — alle `<thead>` der Budget-Tabellen (`<th>Jährlich</th><th>Monatlich</th>` → umgekehrt); Zeilenaufbau der Positionen (Reihenfolge der beiden Betragszellen); `makeAdjustmentRow` (`['jaehrlich', 'monatlich'].forEach` → `['monatlich', 'jaehrlich']`); Zwischensummenzeile; «Total Fixkosten»; Zusammenfassung (`<thead>` und die drei `<tr>` mit `data-summary`); die Stand-Zeilen in `#summaryStands` (wo sie in `recomputeAll` gebaut werden); Druck-CSS, falls es Spalten über `nth-child` anspricht (`grep -n "nth-child" docs/budgetvorlage.html`).
- Test: `tests/test_budget.py`

**Interfaces:**
- Consumes: Task 1 und 2 (drei Zellen je Zeile).
- Produces: dieselben Elemente mit denselben `data-period`-Attributen, nur in anderer Folge.

- [ ] **Step 1: Failing Tests**

```python
def test_monatlich_steht_vor_jaehrlich_in_jeder_kopfzeile():
    text = _seite_text()
    koepfe = re.findall(r"<thead>.*?</thead>", text, re.S)
    paare = [k for k in koepfe if "Jährlich" in k and "Monatlich" in k]
    assert len(paare) >= 14            # 13 Budget-Tabellen + Zusammenfassung
    assert all(k.index("Monatlich") < k.index("Jährlich") for k in paare)

def test_anpassungszeile_erst_monatlich():
    assert "['monatlich', 'jaehrlich'].forEach" in _funktionsblock("makeAdjustmentRow")

def test_zusammenfassung_erst_monatlich():
    text = _seite_text()
    zeile = re.search(r'data-summary="einnahmen" data-period="(\w+)".*?data-summary="einnahmen" data-period="(\w+)"', text, re.S)
    assert zeile.groups() == ("monatlich", "jaehrlich")
```

Dazu einen Test für die Zwischensumme und die Positionszeilen nach demselben Muster (Reihenfolge der `data-period`-Werte in der Funktion, die sie baut).

- [ ] **Step 2: Fehlschlag sehen** — `... -k "monatlich"` → FAIL

- [ ] **Step 3: Umsetzen** — nur Reihenfolge; keine Logik ändern. Das gegenseitige Füllen (`handleAmountInput`) hängt an `data-period` und bleibt. Prüfen, ob irgendwo Zellen über Position statt `data-period` gelesen werden (`cells[1]`, `children[1]`, `nth-child`, `firstElementChild`): solche Stellen auf `data-period` umstellen.

- [ ] **Step 4: Alle Tests grün** — volle Suite → grün

- [ ] **Step 5: Im Browser ansehen** — eine Zeile monatlich ausfüllen: Jährlich füllt sich rechts daneben; Tab springt von Monatlich nach Jährlich; Zwischensumme und Zusammenfassung stimmen mit dem Vorher überein (Ladeprüfung, Task 4). Screenshot 1280 und 375.

- [ ] **Step 6: Commit**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Monatlich vor Jaehrlich: die Jahressumme steht rechts, wo man sie liest"
```

### Task 4: Ladeprüfung, Nachziehen

- [ ] **Step 1: Ladeprüfung** — wie in `tests/budget_ladepruefung.js` beschrieben ausführen; das Ergebnis muss `tests/fixtures/budget/erwartet.json` gleichen (Vergleich nach `json.dumps(…, sort_keys=True)`). Abweichung = Fehler dieser Welle, nicht den Sollwert nachführen.
- [ ] **Step 2: Nachziehen** — `plans/2026-10-22-budget-offene-arbeiten.md`, Punkt 10: Zeile «✔ erledigt am <Datum>, siehe `specs/2026-10-26-budget-ausblick-reiter-spalte-design.md`, Teil 3» unter die Überschrift.
- [ ] **Step 3: Commit**

```bash
git add plans/2026-10-22-budget-offene-arbeiten.md
git commit -m "Punkt 10 als erledigt vermerkt"
```
