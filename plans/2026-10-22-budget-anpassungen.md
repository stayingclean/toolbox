# Anpassungen mit Stichtag und private Versionsnotiz — Umsetzungsplan

> **Für agentische Bearbeitung:** ERFORDERLICHER UNTER-SKILL: `superpowers:subagent-driven-development` (empfohlen) oder `superpowers:executing-plans`, Aufgabe für Aufgabe. Schritte sind als Kästchen (`- [ ]`) geführt.

**Ziel:** Jede Budget-Position bekommt eine Anpassung (Zielbetrag plus freiwilliges Datum); daraus rechnet die Seite Stände zu Stichtagen und zeigt «heute / ab 01.01.2027 / mit allen Vorschlägen» nebeneinander.

**Architektur:** Die Rechenlogik kommt als reiner, DOM-freier **Rechenkern** zwischen zwei Marker-Kommentare in `docs/budgetvorlage.html` und wird von Node aus der ausgelieferten Datei herausgeschnitten und geprüft — genau das Muster, das `tests/plakat_pdf_treiber.mjs` für den PDF-Kern schon verwendet. Alles Übrige (Felder, Reiter, Knöpfe, Druck) baut nur auf diesem Kern auf und wird über statische Prüfungen der Datei abgesichert.

**Tech Stack:** Eine einzelne HTML-Datei mit eingebettetem CSS und Vanilla-JS (kein Build, kein Generat). Tests: pytest, Node 24 als Treiber.

**Zugehöriger Entwurf:** `specs/2026-10-21-budget-anpassungen-design.md` — der Plan argumentiert aus ihm heraus, beide gehören zusammen gelesen.

**Branch:** `budget-anpassungen-stichtag` (der Entwurf ist dort bereits committet).

## Global Constraints

- **Das CSS bleibt in der Datei eingebettet.** Kein externes Stylesheet, keine Netzabfrage zur Laufzeit — die Seite muss per `file://` ohne Internet laufen (`CLAUDE.md`).
- **`docs/` wird öffentlich veröffentlicht.** Keine echten Personendaten in Beispielen, Platzhaltern oder Kommentaren.
- **Die Fusszeile mit Urheber-Credit und Kaffee-Link bleibt unangetastet.**
- **`docs/budgetvorlage.html` ist kein Generat** und wird direkt bearbeitet.
- **Echte Umlaute** in Kommentaren und sichtbarem Text dieser Datei (so ist sie heute durchgehend geschrieben). Bezeichner bleiben ASCII.
- **`leer` ist nicht `0`.** In `values` gilt weiterhin `|| 0`; in `adjustments` ist `null` leer und `0` ein gültiger Zielbetrag. Nirgends `|| 0` auf einen Anpassungsbetrag.
- **Zielbetrag, nicht Differenz.** Gespeichert wird, was die Position künftig kostet.
- **«heute» wendet keine einzige Anpassung an**, auch keine mit verstrichenem Datum.
- **Stände bauen aufeinander auf:** ein Stand enthält alles, was bis zu seinem Datum gilt.
- **Höchstens eine Anpassung je Position und Version.**
- **Datumsformat ist ISO** `YYYY-MM-DD`; alles andere gilt als kein Datum.
- **Tests:** `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q` — heute **286 bestanden**. Nach jedem Task muss diese Zahl gewachsen und kein Test rot sein.

## Review Focus

Fälle, die der Entwurf voraussetzt, ohne sie auszubuchstabieren. Jeder bekommt seinen Test in der Aufgabe, der der Code gehört:

1. **Speichern, während die Vorschau offen ist**, darf die erfassten Werte nicht durch gerechnete ersetzen — der einzige Fall im ganzen Vorhaben, der Daten vernichtet statt nur anders auszusehen. (Task 6)
2. **Anpassung mit Datum, aber ohne Betrag** wird nicht gerechnet und erzeugt keinen Stichtag; die Zeile zeigt, dass sie unvollständig ist. (Task 1, Task 3)
3. **Unlesbares Datum** aus einer von Hand bearbeiteten Datei (`"01.01.2027"`, `""`, `"demnächst"`) darf keinen Stand und kein `NaN` erzeugen. (Task 1)
4. **Anpassung auf einer Zeile, die das Schema nicht kennt** (ältere Datei, umbenannte `rowId`) wird übergangen statt angezeigt oder gerechnet. (Task 2)
5. **Zwei Anpassungen am selben Datum** ergeben einen Stand, dessen Beträge addiert sind — nicht zwei Stände. (Task 1)

---

### Task 1: Rechenkern und Testgerüst

