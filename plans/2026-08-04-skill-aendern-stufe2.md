# Bestehende Skills ergänzen — Ausbaustufe 2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Besucher können über einen zweiten Reiter auf `docs/skill-vorschlagen.html` einen **bestehenden** Skill ergänzen; die Änderung läuft denselben Weg wie ein neuer Vorschlag und ersetzt nach der Freigabe die vorhandene Zeile in `skills_daten.xlsx`.

**Architecture:** Der bestehende Weg bleibt unverändert: Formular → Cloudflare Worker → Issue → `vorschlaege.bat` → Excel → Build. Neu ist eine zweite Einreichungsart `aenderung`, die überall dort abzweigt, wo bisher `neu` fest verdrahtet war. Der geänderte Skill wird über **Stufe + Kategorie + ursprünglicher Titel** wiedergefunden; Stufe und Kategorie sind dabei nicht änderbar, damit dieser Schlüssel stabil bleibt. Die Excel bekommt eine zweite Namensspalte `Ergaenzt`, sodass beide Beitragenden genannt werden.

**Tech Stack:** unverändert — Python 3.11 + openpyxl (Aufruf über `uv`), pytest, JavaScript (Cloudflare Worker, ESM) mit `node --test`, `gh` CLI, statisches HTML/CSS/JS ohne Framework.

## Global Constraints

- **Sprache:** Alle sichtbaren Texte, Kommentare, Docstrings und Commit-Meldungen auf Deutsch, Schweizer Schreibweise (`ss` statt `ß`, **nie** `ß`).
- **Zwei Entscheidungen des Auftraggebers, nicht verhandelbar:**
  1. Eine Änderung darf **Emoji, Titel, Beschreibung und Tipp** ändern. **Stufe und Kategorie bleiben.** Der Skill wird nicht verschoben.
  2. **Beide Beitragenden werden genannt:** der ursprüngliche in `Von`, der ergänzende in der neuen Spalte `Ergaenzt`. Eine Änderung überschreibt `Von` nie.
- **`validate.js` ist die Prüfinstanz für Einreichungen über das Formular**; `tools/vorschlaege_holen.py` prüft zusätzlich Herkunft und Felder, weil Issues auch von Hand eröffnet werden können. Beide Regelwerke müssen deckungsgleich bleiben.
- **Feldgrenzen (unverändert):** Emoji genau **ein** Graphem-Cluster und höchstens 16 Codepunkte, Titel 60, Beschreibung 300, Tipp 200, Name 30 Zeichen. Kein `http`, keine `<!--`/`-->`, keine `<`/`>`.
- **Anonymität:** Weder IP-Adresse noch Browserkennung dürfen ins Issue, in die Antwort an den Browser oder in ein Log gelangen.
- **Generierte Dateien** (`docs/skillsliste.html`, `docs/skill-vorschlagen.html`, `docs/skills-daten.json`) werden **nie** von Hand bearbeitet — Änderungen gehen in `template.html` bzw. `template-vorschlag.html`, danach `uv run build.py`.
- **Ausgabekonvention:** HTML-Erzeugnisse UTF-8 **mit** BOM, `skills-daten.json` **ohne** BOM.
- **Fusszeile:** Jede Seite in `docs/` trägt Urheber-Credit **und** Kaffee-Link nach der Konvention in `CLAUDE.md`.
- **Keine neuen Abhängigkeiten.** Python: nur `openpyxl` und Standardbibliothek. Worker: keine, nur der eingebaute Testläufer von Node.
- **Kein automatischer Push, kein automatisches Deploy.** Beides macht der Mensch.

**Testbefehle:**

```bash
uv run --with pytest --with openpyxl pytest tests -v     # Python, aktuell 44 grün
(cd worker && node --test)                                # Worker, aktuell 35 grün
```

**Ausgangsstand:** `master` = `fcfb248`, Zweig `feature/formulare-toolbox`, Arbeitsverzeichnis `C:\workspace\eraschle\.worktrees\formulare-toolbox`.

---

### Task 1: Spalte `Ergaenzt` durch die Datenkette

**Files:**
- Modify: `build.py` (`load_data`, `optional_header`)
- Modify: `template.html` (CSS neben `.modal-von`, Modal-Rumpf, `sObj`, `openModal`)
- Modify: `tools/seed_excel.py` (Kopfzeile, Anhänge-Block, `style_sheet`)
- Modify: `skills_daten.xlsx` (achte Spalte, einmalig per Skript)
- Modify: `tests/test_build.py`

**Interfaces:**
- Consumes: `build.read_rows(ws, expected_header, optional_header=())` aus Ausbaustufe 1
- Produces: Jeder Skill in `build.load_data()` hat neu den Schlüssel `"erg"` (String, leer wenn niemand ergänzt hat). Der Detail-Dialog zeigt eine Zeile, die beide Namen nennt.

- [ ] **Step 1: Fehlschlagende Tests schreiben**

An `tests/test_build.py` anhängen:

```python
def test_erg_wird_gelesen_wenn_spalte_vorhanden(mappe, monkeypatch):
    pfad = mappe(SKILLS_HEADER + ["Von", "Ergaenzt"], [SKILLS_ROW + ["Max", "Lea"]])
    monkeypatch.setattr(build, "XLSX", pfad)
    daten = build.load_data()
    skill = daten["hoch"]["kategorien"][0]["skills"][0]
    assert skill["von"] == "Max"
    assert skill["erg"] == "Lea"


def test_erg_ist_leer_wenn_spalte_fehlt(mappe, monkeypatch):
    pfad = mappe(SKILLS_HEADER, [SKILLS_ROW])
    monkeypatch.setattr(build, "XLSX", pfad)
    skill = build.load_data()["hoch"]["kategorien"][0]["skills"][0]
    assert skill["erg"] == ""


def test_vorlage_nennt_beide_beitragenden():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    assert 'id="m-von"' in vorlage
    assert "s.erg" in vorlage
    assert "ergänzt von" in vorlage
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl pytest tests/test_build.py -k "erg or beide" -v`
Expected: FAIL — `KeyError: 'erg'` in den ersten beiden, `assert "s.erg" in vorlage` im dritten.

- [ ] **Step 3: `build.py` liest die Spalte**

Den Aufruf für das Skills-Blatt erweitern:

```python
    skill_rows = read_rows(
        get_sheet(wb, "Skills"),
        ["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp"],
        optional_header=["Von", "Ergaenzt"],
    )
```

und beim Aufbau von `skills_by` das Feld ergänzen:

```python
                "von": rec["Von"],
                "erg": rec["Ergaenzt"],
```

- [ ] **Step 4: Detail-Dialog nennt beide**

In `template.html` das CSS neben `.modal-von` unverändert lassen und die Anzeige-Logik in `openModal` ersetzen. Die bestehende Zeile

```javascript
  if(s.von){ mVon.textContent='Vorgeschlagen von '+s.von; mVon.hidden=false; }
  else { mVon.textContent=''; mVon.hidden=true; }
```

wird zu:

