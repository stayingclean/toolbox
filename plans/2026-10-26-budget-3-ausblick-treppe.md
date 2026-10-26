# Welle 3 — Ausblick als Treppe: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unter den Stand-Zeilen der Zusammenfassung zeigt eine Treppe auf einer Zeitachse, was am Monatsende bleibt — vor heute grau, ab heute der Ausblick, Vorschläge ohne Datum in einem eigenen Streifen rechts.

**Architecture:** Die Werte liefert das bestehende `standVerlauf`. Neu im Rechenkern ist nur die Geometrie (Zeitspanne, Ticks, Lage eines Datums, senkrechter Bereich mit 0, Stufen). Gezeichnet wird handgeschriebenes SVG ausserhalb des Kerns, nach dem Muster von `zeichneWeg`, mit ResizeObserver. Ein drittes Druck-Häkchen steuert den Ausdruck.

**Tech Stack:** Vanilla JS, SVG, CSS inkl. `@media print` in `docs/budgetvorlage.html`; Kern-Tests über `tests/budget_treiber.mjs`, statische Tests über `_funktionsblock`/`_seite_text`.

**Spec:** `specs/2026-10-26-budget-ausblick-reiter-spalte-design.md`, Teil 1.

## Global Constraints

- Dateiformat v5 bleibt; das Häkchen wird nirgends gespeichert.
- Keine Bibliothek, kein CDN, kein Canvas — SVG wie «Der Weg».
- **Keine schrägen Linien**: die Treppe springt senkrecht, sonst nur waagrechte Stücke.
- Linker Anfang = erfasste Werte (Stand `heute` von `standVerlauf`), verstrichene Daten liegen links der Heute-Linie. Ein Datum gleich heute gilt als eingetreten (`ab <= heuteIso`).
- Die senkrechte Achse schliesst **immer 0** ein.
- Sichtbar genau dann, wenn die aktive Version eine Anpassung mit Betrag hat (dasselbe Tor wie `renderGrafik`).
- Häkchen `#chkPrintAusblick`, Text «Ausblick drucken», **nicht gesetzt**; Klasse `print-ausblick` auf `body`.
- Ort: im Abschnitt `.summary-section`, nach der Tabelle; im Druck ein Block mit der Zusammenfassung.
- Zeitangaben ohne Zeitzonen-Fallen: nur `Date.UTC` oder Zerlegen von `JJJJ-MM-TT`, nie `new Date('JJJJ-MM-TT')` mit lokaler Zeit.
- «Stand für Stand» in der Auswertung bleibt unverändert.
- Farben nur über `var(--color-*)`.
- Tests: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
- Voraussetzung: Welle 2 (`plans/2026-10-26-budget-2-spalte-total-weg.md`) ist auf diesem Branch committed.

## Review Focus

1. **Nur Vorschläge, kein Datum**: flache Linie ab heute über ein halbes Jahr, Streifen rechts — kein leeres oder kaputtes SVG.
2. **Überschuss wird zum Fehlbetrag** (Stufe unter 0): Nulllinie sichtbar, Achse reicht unter 0, Beschriftung nicht abgeschnitten.
3. **Zwei Daten im selben Monat** oder ein Datum Jahre entfernt: Beschriftungen überdecken sich nicht unlesbar, Ticks bleiben lesbar.
4. **Vorschau offen**: Klick auf eine Stufe wechselt den Stand, das Ziel des gezeigten Stands ist markiert; Escape/«Vorschau verlassen» nimmt die Markierung weg.
5. **Fensterbreite ändert sich** (auch durch Auf-/Zuklappen der Anleitung): neu gezeichnet, nicht gestreckt.

---

### Task 1: Geometrie im Rechenkern

**Files:**
- Modify: `docs/budgetvorlage.html` — Kern, nach `rasterSchritt`
- Test: `tests/test_budget.py`, Block `# --- Welle 3: Treppe ---`