Der Kern ist reine Rechnung ohne DOM. Alles Spätere hängt daran, also kommt er zuerst und wird als Einziges richtig durchgetestet.

**Files:**
- Modify: `docs/budgetvorlage.html` (neuer Block direkt nach `GROUP_LABELS`, ca. Z. 1934)
- Create: `tests/budget_treiber.mjs`
- Create: `tests/test_budget.py`

**Interfaces:**
- Produces, zwischen `/* == budget-kern:anfang == */` und `/* == budget-kern:ende == */`:
  - `anpassungBetrag(a) -> { jaehrlich: number, monatlich: number } | null`
  - `stichtagListe(adjustments, heuteIso) -> [{ key: string, ab: string|null, faellig: boolean }]`
  - `werteFuerStand(values, adjustments, standKey) -> values`
  - `summen(schema, values) -> { einnahmenY, einnahmenM, ausgabenY, ausgabenM, diffY, diffM }`

- [ ] **Step 1: Treiber und fehlschlagende Tests schreiben**

`tests/budget_treiber.mjs` schneidet den Kern aus der Datei und ruft eine Funktion daraus auf. Aufbau wie `tests/plakat_pdf_treiber.mjs`: Marker suchen, bei Fehlen mit Code 2 abbrechen, `new Function(kern + '\nreturn { anpassungBetrag, stichtagListe, werteFuerStand, summen };')()`. Aufruf: `node budget_treiber.mjs <html> <funktion> <argumenteAlsJson>`, Ergebnis als JSON auf stdout.

`tests/test_budget.py` mit `pytestmark = pytest.mark.skipif(shutil.which("node") is None, ...)` wie in `test_plakat.py`, einer Hilfsfunktion `kern(funktion, *args)` und diesem Beispielbudget als Modulkonstante:

```python
SCHEMA = {
    "einnahmen": [{"id": "lohn"}],
    "fix": [{"id": "handy"}, {"id": "fitness"}, {"id": "hausrat"},
            {"id": "kasse"}, {"id": "rest"}],
}
WERTE = {
    "lohn.monatlich": 3800, "handy.monatlich": 60, "fitness.monatlich": 89,
    "hausrat.monatlich": 42, "kasse.monatlich": 410, "rest.monatlich": 3319,
}
ANPASSUNGEN = {
    "handy":   {"jaehrlich": None, "monatlich": 0,   "ab": "2027-01-01"},
    "fitness": {"jaehrlich": None, "monatlich": 0,   "ab": "2027-01-01"},
    "hausrat": {"jaehrlich": None, "monatlich": 28,  "ab": "2027-04-01"},
    "kasse":   {"jaehrlich": None, "monatlich": 340, "ab": None},
}
```

Die Tests:

```python
def test_leer_ist_keine_anpassung():
    assert kern("anpassungBetrag", {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}) is None
    assert kern("anpassungBetrag", None) is None

def test_null_ist_ein_gueltiger_zielbetrag():
    assert kern("anpassungBetrag", {"jaehrlich": None, "monatlich": 0, "ab": None}) == {"jaehrlich": 0, "monatlich": 0}

def test_jaehrlich_gewinnt_sonst_monatlich_mal_zwoelf():
    assert kern("anpassungBetrag", {"jaehrlich": None, "monatlich": 50, "ab": None}) == {"jaehrlich": 600, "monatlich": 50}
    assert kern("anpassungBetrag", {"jaehrlich": 1200, "monatlich": None, "ab": None}) == {"jaehrlich": 1200, "monatlich": 100}

def test_staende_in_reihenfolge_mit_offen_am_schluss():
    liste = kern("stichtagListe", ANPASSUNGEN, "2026-10-22")
    assert [s["key"] for s in liste] == ["heute", "2027-01-01", "2027-04-01", "offen"]

def test_zwei_anpassungen_am_selben_datum_ergeben_einen_stand():
    assert sum(1 for s in kern("stichtagListe", ANPASSUNGEN, "2026-10-22") if s["key"] == "2027-01-01") == 1

def test_offen_fehlt_ohne_undatierte_anpassung():
    nur_datiert = {k: v for k, v in ANPASSUNGEN.items() if v["ab"]}
    assert "offen" not in [s["key"] for s in kern("stichtagListe", nur_datiert, "2026-10-22")]

def test_verstrichenes_datum_ist_faellig_aber_ein_eigener_stand():
    liste = kern("stichtagListe", ANPASSUNGEN, "2027-02-01")
    faellig = {s["key"]: s["faellig"] for s in liste}
    assert faellig == {"heute": False, "2027-01-01": True, "2027-04-01": False, "offen": False}

def test_unlesbares_datum_erzeugt_keinen_stand():
    for kaputt in ("01.01.2027", "", "demnaechst", "2027-13-99"):
        liste = kern("stichtagListe", {"handy": {"jaehrlich": None, "monatlich": 0, "ab": kaputt}}, "2026-10-22")
        assert [s["key"] for s in liste] == ["heute", "offen"]

def test_anpassung_ohne_betrag_zaehlt_nicht_mit():
    liste = kern("stichtagListe", {"handy": {"jaehrlich": None, "monatlich": None, "ab": "2027-01-01"}}, "2026-10-22")
    assert [s["key"] for s in liste] == ["heute"]

def test_heute_wendet_nichts_an():
    assert kern("werteFuerStand", WERTE, ANPASSUNGEN, "heute") == WERTE

def test_stand_setzt_beide_schluessel():
    neu = kern("werteFuerStand", WERTE, ANPASSUNGEN, "2027-01-01")
    assert neu["handy.monatlich"] == 0 and neu["handy.jaehrlich"] == 0
    assert neu["hausrat.monatlich"] == 42   # spaeteres Datum, noch nicht angewendet
    assert neu["kasse.monatlich"] == 410    # ohne Datum, nur im Stand "offen"

def test_die_vier_differenzen_aus_dem_entwurf():
    ergebnis = {}
    for key in ("heute", "2027-01-01", "2027-04-01", "offen"):
        werte = kern("werteFuerStand", WERTE, ANPASSUNGEN, key)
        ergebnis[key] = round(kern("summen", SCHEMA, werte)["diffM"], 2)
    assert ergebnis == {"heute": -120, "2027-01-01": 29, "2027-04-01": 43, "offen": 113}

def test_werte_fuer_stand_laesst_das_original_in_ruhe():
    kern("werteFuerStand", WERTE, ANPASSUNGEN, "offen")
    assert WERTE["handy.monatlich"] == 60
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests/test_budget.py -q`
Erwartet: FAIL, Treiber bricht mit «Die Marker des Rechenkerns stehen nicht in …» ab.

- [ ] **Step 3: Den Kern in `docs/budgetvorlage.html` schreiben**

Direkt nach `GROUP_LABELS` (vor `FILE_FORMAT_VERSION`), eingefasst von `/* == budget-kern:anfang == */` und `/* == budget-kern:ende == */`. Ein Kommentar über dem Anfangsmarker sagt, dass der Block von `tests/budget_treiber.mjs` herausgeschnitten wird und darum **ohne Zugriff auf `SCHEMA`, `state` oder das DOM** auskommen muss.

Die vier Signaturen stehen oben im Interfaces-Block. Festgelegt sind:

- Ein Datum ist gültig, wenn es `/^\d{4}-\d{2}-\d{2}$/` erfüllt **und** `Date.parse` darauf eine Zahl liefert. Vergleiche laufen als Zeichenkettenvergleich — ISO-Daten sortieren von selbst richtig.
- `anpassungBetrag` prüft mit `typeof === 'number' && isFinite(…)`, nicht auf Wahrheitswert.
- `summen` zählt die Gruppe `einnahmen` als Einnahme, jede andere als Ausgabe, und rechnet je Zeile wie `recomputeAll` heute: `y || (m * 12)` für jährlich, `m || (y / 12)` für monatlich.
- `werteFuerStand` gibt immer eine Kopie zurück.

- [ ] **Step 4: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Erwartet: PASS, mehr als 286 Tests.

- [ ] **Step 5: Committen**

```bash
git add docs/budgetvorlage.html tests/budget_treiber.mjs tests/test_budget.py
git commit -m "Budget: Rechenkern fuer Anpassungen und Stichtage, mit Node-Treiber"
```

---

### Task 2: Datenmodell, Dateiformat v5

**Files:**
- Modify: `docs/budgetvorlage.html` (`FILE_FORMAT_VERSION` Z. 1936, `SUPPORTED_VERSIONS` Z. 1939, `makeBlankVersion` ca. Z. 1978, `createVersion` ca. Z. 2119, `serialize` ca. Z. 2519, Laden ca. Z. 2628-2660, «Zurücksetzen»)
- Modify: `tests/test_budget.py`

**Interfaces:**
- Consumes: nichts aus Task 1.
- Produces: Versionsobjekte mit `adjustments: {}` und `privateNote: ''`. Neue Hilfsfunktion **ausserhalb** des Kerns: `bekannteAnpassungen(adjustments) -> adjustments` — wirft Einträge weg, deren `rowId` in `ROW_INDEX` fehlt. Jede Stelle, die Anpassungen liest, geht durch sie.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