```javascript
  var teile=[];
  if(s.von){ teile.push('Vorgeschlagen von '+s.von); }
  if(s.erg){ teile.push('ergänzt von '+s.erg); }
  if(teile.length){ mVon.textContent=teile.join(' · '); mVon.hidden=false; }
  else { mVon.textContent=''; mVon.hidden=true; }
```

Und im Kartenobjekt `sObj` das Feld mitgeben:

```javascript
      var sObj={lv:S.level,kid:k.id,klbl:k.label,idx:cardIdx,e:s.e,t:s.t,b:s.b,tip:s.tip,von:s.von,erg:s.erg};
```

- [ ] **Step 5: `tools/seed_excel.py` schreibt die Spalte mit**

Kopfzeile:

```python
    ws.append(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp", "Von", "Ergaenzt"])
```

Anhänge-Block um einen Wert erweitern:

```python
                        s.get("von", ""),
                        s.get("erg", ""),
```

und die Formatierung auf acht Spalten:

```python
    style_sheet(ws, 8, [9, 18, 8, 26, 60, 55, 16, 16], emoji_col=3)
```

- [ ] **Step 6: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: PASS, 47 Tests (44 bestehende + 3 neue).

- [ ] **Step 7: Sicherungskopie und Spalte in der echten Excel**

```bash
cp skills_daten.xlsx skills_daten.xlsx.bak
```

```bash
uv run --with openpyxl python - <<'PY'
import openpyxl
from copy import copy
from openpyxl.utils import get_column_letter
wb = openpyxl.load_workbook("skills_daten.xlsx")
ws = wb["Skills"]
kopf = [(c.value or "").strip() for c in ws[1]]
if "Ergaenzt" in kopf:
    print("Spalte 'Ergaenzt' ist bereits vorhanden - nichts zu tun.")
else:
    spalte = len(kopf) + 1
    quelle = ws.cell(row=1, column=spalte - 1)   # Kopfzelle 'Von' als Muster
    ziel = ws.cell(row=1, column=spalte, value="Ergaenzt")
    ziel.fill, ziel.font, ziel.alignment = copy(quelle.fill), copy(quelle.font), copy(quelle.alignment)
    ws.column_dimensions[get_column_letter(spalte)].width = 16
    ws.auto_filter.ref = f"A1:{get_column_letter(spalte)}{ws.max_row}"
    wb.save("skills_daten.xlsx")
    print(f"Spalte 'Ergaenzt' als Spalte {spalte} ergaenzt, Filter {ws.auto_filter.ref}.")
PY
```

Expected: `Spalte 'Ergaenzt' als Spalte 8 ergaenzt, Filter A1:H101.`

- [ ] **Step 8: Excel programmatisch prüfen**

```bash
uv run --with openpyxl python -c "
import openpyxl
ws = openpyxl.load_workbook('skills_daten.xlsx')['Skills']
print('Kopf:', [c.value for c in ws[1]])
print('Zeilen:', ws.max_row, 'Filter:', ws.auto_filter.ref, 'Dropdown:', [str(d.sqref) for d in ws.data_validations.dataValidation])
for sp in ('G1','H1'):
    c = ws[sp]; print(sp, c.fill.fgColor.rgb, c.font.bold, c.alignment.horizontal)
"
```

Expected: acht Spalten mit `Ergaenzt` als letzter, 101 Zeilen, Filter `A1:H101`, Dropdown `A2:A101`, und `H1` trägt dieselbe Füllung, Fettschrift und Zentrierung wie `G1`.

Weicht etwas ab: `cp skills_daten.xlsx.bak skills_daten.xlsx` und als DONE_WITH_CONCERNS melden statt an der Formatierung zu basteln.

- [ ] **Step 9: Build prüfen und Sicherungskopie löschen**

Run: `uv run build.py`
Expected: drei ✅-Zeilen, `Skills: 100`.

Run: `git status --short`
Expected: nur `skills_daten.xlsx`, `template.html`, `build.py`, `tools/seed_excel.py`, `tests/test_build.py` und die drei erzeugten Dateien in `docs/`.

```bash
rm skills_daten.xlsx.bak
```

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "Spalte Ergaenzt durch die Datenkette, Detail-Dialog nennt beide Beitragenden"
```

---

### Task 2: Prüflogik für Änderungen im Worker

**Files:**
- Modify: `worker/validate.js`
- Modify: `worker/validate.test.js`

**Interfaces:**
- Consumes: `GRENZEN`, `pruefeVorschlag(eingabe, daten)` aus Ausbaustufe 1 — beide bleiben unverändert
- Produces: `pruefeAenderung(eingabe, daten) -> {ok: true, wert: {...}} | {ok: false, fehler: "…"}`
  - `eingabe`: `{stufe, kategorie, original, emoji, titel, beschreibung, tipp, erg, falle}`
  - `wert` bei Erfolg: `{art: "aenderung", stufe, kategorie, original, emoji, titel, beschreibung, tipp, erg}` — alle Werte getrimmt

- [ ] **Step 1: Fehlschlagende Tests schreiben**

An `worker/validate.test.js` anhängen. Die Testdaten brauchen einen Skill mit Inhalt — die bestehende Konstante `DATEN` hat eine leere `skills`-Liste, darum hier eine eigene:

```javascript
const DATEN_MIT_SKILL = {
  hoch: {
    kategorien: [
      {
        id: "ablenkung",
        label: "Ablenkung",
        skills: [
          { e: "🎧", t: "Musik hören", b: "Ein Lied auflegen.", tip: "", von: "Max", erg: "" },
        ],
      },
    ],
  },
  mittel: { kategorien: [] },
  tief: { kategorien: [] },
};

const AENDERUNG = {
  stufe: "Hoch",
  kategorie: "Ablenkung",
  original: "Musik hören",
  emoji: "🎧",
  titel: "Musik bewusst hören",
  beschreibung: "Ein Lied aussuchen und nur darauf achten.",
  tipp: "Kopfhörer bereitlegen",
  erg: "Lea",
  falle: "",
};

test("nimmt eine gültige Änderung an", () => {
  const r = pruefeAenderung(AENDERUNG, DATEN_MIT_SKILL);
  assert.equal(r.ok, true);
  assert.equal(r.wert.art, "aenderung");
  assert.equal(r.wert.original, "Musik hören");
  assert.equal(r.wert.titel, "Musik bewusst hören");
  assert.equal(r.wert.erg, "Lea");
});

test("liefert nur die erlaubten Schlüssel zurück", () => {
  const r = pruefeAenderung({ ...AENDERUNG, art: "neu", extra: "x" }, DATEN_MIT_SKILL);
  assert.deepEqual(
    Object.keys(r.wert).sort(),
    ["art", "beschreibung", "emoji", "erg", "kategorie", "original", "stufe", "tipp", "titel"].sort()
  );
  assert.equal(r.wert.art, "aenderung");
});

test("lehnt eine Änderung an einem unbekannten Skill ab", () => {
  const r = pruefeAenderung({ ...AENDERUNG, original: "Gibt es nicht" }, DATEN_MIT_SKILL);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /nicht mehr|unbekannt/i);
});

test("lehnt eine Änderung in unbekannter Kategorie ab", () => {
  const r = pruefeAenderung({ ...AENDERUNG, kategorie: "Erfunden" }, DATEN_MIT_SKILL);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Kategorie/);
});

