# Bezugsquellen — Stufe 1: Links erfassen, prüfen, anzeigen

> **Für agentische Bearbeitung:** ERFORDERLICHER UNTER-SKILL: `superpowers:subagent-driven-development` (empfohlen) oder `superpowers:executing-plans`, Aufgabe für Aufgabe. Schritte sind als Kästchen (`- [ ]`) geführt.

**Ziel:** Ein Skill kann bis zu drei `https`-Bezugsquellen tragen; Besucher reichen sie über das Formular ein, nach Freigabe erscheinen sie als Knöpfe im Detail-Dialog der Skillsliste.

**Architektur:** Drei Excel-Spalten `Link1..Link3` tragen die Daten. Dieselben URL-Regeln stehen an drei Stellen — `build.py` (letzte Schranke vor der Website), `worker/validate.js` (Formularweg) und `tools/vorschlaege_holen.py` (Issues, die nicht übers Formular kamen). Das ist das im Projekt bereits gelebte Muster (vgl. `GRENZEN`), kein Versehen. Die Anzeige leitet die Knopfaufschrift aus dem Hostnamen ab; im Formular verwaltet eine dynamische Liste bis zu drei Eingabezeilen.

**Tech Stack:** Python 3.11 + openpyxl (uv-Skripte), Cloudflare Worker (ES-Module, `node --test`), reines Vanilla-JS in den HTML-Vorlagen.

**Zugehöriger Entwurf:** `specs/2026-08-06-bezugsquellen-design.md`

## Global Constraints

Diese Punkte gelten für **jede** Aufgabe:

- **Höchstens 3 Links** je Skill. Konstante heisst überall `MAX_LINKS` bzw. ist durch die drei Spalten `Link1`, `Link2`, `Link3` gegeben.
- **Höchstens 300 Zeichen** je URL. Konstante: `LINK_MAX_LAENGE`.
- **Nur `https://`.** Kein `http`, kein anderes Schema.
- **Verboten:** Benutzerangabe (`@`), Portnummer, IP-Adresse als Host, Host ohne Punkt, spitze Klammern, Linkverkürzer.
- **Verkürzer-Liste, überall identisch:** `bit.ly`, `tinyurl.com`, `t.co`, `goo.gl`, `ow.ly`, `is.gd`, `buff.ly`, `rb.gy`, `cutt.ly`, `shorturl.at`, `s.id`, `lnkd.in`
- **Die bestehende `http`-Sperre für Titel, Beschreibung, Tipp und Name bleibt unverändert.** Sie wird ausschliesslich für das neue Link-Feld nicht angewandt. Ein Test muss das festhalten.
- **Jeder ausgehende Link trägt `rel="noopener noreferrer nofollow ugc"`.** Ohne `nofollow ugc` wird die Seite zum Ziel für Link-Spam.
- **Kein Netzwerkzugriff in `build.py`** und in keinem Test.
- **Deutsche Bezeichner und Kommentare**, wie im ganzen Projekt. Kommentare erklären das *Warum*, nicht das *Was*.
- **Umlaute — die Konvention hängt an der Datei, nicht am Projekt.** Das ist
  in Aufgabe 1 und 2 je einmal aufgelaufen; die Beispielblöcke unten sind
  entsprechend gesetzt, aber im Zweifel gilt diese Tabelle:

  | Datei | Kommentare | Zeichenketten, die jemand liest |
  |---|---|---|
  | `build.py` | **Umlaute** | **Umlaute** |
  | `template.html` | **Umlaute** | **Umlaute** |
  | `tests/test_build.py` | **Umlaute** (die Datei ist gemischt — neuer Text vereinheitlicht auf Umlaute) | **Umlaute** |
  | `template-vorschlag.html` | ASCII (`Aenderung`, `loeschen`) | **Umlaute** |
  | `worker/validate.js` | ASCII (`Pruefungen`, `Laengen`) | **Umlaute** (`Ungültige Einreichung.`) |
  | `worker/index.js` | ASCII (`fuer`, `waere`) | **Umlaute** |
  | `tools/vorschlaege_holen.py` | ASCII | ASCII (auch die Konsolenausgabe) |
  | `CLAUDE.md`, `ANLEITUNG.md` | — | **Umlaute** |

  **Python- und JavaScript-Bezeichner bleiben immer ASCII** (`pruefe_link`,
  `test_ungueltiger_link_bricht_ab`) — das ist keine Ausnahme, sondern die
  durchgehende Praxis im Projekt.
- **`docs/skillsliste.html`, `docs/skill-vorschlagen.html` und `docs/skills-daten.json` sind erzeugt** — niemals von Hand bearbeiten. Geändert werden `template.html`, `template-vorschlag.html` und `build.py`.
- **Tests laufen so:** `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q` (bzw. `test.bat`) und `cd worker && node --test`.

---

### Task 1: URL-Regeln und Link-Spalten in `build.py`

**Files:**
- Modify: `build.py` (neue Konstanten und `pruefe_link` nach `sortier_schluessel`, Zeile ~62; `optional_header` in `load_data`, Zeile 163; Skill-Aufbau, Zeile 228-237)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: nichts.
- Produces: `build.LINK_SPALTEN` (`list[str]`, `["Link1","Link2","Link3"]`), `build.LINK_MAX_LAENGE` (`int`, 300), `build.VERKUERZER` (`frozenset[str]`), `build.pruefe_link(roh: str) -> tuple[str|None, str|None]` — liefert `(url, None)` oder `(None, meldung)`. Jeder Skill im Ergebnis von `load_data()` bekommt zusätzlich `"links": list[str]`.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_build.py` anhängen:

```python
LINK_HEADER = SKILLS_HEADER + ["Link1", "Link2", "Link3"]


def erste_skills(daten):
    return daten["hoch"]["kategorien"][0]["skills"][0]


def test_links_werden_gelesen(mappe, monkeypatch):
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + ["https://www.skillsbox.ch/p/1", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    assert erste_skills(build.load_data())["links"] == ["https://www.skillsbox.ch/p/1"]


def test_links_sind_leer_wenn_spalten_fehlen(mappe, monkeypatch):
    pfad = mappe(SKILLS_HEADER, [SKILLS_ROW])
    monkeypatch.setattr(build, "XLSX", pfad)
    assert erste_skills(build.load_data())["links"] == []


def test_luecke_wird_zusammengeschoben(mappe, monkeypatch):
    """Wer den ersten von zwei Links entfernt, soll die uebrigen nicht
    von Hand aufruecken muessen."""
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + ["", "https://a.ch/x", "https://b.ch/y"]])
    monkeypatch.setattr(build, "XLSX", pfad)
    assert erste_skills(build.load_data())["links"] == ["https://a.ch/x", "https://b.ch/y"]