Statische Prüfungen der ausgelieferten Datei, im Stil der Datei-Eigenschaftstests in `tests/test_plakat.py`:

```python
SEITE = ROOT / "docs" / "budgetvorlage.html"

def test_dateiformat_ist_fuenf():
    text = SEITE.read_text(encoding="utf-8")
    assert "const FILE_FORMAT_VERSION = 5;" in text
    assert re.search(r"SUPPORTED_VERSIONS = new Set\(\[1, 2, 3, 4, 5\]\)", text)

def test_neue_version_traegt_die_neuen_felder():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function makeBlankVersion"):][:700]
    assert "adjustments: {}" in block and "privateNote: ''" in block

def test_kein_oder_null_auf_einem_anpassungsbetrag():
    """`|| 0` wuerde aus jeder leeren Anpassung eine Nullsetzung machen."""
    text = SEITE.read_text(encoding="utf-8")
    assert not re.search(r"(adjustments|anpassung)\w*\.(jaehrlich|monatlich)\s*\|\|", text, re.I)
```

Dazu ein Kern-naher Test für `bekannteAnpassungen` — die Funktion steht ausserhalb des Kerns, ihr Verhalten lässt sich aber über `stichtagListe` prüfen, wenn der Aufrufer filtert. Stattdessen genügt hier die statische Zusicherung:

```python
def test_anpassungen_werden_gegen_das_schema_gefiltert():
    text = SEITE.read_text(encoding="utf-8")
    assert "function bekannteAnpassungen" in text
    # Jede Leseseite geht durch den Filter, keine greift roh auf .adjustments zu.
    roh = re.findall(r"(?<!function )\b\w+\.adjustments\b", text)
    assert len(roh) <= 4, f"ungefilterte Zugriffe: {roh}"
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests/test_budget.py -q`
Erwartet: FAIL bei den vier neuen Tests.

- [ ] **Step 3: Das Datenmodell erweitern**

- `FILE_FORMAT_VERSION` auf 5, `SUPPORTED_VERSIONS` um 5 ergänzt.
- `makeBlankVersion` gibt zusätzlich `adjustments: {}` und `privateNote: ''` zurück.
- `serialize` schreibt beide mit, als Kopie (`{ ...(v.adjustments || {}) }`).
- Beim Laden fehlender Felder: `{}` und `''`. v1–v3 laufen unverändert durch die bestehende Migration; sie erzeugt weiterhin «Original» und «Nach Reduktion» und **keine** Anpassungen.
- `createVersion` kopiert `adjustments` und `privateNote` **nicht** mit — gleich wie `comments` heute.
- «Zurücksetzen» löscht beide mit.
- `bekannteAnpassungen` neu neben `lookupRow`.

- [ ] **Step 4: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`

- [ ] **Step 5: Committen**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Budget: Anpassungen und private Notiz im Datenmodell, Dateiformat v5"
```

---

### Task 3: Die Zeile — Anpassungsfelder, Markierung, Einnahmen mit Aufklappbereich

**Files:**
- Modify: `docs/budgetvorlage.html` (`EXPANDABLE_GROUPS` Z. 2238, `makeCommentExpanderButton` Z. 2243, `makeCommentRow` Z. 2259, `hydrateFormFromActiveVersion`, `captureFormToActiveVersion`, `refreshExpanderUI` Z. 2325, CSS)
- Modify: `tests/test_budget.py`

**Interfaces:**
- Consumes: `anpassungBetrag` aus Task 1, `bekannteAnpassungen` aus Task 2.
- Produces: `rowHasAdjustment(rowId) -> boolean`; die Klasse `has-adjustment` auf `tr.budget-row` und auf der zugehörigen `tr.expander-row`.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

```python
def test_einnahmen_bekommen_den_aufklappbereich():
    text = SEITE.read_text(encoding="utf-8")
    assert re.search(r"EXPANDABLE_GROUPS = new Set\(\['einnahmen', \.\.\.AUSGABEN_GROUPS\]\)", text)

def test_panel_traegt_drei_anpassungsfelder():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function makeCommentRow"):][:3000]
    for feld in ("adj-jaehrlich", "adj-monatlich", "adj-ab"):
        assert feld in block, feld
    assert 'type="date"' in block

def test_zeile_mit_anpassung_bleibt_zugeklappt_markiert():
    text = SEITE.read_text(encoding="utf-8")
    assert "has-adjustment" in text
    assert re.search(r"\.budget-row\.has-adjustment\b", text)
    assert "--color-warning" in text[text.index(".budget-row.has-adjustment"):][:400]

def test_unvollstaendige_anpassung_wird_angezeigt():
    """Datum ohne Betrag rechnet nicht — die Zeile muss es sagen."""
    text = SEITE.read_text(encoding="utf-8")
    assert "adj-unvollstaendig" in text
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests/test_budget.py -q`