test("lehnt eine Änderung mit ausgefüllter Falle ab", () => {
  const r = pruefeAenderung({ ...AENDERUNG, falle: "bot" }, DATEN_MIT_SKILL);
  assert.equal(r.ok, false);
});

test("wendet dieselben Feldregeln an wie bei einem neuen Skill", () => {
  for (const [feld, wert, muster] of [
    ["titel", "x".repeat(61), /Titel/],
    ["beschreibung", "x".repeat(301), /Beschreibung/],
    ["erg", "x".repeat(31), /Name/],
    ["titel", "siehe http://spam.example", /Link/],
    ["beschreibung", "a <!-- b", /Kommentarzeichen/],
    ["tipp", "a < b", /Klammern/],
  ]) {
    const r = pruefeAenderung({ ...AENDERUNG, [feld]: wert }, DATEN_MIT_SKILL);
    assert.equal(r.ok, false, `${feld} muss abgelehnt werden`);
    assert.match(r.fehler, muster);
  }
});

test("verlangt genau ein Emoji auch bei einer Änderung", () => {
  assert.equal(pruefeAenderung({ ...AENDERUNG, emoji: "🧘‍♀️" }, DATEN_MIT_SKILL).ok, true);
  assert.equal(pruefeAenderung({ ...AENDERUNG, emoji: "ab" }, DATEN_MIT_SKILL).ok, false);
});

test("der Name des Ergänzenden ist freiwillig", () => {
  const r = pruefeAenderung({ ...AENDERUNG, erg: "" }, DATEN_MIT_SKILL);
  assert.equal(r.ok, true);
  assert.equal(r.wert.erg, "");
});
```

Und die Import-Zeile oben in der Datei erweitern:

```javascript
import { pruefeVorschlag, pruefeAenderung } from "./validate.js";
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `(cd worker && node --test)`
Expected: FAIL — `pruefeAenderung is not a function`.

- [ ] **Step 3: Gemeinsame Feldprüfung herausziehen**

In `worker/validate.js` die Feldregeln, die `pruefeVorschlag` heute inline anwendet, in eine eigene Funktion heben, damit beide Einreichungsarten dieselbe Wahrheit benutzen. Neben den bestehenden Hilfsfunktionen einfügen:

```javascript
/**
 * Prueft die inhaltlichen Feldregeln, die fuer neue Skills und fuer Aenderungen
 * gleichermassen gelten: Pflichtfelder, Laengen, genau ein Emoji, keine Links,
 * keine Kommentarzeichen, keine spitzen Klammern.
 *
 * `namensfeld` ist der Schluessel des freiwilligen Namens – bei einem neuen
 * Skill `von`, bei einer Aenderung `erg`.
 * Liefert null, wenn alles stimmt, sonst die Fehlermeldung.
 */
function feldregeln(wert, namensfeld) {
  for (const feld of ["emoji", "titel", "beschreibung"]) {
    if (!wert[feld]) {
      return `Pflichtfeld fehlt: ${FELDNAMEN[feld]}.`;
    }
  }
  if (
    Array.from(wert.emoji).length > EMOJI_CODEPUNKT_GRENZE ||
    grapheme(wert.emoji) !== 1
  ) {
    return "Bitte genau ein Emoji angeben.";
  }
  for (const [feld, grenze] of Object.entries(GRENZEN)) {
    const inhalt = feld === "von" ? wert[namensfeld] : wert[feld];
    if (inhalt !== undefined && Array.from(inhalt).length > grenze) {
      const name = feld === "von" ? FELDNAMEN.von : FELDNAMEN[feld];
      return `Zu lang: ${name} (max. ${grenze} Zeichen).`;
    }
  }
  const textfelder = ["titel", "beschreibung", "tipp", namensfeld];
  for (const feld of textfelder) {
    if ((wert[feld] || "").toLowerCase().includes("http")) {
      return "Links sind nicht erlaubt.";
    }
  }
  for (const feld of [...textfelder, "emoji"]) {
    const inhalt = wert[feld] || "";
    if (inhalt.includes("<!--") || inhalt.includes("-->")) {
      return "Kommentarzeichen sind nicht erlaubt.";
    }
    if (inhalt.includes("<") || inhalt.includes(">")) {
      return "Spitze Klammern sind nicht erlaubt.";
    }
  }
  return null;
}
```

`pruefeVorschlag` so umbauen, dass es diese Funktion benutzt statt seiner bisherigen Schleifen — das Verhalten bleibt identisch, die bestehenden Tests müssen unverändert grün bleiben:

```javascript
  const fehler = feldregeln(wert, "von");
  if (fehler) {
    return { ok: false, fehler };
  }
  return { ok: true, wert };
```

- [ ] **Step 4: `pruefeAenderung` schreiben**

Darunter einfügen:

```javascript
/**
 * Prueft eine Aenderung an einem bestehenden Skill.
 *
 * Stufe und Kategorie sind NICHT aenderbar – sie bilden zusammen mit dem
 * urspruenglichen Titel den Schluessel, ueber den das Uebernahme-Skript die
 * Zeile in der Excel wiederfindet.
 */
export function pruefeAenderung(eingabe, daten) {
  const roh = eingabe && typeof eingabe === "object" ? eingabe : {};

  if (text(roh.falle)) {
    return { ok: false, fehler: "Ungültige Einreichung." };
  }

  const stufe = text(roh.stufe);
  const schluessel = STUFEN[stufe];
  if (!schluessel || !daten[schluessel]) {
    return { ok: false, fehler: "Unbekannte Stufe." };
  }

  const kategorie = text(roh.kategorie);
  const kat = (daten[schluessel].kategorien || []).find(
    (k) => k.label === kategorie
  );
  if (!kat) {
    return { ok: false, fehler: "Unbekannte Kategorie." };
  }

  const original = text(roh.original);
  const vorhanden = (kat.skills || []).some((s) => s.t === original);
  if (!vorhanden) {
    return {
      ok: false,
      fehler: "Diesen Skill gibt es nicht mehr. Bitte die Seite neu laden.",
    };
  }

  const wert = {
    art: "aenderung",
    stufe,
    kategorie,
    original,
    emoji: text(roh.emoji),
    titel: text(roh.titel),
    beschreibung: text(roh.beschreibung),
    tipp: text(roh.tipp),
    erg: text(roh.erg),
  };

  const fehler = feldregeln(wert, "erg");
  if (fehler) {
    return { ok: false, fehler };
  }

  return { ok: true, wert };
}
```

- [ ] **Step 5: Tests laufen lassen**

Run: `(cd worker && node --test)`
Expected: PASS, 43 Tests (35 bestehende + 8 neue). **Kein bestehender Test darf angepasst worden sein** — prüf das mit `git diff worker/validate.test.js`: es dürfen nur Zeilen hinzugekommen sein.

- [ ] **Step 6: Commit**

```bash
git add worker/validate.js worker/validate.test.js
git commit -m "Prueflogik fuer Aenderungen an bestehenden Skills"
```

---

### Task 3: Worker nimmt Änderungen entgegen

**Files:**
- Modify: `worker/index.js`
- Modify: `worker/index.test.js`