**Interfaces:**
- Consumes: `standVerlauf` (liefert `[{key, ab, faellig, diffM, deltaM, …}]`, erstes Element `heute`, letztes evtl. `offen`), `rasterSchritt`, `istIsoDatum`, `istZahl`.
- Produces:
  - `monateDazu(iso, n) -> iso` — erster Tag des Monats, `n` Monate nach dem Monat von `iso`.
  - `treppenSpanne(verlauf, heuteIso) -> { von: iso, bis: iso }` — `von` = 1. des Monats von `min(frühestes ab, heute)`; `bis` = `monateDazu(max(letztes ab, heute), 3)`; mindestens 6 Monate: sonst `bis = monateDazu(von, 6)`.
  - `zeitAnteil(iso, von, bis) -> number` — 0…1 nach Tagen (über `Date.UTC`).
  - `treppenTicks(von, bis) -> [{ iso, text }]` — jeder Monatserste in `(von, bis)`; bei bis 18 Monaten jeder, bis 48 nur Jan/Apr/Jul/Okt, darüber nur Januar. `text`: `Jan Feb Mär Apr Mai Jun Jul Aug Sep Okt Nov Dez`, im Januar mit Jahr (`Jan 2027`).
  - `treppenBereich(werte) -> { basis, dach, schritt }` — `basis <= min(0, …werte)`, `dach >= max(0, …werte)`, beide Vielfache von `schritt = rasterSchritt(spanne * 1.12, 4)` mit `spanne = max(max−min, 1)`.
  - `treppenStufen(verlauf, heuteIso) -> { anfang: number, stufen: [{ key, ab, wert, delta, faellig }], offen: number|null }` — `anfang` = `diffM` von `heute`; je datiertem Stand eine Stufe, `delta` = `diffM` minus `diffM` des Stands davor; `offen` = `diffM` von `offen` oder `null`.
  - `treppenPunkte(treppe, von, bis) -> [[iso, wert], …]` — die Eckpunkte des Pfads: `[von, anfang]`, je Stufe `[ab, wert davor]` und `[ab, wert]`, zuletzt `[bis, letzter wert]`. Zwei aufeinanderfolgende Punkte unterscheiden sich in **genau einer** Koordinate — darauf beruht «keine Schrägen».

- [ ] **Step 1: Failing Tests**

`HEUTE` steht seit Welle 1 im Testmodul. Den Verlauf **nicht** auf Modulebene rechnen — dort liefe Node schon beim Sammeln, auch wo der `skipif` greifen soll.

```python
def _verlauf(anpassungen=ANPASSUNGEN):
    return kern("standVerlauf", SCHEMA, WERTE, anpassungen, HEUTE)

def test_monate_dazu():
    assert kern("monateDazu", "2026-11-15", 3) == "2027-02-01"
    assert kern("monateDazu", "2026-12-31", 1) == "2027-01-01"

def test_spanne_ab_heute_und_drei_monate_nach_dem_letzten_datum():
    assert kern("treppenSpanne", _verlauf(), HEUTE) == {"von": "2026-10-01", "bis": "2027-07-01"}

def test_spanne_beginnt_beim_verstrichenen_datum():
    a = dict(ANPASSUNGEN, handy={"jaehrlich": None, "monatlich": 0, "ab": "2026-08-01"})
    assert kern("treppenSpanne", _verlauf(a), HEUTE)["von"] == "2026-08-01"

def test_spanne_nur_vorschlaege_ist_ein_halbes_jahr():
    a = {"kasse": {"jaehrlich": None, "monatlich": 340, "ab": None}}
    assert kern("treppenSpanne", _verlauf(a), HEUTE) == {"von": "2026-10-01", "bis": "2027-04-01"}

def test_zeitanteil():
    assert kern("zeitAnteil", "2026-10-01", "2026-10-01", "2027-10-01") == 0
    assert kern("zeitAnteil", "2027-10-01", "2026-10-01", "2027-10-01") == 1
    assert abs(kern("zeitAnteil", "2027-04-01", "2026-10-01", "2027-10-01") - 182 / 365) < 1e-9

def test_ticks_monatlich_mit_jahr_im_januar():
    ticks = kern("treppenTicks", "2026-10-01", "2027-03-01")
    assert [t["text"] for t in ticks] == ["Nov", "Dez", "Jan 2027", "Feb"]

def test_ticks_bei_langer_spanne_nur_quartale():
    ticks = kern("treppenTicks", "2026-10-01", "2029-01-01")
    assert all(t["iso"][5:7] in ("01", "04", "07", "10") for t in ticks)

def test_bereich_schliesst_null_ein():
    b = kern("treppenBereich", [120, 138, 96, 246])
    assert b["basis"] == 0 and b["dach"] >= 246
    b = kern("treppenBereich", [80, -40])
    assert b["basis"] <= -40 and b["dach"] >= 80 and b["basis"] % b["schritt"] == 0

def test_stufen_aus_dem_verlauf():
    s = kern("treppenStufen", _verlauf(), HEUTE)
    assert [x["ab"] for x in s["stufen"]] == ["2027-01-01", "2027-04-01"]
    assert s["stufen"][0]["delta"] == pytest.approx(149)      # handy 60 + fitness 89 fallen weg
    assert s["stufen"][1]["delta"] == pytest.approx(14)       # hausrat 42 → 28
    assert s["offen"] == pytest.approx(s["stufen"][-1]["wert"] + 70)   # kasse 410 → 340
    assert s["anfang"] == pytest.approx(3800 - (60 + 89 + 42 + 410 + 3319))   # −120: Fehlbetrag

def test_treppe_hat_keine_schraegen():
    # Stände sind Sprünge (Entwurf vom 2026-10-23): je Schritt ändert sich Zeit ODER Wert.
    treppe = kern("treppenStufen", _verlauf(), HEUTE)
    punkte = kern("treppenPunkte", treppe, "2026-10-01", "2027-07-01")
    assert punkte[0] == ["2026-10-01", treppe["anfang"]] and punkte[-1][0] == "2027-07-01"
    for (t1, w1), (t2, w2) in zip(punkte, punkte[1:]):
        assert (t1 == t2) != (w1 == w2)
```