- [ ] **Step 3: Das Panel erweitern und die Einnahmen aufnehmen**

- `EXPANDABLE_GROUPS = new Set(['einnahmen', ...AUSGABEN_GROUPS])`. Der Kommentar darüber stimmt dann nicht mehr und wird mitgezogen: der Aufklappbereich trägt jetzt Anpassung **und** Kommentar, und beides ist bei den Einnahmen genauso nötig («neue Stelle ab 01.03.»).
- In `makeCommentRow`, **über** dem Kommentar-Label, ein Block «Anpassung dieser Position» mit drei Feldern: `adj-jaehrlich`, `adj-monatlich` (beide wie die Betragsfelder der Zeile, mit `parseAmount`/`formatComputed`), `adj-ab` als `<input type="date">`. Beschriftungen: «Neu jährlich», «Neu monatlich», «Gilt ab (darf leer bleiben)».
- Leeres Betragsfeld ergibt `null`, nicht `0`.
- Steht ein Datum, aber kein Betrag, erscheint im Panel der Hinweis `adj-unvollstaendig`: «Ohne Betrag wird diese Anpassung nicht gerechnet.»
- `hydrateFormFromActiveVersion` füllt die Felder; eine Zeile mit Anpassung wird aufgeklappt wie heute eine mit Kommentar.
- `captureFormToActiveVersion` schreibt sie zurück. Ein Eintrag ohne Betrag **und** ohne Datum wird gelöscht statt als leeres Objekt gespeichert.
- `rowHasAdjustment` setzt `has-adjustment` auf Zeile und Expander-Zeile.
- CSS: linker Balken `--color-warning`, Hintergrund `--color-warning-bg`, auch zugeklappt sichtbar.
- Der Chevron trägt heute schon eine Füllung für «hat Kommentar». Für «hat Anpassung» kommt ein **davon unterscheidbares** Zeichen dazu (etwa ein kleiner Punkt am Knopf); die Füllung bleibt dem Kommentar. `btn.title` nennt beides.
- Zu prüfen: die Einnahmen-Zeilen geben links erstmals Platz für den Chevron ab — Spaltenbreiten gegenlesen.

- [ ] **Step 4: Tests laufen lassen und die Seite im Browser anschauen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Dann `docs/budgetvorlage.html` öffnen: eine Einnahmen- und eine Ausgabenzeile aufklappen, Betrag und Datum eintragen, zuklappen — die Markierung muss stehen bleiben.

- [ ] **Step 5: Committen**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Budget: Anpassungsfelder in der Zeile, Einnahmen mit Aufklappbereich"
```

---

### Task 4: Die Stände in der Zusammenfassung

Hier wird die Kernzusage eingelöst. Sie hängt an keinem Reiter und an keiner Version.

**Files:**
- Modify: `docs/budgetvorlage.html` (Zusammenfassungs-Tabelle Z. 1630-1648, `recomputeAll` Z. 2455-2515)
- Modify: `tests/test_budget.py`

**Interfaces:**
- Consumes: `stichtagListe`, `werteFuerStand`, `summen` aus Task 1; `bekannteAnpassungen` aus Task 2.
- Produces: `tbody#summaryStands` unter `#differenceRow`, je Stand eine `tr.stand-row` mit `data-stand="<key>"`.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

```python
def test_zusammenfassung_hat_platz_fuer_die_staende():
    text = SEITE.read_text(encoding="utf-8")
    assert 'id="summaryStands"' in text
    assert text.index('id="differenceRow"') < text.index('id="summaryStands"')

def test_staende_haengen_nicht_am_versionsvergleich():
    """Der Vergleich ist bei einer Version ausgeblendet — die Staende nicht."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function recomputeAll"):][:6000]
    assert "isMultiVersion" not in block

def test_staende_kommen_aus_dem_kern():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function recomputeAll"):][:6000]
    for fn in ("stichtagListe", "werteFuerStand", "summen"):
        assert fn in block, fn
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

- [ ] **Step 3: `recomputeAll` um die Stände erweitern**

Am Ende von `recomputeAll`, nachdem `diffY`/`diffM` stehen: `stichtagListe(bekannteAnpassungen(aktiveAnpassungen), heuteIso())` holen, den Stand `heute` überspringen (seine Zahl steht schon in `#differenceRow`) und für jeden weiteren eine Zeile in `#summaryStands` schreiben — Beschriftung «ab 01.01.2027» bzw. «mit allen Vorschlägen», dazu jährlich und monatlich aus `summen(SCHEMA, werteFuerStand(...))`.