**Interfaces:**
- Consumes: `pruefeAenderung(eingabe, daten)` aus Task 2, `zelle(wert)` und `issueRumpf(w)` aus Ausbaustufe 1
- Produces:
  - `issueRumpfAenderung(w, alt)` — Markdown mit einer Spalte „bisher" und einer Spalte „neu", darunter derselbe `<!-- vorschlag … -->`-Block
  - Der Endpunkt wählt anhand von `eingabe.art` zwischen beiden Prüfungen; der Issue-Titel einer Änderung beginnt mit `[Änderung] `

- [ ] **Step 1: Fehlschlagende Tests schreiben**

An `worker/index.test.js` anhängen:

```javascript
import { issueRumpfAenderung } from "./index.js";

const ALT = { e: "🎧", t: "Musik hören", b: "Ein Lied auflegen.", tip: "", von: "Max", erg: "" };
const NEU = {
  art: "aenderung",
  stufe: "Hoch",
  kategorie: "Ablenkung",
  original: "Musik hören",
  emoji: "🎵",
  titel: "Musik bewusst hören",
  beschreibung: "Ein Lied aussuchen und nur darauf achten.",
  tipp: "Kopfhörer bereitlegen",
  erg: "Lea",
};

test("zeigt bisher und neu nebeneinander", () => {
  const rumpf = issueRumpfAenderung(NEU, ALT);
  assert.match(rumpf, /bisher/i);
  assert.match(rumpf, /neu/i);
  assert.ok(rumpf.includes("Musik hören"), "alter Titel fehlt");
  assert.ok(rumpf.includes("Musik bewusst hören"), "neuer Titel fehlt");
  assert.ok(rumpf.includes("Ein Lied auflegen."), "alte Beschreibung fehlt");
});

test("enthält genau einen maschinenlesbaren Block mit gültigem JSON", () => {
  const rumpf = issueRumpfAenderung(NEU, ALT);
  const treffer = rumpf.match(/<!-- vorschlag/g) || [];
  assert.equal(treffer.length, 1);
  const block = rumpf.match(/<!-- vorschlag\n([\s\S]*?)\n-->/);
  const daten = JSON.parse(block[1]);
  assert.equal(daten.art, "aenderung");
  assert.equal(daten.original, "Musik hören");
  assert.equal(daten.erg, "Lea");
});

test("maskiert Trennstriche und Zeilenumbrüche in beiden Spalten", () => {
  const rumpf = issueRumpfAenderung(
    { ...NEU, beschreibung: "a | b\nc" },
    { ...ALT, b: "x | y" }
  );
  const tabelle = rumpf.split("<!-- vorschlag")[0];
  assert.ok(!/[^\\]\| b/.test(tabelle), "Trennstrich im neuen Wert nicht maskiert");
  assert.ok(!/[^\\]\| y/.test(tabelle), "Trennstrich im alten Wert nicht maskiert");
  assert.ok(!tabelle.includes("b\nc"), "Zeilenumbruch nicht maskiert");
});
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `(cd worker && node --test)`
Expected: FAIL — `issueRumpfAenderung is not a function`.

- [ ] **Step 3: `issueRumpfAenderung` schreiben**

In `worker/index.js` neben `issueRumpf` einfügen:

```javascript
/**
 * Rumpf fuer eine Aenderung: links der bisherige Stand, rechts der
 * vorgeschlagene. Die betreuende Person soll auf einen Blick sehen, was sich
 * aendert, ohne die Skillsliste daneben aufschlagen zu muessen.
 */
export function issueRumpfAenderung(w, alt) {
  const zeilen = [
    "| Feld | bisher | neu |",
    "| --- | --- | --- |",
    `| Emoji | ${zelle(alt.e)} | ${zelle(w.emoji)} |`,
    `| Titel | ${zelle(alt.t)} | ${zelle(w.titel)} |`,
    `| Beschreibung | ${zelle(alt.b)} | ${zelle(w.beschreibung)} |`,
    `| Tipp | ${alt.tip ? zelle(alt.tip) : "—"} | ${w.tipp ? zelle(w.tipp) : "—"} |`,
  ];
  const kopf =
    `**Stufe:** ${zelle(w.stufe)} · **Kategorie:** ${zelle(w.kategorie)}` +
    (w.erg ? ` · **Ergänzt von:** ${zelle(w.erg)}` : " · **Ergänzt von:** — (anonym)");
  return (
    kopf +
    "\n\n" +
    zeilen.join("\n") +
    "\n\n<!-- vorschlag\n" +
    JSON.stringify(w) +
    "\n-->\n"
  );
}
```

- [ ] **Step 4: Endpunkt verzweigen lassen**

Den Import oben in `worker/index.js` erweitern:

```javascript
import { pruefeVorschlag, pruefeAenderung } from "./validate.js";
```

Die Stelle, an der heute `pruefeVorschlag` aufgerufen wird, ersetzen durch:

```javascript
    const istAenderung = eingabe && eingabe.art === "aenderung";
    const geprueft = istAenderung
      ? pruefeAenderung(eingabe, daten)
      : pruefeVorschlag(eingabe, daten);
    if (!geprueft.ok) {
      return antwort({ fehler: geprueft.fehler }, 400);
    }
```

Und den Aufruf, der das Issue anlegt, so erweitern, dass er Titel und Rumpf abhängig von der Art bildet. Den bisherigen `body: issueRumpf(geprueft.wert)` ersetzen durch:

```javascript
        body: JSON.stringify({
          title: istAenderung
            ? `[Änderung] ${geprueft.wert.original}`
            : geprueft.wert.titel,
          body: istAenderung
            ? issueRumpfAenderung(geprueft.wert, altenSkillFinden(daten, geprueft.wert))
            : issueRumpf(geprueft.wert),
        }),
```

Dafür eine kleine Hilfsfunktion neben `issueRumpfAenderung`:

```javascript
/**
 * Sucht den bisherigen Stand des Skills im Datenbestand.
 * pruefeAenderung hat bereits sichergestellt, dass es ihn gibt.
 */
function altenSkillFinden(daten, wert) {
  const STUFEN = { Hoch: "hoch", Mittel: "mittel", Tief: "tief" };
  const kat = daten[STUFEN[wert.stufe]].kategorien.find(
    (k) => k.label === wert.kategorie
  );
  return kat.skills.find((s) => s.t === wert.original);
}
```

- [ ] **Step 5: Tests laufen lassen**

Run: `(cd worker && node --test)`
Expected: PASS, 46 Tests (43 aus Task 2 + 3 neue).

Run: `node --check worker/index.js`
Expected: keine Ausgabe.

- [ ] **Step 6: Commit**

```bash
git add worker/index.js worker/index.test.js
git commit -m "Worker nimmt Aenderungen entgegen und zeigt bisher und neu im Issue"
```

---

### Task 4: Zweiter Reiter im Formular

**Files:**
- Modify: `template-vorschlag.html`
- Modify: `tests/test_build.py`

**Interfaces:**
- Consumes: `DATEN` (der eingebettete Datenbestand) — je Skill `e`, `t`, `b`, `tip`, `von`, `erg`
- Produces: Die Seite sendet bei einer Änderung `{art: "aenderung", stufe, kategorie, original, emoji, titel, beschreibung, tipp, erg, falle, turnstile}` an dieselbe Adresse wie bisher

- [ ] **Step 1: Fehlschlagende Tests schreiben**

An `tests/test_build.py` anhängen:

```python
def test_vorschlagsvorlage_hat_zwei_reiter():
    vorlage = build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")
    assert 'id="reiter-neu"' in vorlage
    assert 'id="reiter-aenderung"' in vorlage
    assert 'role="tab"' in vorlage