- [ ] **Step 2: Fehlschlag sehen**

Run: `... python -m pytest tests/test_budget.py -q -k "monate_dazu or spanne or zeitanteil or ticks or bereich or stufen or schraegen"` — Expected: FAIL «Unbekannte Funktion …»

- [ ] **Step 3: Sieben Funktionen im Kern schreiben**

Eine Stufe, deren Wert sich nicht ändert (Unterschied 0), erzeugt keine zwei gleichen Punkte hintereinander — sonst bräche die Prüfung «genau eine Koordinate»; sie bleibt aber als Stufe in `treppenStufen` (Punkt und Beschriftung «±0»).

Jede mit einem Kommentar, warum (z. B. bei `treppenBereich`: «anders als `achsenBereich` immer mit 0 — hier geht es um Überschuss oder Fehlbetrag»).

- [ ] **Step 4: Tests grün** — Run wie Step 2. Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Kern: Geometrie der Treppe (Spanne, Ticks, Bereich mit Null, Stufen)"
```

### Task 2: Treppe zeichnen, Klickziele, Neuzeichnen

**Files:**
- Modify: `docs/budgetvorlage.html` — Markup in `.summary-section` nach der Tabelle mit `#summaryStands`; neue DOM-Funktionen bei `renderGrafik`; Aufruf in `recomputeAll` direkt neben `renderGrafik(...)`; ResizeObserver neben dem von `#auswertungWeg`; Aufruf auch in `enterPreview`/`leavePreview` über `recomputeAll` (schon vorhanden); CSS bei `.grafik-titel`.
- Test: `tests/test_budget.py`

**Interfaces:**
- Consumes: Task 1; `standVerlauf`, `anpassungsGruppen`, `stichtagListe`, `rowAnzeigename`, `deltaAnzeige`, `formatComputed`, `datumAnzeige`, `enterPreview`, `heuteIso`, `state.previewStand`.
- Produces:
  - Markup: `<div class="ausblick" id="ausblickBlock" hidden>` mit `<h3 class="grafik-titel">Ausblick</h3>`, `<p class="grafik-untertitel">Was am Monatsende bleibt – vor heute grau, ab heute der Ausblick. Ein Klick zeigt das ganze Budget zu diesem Stand.</p>`, `<svg class="treppe" id="ausblickTreppe" role="img"></svg>`.
  - `renderAusblick(verlauf, anpassungen, werte)` — Tor, merkt die Daten, ruft `zeichneTreppe()`.
  - `zeichneTreppe()` — zeichnet aus den gemerkten Daten in der gemessenen Breite; `viewBox` = gemessene Breite × feste Höhe (220), `width:100%`, damit der Druck skaliert.

- [ ] **Step 1: Failing statische Tests**