Ohne Anpassungen bleibt `#summaryStands` leer; die Tabelle sieht dann aus wie heute. Die Zeilen tragen dieselbe Positiv/Negativ-Einfärbung wie `#differenceRow`.

Das Datum kommt aus einer kleinen Hilfe `heuteIso()`, damit nur eine Stelle `new Date()` aufruft.

- [ ] **Step 4: Tests laufen lassen und das Beispiel aus dem Entwurf von Hand nachstellen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Dann im Browser die Zahlen aus `test_die_vier_differenzen_aus_dem_entwurf` eintippen: unten müssen −120.00, +29.00, +43.00 und +113.00 stehen.

- [ ] **Step 5: Committen**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Budget: Staende zu den Stichtagen in der Zusammenfassung"
```

---

### Task 5: Knopf «Anpassungen» in der Kopfleiste

**Files:**
- Modify: `docs/budgetvorlage.html` (Versionsleiste Z. 1383-1390, neues Panel, `renderVersionTabs`, CSS)
- Modify: `tests/test_budget.py`

**Interfaces:**
- Consumes: `stichtagListe`, `anpassungBetrag`, `werteFuerStand`, `summen`; `bekannteAnpassungen`; `setRowExpanded` (bestehend).
- Produces: `renderAdjustmentList()`; `springeZuZeile(rowId)`.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

```python
def test_knopf_nennt_die_anzahl():
    text = SEITE.read_text(encoding="utf-8")
    assert 'id="adjustmentsBtn"' in text and 'id="adjustmentsPanel"' in text

def test_gesprungen_wird_ueber_die_position_nicht_das_datum():
    """Mehrere Positionen koennen auf dasselbe Datum fallen."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function renderAdjustmentList"):][:4000]
    assert "springeZuZeile" in block
    assert re.search(r"springeZuZeile\([^)]*rowId", block)

def test_sprung_zieht_die_klebende_kopfleiste_ab():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function springeZuZeile"):][:800]
    assert "sticky-head" in block or "stickyHead" in block

def test_je_datumsgruppe_ein_versionsknopf():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function renderAdjustmentList"):][:4000]
    assert "Neue Version aus diesem Stand" in block
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

- [ ] **Step 3: Knopf und Panel bauen**

- In der Versionsleiste, rechts neben den Reitern: `#adjustmentsBtn` mit der Aufschrift «⏱ N Anpassungen». Erscheint nur, wenn `N > 0`.
- `#adjustmentsPanel` klappt darunter auf, gruppiert nach Datum (aufsteigend, «ohne Datum» zuletzt). Je Gruppe: Überschrift mit Datum, Anzahl Positionen und Summe der Deltas; ein verstrichenes Datum trägt zusätzlich «fällig seit …».
- Je Eintrag: Positionsname als Knopf, `alt → neu`, Delta. Einträge, deren `rowId` das Schema nicht kennt, erscheinen nicht (`bekannteAnpassungen`).
- `springeZuZeile(rowId)` klappt die Zeile auf (`setRowExpanded(rowId, true)`) und scrollt sie in den Blick. **Die Höhe von `.sticky-head` wird abgezogen**, sonst verschwindet die Zeile darunter.
- Je Datumsgruppe ein Knopf «Neue Version aus diesem Stand». Er öffnet das bestehende «Neue Version»-Modal mit vorausgefülltem Namen «Stand ab 01.01.2027». Die neue Version erhält:
  - `values` = `werteFuerStand(aktuelleWerte, anpassungen, standKey)`
  - `basedOn` = die Version, aus der gerechnet wurde (daran hängen «Δ vs. Basis», der Chevron-Tooltip und «Unterschiede pro Position»)
  - `adjustments` = alle Anpassungen mit späterem Datum **und** alle ohne Datum, unverändert; die bis zum Stichtag eingelösten entfallen
  - `comments` und `privateNote` leer, wie bei «Neue Version» heute
- Das Panel schliesst bei Klick ausserhalb und bei `Escape`.

- [ ] **Step 4: Tests laufen lassen und von Hand prüfen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Dann im Browser: zwei Positionen auf dasselbe Datum setzen, beide müssen einzeln anspringbar sein und je an der richtigen Zeile landen, nicht darunter. Danach «Neue Version aus diesem Stand» für das frühere Datum — die spätere Anpassung muss in der neuen Version noch stehen.

- [ ] **Step 5: Committen**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Budget: Anpassungsliste in der Kopfleiste mit Sprung und Versionsknopf"
```

---

### Task 6: Vorschau-Reiter mit Stand-Leiste und Schreibsperre

Die Schreibsperre ist der gefährlichste Teil des Vorhabens und darum der erste Schritt dieser Aufgabe.

**Files:**
- Modify: `docs/budgetvorlage.html` (`captureFormToActiveVersion` Z. 2055, `switchVersion` Z. 2108, Versionsleiste, `renderVersionsOverview` Z. 2747, CSS)
- Modify: `tests/test_budget.py`

**Interfaces:**
- Consumes: alles aus Task 1, Task 2 und `#adjustmentsBtn` aus Task 5.
- Produces: `state.previewStand` (`null` oder ein Stand-Key); `enterPreview(standKey)`, `leavePreview()`.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

```python
def test_vorschau_schreibt_nicht_zurueck():
    """Sonst ersetzt der naechste Aufruf die erfassten Werte durch gerechnete."""
    text = SEITE.read_text(encoding="utf-8")
    ab = text.index("function captureFormToActiveVersion")
    assert "if (state.previewStand) return;" in text[ab:ab + 500], \
        "die Sperre fehlt am Anfang von captureFormToActiveVersion"

def test_vorschau_ist_kein_versionsreiter():
    """In derselben tablist behauptete sie, die aktive Version sei inaktiv."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index('id="previewBtn"')-400:text.index('id="previewBtn"')+400]
    assert 'role="tab"' not in block