def test_vorschlagsvorlage_sendet_die_aenderungsart():
    """Ohne art und original kann der Worker eine Aenderung nicht zuordnen."""
    vorlage = build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")
    assert 'art:' in vorlage
    assert '"aenderung"' in vorlage
    assert 'original:' in vorlage
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl pytest tests/test_build.py -k "reiter or aenderungsart" -v`
Expected: FAIL — `assert 'id="reiter-neu"' in vorlage`.

- [ ] **Step 3: Reiter-Umschaltung einbauen**

In `template-vorschlag.html` **vor** dem bestehenden `<form id="formular">` einfügen:

```html
    <div class="reiter" role="tablist">
      <button type="button" class="reiter-knopf aktiv" id="reiter-neu"
              role="tab" aria-selected="true" aria-controls="formular">Neuer Skill</button>
      <button type="button" class="reiter-knopf" id="reiter-aenderung"
              role="tab" aria-selected="false" aria-controls="formular">Bestehenden ergänzen</button>
    </div>
```

Dazu das CSS zu den übrigen Regeln:

```css
    .reiter{display:flex;gap:6px;margin-bottom:16px}
    .reiter-knopf{flex:1;padding:10px 12px;font-family:inherit;font-size:.95rem;
      background:var(--card);color:var(--muted);border:1px solid var(--border);
      border-radius:10px;cursor:pointer;transition:background .15s ease,color .15s ease}
    .reiter-knopf.aktiv{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600}
    .nur-aenderung{display:none}
    body.modus-aenderung .nur-aenderung{display:block}
    body.modus-aenderung .nur-neu{display:none}
```

- [ ] **Step 4: Auswahlfeld für den bestehenden Skill ergänzen**

Direkt **nach** dem Kategorie-Feld einfügen:

```html
      <div class="feld nur-aenderung">
        <label for="original">Welchen Skill möchtest du ergänzen?</label>
        <p class="hinweis">Die Felder darunter werden mit dem bisherigen Text gefüllt. Ändere, was du ändern möchtest.</p>
        <select id="original"></select>
      </div>
```

Das bestehende Namensfeld bekommt zwei Beschriftungen, je nach Reiter. Ersetze den Beschriftungstext des Namensfeldes durch:

```html
        <label for="von">Dein Name <span class="hinweis" style="display:inline">(freiwillig)</span></label>
        <p class="hinweis nur-neu"><strong>Achtung:</strong> Der Name erscheint öffentlich und dauerhaft auf der Skillsliste. Vorname oder Spitzname genügt. Lass das Feld leer, wenn du anonym bleiben willst.</p>
        <p class="hinweis nur-aenderung"><strong>Achtung:</strong> Der Name erscheint öffentlich und dauerhaft auf der Skillsliste, neben dem Namen der Person, die den Skill ursprünglich vorgeschlagen hat. Lass das Feld leer, wenn du anonym bleiben willst.</p>
```

- [ ] **Step 5: Umschaltung und Vorausfüllen in JavaScript**

Bei den übrigen Funktionen ergänzen:

```javascript
var modus = 'neu';

function skillsDerKategorie(){
  var schluessel=STUFEN.filter(function(p){return p[1]===el('stufe').value;})[0][0];
  var liste=(DATEN[schluessel]&&DATEN[schluessel].kategorien)||[];
  var kat=liste.filter(function(k){return k.label===el('kategorie').value;})[0];
  return (kat&&kat.skills)||[];
}

function originalAuswahlFuellen(){
  var wahl=el('original');
  wahl.innerHTML='';
  skillsDerKategorie().forEach(function(s){
    var o=document.createElement('option');
    o.value=s.t;
    o.textContent=(s.e?s.e+' ':'')+s.t;
    wahl.appendChild(o);
  });
  originalUebernehmen();
}

function originalUebernehmen(){
  if(modus!=='aenderung'){ return; }
  var s=skillsDerKategorie().filter(function(k){return k.t===el('original').value;})[0];
  if(!s){ return; }
  el('emoji').value=s.e||'';
  el('titel').value=s.t||'';
  el('beschreibung').value=s.b||'';
  // Der Tipp traegt in den Daten eine fuehrende Gluehbirne; im Formular gehoert
  // sie nicht hinein, sie wird beim Bauen wieder ergaenzt.
  el('tipp').value=(s.tip||'').replace(/^💡\s*/,'');
}

function modusSetzen(neuerModus){
  modus=neuerModus;
  document.body.classList.toggle('modus-aenderung', modus==='aenderung');
  el('reiter-neu').classList.toggle('aktiv', modus==='neu');
  el('reiter-aenderung').classList.toggle('aktiv', modus==='aenderung');
  el('reiter-neu').setAttribute('aria-selected', modus==='neu');
  el('reiter-aenderung').setAttribute('aria-selected', modus==='aenderung');
  if(modus==='aenderung'){ originalAuswahlFuellen(); }
  else { ['emoji','titel','beschreibung','tipp'].forEach(function(f){ el(f).value=''; }); }
}

el('reiter-neu').addEventListener('click', function(){ modusSetzen('neu'); });
el('reiter-aenderung').addEventListener('click', function(){ modusSetzen('aenderung'); });
el('original').addEventListener('change', originalUebernehmen);
```

Die bestehende Funktion `kategorienFuellen` am Ende um einen Aufruf erweitern, damit die Skill-Auswahl mitzieht:

```javascript
  if(modus==='aenderung'){ originalAuswahlFuellen(); }