```python
def test_ausblick_steht_in_der_zusammenfassung():
    text = _seite_text()
    abschnitt = text[text.index('class="section summary-section"'):]
    abschnitt = abschnitt[:abschnitt.index("</section>")]
    assert 'id="ausblickBlock"' in abschnitt and 'id="ausblickTreppe"' in abschnitt

def test_ausblick_hat_dasselbe_tor_wie_die_grafik():
    assert "anpassungHatBetrag" in _funktionsblock("renderAusblick")
    assert "renderAusblick(" in _funktionsblock("recomputeAll")

def test_treppe_zeichnet_aus_den_eckpunkten_des_kerns():
    block = _funktionsblock("zeichneTreppe")
    assert "treppenPunkte(" in block

def test_klickziele_sind_bedienbar():
    block = _funktionsblock("zeichneTreppe")
    assert "enterPreview(" in block and "tabindex" in block and "keydown" in block

def test_treppe_wird_bei_breitenaenderung_neu_gezeichnet():
    assert "observe($('#ausblickTreppe'))" in _seite_text()
```

- [ ] **Step 2: Fehlschlag sehen** — `... -k "ausblick or treppe or klickziele"` → FAIL

- [ ] **Step 3: Umsetzen**

Was `zeichneTreppe` zeichnet (Spec Teil 1, «Was gezeichnet wird»):
- Zeitskala links bis `breite − streifen`, wobei `streifen = 90` px nur bei `offen !== null`, sonst 0; Lücke 12 px davor.
- Waagrechte Rasterlinien bei jedem `schritt` von `basis` bis `dach`, Werte links daran; Nulllinie kräftiger (`--color-text-muted`, 1.5 px).
- Ticks unten mit `text`.
- Treppenpfad aus `treppenPunkte(...)`: `M` zum ersten Punkt, danach je Punkt `H` (Zeit geändert) oder `V` (Wert geändert) — kein `L`. Zwei Pfade: bis zur Heute-Linie in `--color-text-light`, ab dort in `--color-primary` (gleiche Punkte, per `clipPath` oder geteilt). Strichstärke 2.5, `stroke-linejoin: round`.
- Heute-Linie bei `x(heute)`, gestrichelt, Beschriftung «heute».
- Je Stufe ein Punkt (r 5), Klasse `ist-gut` bei `delta > 0`, `ist-schlecht` bei `< 0` (Farben `--color-success`/`--color-danger`); daneben `deltaAnzeige(delta)` und — aus `anpassungsGruppen` für dieses Datum — der Positionsname bei genau einer Position, sonst `"<n> Positionen"`; `<title>` mit allen Namen und ihren Monatsunterschieden.
- Anfangswert links (`formatComputed`), Endwert rechts am Ende der Zeitskala.
- Streifen: unten «ohne Datum», darin gestrichelte waagrechte Linie auf `y(offen)`, Beschriftung «mit Vorschlägen» und Wert.
- Klickziele: `<g class="treppe-ziel" tabindex="0" role="button" data-stand="…" aria-label="Vorschau: <standName>">` um jeden Punkt, um das gestrichelte Stück (`offen`) und um den Anfangswert (`heute`); `click` und `keydown` (Enter, Leertaste) → `enterPreview(key)`. Klasse `is-preview` am Ziel mit `key === state.previewStand`.
- Liegen zwei Beschriftungen näher als ihre Breite, die zweite unter die Linie setzen (abwechselnd oben/unten); der `<title>` trägt immer alles.
- `aria-label` am SVG: «Ausblick: heute <anfang> pro Monat, ab <letztes Datum> <letzter Wert>[, mit Vorschlägen <offen>]».

- [ ] **Step 4: Alle Tests grün** — Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q` → grün

- [ ] **Step 5: Im Browser prüfen**

`docs/budgetvorlage.html` im eingebauten Browser. Fälle der Reihe nach eintragen und jeweils Screenshot: (a) drei Daten in der Zukunft + ein Vorschlag, nach dem Muster der Skizze aus dem Gespräch: eine Ausgabe sinkt ab 01.12.2026, eine steigt ab 01.01.2027, der Lohn steigt ab 01.04.2027, eine weitere Ausgabe sinkt ohne Datum; (b) zusätzlich ein Datum 01.08.2026 → Teil links von heute grau; (c) nur ein Vorschlag; (d) eine Ausgabe so hoch, dass ein Stand unter 0 fällt; (e) zwei Daten im selben Monat. Klick und Tastatur auf ein Ziel öffnen die Vorschau, markiert ist das richtige Ziel. `resize_window` mobile und zurück: neu gezeichnet. `read_console_messages` ohne Fehler.

- [ ] **Step 6: Commit**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Ausblick: die Treppe unter der Zusammenfassung"
```