def test_vorschau_sperrt_die_eingabefelder():
    text = SEITE.read_text(encoding="utf-8")
    assert "previewStand" in text and re.search(r"\.disabled = ", text)

def test_speichern_laeuft_in_der_vorschau_normal_weiter():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function serialize"):][:900]
    assert "previewStand" not in block, "serialize darf nicht auf die Vorschau reagieren"
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

- [ ] **Step 3: Sperre zuerst, dann die Anzeige**

1. `state.previewStand = null` neben `activeVersionId`.
2. **Ganz am Anfang** von `captureFormToActiveVersion`: `if (state.previewStand) return;`. Der Kommentar darüber sagt warum — die Funktion wird aus `serialize`, `renderVersionsOverview` und den Eingabe-Handlern gerufen, und jeder dieser Aufrufe würde die erfassten Werte überschreiben.
3. `enterPreview(standKey)` ruft **vorher einmal** `captureFormToActiveVersion()` (solange `previewStand` noch `null` ist), setzt dann `previewStand` und füllt das Formular mit `werteFuerStand(...)`.
4. Alle Betrags- und Anpassungsfelder werden `disabled`, ein Hinweis sagt, dass hier nicht erfasst wird.
5. `leavePreview()` setzt `previewStand` auf `null` und füllt aus der Version neu. Wege hinaus: der Vorschau-Knopf selbst, ein Versionsreiter, `Escape`.
6. `switchVersion` ruft `leavePreview()` als Erstes.
7. **`serialize` bleibt unverändert** — es speichert die dahinterliegende Version, und der gerechnete Stand steht ohnehin nicht in der Datei.
8. `#previewBtn` steht neben `#adjustmentsBtn` in der Versionsleiste, **ausserhalb** der `role="tablist"`, gestrichelt umrandet. Er erscheint nur, wenn Anpassungen vorliegen.
9. Die Stand-Leiste erscheint nur, solange die Vorschau offen ist. «heute» darin ist das gesperrte Abbild der Version, kein Verlassen.
10. In `renderVersionsOverview`: wo die Übersicht ohnehin sichtbar ist (ab zwei Versionen), kommen die Stände als abgesetzte Zeilen dazu. Das `isMultiVersion`-Gate bleibt, wie es ist.

- [ ] **Step 4: Tests laufen lassen und den gefährlichen Fall von Hand prüfen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Dann im Browser, in dieser Reihenfolge: Budget erfassen, speichern, Vorschau öffnen, einen Stichtag wählen, **nochmals speichern**, Vorschau verlassen. Die erfassten Beträge müssen unverändert dastehen. Danach die Datei neu öffnen und gegenprüfen.