```

- [ ] **Step 6: Absenden erweitern**

Im Absende-Handler den Rumpf abhängig vom Modus bilden. Ersetze das bestehende `body:JSON.stringify({…})` durch:

```javascript
      body:JSON.stringify(modus==='aenderung' ? {
        art:'aenderung',
        stufe:el('stufe').value,
        kategorie:el('kategorie').value,
        original:el('original').value,
        emoji:el('emoji').value,
        titel:el('titel').value,
        beschreibung:el('beschreibung').value,
        tipp:el('tipp').value,
        erg:el('von').value,
        falle:el('falle').value,
        turnstile:token
      } : {
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
```

- [ ] **Step 7: Tests und Build**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: PASS, 49 Tests.

Run: `uv run build.py`
Expected: drei ✅-Zeilen.

- [ ] **Step 8: Sichtprüfung im Browser**

Starte einen lokalen Webserver im Ordner `docs` (`python -m http.server 8765 --directory docs`), öffne `http://localhost:8765/skill-vorschlagen.html` und prüfe:

- Beide Reiter sind sichtbar, „Neuer Skill" ist zu Beginn aktiv
- Ein Klick auf „Bestehenden ergänzen" zeigt das Auswahlfeld und füllt Emoji, Titel, Beschreibung und Tipp mit dem bisherigen Text
- Ein Wechsel der Stufe oder Kategorie füllt die Skill-Auswahl neu
- Ein Wechsel zurück auf „Neuer Skill" leert die Felder wieder
- Der Hinweis beim Namensfeld wechselt mit
- Keine Fehler in der Browser-Konsole ausser der erwarteten Turnstile-Domainmeldung

Server danach beenden. Halte im Bericht fest, was du gesehen hast.

- [ ] **Step 9: Commit**

```bash
git add template-vorschlag.html tests/test_build.py docs/skill-vorschlagen.html
git commit -m "Zweiter Reiter: bestehenden Skill ergaenzen"
```

---

### Task 5: Übernahme-Skript verarbeitet Änderungen

**Files:**
- Modify: `tools/vorschlaege_holen.py`
- Modify: `tests/test_vorschlaege_holen.py`

**Interfaces:**
- Consumes: `parse_body`, `hat_label`, `lade_datenstand`, `bereinigt`, `an_excel_anhaengen`, `issue_schliessen` aus Ausbaustufe 1
- Produces:
  - `pruefe_eintrag(eintrag, daten)` behandelt zusätzlich `art == "aenderung"` (Schlüssel `original` muss vorhanden sein und der Skill existieren; `erg` statt `von`)
  - `in_excel_aendern(pfad, eintraege) -> int` — ersetzt bestehende Zeilen, gibt die Anzahl geänderter Zeilen zurück

- [ ] **Step 1: Fehlschlagende Tests schreiben**

An `tests/test_vorschlaege_holen.py` anhängen:

```python
AENDERUNG = {
    "art": "aenderung",
    "stufe": "Hoch",
    "kategorie": "Ablenkung",
    "original": "Musik hören",
    "emoji": "🎵",
    "titel": "Musik bewusst hören",
    "beschreibung": "Ein Lied aussuchen und nur darauf achten.",
    "tipp": "Kopfhörer bereitlegen",
    "erg": "Lea",
}

DATEN_MIT_SKILL = {
    "hoch": {"kategorien": [{"id": "ablenkung", "label": "Ablenkung", "skills": [
        {"e": "🎧", "t": "Musik hören", "b": "Ein Lied auflegen.", "tip": "", "von": "Max", "erg": ""}
    ]}]},
    "mittel": {"kategorien": []},
    "tief": {"kategorien": []},
}


def mappe_mit_skill(tmp_path):
    """Eine Excel mit genau dem Skill, den DATEN_MIT_SKILL beschreibt."""
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp", "Von", "Ergaenzt"])
    ws.append(["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.", "", "Max", ""])
    ws.append(["Tief", "Ruhe", "🌊", "Atmen", "Ruhig atmen.", "", "", ""])
    wb.save(pfad)
    return pfad


def test_aenderung_wird_angenommen():
    assert vh.pruefe_eintrag(AENDERUNG, DATEN_MIT_SKILL) is None


def test_aenderung_ohne_original_wird_abgelehnt():
    ohne = {k: v for k, v in AENDERUNG.items() if k != "original"}
    meldung = vh.pruefe_eintrag(ohne, DATEN_MIT_SKILL)
    assert meldung is not None


def test_aenderung_an_verschwundenem_skill_wird_abgelehnt():
    meldung = vh.pruefe_eintrag(dict(AENDERUNG, original="Gibt es nicht"), DATEN_MIT_SKILL)
    assert meldung is not None
    assert "nicht" in meldung.lower()


def test_aenderung_ersetzt_die_zeile(tmp_path):
    pfad = mappe_mit_skill(tmp_path)
    anzahl = vh.in_excel_aendern(pfad, [AENDERUNG])
    assert anzahl == 1
    ws = openpyxl.load_workbook(pfad)["Skills"]
    assert ws.max_row == 3, "es darf keine Zeile dazugekommen sein"
    kopf = [c.value for c in ws[1]]
    zeile = dict(zip(kopf, [c.value for c in ws[2]]))
    assert zeile["Titel"] == "Musik bewusst hören"
    assert zeile["Emoji"] == "🎵"
    assert zeile["Beschreibung"] == "Ein Lied aussuchen und nur darauf achten."
    assert zeile["Tipp"] == "Kopfhörer bereitlegen"
    assert zeile["Von"] == "Max", "der urspruengliche Beitragende bleibt stehen"
    assert zeile["Ergaenzt"] == "Lea"


def test_aenderung_ohne_passende_zeile_meldet_es(tmp_path):
    pfad = mappe_mit_skill(tmp_path)
    try:
        vh.in_excel_aendern(pfad, [dict(AENDERUNG, original="Gibt es nicht")])
    except vh.ZeileNichtGefunden as fehler:
        assert "Gibt es nicht" in str(fehler)
    else:
        raise AssertionError("ZeileNichtGefunden erwartet")
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl pytest tests/test_vorschlaege_holen.py -k "aenderung" -v`
Expected: FAIL — `module 'vorschlaege_holen' has no attribute 'in_excel_aendern'`.

- [ ] **Step 3: `pruefe_eintrag` um die Änderungsart erweitern**

In `tools/vorschlaege_holen.py` bei den Konstanten ergänzen:

```python
SPALTEN_AENDERUNG = [
    ("Emoji", "emoji"),
    ("Titel", "titel"),
    ("Beschreibung", "beschreibung"),
    ("Tipp", "tipp"),
    ("Ergaenzt", "erg"),
]


class ZeileNichtGefunden(Exception):
    """Der zu aendernde Skill steht nicht (mehr) in der Excel."""
```

In `pruefe_eintrag` **am Anfang** die Art bestimmen und das Namensfeld danach wählen:

```python
    art = str(eintrag.get("art") or "neu").strip()
    if art not in ("neu", "aenderung"):
        return f"Unbekannte Art: {art!r}."
    namensfeld = "erg" if art == "aenderung" else "von"
```

Die Längen- und Inhaltsprüfungen darunter arbeiten auf dem dict `felder`, dessen Schlüssel aus `GRENZEN` und `TEXTFELDER` stammen — dort heisst das Namensfeld `von`. Statt alle Schleifen umzubauen, lässt du bei einer Änderung `erg` diesen Platz einnehmen. Direkt **nach** der Zeile, die `felder` um `stufe` und `kategorie` ergänzt, einfügen:

```python
    # Bei einer Aenderung traegt `erg` den Namen. Er nimmt hier den Platz von
    # `von` ein, damit die Laengen-, Link- und Zeichenpruefungen darunter
    # unveraendert gelten – die Meldung nennt in beiden Faellen „Name".
    if art == "aenderung":
        felder["von"] = str(eintrag.get("erg") or "").strip()
```

Damit bleiben die vorhandenen Schleifen unangetastet. Zusätzlich für Änderungen prüfen, dass der Skill existiert — **nach** der bestehenden Kategorie-Prüfung, also unmittelbar vor dem abschliessenden `return None`, einfügen:

```python
    if art == "aenderung":
        original = str(eintrag.get("original") or "").strip()
        if not original:
            return "Pflichtfeld fehlt: urspruenglicher Titel."
        kat = next(
            (k for k in daten[schluessel]["kategorien"] if k["label"] == kategorie),
            None,
        )
        if not any(s.get("t") == original for s in (kat or {}).get("skills", [])):
            return (
                f"Der Skill {original!r} steht nicht mehr in der Stufe "
                f"{stufe!r}, Kategorie {kategorie!r} - vermutlich inzwischen "
                f"umbenannt oder entfernt."
            )
```

- [ ] **Step 4: `in_excel_aendern` schreiben**

Neben `an_excel_anhaengen` einfügen:

```python
def in_excel_aendern(pfad: Path, eintraege: list) -> int:
    """Ersetzt bestehende Zeilen im Blatt `Skills`.

    Gefunden wird ueber Stufe + Kategorie + urspruenglicher Titel. Die Spalte
    `Von` bleibt unangetastet – der urspruengliche Beitragende wird nie durch
    eine Ergaenzung verdraengt.
    """
    if not eintraege:
        return 0
    wb = openpyxl.load_workbook(pfad)
    ws = wb["Skills"]
    kopf = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
    for name, _ in SPALTEN_AENDERUNG:
        if name not in kopf:
            ws.cell(row=1, column=len(kopf) + 1, value=name)
            kopf.append(name)

    i_stufe, i_kat, i_titel = kopf.index("Stufe"), kopf.index("Kategorie"), kopf.index("Titel")
    geaendert = 0
    for eintrag in eintraege:
        e = bereinigt(eintrag)
        original = str(eintrag.get("original") or "").strip()
        zeile = None
        for r in range(2, ws.max_row + 1):
            werte = [c.value for c in ws[r]]
            if (
                str(werte[i_stufe] or "").strip() == e["stufe"]
                and str(werte[i_kat] or "").strip() == e["kategorie"]
                and str(werte[i_titel] or "").strip() == original
            ):
                zeile = r
                break
        if zeile is None:
            raise ZeileNichtGefunden(
                f"{original!r} in {e['stufe']} / {e['kategorie']}"
            )
        for name, schluessel in SPALTEN_AENDERUNG:
            ws.cell(row=zeile, column=kopf.index(name) + 1, value=e.get(schluessel, ""))
        geaendert += 1

    try:
        wb.save(pfad)
    except PermissionError:
        raise SystemExit(
            f"❌ Die Datei {pfad.name} laesst sich nicht speichern.\n\n"
            f"   Sie ist vermutlich gerade in Excel geoeffnet. Bitte schliesse\n"
            f"   Excel und starte vorschlaege.bat noch einmal.\n\n"
            f"   Es wurde nichts veraendert – die Vorschlaege bleiben freigegeben\n"
            f"   und werden beim naechsten Lauf uebernommen."
        )
    return geaendert
```

`bereinigt` trimmt heute nur die Schlüssel aus `SPALTEN` — `erg` fehlt darin. Ersetze in `bereinigt` die Schleifenzeile

```python
    for schluessel in (s for _, s in SPALTEN):
```

durch

```python
    for schluessel in {s for _, s in SPALTEN} | {s for _, s in SPALTEN_AENDERUNG}:
```

Damit wird auch `erg` getrimmt, ohne dass eine zweite Aufzählung entsteht, die auseinanderlaufen könnte.

- [ ] **Step 5: `main` verzweigen lassen**

Die Sammelschleife trennt die beiden Arten, und beide werden **vor** dem Schliessen der Issues geschrieben:

```python
    neue = [(i, d) for i, d in uebernehmen if d.get("art", "neu") != "aenderung"]
    aenderungen = [(i, d) for i, d in uebernehmen if d.get("art") == "aenderung"]

    anzahl = an_excel_anhaengen(XLSX, [d for _, d in neue])
    try:
        anzahl += in_excel_aendern(XLSX, [d for _, d in aenderungen])
    except ZeileNichtGefunden as fehler:
        raise SystemExit(
            f"❌ Eine Aenderung liess sich nicht zuordnen: {fehler}\n\n"
            f"   Der Skill wurde vermutlich zwischen Einreichung und Freigabe\n"
            f"   umbenannt oder entfernt. Nimm dem betroffenen Issue das Label\n"
            f"   `freigegeben` und starte vorschlaege.bat noch einmal.\n\n"
            f"   Die uebrigen Vorschlaege stehen bereits in der Excel."
        )
```

In der Ausgabeschleife die Art sichtbar machen:

```python
        kennung = "~" if daten.get("art") == "aenderung" else "+"
        print(f"  {kennung} {daten['stufe']} / {daten['kategorie']}: {daten['titel']}")
```

- [ ] **Step 6: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl pytest tests -v`
Expected: PASS, 54 Tests (49 aus Task 4 + 5 neue). Bestehende Tests unverändert.

- [ ] **Step 7: Leerlauf gegen das echte Repo**

Run: `uv run tools/vorschlaege_holen.py`
Expected: `Keine freigegebenen Vorschläge offen. Nichts zu tun.` — es gibt gerade keine offenen Issues.

- [ ] **Step 8: Commit**

```bash
git add tools/vorschlaege_holen.py tests/test_vorschlaege_holen.py
git commit -m "Uebernahme-Skript ersetzt bestehende Zeilen bei Aenderungen"
```

---

### Task 6: Dokumentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `ANLEITUNG.md`
- Modify: `specs/2026-08-03-skill-vorschlagen-design.md`

**Interfaces:**
- Consumes: alles aus Task 1–5
- Produces: keine

- [ ] **Step 1: `CLAUDE.md` erweitern**

Im Abschnitt „Skill-Vorschläge von aussen" nach dem ersten Absatz ergänzen:

```markdown
Das Formular hat zwei Reiter: **Neuer Skill** und **Bestehenden ergänzen**. Eine
Ergänzung ändert Emoji, Titel, Beschreibung und Tipp eines vorhandenen Skills;
Stufe und Kategorie bleiben, weil sie zusammen mit dem ursprünglichen Titel den
Schlüssel bilden, über den `vorschlaege.bat` die Zeile wiederfindet. Der Issue-
Titel beginnt dann mit `[Änderung]`, und der Rumpf zeigt „bisher" und „neu"
nebeneinander.

Beide Beitragenden werden genannt: die Spalte `Von` bleibt beim ursprünglichen
Vorschlag, die neue Spalte `Ergaenzt` nennt die Person, die ergänzt hat. Im
Detail-Dialog steht dann „Vorgeschlagen von A · ergänzt von B".
```

Im Abschnitt „Skillsliste pflegen" den Hinweis auf die Blätter um die Spalte ergänzen:

```markdown
1. Inhalte in **`skills_daten.xlsx`** ändern (Blätter `Skills`, `Stufen`, `Kategorien`).
   Das Blatt `Skills` hat acht Spalten; `Von` und `Ergaenzt` nennen die Beitragenden
   und dürfen leer bleiben.
```

- [ ] **Step 2: `ANLEITUNG.md` erweitern**

Im Abschnitt „Vorschläge von anderen übernehmen" nach Schritt 2 ergänzen:

```markdown
**Zwei Arten von Vorschlägen.** Beginnt der Titel mit `[Änderung]`, will jemand
einen bestehenden Skill verbessern. Im Eintrag stehen dann zwei Spalten
nebeneinander: links, was heute in der Liste steht, rechts der Vorschlag. Du
siehst also auf einen Blick, was sich ändern würde. Alles andere läuft gleich.

Wenn im Fenster steht, eine Änderung liesse sich nicht zuordnen, dann wurde der
betroffene Skill in der Zwischenzeit umbenannt oder gelöscht. Nimm dem Eintrag
das Kennzeichen `freigegeben` weg und starte noch einmal — die übrigen
Vorschläge sind dann schon übernommen.
```

- [ ] **Step 3: Spezifikation nachziehen**

In `specs/2026-08-03-skill-vorschlagen-design.md` im Abschnitt „Ausbaustufen" den Punkt 2 als erledigt kennzeichnen und die beiden Entscheidungen festhalten:

```markdown
2. **Ändern** — umgesetzt. Zwei Entscheidungen dabei: Eine Änderung ändert nur
   die Texte (Emoji, Titel, Beschreibung, Tipp), nicht Stufe oder Kategorie —
   sonst wäre der Schlüssel zum Wiederfinden nicht stabil. Und beide
   Beitragenden werden genannt, über eine zweite Spalte `Ergaenzt`; eine
   Ergänzung verdrängt den ursprünglichen Namen nie.
```

- [ ] **Step 4: Build prüfen**

Run: `uv run build.py` und `git status --short`
Expected: keine Änderung an den erzeugten Dateien — diese Aufgabe fasst nur Text an.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md ANLEITUNG.md specs/2026-08-03-skill-vorschlagen-design.md
git commit -m "Ausbaustufe 2 dokumentieren"
```

---

### Task 7: Durchlauf von Ende zu Ende

**Files:** keine neuen; ggf. Korrekturen an den Dateien aus Task 1–5

**Interfaces:**
- Consumes: alles
- Produces: bestätigte Funktionsfähigkeit

- [ ] **Step 1: Zusammenführen und veröffentlichen**

Der fremde Stand wird **in den Worktree** geholt, dort aufgelöst und geprüft; erst danach geht es auf `master`. Nie umgekehrt.

```bash
git fetch https://github.com/stayingclean/toolbox.git master:refs/remotes/fern/master --force
git merge fern/master --no-edit
uv run build.py
git status --short          # erzeugte Dateien duerfen sich nicht unterscheiden
uv run --with pytest --with openpyxl pytest tests -q
(cd worker && node --test)
```

Danach im Hauptverzeichnis `C:\workspace\eraschle`:

```bash
git merge --no-ff feature/formulare-toolbox -m "Bestehende Skills ergaenzen (Ausbaustufe 2)"
git push https://github.com/stayingclean/toolbox.git master:master
```

Warten, bis die Veröffentlichung durch ist (`gh run watch`), dann prüfen, dass `https://stayingclean.github.io/toolbox/skill-vorschlagen.html` mit 200 antwortet und beide Reiter enthält.

- [ ] **Step 2: Worker veröffentlichen lassen**

Der Worker hat sich geändert (`validate.js`, `index.js`). **Das kann der Implementierer nicht selbst** — melde dem Menschen, dass er

```
cd C:\workspace\eraschle\.worktrees\formulare-toolbox\worker
npx wrangler deploy
```

ausführen muss, **bevor** Schritt 3 sinnvoll ist. Ohne das lehnt der Worker jede Änderung ab, weil er `art: "aenderung"` nicht kennt.

- [ ] **Step 3: Echte Änderung einreichen**

Auf der veröffentlichten Seite den Reiter „Bestehenden ergänzen" wählen, einen Skill aussuchen, den Tipp leicht ändern, einen Namen eintragen und absenden.

Expected: Dankesmeldung mit Link. Das Issue trägt den Titel `[Änderung] <ursprünglicher Titel>` und zeigt „bisher" und „neu" nebeneinander.

- [ ] **Step 4: Anonymität und Herkunft prüfen**

```bash
gh issue view <n> --repo stayingclean/skills-suggestions --json author,body --jq '.author.login, .body'
```

Expected: Autor `eraschle`; im Rumpf weder IP-Adresse noch Browserkennung; genau **ein** `<!-- vorschlag`-Block mit `"art":"aenderung"` und dem richtigen `original`.

- [ ] **Step 5: Freigeben und übernehmen**

```bash
gh issue edit <n> --repo stayingclean/skills-suggestions --add-label freigegeben
uv run tools/vorschlaege_holen.py
```

Expected: Zeile mit `~` statt `+`, `1 Vorschlag … übernommen`, Issue geschlossen.

- [ ] **Step 6: Ergebnis prüfen**

```bash
uv run --with openpyxl python -c "
import openpyxl
ws = openpyxl.load_workbook('skills_daten.xlsx')['Skills']
print('Zeilen:', ws.max_row, 'Filter:', ws.auto_filter.ref)
"
```

Expected: **gleiche Zeilenzahl wie vorher** — eine Änderung darf keine Zeile hinzufügen.

`docs/skillsliste.html` öffnen, den Skill antippen.
Expected: der geänderte Text, und die Zeile „Vorgeschlagen von … · ergänzt von …".

- [ ] **Step 7: Randfall prüfen — verschwundener Skill**

Ein zweites Issue von Hand anlegen, das eine Änderung an einem nicht existierenden Skill beschreibt, freigeben und das Skript laufen lassen:

```bash
gh issue create --repo stayingclean/skills-suggestions --title "[Änderung] Gibt es nicht" \
  --label freigegeben --body '<!-- vorschlag
{"art":"aenderung","stufe":"Hoch","kategorie":"Anti-Craving","original":"Gibt es nicht","emoji":"X","titel":"X","beschreibung":"X","tipp":"","erg":""}
-->'
uv run tools/vorschlaege_holen.py
```

Expected: verständliche Meldung, dass sich die Änderung nicht zuordnen lässt; Excel unverändert; Issue bleibt offen. Danach das Test-Issue löschen.

- [ ] **Step 8: Aufräumen**

Die Teständerung in der Excel von Hand zurücknehmen (oder `git checkout -- skills_daten.xlsx`, falls sie noch nicht committet ist), `uv run build.py`, und prüfen, dass das Arbeitsverzeichnis wieder sauber ist.

- [ ] **Step 9: Abnahme**

- [ ] Beide Reiter funktionieren auf dem Handy und am Rechner
- [ ] Eine Änderung fügt **keine** Zeile hinzu, sondern ersetzt die vorhandene
- [ ] `Von` bleibt beim ursprünglichen Beitragenden stehen
- [ ] Der Detail-Dialog nennt beide, wenn beide gesetzt sind
- [ ] Eine Änderung an einem verschwundenen Skill wird verständlich abgelehnt, das Issue bleibt offen
- [ ] Issue enthält weder IP noch Browserkennung
- [ ] Eine bestehende Excel **ohne** Spalte `Ergaenzt` baut weiterhin fehlerfrei (durch `test_erg_ist_leer_wenn_spalte_fehlt` abgedeckt)