def test_doppelte_url_faellt_weg(mappe, monkeypatch):
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + ["https://a.ch/x", "https://a.ch/x", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    assert erste_skills(build.load_data())["links"] == ["https://a.ch/x"]


@pytest.mark.parametrize(
    "url, teil",
    [
        ("http://a.ch/x", "https://"),
        ("https://bit.ly/abc", "Linkverkuerzer"),
        ("https://192.168.0.1/x", "IP-Adresse"),
        ("https://a.ch:8080/x", "Portnummer"),
        ("https://wer:was@a.ch/x", "Benutzerangabe"),
        ("https://ohnepunkt/x", "Hostnamen"),
        ("https://a.ch/<script>", "Klammern"),
        ("ftp://a.ch/x", "https://"),
    ],
)
def test_ungueltiger_link_bricht_ab(mappe, monkeypatch, url, teil):
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + [url, "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    with pytest.raises(build.BuildError) as fehler:
        build.load_data()
    meldung = str(fehler.value)
    assert teil in meldung
    # Die Meldung muss Zeile UND Spalte nennen, sonst sucht man in der Excel.
    assert "Zeile 2" in meldung
    assert "Link1" in meldung


def test_zu_langer_link_bricht_ab(mappe, monkeypatch):
    lang = "https://a.ch/" + "x" * 300
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + [lang, "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    with pytest.raises(build.BuildError) as fehler:
        build.load_data()
    assert "zu lang" in str(fehler.value).lower()


def test_links_stehen_in_der_json(mappe, monkeypatch, tmp_path):
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + ["https://a.ch/x", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    ziel = tmp_path / "skills-daten.json"
    monkeypatch.setattr(build, "DATEN_JSON", ziel)
    build.write_daten_json(build.load_data())
    daten = json.loads(ziel.read_text(encoding="utf-8"))
    assert daten["hoch"]["kategorien"][0]["skills"][0]["links"] == ["https://a.ch/x"]
```

Ganz oben in `tests/test_build.py` `import pytest` ergänzen, falls noch nicht vorhanden.

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q -k link`
Expected: FAIL — `KeyError: 'links'` bzw. `AttributeError: module 'build' has no attribute 'pruefe_link'`

- [ ] **Step 3: Konstanten und `pruefe_link` einbauen**

In `build.py` bei den Importen ergänzen:

```python
import ipaddress
from urllib.parse import urlsplit
```

Nach `sortier_schluessel` (nach Zeile 61) einfügen:

```python
# ── Bezugsquellen ────────────────────────────────────────────
# Dieselben Regeln stehen in worker/validate.js (pruefeLinks) und in
# tools/vorschlaege_holen.py. Wer hier etwas aendert, muss dort nachziehen —
# so wie bei GRENZEN. Ein Test in tests/test_vorschlaege_holen.py haelt die
# beiden Python-Fassungen zusammen; die JavaScript-Fassung haelt niemand.
LINK_SPALTEN = ["Link1", "Link2", "Link3"]
LINK_MAX_LAENGE = 300

# Linkverkuerzer verbergen das Ziel vor der Freigabe – die Pruefung im Issue
# waere wertlos – und ergaeben als Knopfaufschrift nur "bit.ly" statt eines
# erkennbaren Haendlers.
VERKUERZER = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "rb.gy", "cutt.ly", "shorturl.at", "s.id", "lnkd.in",
})


def _ist_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def pruefe_link(roh):
    """Prueft eine Bezugsquelle aus der Excel.

    Liefert (url, None) bei gueltigem Link, sonst (None, Meldung). Der Build ist
    die letzte Schranke vor der Website: eine kaputte Adresse soll hier
    auffallen, nicht spaeter einem Besucher beim Klicken.
    """
    url = str(roh or "").strip()
    if len(url) > LINK_MAX_LAENGE:
        return None, f"Link ist zu lang (hoechstens {LINK_MAX_LAENGE} Zeichen)"
    # Spitze Klammern koennten in der erzeugten Skillsliste das <script>-Element
    # beenden. Die Ausgabecodierung in _render faengt das ab; dies ist die
    # zweite Schicht, wie schon bei den Textfeldern im Worker.
    if "<" in url or ">" in url:
        return None, "Link darf keine spitzen Klammern enthalten"
    try:
        teile = urlsplit(url)
    except ValueError:
        return None, "Link ist keine gueltige Adresse"
    if teile.scheme != "https":
        return None, "Link muss mit https:// beginnen"
    if teile.username or teile.password:
        return None, "Link darf keine Benutzerangabe (@) enthalten"
    try:
        if teile.port is not None:
            return None, "Link darf keine Portnummer enthalten"
    except ValueError:
        return None, "Link hat eine ungueltige Portnummer"
    host = (teile.hostname or "").strip(".")
    if _ist_ip(host):
        return None, "Link darf keine IP-Adresse sein"
    if "." not in host:
        return None, "Link hat keinen gueltigen Hostnamen"
    if host.removeprefix("www.") in VERKUERZER:
        return None, "Linkverkuerzer sind nicht erlaubt"
    return url, None
```

- [ ] **Step 4: Spalten lesen und in den Skill hängen**

In `load_data` die Kopfzeile erweitern (Zeile 161-164):

```python
    skill_rows = read_rows(
        get_sheet(wb, "Skills"),
        ["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp"],
        optional_header=["Von", "Ergaenzt"] + LINK_SPALTEN,
    )
```

In der Skill-Schleife, unmittelbar vor `skills_by.setdefault(...)` (vor Zeile 228):

```python
        # Luecken werden zusammengeschoben: wer den ersten von zwei Links
        # entfernt, soll die uebrigen nicht von Hand aufruecken muessen.
        links = []
        for spalte in LINK_SPALTEN:
            if not rec[spalte]:
                continue
            url, meldung = pruefe_link(rec[spalte])
            if meldung:
                errors.append(
                    f"Blatt 'Skills', Zeile {rec['_row']}, Spalte '{spalte}': "
                    f"{meldung}."
                )
                continue
            if url not in links:
                links.append(url)
```

und im Skill-Wörterbuch (nach `"erg": rec["Ergaenzt"],`) ergänzen:

```python
                "links": links,
```

- [ ] **Step 5: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q`
Expected: PASS, alle Tests der Datei

- [ ] **Step 6: Committen**

```bash
git add build.py tests/test_build.py
git commit -m "Bezugsquellen: Link-Spalten in build.py lesen und pruefen"
```

---

### Task 2: Bezugsquellen im Detail-Dialog anzeigen

**Files:**
- Modify: `template.html` (CSS nach `.modal-von`, Zeile 141; Markup in `.modal-body`, Zeile ~301; `openModal` samt Variablenzeile, Zeile 419-431)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `skill.links` (`list[str]`) aus Task 1.
- Produces: nichts für spätere Aufgaben.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_build.py` anhängen:

```python
def test_vorlage_zeigt_bezugsquellen():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    assert 'id="m-links"' in vorlage
    assert 'id="m-links-liste"' in vorlage
    assert "Von Besuchern vorgeschlagen · keine Empfehlung, keine Provision" in vorlage

    block = ohne_umbrueche(js_funktion(vorlage, "openModal"))
    # Ohne Links bleibt der ganze Bereich verborgen – keine leere Ueberschrift.
    assert "mLinks.hidden = !(s.links && s.links.length);" in block
    # Ohne nofollow/ugc waere die Seite ein lohnendes Ziel fuer Link-Spam.
    assert "a.rel='noopener noreferrer nofollow ugc';" in block
    # Der Bereich muss bei jedem Oeffnen geleert werden, sonst stehen die
    # Quellen des zuvor angesehenen Skills noch da.
    assert "mLinksListe.textContent='';" in block


def test_gastgeber_kuerzt_www():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    rumpf = ohne_umbrueche(js_funktion(vorlage, "gastgeber"))
    assert "new URL(u).hostname.replace(/^www\\./,'')" in rumpf
    # Faellt das Zerlegen aus, darf der Dialog nicht leer bleiben.
    assert "catch" in rumpf
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q -k "bezugsquellen or gastgeber"`
Expected: FAIL — `assert 'id="m-links"' in vorlage`

- [ ] **Step 3: CSS ergänzen**

In `template.html` direkt nach der Zeile mit `.modal-von{…}` (Zeile 141) einfügen:

```css
.modal-links{margin-top:1rem}
.modal-links-titel{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:.5rem}
.modal-links-liste{display:flex;flex-wrap:wrap;gap:.5rem}
.modal-links-liste a{display:inline-flex;align-items:center;gap:.35rem;padding:.4rem .7rem;border:1px solid var(--border);border-radius:var(--r-xs);font-size:.82rem;color:var(--text);text-decoration:none;transition:border-color var(--tr),background var(--tr)}
.modal-links-liste a:hover{border-color:var(--active);background:var(--active-h)}
.modal-links-fuss{margin-top:.55rem;font-size:.72rem;color:var(--muted)}
```

- [ ] **Step 4: Markup ergänzen**

In `.modal-body` zwischen `m-tip` und `m-von` einfügen:

```html
      <div class="modal-links" id="m-links" hidden>
        <div class="modal-links-titel">Bezugsquellen</div>
        <div class="modal-links-liste" id="m-links-liste"></div>
        <div class="modal-links-fuss">Von Besuchern vorgeschlagen · keine Empfehlung, keine Provision</div>
      </div>
```

- [ ] **Step 5: `openModal` erweitern**

Die Variablenzeile (Zeile 419) ergänzen:

```js
var mEmoji=el('m-emoji'), mCat=el('m-cat'), mTitle=el('m-title'), mDesc=el('m-desc'), mTip=el('m-tip'), mVon=el('m-von');
var mLinks=el('m-links'), mLinksListe=el('m-links-liste');
```

Direkt davor `gastgeber` einfügen:

```js
/* Aufschrift des Knopfes ist der Hostname, nicht ein frei getippter Name:
   so sieht man vor dem Klick, wo man landet. Faellt das Zerlegen aus, steht
   die ganze Adresse da – besser als ein leerer Knopf. */
function gastgeber(u){
  try{ return new URL(u).hostname.replace(/^www\./,''); }
  catch(e){ return u; }
}
```

In `openModal` nach dem `mVon`-Block (nach Zeile 431) einfügen:

```js
  mLinksListe.textContent='';
  (s.links||[]).forEach(function(u){
    var a=document.createElement('a');
    a.href=u;
    a.target='_blank';
    a.rel='noopener noreferrer nofollow ugc';
    a.textContent='↗ '+gastgeber(u);
    mLinksListe.appendChild(a);
  });
  mLinks.hidden = !(s.links && s.links.length);
```

- [ ] **Step 6: Tests laufen lassen und die Seite neu bauen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q`
Expected: PASS

Run: `uv run build.py`
Expected: `✅ docs/skillsliste.html wurde neu erstellt.` — `git diff --stat docs/` zeigt nur erzeugte Dateien.

- [ ] **Step 7: Committen**

```bash
git add template.html tests/test_build.py docs/
git commit -m "Bezugsquellen: Knöpfe im Detail-Dialog der Skillsliste"
```

---

### Task 3: Link-Regeln im Worker (`pruefeLinks`)

**Files:**
- Modify: `worker/validate.js` (Konstanten am Kopf; neue Funktion vor `pruefeVorschlag`, Zeile ~107; Einbau in `pruefeVorschlag` Zeile 122-139 und `pruefeAenderung` Zeile 168-195)
- Test: `worker/validate.test.js`

**Interfaces:**
- Consumes: nichts.
- Produces: `pruefeLinks(rohe: unknown) -> {ok:true, links:string[]} | {ok:false, fehler:string}` (exportiert), `MAX_LINKS` (`3`) und `LINK_MAX_LAENGE` (`300`) als Exporte. `pruefeVorschlag` und `pruefeAenderung` liefern in `wert` zusätzlich `links: string[]`.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `worker/validate.test.js` anhängen (Importzeile oben um `pruefeLinks, MAX_LINKS` erweitern):

```js
test("ohne Angabe ist die Liste leer", () => {
  assert.deepEqual(pruefeLinks(undefined), { ok: true, links: [] });
  assert.deepEqual(pruefeLinks([]), { ok: true, links: [] });
});

test("normalisiert und entfernt Dubletten", () => {
  const ergebnis = pruefeLinks([
    "  https://www.skillsbox.ch/p/1  ",
    "https://www.skillsbox.ch/p/1",
    "",
  ]);
  assert.equal(ergebnis.ok, true);
  assert.deepEqual(ergebnis.links, ["https://www.skillsbox.ch/p/1"]);
});

test("mehr als drei Bezugsquellen werden abgelehnt", () => {
  const ergebnis = pruefeLinks([
    "https://a.ch/1", "https://b.ch/2", "https://c.ch/3", "https://d.ch/4",
  ]);
  assert.equal(ergebnis.ok, false);
  assert.match(ergebnis.fehler, /3/);
});

for (const [url, muster] of [
  ["http://a.ch/x", /https/],
  ["ftp://a.ch/x", /https/],
  ["javascript:alert(1)", /https/],
  ["https://bit.ly/abc", /Linkverk/],
  ["https://www.tinyurl.com/abc", /Linkverk/],
  ["https://192.168.0.1/x", /IP-Adresse/],
  ["https://[::1]/x", /IP-Adresse/],
  ["https://a.ch:8080/x", /Portnummer/],
  ["https://wer:was@a.ch/x", /Benutzerangabe/],
  ["https://ohnepunkt/x", /Hostnamen/],
  ["kein link", /Adresse/],
]) {
  test(`lehnt ab: ${url}`, () => {
    const ergebnis = pruefeLinks([url]);
    assert.equal(ergebnis.ok, false);
    assert.match(ergebnis.fehler, muster);
  });
}

test("zu lange Adresse wird abgelehnt", () => {
  const ergebnis = pruefeLinks(["https://a.ch/" + "x".repeat(300)]);
  assert.equal(ergebnis.ok, false);
  assert.match(ergebnis.fehler, /lang/);
});

test("spitze Klammern werden beim Normalisieren codiert", () => {
  // Sie duerfen den Kommentarblock im Issue nicht beenden koennen.
  const ergebnis = pruefeLinks(["https://a.ch/a-->b"]);
  assert.equal(ergebnis.ok, true);
  assert.equal(ergebnis.links[0].includes(">"), false);
});

test("ein neuer Skill traegt seine Bezugsquellen", () => {
  const ergebnis = pruefeVorschlag(
    { ...GUELTIG, links: ["https://a.ch/x"] },
    DATEN
  );
  assert.equal(ergebnis.ok, true);
  assert.deepEqual(ergebnis.wert.links, ["https://a.ch/x"]);
});

test("die http-Sperre gilt weiterhin fuer die Beschreibung", () => {
  // Kernpunkt des ganzen Entwurfs: NUR das Link-Feld darf eine Adresse tragen.
  const ergebnis = pruefeVorschlag(
    { ...GUELTIG, beschreibung: "Siehe http://a.ch", links: ["https://a.ch/x"] },
    DATEN
  );
  assert.equal(ergebnis.ok, false);
  assert.equal(ergebnis.fehler, "Links sind nicht erlaubt.");
});

test("eine Aenderung traegt ihre Bezugsquellen", () => {
  const ergebnis = pruefeAenderung(
    { ...AENDERUNG, links: ["https://a.ch/x"] },
    DATEN_MIT_SKILL
  );
  assert.equal(ergebnis.ok, true);
  assert.deepEqual(ergebnis.wert.links, ["https://a.ch/x"]);
});
```

`GUELTIG`, `DATEN`, `AENDERUNG` und `DATEN_MIT_SKILL` sind die in `worker/validate.test.js` bereits vorhandenen Testdaten (Zeilen 5, 11, 193, 209) — genau diese Namen verwenden, keine neuen erfinden.

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `cd worker && node --test`
Expected: FAIL — `pruefeLinks is not a function`

- [ ] **Step 3: `pruefeLinks` einbauen**

In `worker/validate.js` nach `EMOJI_CODEPUNKT_GRENZE` (Zeile 17) ergänzen:

```js
export const MAX_LINKS = 3;
export const LINK_MAX_LAENGE = 300;

// Linkverkuerzer verbergen das Ziel vor der Freigabe – die Pruefung im Issue
// waere wertlos – und ergaeben als Knopfaufschrift nur "bit.ly" statt eines
// erkennbaren Haendlers. Dieselbe Liste steht in build.py und in
// tools/vorschlaege_holen.py.
const VERKUERZER = new Set([
  "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
  "buff.ly", "rb.gy", "cutt.ly", "shorturl.at", "s.id", "lnkd.in",
]);

const IPV4 = /^\d{1,3}(\.\d{1,3}){3}$/;
```

Vor `pruefeVorschlag` (vor Zeile 108) einfügen:

```js
/**
 * Prueft die eingereichten Bezugsquellen.
 *
 * Das ist das EINZIGE Feld, das eine Adresse tragen darf – feldregeln() weist
 * fuer alle Textfelder weiterhin jedes "http" ab. Gespeichert wird die von
 * URL normalisierte Fassung: das codiert nebenbei spitze Klammern, die sonst
 * den Kommentarblock im Issue beenden koennten.
 *
 * Liefert {ok:true, links} oder {ok:false, fehler}.
 */
export function pruefeLinks(rohe) {
  if (rohe === undefined || rohe === null) {
    return { ok: true, links: [] };
  }
  if (!Array.isArray(rohe)) {
    return { ok: false, fehler: "Bezugsquellen sind unlesbar." };
  }
  const links = [];
  for (const eintrag of rohe) {
    const url = text(eintrag);
    if (!url) continue;
    if (url.length > LINK_MAX_LAENGE) {
      return {
        ok: false,
        fehler: `Zu lang: Bezugsquelle (max. ${LINK_MAX_LAENGE} Zeichen).`,
      };
    }
    let zerlegt;
    try {
      zerlegt = new URL(url);
    } catch {
      return { ok: false, fehler: "Bezugsquelle ist keine gültige Adresse." };
    }
    if (zerlegt.protocol !== "https:") {
      return { ok: false, fehler: "Bezugsquelle muss mit https:// beginnen." };
    }
    if (zerlegt.username || zerlegt.password) {
      return {
        ok: false,
        fehler: "Bezugsquelle darf keine Benutzerangabe (@) enthalten.",
      };
    }
    if (zerlegt.port) {
      return { ok: false, fehler: "Bezugsquelle darf keine Portnummer enthalten." };
    }
    const host = zerlegt.hostname.replace(/\.+$/, "");
    // Eckige Klammer: so schreibt URL eine IPv6-Adresse.
    if (host.startsWith("[") || IPV4.test(host)) {
      return { ok: false, fehler: "Bezugsquelle darf keine IP-Adresse sein." };
    }
    if (!host.includes(".")) {
      return { ok: false, fehler: "Bezugsquelle hat keinen gültigen Hostnamen." };
    }
    if (VERKUERZER.has(host.replace(/^www\./, ""))) {
      return { ok: false, fehler: "Linkverkürzer sind nicht erlaubt." };
    }
    if (!links.includes(zerlegt.href)) {
      links.push(zerlegt.href);
    }
    if (links.length > MAX_LINKS) {
      return { ok: false, fehler: `Höchstens ${MAX_LINKS} Bezugsquellen.` };
    }
  }
  return { ok: true, links };
}
```

- [ ] **Step 4: In beide Prüffunktionen einhängen**

In `pruefeVorschlag`, nach der Kategorie-Prüfung und **vor** dem Aufbau von `wert`:

```js
  const quellen = pruefeLinks(roh.links);
  if (!quellen.ok) {
    return { ok: false, fehler: quellen.fehler };
  }
```

und im `wert`-Objekt nach `von: text(roh.von),` ergänzen:

```js
    links: quellen.links,
```

In `pruefeAenderung` genau dasselbe: die drei Zeilen nach der `original`-Prüfung, und `links: quellen.links,` nach `erg: text(roh.erg),`.

- [ ] **Step 5: Tests laufen lassen, grün bestätigen**

Run: `cd worker && node --test`
Expected: PASS, alle Tests

- [ ] **Step 6: Committen**

```bash
git add worker/validate.js worker/validate.test.js
git commit -m "Bezugsquellen: pruefeLinks im Worker, http-Sperre bleibt fuer Textfelder"
```

---

### Task 4: Bezugsquellen im Issue-Rumpf

**Files:**
- Modify: `worker/index.js` (`issueRumpf` Zeile 77-96, `issueRumpfAenderung` Zeile 103-123)
- Test: `worker/index.test.js`

**Interfaces:**
- Consumes: `wert.links` (`string[]`) aus Task 3; `alt.links` aus `docs/skills-daten.json` (kann bei altem Datenstand fehlen).
- Produces: `quellen(liste: string[]|undefined) -> string` (exportiert, für Task 5 nicht nötig, aber getestet).

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `worker/index.test.js` anhängen (Importzeile um `quellen` erweitern):

```js
test("Bezugsquellen stehen in der Tabelle eines neuen Skills", () => {
  const rumpf = issueRumpf({
    stufe: "Hoch", kategorie: "Ablenkung", emoji: "🎧",
    titel: "Musik", beschreibung: "Ein Lied", tipp: "", von: "",
    links: ["https://a.ch/x", "https://b.ch/y"],
  });
  assert.match(rumpf, /\| Bezugsquellen \| https:\/\/a\.ch\/x<br>https:\/\/b\.ch\/y \|/);
});

test("ohne Bezugsquellen steht ein Strich", () => {
  const rumpf = issueRumpf({
    stufe: "Hoch", kategorie: "Ablenkung", emoji: "🎧",
    titel: "Musik", beschreibung: "Ein Lied", tipp: "", von: "", links: [],
  });
  assert.match(rumpf, /\| Bezugsquellen \| — \|/);
});

test("die Aenderung stellt alte und neue Quellen nebeneinander", () => {
  const rumpf = issueRumpfAenderung(
    { stufe: "Hoch", kategorie: "Ablenkung", emoji: "🎧", titel: "Musik",
      beschreibung: "Neu", tipp: "", erg: "", original: "Musik",
      links: ["https://neu.ch/x"] },
    { e: "🎧", t: "Musik", b: "Alt", tip: "", links: ["https://alt.ch/x"] }
  );
  assert.match(rumpf, /\| Bezugsquellen \| https:\/\/alt\.ch\/x \| https:\/\/neu\.ch\/x \|/);
});

test("ein alter Datenstand ohne links bricht nicht", () => {
  // docs/skills-daten.json wird zwischengespeichert; eine Fassung von vor
  // dieser Neuerung darf den Worker nicht umwerfen.
  assert.equal(quellen(undefined), "—");
});
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `cd worker && node --test`
Expected: FAIL — `quellen is not a function` bzw. fehlende Tabellenzeile

- [ ] **Step 3: `quellen` einbauen und beide Rümpfe erweitern**

In `worker/index.js` nach `zelle` (nach Zeile 75) einfügen:

```js
/**
 * Bezugsquellen fuer eine Tabellenzelle. Undefiniert kommt vor: ein
 * zwischengespeicherter Datenstand von vor dieser Neuerung kennt das Feld nicht.
 */
export function quellen(liste) {
  return liste && liste.length ? liste.map(zelle).join("<br>") : "—";
}
```

In `issueRumpf` nach der `Name`-Zeile ergänzen:

```js
    `| Bezugsquellen | ${quellen(w.links)} |`,
```

In `issueRumpfAenderung` nach der `Tipp`-Zeile ergänzen:

```js
    `| Bezugsquellen | ${quellen(alt.links)} | ${quellen(w.links)} |`,
```

- [ ] **Step 4: Tests laufen lassen, grün bestätigen**

Run: `cd worker && node --test`
Expected: PASS

- [ ] **Step 5: Committen**

```bash
git add worker/index.js worker/index.test.js
git commit -m "Bezugsquellen: im Issue-Rumpf sichtbar, alt neben neu"
```

---

### Task 5: Erreichbarkeits-Notiz beim Einreichen

**Files:**
- Modify: `worker/index.js` (neue Funktionen nach `quellen`; Aufruf im `fetch`-Handler nach der Prüfung, Zeile ~207)
- Test: `worker/index.test.js`

**Interfaces:**
- Consumes: `wert.links` aus Task 3.
- Produces: `linkBefund(url: string) -> Promise<string>` und `mitBefunden(rumpf: string, befunde: string[]) -> string` (beide exportiert).

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `worker/index.test.js` anhängen (Import um `linkBefund, mitBefunden` erweitern):

```js
function mitStubFetch(antwort, lauf) {
  const echt = globalThis.fetch;
  globalThis.fetch = async () => {
    if (antwort instanceof Error) throw antwort;
    return antwort;
  };
  try {
    return lauf();
  } finally {
    globalThis.fetch = echt;
  }
}

test("200 gilt als erreichbar", async () => {
  const befund = await mitStubFetch({ ok: true, status: 200 }, () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^✓ https:\/\/a\.ch\/x — 200 OK$/);
});

test("404 wird als toter Link gemeldet", async () => {
  const befund = await mitStubFetch({ ok: false, status: 404 }, () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^⚠ /);
  assert.match(befund, /404/);
});

test("410 wird als toter Link gemeldet", async () => {
  const befund = await mitStubFetch({ ok: false, status: 410 }, () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^⚠ /);
});

test("403 ist keine Aussage – Shops sperren Bots aus", async () => {
  const befund = await mitStubFetch({ ok: false, status: 403 }, () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^· /);
  assert.match(befund, /keine Aussage/);
});

test("ein Netzwerkfehler ist keine Aussage", async () => {
  const befund = await mitStubFetch(new Error("weg"), () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^· /);
  assert.match(befund, /keine Aussage/);
});

test("ohne Befunde bleibt der Rumpf unveraendert", () => {
  assert.equal(mitBefunden("RUMPF", []), "RUMPF");
});

test("Befunde stehen NACH dem Kommentarblock", () => {
  // Der Block muss der einzige bleiben: parse_body in vorschlaege_holen.py
  // verwirft ein Issue mit mehr als einem Block.
  const rumpf = issueRumpf({
    stufe: "Hoch", kategorie: "Ablenkung", emoji: "🎧",
    titel: "Musik", beschreibung: "Ein Lied", tipp: "", von: "", links: [],
  });
  const ganz = mitBefunden(rumpf, ["✓ https://a.ch/x — 200 OK"]);
  assert.equal(ganz.match(/<!-- vorschlag/g).length, 1);
  assert.ok(ganz.indexOf("Erreichbarkeit") > ganz.indexOf("<!-- vorschlag"));
});
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `cd worker && node --test`
Expected: FAIL — `linkBefund is not a function`

- [ ] **Step 3: Die beiden Funktionen einbauen**

In `worker/index.js` nach `quellen` einfügen:

```js
/**
 * Ruft eine Bezugsquelle einmal ab und fasst das Ergebnis in einer Zeile.
 *
 * Lehnt NIE ab: ein Shop, der Cloudflare-Adressen aussperrt, darf keine
 * ehrliche Einreichung blockieren – der Link funktioniert im Browser tadellos,
 * und die einreichende Person haette keine Chance zu verstehen, was von ihr
 * verlangt wird. Die Zeile ist Entscheidungshilfe fuer die Freigabe, nicht mehr.
 *
 * Darum gilt nur 404/410 als Befund; 403, 429 und 5xx heissen "keine Aussage".
 *
 * Der Abruf ist ungefaehrlich, weil pruefeLinks vorher nur https ohne Port und
 * ohne IP-Adresse durchgelassen hat – auf interne Adressen laesst sich der
 * Worker damit nicht richten.
 */
export async function linkBefund(url) {
  try {
    const res = await fetch(url, {
      method: "GET",
      redirect: "follow",
      headers: { "user-agent": "toolbox-linkpruefung" },
      signal: AbortSignal.timeout(5000),
    });
    if (res.status === 404 || res.status === 410) {
      return `⚠ ${url} — ${res.status}, Link zeigt ins Leere`;
    }
    if (res.ok) {
      return `✓ ${url} — ${res.status} OK`;
    }
    return `· ${url} — ${res.status}, keine Aussage`;
  } catch {
    return `· ${url} — nicht erreichbar, keine Aussage`;
  }
}

/**
 * Haengt die Befunde an den Rumpf – hinter den Kommentarblock, damit dieser
 * der einzige bleibt (parse_body in vorschlaege_holen.py verwirft ein Issue
 * mit mehr als einem Block).
 */
export function mitBefunden(rumpf, befunde) {
  if (!befunde.length) {
    return rumpf;
  }
  return (
    rumpf +
    "\n**Erreichbarkeit beim Einreichen**\n\n```\n" +
    befunde.join("\n") +
    "\n```\n"
  );
}
```

- [ ] **Step 4: Im `fetch`-Handler aufrufen**

Nach der `if (!geprueft.ok)`-Prüfung (nach Zeile 207) einfügen:

```js
    const quellenListe = geprueft.wert.links || [];
    const befunde = quellenListe.length
      ? await Promise.all(quellenListe.map(linkBefund))
      : [];
```

und den `body` im Issue-Aufruf umschreiben:

```js
          body: mitBefunden(
            istAenderung
              ? issueRumpfAenderung(geprueft.wert, altenSkillFinden(daten, geprueft.wert))
              : issueRumpf(geprueft.wert),
            befunde
          ),
```

- [ ] **Step 5: Tests laufen lassen, grün bestätigen**

Run: `cd worker && node --test`
Expected: PASS

- [ ] **Step 6: Committen**

```bash
git add worker/index.js worker/index.test.js
git commit -m "Bezugsquellen: Erreichbarkeits-Notiz im Issue, blockiert nie"
```

---

### Task 6: Dynamische Link-Liste im Vorschlagsformular

**Files:**
- Modify: `template-vorschlag.html` (CSS bei `.emoji-zeile`, Zeile 49-56; Markup nach dem Tipp-Feld, Zeile 152; JS bei `originalUebernehmen` Zeile 397, `ENTWURF_FELDER` Zeile 419, `entwurfSichern` Zeile 422, `felderSetzen` Zeile 431, Absende-Rumpf Zeile 534-556)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `s.links` aus `DATEN` (Task 1); die Worker-Regeln aus Task 3.
- Produces: sendet `links: string[]` an den Worker.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_build.py` anhängen:

```python
def vorschlagsvorlage():
    return build.TEMPLATE_VORSCHLAG.read_bytes().decode("utf-8-sig")


def test_formular_hat_dynamische_linkliste():
    vorlage = vorschlagsvorlage()
    assert 'id="links-liste"' in vorlage
    assert 'id="link-plus"' in vorlage
    assert "var MAX_LINKS = 3;" in vorlage
    # type=url braucht dieselbe Gestaltung wie die uebrigen Felder, sonst
    # steht ein nacktes Eingabefeld mitten im Formular.
    assert "input[type=text],input[type=url],textarea,select{" in vorlage


def test_letzte_linkzeile_wird_geleert_statt_entfernt():
    vorlage = vorschlagsvorlage()
    rumpf = ohne_umbrueche(js_funktion(vorlage, "linkZeileBauen"))
    assert "if(el('links-liste').children.length>1){ zeile.remove(); }" in rumpf
    assert "else { feld.value=''; }" in rumpf


def test_entwurf_traegt_die_links_mit():
    vorlage = vorschlagsvorlage()
    # Ohne diese beiden Zeilen verlieren die Links beim Reiterwechsel ihren
    # Inhalt – genau der Fehler, gegen den es die Entwuerfe ueberhaupt gibt.
    assert "e.links=linksLesen();" in ohne_umbrueche(js_funktion(vorlage, "entwurfSichern"))
    assert "linksSetzen(e?e.links:[]);" in ohne_umbrueche(js_funktion(vorlage, "felderSetzen"))


def test_ergaenzen_fuellt_die_bestehenden_links_vor():
    vorlage = vorschlagsvorlage()
    rumpf = ohne_umbrueche(js_funktion(vorlage, "originalUebernehmen"))
    # Traegt das Vorausfuellen die Links nicht mit, wuerde eine Ergaenzung sie
    # loeschen: das Uebernahme-Skript ersetzt die Spalten vollstaendig.
    assert "linksSetzen(s.links||[]);" in rumpf


def test_beide_absende_ruempfe_schicken_links():
    assert vorschlagsvorlage().count("links:linksLesen(),") == 2
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q -k "link"`
Expected: FAIL — `assert 'id="links-liste"' in vorlage`

- [ ] **Step 3: CSS ergänzen**

In `template-vorschlag.html` die Zeile 49 und 52 erweitern (`input[type=url]` aufnehmen):

```css
    input[type=text],input[type=url],textarea,select{
      width:100%;padding:10px 12px;font-family:inherit;font-size:1rem;color:var(--text);
      background:var(--bg);border:1px solid var(--border);border-radius:10px}
    input[type=text]:focus,input[type=url]:focus,textarea:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
```

Nach `.emoji-zeile input{…}` (Zeile 56) einfügen:

```css
    .link-zeile{display:flex;gap:8px;align-items:stretch;margin-bottom:8px}
    .link-zeile input{flex:1;min-width:0}
    .link-weg{flex:0 0 auto;font-size:1.1rem;font-weight:600;padding:0 14px;
      border:1px solid var(--border);border-radius:10px;background:var(--card);
      color:var(--muted);cursor:pointer;transition:background .15s ease}
    .link-weg:hover{background:var(--accent-tint);color:var(--accent-dark)}
    .link-plus{font-size:.85rem;padding:8px 14px;border:1px solid var(--border);
      border-radius:10px;background:var(--card);color:var(--accent-dark);cursor:pointer}
    .link-plus:hover:not(:disabled){background:var(--accent-tint)}
    .link-plus:disabled{opacity:.5;cursor:not-allowed}
```

- [ ] **Step 4: Markup ergänzen**

Nach dem Tipp-Feld (nach Zeile 152) und **vor** dem Feld „Dein Name" einfügen:

```html
      <div class="feld">
        <label id="links-label">Bezugsquellen <span class="hinweis" style="display:inline">(freiwillig, höchstens 3)</span></label>
        <p class="hinweis">Wo bekommt man das Nötige? Vollständige Adresse mit <strong>https://</strong> — keine Kurzlinks (bit.ly und ähnliche).</p>
        <div id="links-liste" role="group" aria-labelledby="links-label"></div>
        <button type="button" class="link-plus" id="link-plus">+ Bezugsquelle hinzufügen</button>
      </div>
```

- [ ] **Step 5: Die Listenverwaltung einbauen**

In `template-vorschlag.html` vor `function skillsDerKategorie()` (vor Zeile 378) einfügen:

```js
/* Bezugsquellen: eine dynamische Liste statt drei starrer Felder. Muss zu
   MAX_LINKS in worker/validate.js passen. */
var MAX_LINKS = 3;

function linkKnopfNachziehen(){
  el('link-plus').disabled = el('links-liste').children.length >= MAX_LINKS;
}

function linkZeileBauen(wert){
  var zeile=document.createElement('div');
  zeile.className='link-zeile';
  var feld=document.createElement('input');
  feld.type='url';
  feld.inputMode='url';
  feld.placeholder='https://';
  feld.setAttribute('aria-label','Bezugsquelle');
  feld.value=wert||'';
  var weg=document.createElement('button');
  weg.type='button';
  weg.className='link-weg';
  weg.setAttribute('aria-label','Diese Bezugsquelle entfernen');
  weg.textContent='×';
  weg.addEventListener('click', function(){
    /* Die letzte Zeile wird geleert statt entfernt: sonst staende das Formular
       ohne jedes Eingabefeld da, und der Plus-Knopf waere der einzige Weg
       zurueck – das sieht wie ein Fehler aus. */
    if(el('links-liste').children.length>1){ zeile.remove(); }
    else { feld.value=''; }
    linkKnopfNachziehen();
  });
  zeile.appendChild(feld);
  zeile.appendChild(weg);
  return zeile;
}

function linksSetzen(liste){
  var behaelter=el('links-liste');
  behaelter.textContent='';
  var werte=(liste&&liste.length)?liste.slice(0,MAX_LINKS):[''];
  werte.forEach(function(w){ behaelter.appendChild(linkZeileBauen(w)); });
  linkKnopfNachziehen();
}

function linksLesen(){
  var raus=[];
  Array.prototype.forEach.call(el('links-liste').querySelectorAll('input'), function(f){
    var w=f.value.trim();
    if(w && raus.indexOf(w)<0){ raus.push(w); }
  });
  return raus;
}

el('link-plus').addEventListener('click', function(){
  if(el('links-liste').children.length>=MAX_LINKS){ return; }
  var zeile=linkZeileBauen('');
  el('links-liste').appendChild(zeile);
  zeile.querySelector('input').focus();
  linkKnopfNachziehen();
});

linksSetzen([]);
```

- [ ] **Step 6: In Vorausfüllen, Entwurf und Absenden einhängen**

In `originalUebernehmen`, als letzte Zeile vor der schliessenden Klammer:

```js
  linksSetzen(s.links||[]);
```

In `entwurfSichern`, nach der `ENTWURF_FELDER`-Schleife:

```js
  e.links=linksLesen();
```

In `felderSetzen`, nach der `ENTWURF_FELDER`-Schleife:

```js
  linksSetzen(e?e.links:[]);
```

Im Absende-Rumpf **beide** Zweige ergänzen — im `aenderung`-Zweig nach `erg:el('von').value,` und im `neu`-Zweig nach `von:el('von').value,` jeweils:

```js
        links:linksLesen(),
```

- [ ] **Step 7: Tests laufen lassen und die Seite neu bauen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q`
Expected: PASS

Run: `uv run build.py`
Expected: alle drei ✅-Zeilen

- [ ] **Step 8: Von Hand anschauen**

`docs/skill-vorschlagen.html` im Browser öffnen und prüfen:
- eine leere Zeile ist da, `+` fügt bis drei an, dann ist der Knopf ausgegraut
- `×` entfernt eine Zeile; bei nur einer Zeile leert es sie stattdessen
- Reiterwechsel „Neuer Skill" ↔ „Bestehenden ergänzen" verliert nichts
- ein Skill mit Links im Ergänzen-Reiter füllt die Zeilen vor

- [ ] **Step 9: Committen**

```bash
git add template-vorschlag.html tests/test_build.py docs/
git commit -m "Bezugsquellen: dynamische Linkliste im Vorschlagsformular"
```

---

### Task 7: Übernahme in die Excel

**Files:**
- Modify: `tools/vorschlaege_holen.py` (Konstanten Zeile 54-104, `pruefe_eintrag` Zeile 154-237, `bereinigt` Zeile 240-251)
- Test: `tests/test_vorschlaege_holen.py`

**Interfaces:**
- Consumes: `links` aus dem JSON-Block des Issues (Task 3/4); `build.pruefe_link`, `build.LINK_SPALTEN`, `build.LINK_MAX_LAENGE`, `build.VERKUERZER` (Task 1) — **per Import**, nicht als Kopie.
- Produces: Spalten `Link1..Link3` im Blatt `Skills`.

**Entscheidung des Auftraggebers (weicht vom ursprünglichen Entwurf ab):** Die
URL-Regeln werden **importiert, nicht kopiert**. `GRENZEN` steht in diesem
Projekt zwar doppelt, aber das sind vier Zeilen Daten — `pruefe_link` sind
vierzig Zeilen Logik mit sieben Regeln, und `vorschlaege_holen.py` ruft
`build.py` ohnehin bereits auf. Eine Kopie könnte auseinanderlaufen; ein Import
kann es nicht.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_vorschlaege_holen.py` anhängen:

```python
LINK_KOPF = KOPF + ["Link1", "Link2", "Link3"]


def mappe_mit_kopf(tmp_path, kopf):
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(kopf)
    wb.save(pfad)
    return pfad


def test_die_regeln_kommen_aus_build():
    """Eine Quelle, nicht zwei. Eine Kopie koennte auseinanderlaufen: der
    Worker liesse dann etwas durch, das der Build spaeter ablehnt – und der
    Vorschlag steckte in der Excel fest."""
    import build

    assert vh.pruefe_link is build.pruefe_link
    assert vh.LINK_SPALTEN is build.LINK_SPALTEN


def test_neue_zeile_traegt_die_links(tmp_path):
    pfad = mappe_mit_kopf(tmp_path, LINK_KOPF)

    vh.in_excel_uebernehmen(
        pfad, [], [{**BEISPIEL, "links": ["https://a.ch/x", "https://b.ch/y"]}]
    )

    ws = openpyxl.load_workbook(pfad)["Skills"]
    zeile = dict(zip([c.value for c in ws[1]], [c.value for c in ws[2]]))
    assert zeile["Link1"] == "https://a.ch/x"
    assert zeile["Link2"] == "https://b.ch/y"
    assert zeile["Link3"] == ""


def test_fehlende_linkspalten_werden_angelegt(tmp_path):
    pfad = mappe_mit_kopf(tmp_path, KOPF)     # KOPF kennt die Link-Spalten nicht

    vh.in_excel_uebernehmen(pfad, [], [{**BEISPIEL, "links": ["https://a.ch/x"]}])

    kopf = [c.value for c in openpyxl.load_workbook(pfad)["Skills"][1]]
    assert kopf[-3:] == ["Link1", "Link2", "Link3"]


def test_aenderung_ersetzt_die_links_vollstaendig(tmp_path):
    """Das Formular schickt die Liste vollstaendig zurueck – ein Link, der
    nicht mehr dabei ist, wurde absichtlich entfernt."""
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(LINK_KOPF)
    ws.append(["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.", "",
               "Max", "", "https://alt.ch/1", "https://alt.ch/2", ""])
    wb.save(pfad)

    vh.in_excel_uebernehmen(pfad, [{**AENDERUNG, "links": ["https://neu.ch/1"]}], [])

    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    zeile = dict(zip([c.value for c in ws2[1]], [c.value for c in ws2[2]]))
    assert zeile["Link1"] == "https://neu.ch/1"
    assert zeile["Link2"] == ""


@pytest.mark.parametrize(
    "url",
    ["http://a.ch/x", "https://bit.ly/x", "https://10.0.0.1/x",
     "https://a.ch:8080/x", "https://ohnepunkt/x"],
)
def test_ungueltiger_link_wird_abgelehnt(url):
    assert vh.pruefe_eintrag({**BEISPIEL, "links": [url]}, BESTAND) is not None


def test_mehr_als_drei_links_werden_abgelehnt():
    meldung = vh.pruefe_eintrag(
        {**BEISPIEL, "links": [f"https://a{i}.ch/x" for i in range(4)]}, BESTAND
    )
    assert meldung is not None
    assert "3" in meldung


def test_beschreibung_darf_weiterhin_keinen_link_tragen():
    meldung = vh.pruefe_eintrag(
        {**BEISPIEL, "beschreibung": "Siehe http://a.ch", "links": []}, BESTAND
    )
    assert meldung == "Links sind nicht erlaubt."
```

`BEISPIEL` (Zeile 17), `BESTAND` (bei den Prüf-Tests), `KOPF` und `AENDERUNG` (bei den Änderungs-Tests) sind in `tests/test_vorschlaege_holen.py` **bereits vorhanden** — genau diese verwenden. Die neuen Tests gehören ans Dateiende, nach `AENDERUNG`, sonst ist der Name dort noch nicht definiert.

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_vorschlaege_holen.py -q -k link`
Expected: FAIL — `AttributeError: module 'vorschlaege_holen' has no attribute 'VERKUERZER'`

- [ ] **Step 3: Regeln aus `build.py` importieren**

In `tools/vorschlaege_holen.py` nach der Zeile `ROOT = Path(__file__).resolve().parent.parent` (Zeile 43) einfügen:

```python
# Die URL-Regeln kommen aus build.py – EINE Quelle. Eine Kopie koennte
# auseinanderlaufen: der Worker liesse dann etwas durch, das der Build spaeter
# ablehnt, und der Vorschlag steckte in der Excel fest. build.py liegt im
# Wurzelverzeichnis, dieses Skript in tools/ – daher der Pfad-Eintrag.
# (Die JavaScript-Fassung in worker/validate.js haelt niemand; dort ist beim
# Aendern Handarbeit gefragt.)
sys.path.insert(0, str(ROOT))
from build import LINK_MAX_LAENGE, LINK_SPALTEN, VERKUERZER, pruefe_link  # noqa: E402

MAX_LINKS = len(LINK_SPALTEN)
```

`VERKUERZER` und `LINK_MAX_LAENGE` werden hier nicht direkt gebraucht, sondern
über `pruefe_link` — sie stehen im Import, damit der Test sie greifen kann und
damit beim Lesen sichtbar ist, woher die Regeln stammen.

> `sys` ist bereits importiert (Zeile 32); `ROOT` ist bereits definiert. Der
> Import muss **nach** `ROOT` stehen, darum das `# noqa: E402`.

`SPALTEN` und `SPALTEN_AENDERUNG` je um drei Einträge erweitern:

```python
    ("Link1", "link1"),
    ("Link2", "link2"),
    ("Link3", "link3"),
```

- [ ] **Step 4: `pruefe_eintrag` und `bereinigt` erweitern**

In `pruefe_eintrag`, unmittelbar vor `return None` am Ende:

```python
    rohe = eintrag.get("links")
    rohe = rohe if isinstance(rohe, list) else []
    gesehen = []
    for roh in rohe:
        url = sauber(roh)
        if not url:
            continue
        geprueft, meldung = pruefe_link(url)
        if meldung:
            return f"Bezugsquelle abgelehnt: {meldung}."
        if geprueft not in gesehen:
            gesehen.append(geprueft)
    if len(gesehen) > MAX_LINKS:
        return f"Hoechstens {MAX_LINKS} Bezugsquellen je Skill."
```

In `bereinigt`, **nach** der bestehenden Schleife (nach Zeile 250):

```python
    # Die Liste aus dem Issue auf die drei Excel-Spalten verteilen. Luecken
    # entstehen dabei nicht: leere Eintraege fallen weg, der Rest rueckt auf.
    rohe = eintrag.get("links")
    rohe = rohe if isinstance(rohe, list) else []
    liste = []
    for roh in rohe:
        url = sauber(roh)
        if url and url not in liste:
            liste.append(url)
    for i in range(len(LINK_SPALTEN)):
        ergebnis[f"link{i + 1}"] = liste[i] if i < len(liste) else ""
```

- [ ] **Step 5: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_vorschlaege_holen.py -q`
Expected: PASS

- [ ] **Step 6: Committen**

```bash
git add tools/vorschlaege_holen.py tests/test_vorschlaege_holen.py
git commit -m "Bezugsquellen: Uebernahme in die Excel samt Spaltenanlage"
```

---

### Task 8: Excel-Neuaufbau und Dokumentation

**Files:**
- Modify: `tools/seed_excel.py` (Zeile 93, 97-109), `CLAUDE.md`, `ANLEITUNG.md`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `skill["links"]` (Task 1).
- Produces: nichts.

- [ ] **Step 1: Den fehlschlagenden Test schreiben**

An `tests/test_build.py` anhängen:

```python
def test_seed_excel_kennt_die_linkspalten():
    """Ein Zurücksetzen der Mappe darf die Bezugsquellen nicht verlieren."""
    quelle = (build.ROOT / "tools" / "seed_excel.py").read_text(encoding="utf-8")
    assert '"Link1", "Link2", "Link3"' in quelle
    assert 's.get("links"' in quelle
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q -k seed_excel`
Expected: FAIL

- [ ] **Step 3: `tools/seed_excel.py` erweitern**

Kopfzeile (Zeile 93):

```python
    ws.append(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp",
               "Von", "Ergaenzt", "Link1", "Link2", "Link3"])
```

In der Zeilen-Schleife nach `s.get("erg", "")` ergänzen:

```python
                        *(list(s.get("links", [])) + ["", "", ""])[:3],
```

Spaltenbreiten (Zeile 109):

```python
    style_sheet(ws, 11, [9, 18, 8, 26, 60, 55, 16, 16, 40, 40, 40], emoji_col=3)
```

- [ ] **Step 4: Test laufen lassen und `seed_excel` gegenprüfen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q`
Expected: PASS

Run: `uv run tools/seed_excel.py && uv run build.py && git diff --stat skills_daten.xlsx docs/`
Expected: `build.py` läuft ohne Fehler durch; die erzeugten Seiten bleiben inhaltlich gleich.

> Wichtig: `seed_excel.py` **überschreibt** `skills_daten.xlsx`. Vorher `git status` prüfen und die Datei notfalls mit `git checkout -- skills_daten.xlsx` zurückholen.

- [ ] **Step 5: `CLAUDE.md` ergänzen**

Im Abschnitt „Skillsliste pflegen" nach der Beschreibung des Blattes `Skills` einfügen:

```markdown
Drei weitere Spalten `Link1`, `Link2`, `Link3` nehmen **Bezugsquellen** auf —
reine `https`-Adressen, jede darf leer bleiben, Lücken werden beim Bauen
zusammengeschoben. Im Detail-Dialog werden daraus Knöpfe, deren Aufschrift der
Hostname ist (`skillsbox.ch`); ohne Link erscheint der Bereich gar nicht.

**Die URL-Regeln stehen an zwei Stellen:**

- `build.py` → `pruefe_link`, `VERKUERZER`, `LINK_MAX_LAENGE`, `LINK_SPALTEN`.
  `tools/vorschlaege_holen.py` **importiert** sie von dort — bewusst keine
  Kopie, anders als bei `GRENZEN` (das sind vier Zeilen Daten, dies ist Logik).
- `worker/validate.js` → `pruefeLinks`, `VERKUERZER`, `LINK_MAX_LAENGE`,
  `MAX_LINKS`.

Die JavaScript-Fassung hält **niemand** mit der Python-Seite zusammen — wird
sie beim Ändern vergessen, lässt der Worker etwas durch, das der Build später
ablehnt, und der Vorschlag steckt in der Excel fest.

**Die `http`-Sperre im Worker gilt weiterhin für Titel, Beschreibung, Tipp und
Name.** Nur das Link-Feld ist ausgenommen. Diese Sperre ist die Spam-Abwehr des
Formulars — sie darf nicht „vereinheitlicht" werden.
```

- [ ] **Step 6: `ANLEITUNG.md` ergänzen**

Beim Abschnitt zum Blatt `Skills` einfügen:

```markdown
## Bezugsquellen (wo man etwas bestellen kann)

Ganz rechts im Blatt `Skills` stehen drei Spalten: **Link1**, **Link2**,
**Link3**. Dort kommt hinein, wo man das Nötige bekommt — zum Beispiel die
Adresse eines Shops für einen Zauberwürfel. Auf der Website werden daraus
Knöpfe im Fenster, das aufgeht, wenn man einen Skill antippt.

- **Alle drei dürfen leer bleiben.** Dann erscheinen gar keine Knöpfe.
- **Auch Lücken sind in Ordnung.** Steht nur in `Link2` etwas, ist das richtig
  so — beim Bauen rückt es von selbst auf.
- Die Adresse muss **mit `https://` anfangen** und vollständig sein. Am
  einfachsten: die Seite im Browser öffnen und die Adresse oben kopieren.
- **Kurzlinks werden nicht angenommen** (`bit.ly`, `tinyurl.com` und ähnliche).
  Man sieht ihnen nicht an, wohin sie führen.

Stimmt eine Adresse nicht, hält `build.bat` an und sagt, in welcher **Zeile**
und welcher **Spalte** — also genau, wo in der Excel nachzuschauen ist. Es
wird dann nichts erzeugt; nach dem Korrigieren einfach nochmals starten.
```

- [ ] **Step 7: Alles laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Expected: PASS, keine Fehlschläge

Run: `cd worker && node --test`
Expected: PASS

- [ ] **Step 8: Committen**

```bash
git add tools/seed_excel.py tests/test_build.py CLAUDE.md ANLEITUNG.md
git commit -m "Bezugsquellen: Excel-Neuaufbau und Dokumentation"
```

---

## Nach Stufe 1

Der Worker muss neu veröffentlicht werden (`worker/README.md`), sonst kennt die
Live-Fassung das Feld `links` nicht und verwirft es stillschweigend. Erst danach
kommen Bezugsquellen über das Formular an.

Stufe 2 (`plans/2026-08-06-bezugsquellen-stufe2.md`) bringt den wöchentlichen
Wächter gegen Linkfäule.