### Task 3: Druck-Häkchen «Ausblick drucken»

**Files:**
- Modify: `docs/budgetvorlage.html` — Werkzeugleiste neben `#chkPrintPrivateNote`; Init neben `applyPrintPrivateNote`; `@media print`.
- Test: `tests/test_budget.py`

**Interfaces:**
- Consumes: `#ausblickBlock` (Task 2).
- Produces: `#chkPrintAusblick` → `body.print-ausblick`.

- [ ] **Step 1: Failing statische Tests**

```python
def test_haekchen_ausblick_ist_nicht_vorgewaehlt():
    text = _seite_text()
    m = re.search(r'<input type="checkbox" id="chkPrintAusblick"[^>]*>', text)
    assert m and "checked" not in m.group(0)
    assert "Ausblick drucken" in text
    assert "classList.toggle('print-ausblick'" in text

def test_ausblick_druckt_nur_mit_haekchen():
    text = _seite_text()
    druck = text[text.index("@media print"):]
    assert re.search(r"body:not\(\.print-ausblick\)\s+#ausblickBlock\s*\{[^}]*display:\s*none", druck)
    assert re.search(r"#ausblickBlock\s*\{[^}]*print-color-adjust:\s*exact", druck)
```

- [ ] **Step 2: Fehlschlag sehen** — `... -k "haekchen_ausblick or druckt_nur"` → FAIL

- [ ] **Step 3: Umsetzen**

`<label class="print-toggle" title="Steuert nur den Ausdruck (Strg+P): den Ausblick unter der Zusammenfassung mitdrucken. Vorgewählt ist das nie.">` nach dem Muster der beiden anderen. Druckregel: `body:not(.print-ausblick) #ausblickBlock { display: none !important; }`, `#ausblickBlock { break-inside: avoid; -webkit-print-color-adjust: exact; print-color-adjust: exact; }`. Die Klickziele sind im Druck reine Grafik (kein Fokusring).

- [ ] **Step 4: Alle Tests grün** — volle Suite → grün

- [ ] **Step 5: Druckansicht prüfen**

Wie in Welle 2: `@media print` per `javascript_tool` auf `all` umschreiben; einmal ohne, einmal mit Häkchen. Mit Häkchen: Treppe steht unter den Stand-Zeilen, in Farbe, im selben Block. Screenshot.

- [ ] **Step 6: Ladeprüfung** — `tests/budget_ladepruefung.js` ausführen; Ergebnis muss `tests/fixtures/budget/erwartet.json` gleichen. Mit der v5-Datei die Treppe ansehen (verstrichenes Datum links grau, Vorschlag im Streifen) — Screenshot.

- [ ] **Step 6b: Nachziehen ausserhalb der Seite**

- `specs/2026-10-23-budget-grafik-und-vergleich-design.md`: Nachtrag am Ende «Nachtrag 2026-10-26: Zeitachse» — die Zeitachse ist mit dem Entscheid des Benutzers vom 2026-10-26 erlaubt; die Begründung «Stände sind Sprünge» bleibt und bindet die Treppe (keine schrägen Linien). Verweis auf den neuen Entwurf.
- `CLAUDE.md`, Abschnitt zu `tokens.css`: Budgetvorlage steht in `MIGRIERT`, nicht `AUSGENOMMEN` (Commit `57de428`); die Testzahl von `tests/test_budget.py` auf die dann gültige Zahl (`... pytest tests/test_budget.py -q` am Ende ablesen). **Vorher** prüfen, ob eine andere Session diese Stellen inzwischen schon geändert hat (`git log -p CLAUDE.md` seit `ed9e2ed`), und nur nachziehen, was noch falsch ist.

- [ ] **Step 7: Commit**

```bash
git add docs/budgetvorlage.html tests/test_budget.py specs/2026-10-23-budget-grafik-und-vergleich-design.md CLAUDE.md
git commit -m "Ausblick drucken: drittes Haekchen, Treppe im Block der Zusammenfassung"
```