- [ ] **Step 5: Committen**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Budget: Vorschau-Reiter mit Stand-Leiste, ohne Rueckschreiben"
```

---

### Task 7: Private Notiz, Druck und die Hinweistexte

**Files:**
- Modify: `docs/budgetvorlage.html` (Werkzeugleiste Z. 1351-1354, Kopf des Budgets, `.info-box` Z. 1398-1402, Druck-CSS Z. 933-1030, `beforeprint` Z. 3328)
- Modify: `tests/test_budget.py`

**Interfaces:**
- Consumes: `privateNote` aus Task 2, `state.previewStand` aus Task 6.
- Produces: `#privateNote`, `#chkPrintPrivateNote`, `#printStandMarker`.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

```python
def test_private_notiz_druckt_nur_mit_haekchen():
    text = SEITE.read_text(encoding="utf-8")
    assert 'id="chkPrintPrivateNote"' in text
    kasten = text[text.index('id="chkPrintPrivateNote"')-200:text.index('id="chkPrintPrivateNote"')+200]
    assert "checked" not in kasten, "die private Notiz darf nicht vorgewaehlt mitdrucken"
    assert "body.print-private-note" in text

def test_private_notiz_steht_in_der_datei():
    """Ausdruecklich so entschieden — geschuetzt ist der Druck, nicht die Datei."""
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("function serialize"):][:900]
    assert "privateNote" in block

def test_gerechneter_stand_wird_im_ausdruck_gekennzeichnet():
    text = SEITE.read_text(encoding="utf-8")
    assert 'id="printStandMarker"' in text
    assert "gerechnet, nicht erfasst" in text

def test_druckmarkierung_kennt_auch_anpassungen():
    text = SEITE.read_text(encoding="utf-8")
    block = text[text.index("beforeprint"):][:900]
    assert "has-comment" in block and "has-adjustment" in block

def test_infobox_verweist_nicht_mehr_nur_auf_versionen():
    text = SEITE.read_text(encoding="utf-8")
    assert "modellieren Sie über <strong>weitere Budget-Versionen</strong>" not in text
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

- [ ] **Step 3: Notiz, Druckregeln und Texte**

- `#privateNote` als mehrzeiliges Feld beim Kopf des Budgets, sichtbar als privat gekennzeichnet, mit Hinweis «wird nicht mitgedruckt». Es gehört zur **aktiven Version** und wechselt mit ihr (füllen in `hydrateFormFromActiveVersion`, zurückschreiben in `captureFormToActiveVersion` — und damit automatisch von der Sperre aus Task 6 erfasst).
- `#chkPrintPrivateNote` in der Werkzeugleiste neben «Kommentare drucken», **ohne `checked`**, schaltet `body.print-private-note`. Im Druck-CSS ist `#privateNote` sonst `display: none`.
- Die Anpassungsfelder im Panel drucken mit der bestehenden Checkbox «Kommentare drucken» mit; die Zeilenmarkierung `has-adjustment` druckt nur dann ebenfalls, sonst stünde eine gelbe Zeile ohne Erklärung auf dem Blatt.
- `beforeprint` setzt neben `has-comment` auch `has-adjustment`.
- `#printStandMarker` im Blattkopf, nur im Ausdruck sichtbar und nur, wenn `state.previewStand` gesetzt und nicht `heute` ist: «Stand ab 01.01.2027 — gerechnet, nicht erfasst».
- Die neuen Stand-Zeilen der Zusammenfassung drucken mit.
- Der Text der `.info-box` wird nachgezogen: Anpassungen stehen jetzt in der Zeile, Versionen sind für den grundsätzlich anderen Haushalt da.

- [ ] **Step 4: Tests laufen lassen und vier Ausdrücke in der Druckvorschau ansehen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Dann Strg+P je einmal: ohne Häkchen (keine Notiz, keine Anpassungen), mit «Kommentare drucken», mit «Private Notiz drucken», und einmal aus einem offenen Stand heraus — dort muss die Kennzeichnung oben stehen.

- [ ] **Step 5: Committen**

```bash
git add docs/budgetvorlage.html tests/test_budget.py
git commit -m "Budget: private Versionsnotiz, Druckregeln und Hinweistexte"
```

---

## Was dieser Plan bewusst offen lässt

- Markup und Feinschliff von Panel, Knopf und Stand-Leiste.
- Ob die Vorschau das bestehende Formular umbefüllt oder eine eigene Darstellung baut — die drei Sperr-Regeln aus Task 6 gelten für beide Wege.
- Das Zeichen am Chevron für «hat Anpassung».
- Die genaue Darstellung der Stände in der Versions-Übersicht.
