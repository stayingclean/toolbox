# Beschriftete Bezugsquellen mit Shop-Symbol — Umsetzungsplan

> **Für agentische Bearbeitung:** ERFORDERLICHER UNTER-SKILL: `superpowers:subagent-driven-development` (empfohlen) oder `superpowers:executing-plans`, Aufgabe für Aufgabe. Schritte sind als Kästchen (`- [ ]`) geführt.

**Ziel:** Ein Bezugsquellen-Knopf zeigt das Symbol des Händlers und eine von Hand gepflegte Beschriftung (`🟧 Igelball`) statt dreimal denselben Hostnamen.

**Architektur:** Drei neue Excel-Spalten `Text1`–`Text3`, paarweise verschränkt mit `Link1`–`Link3`. `links` wird in den erzeugten Daten von einer Liste von Zeichenketten zu einer Liste von Objekten `{u, t}`. Die Symbole liegen als Dateien im Repo und werden beim Bauen als `data:`-URI eingebettet — einmal je Hostname in einer eigenen Tabelle, nicht je Link, sonst stünde dieselbe Bilddatei fünfzigmal in der Seite.

**Tech Stack:** Python 3.11 + openpyxl (uv-Skripte), Pillow nur im Hilfsskript, Vanilla-JS in den Vorlagen, Cloudflare Worker (`node --test`).

**Zugehöriger Entwurf:** `specs/2026-08-07-linkbeschriftung-design.md`
**Baut auf:** `feature/skill-bezugsquellen` (PR #7) — ohne dessen Link-Spalten läuft nichts davon.

## Global Constraints

- **`Text*` ist freiwillig, höchstens 30 Zeichen**, ohne spitze Klammern, ohne `http`. Konstante: `TEXT_MAX_LAENGE`.
- **Ein `Text*` ohne zugehörigen `Link*` bricht den Build ab** — sonst stünde eine Beschriftung ohne Ziel in der Mappe und niemand sähe es.
- **Ohne Beschriftung bleibt es beim Hostnamen** wie bisher.
- **Fehlt eine Symboldatei, gibt es kein Symbol und der Build läuft weiter.** Wer eine Bezugsquelle bei einem neuen Händler einträgt, darf damit nicht die Website blockieren.
- **Kein Netzwerkzugriff in `build.py`** und in keinem Test. Symbole werden ausschliesslich aus `assets/favicons/` gelesen.
- **Jeder Link trägt `title` mit der vollständigen Adresse** und weiterhin `rel="noopener noreferrer nofollow ugc"`.
- **Das Symbol ist Schmuck:** `<img alt="">`. Die Beschriftung daneben trägt die Bedeutung.
- **Umlaute je Datei** (aus Stufe 1 übernommen): `build.py`, `template.html`, `tests/test_build.py` → echte Umlaute in Kommentaren und lesbarem Text. `template-vorschlag.html`, `worker/*.js`, `tools/*.py` → ASCII-Transliteration in Kommentaren, echte Umlaute in Text, den jemand liest. Bezeichner bleiben überall ASCII.
- **Generiert, nie von Hand bearbeiten:** `docs/skillsliste.html`, `docs/skill-vorschlagen.html`, `docs/skills-daten.json`.
- **Tests:** `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q` (aktuell 155) und `cd worker && node --test` (aktuell 81).

---

### Task 1: Text-Spalten und die neue Datenform

**Files:**
- Modify: `build.py` (Konstanten bei `LINK_SPALTEN` Zeile 72; neue `pruefe_text`; `optional_header` Zeile 229; Skill-Aufbau Zeile 294-318)
- Modify: `worker/index.js` (`quellen`, Zeile 88-92)
- Modify: `template-vorschlag.html` (`originalUebernehmen`, Zeile 487)
- Test: `tests/test_build.py`, `worker/index.test.js`

**Interfaces:**
- Produces: `build.TEXT_SPALTEN`, `build.LINK_PAARE`, `build.TEXT_MAX_LAENGE` (30), `build.pruefe_text(roh) -> tuple[str|None, str|None]`. Jeder Skill trägt `links: list[dict]` mit den Schlüsseln `u` (Adresse) und `t` (Beschriftung, `""` wenn keine).

Diese Aufgabe ändert die Datenform **und** beide Verbraucher in einem Zug. Getrennt wäre der Branch zwischendurch kaputt: die erzeugte JSON passte nicht mehr zu dem, was Worker und Formular lesen.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_build.py` anhängen:

```python
TEXT_HEADER = SKILLS_HEADER + ["Link1", "Text1", "Link2", "Text2", "Link3", "Text3"]


def test_beschriftung_wird_gelesen(mappe, monkeypatch):
    pfad = mappe(TEXT_HEADER, [SKILLS_ROW + ["https://a.ch/x", "Igelball", "", "", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    assert erste_skills(build.load_data())["links"] == [
        {"u": "https://a.ch/x", "t": "Igelball"}
    ]


def test_ohne_beschriftung_bleibt_t_leer(mappe, monkeypatch):
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + ["https://a.ch/x", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    assert erste_skills(build.load_data())["links"] == [{"u": "https://a.ch/x", "t": ""}]


def test_beschriftung_ohne_adresse_bricht_ab(mappe, monkeypatch):
    """Sonst staende eine Beschriftung ohne Ziel in der Mappe und niemand saehe es."""
    pfad = mappe(TEXT_HEADER, [SKILLS_ROW + ["", "Igelball", "", "", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    with pytest.raises(build.BuildError) as fehler:
        build.load_data()
    meldung = str(fehler.value)
    assert "Text1" in meldung and "Link1" in meldung
    assert "Zeile 2" in meldung


@pytest.mark.parametrize(
    "text, teil",
    [
        ("x" * 31, "zu lang"),
        ("<b>Igelball", "Klammern"),
        ("Siehe http://a.ch", "Adresse"),
    ],
)
def test_ungueltige_beschriftung_bricht_ab(mappe, monkeypatch, text, teil):
    pfad = mappe(TEXT_HEADER, [SKILLS_ROW + ["https://a.ch/x", text, "", "", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    with pytest.raises(build.BuildError) as fehler:
        build.load_data()
    assert teil in str(fehler.value)
    assert "Text1" in str(fehler.value)


def test_genau_dreissig_zeichen_sind_erlaubt(mappe, monkeypatch):
    pfad = mappe(TEXT_HEADER, [SKILLS_ROW + ["https://a.ch/x", "x" * 30, "", "", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    assert erste_skills(build.load_data())["links"][0]["t"] == "x" * 30


def test_beschriftungen_folgen_ihrem_link_beim_zusammenschieben(mappe, monkeypatch):
    """Luecke in Link1: Link2/Text2 ruecken gemeinsam auf, das Paar darf nicht
    auseinanderfallen."""
    pfad = mappe(
        TEXT_HEADER,
        [SKILLS_ROW + ["", "", "https://b.ch/y", "Massage", "https://c.ch/z", "Kette"]],
    )
    monkeypatch.setattr(build, "XLSX", pfad)
    assert erste_skills(build.load_data())["links"] == [
        {"u": "https://b.ch/y", "t": "Massage"},
        {"u": "https://c.ch/z", "t": "Kette"},
    ]
```

An `worker/index.test.js` anhängen (und die bestehenden `quellen`-Tests auf die neue Form ziehen):

```js
test("Bezugsquellen nutzen die Beschriftung, wenn es eine gibt", () => {
  const zelleInhalt = quellen([
    { u: "https://a.ch/x", t: "Igelball" },
    { u: "https://b.ch/y", t: "" },
  ]);
  assert.match(zelleInhalt, /Igelball/);
  assert.match(zelleInhalt, /https:\/\/b\.ch\/y/);
});

test("ein zwischengespeicherter Datenstand mit Zeichenketten bricht nicht", () => {
  // Der Worker holt docs/skills-daten.json mit 300 Sekunden Zwischenspeicher.
  // Direkt nach einer Veroeffentlichung kann er noch die alte Form sehen.
  assert.match(quellen(["https://a.ch/x"]), /https:\/\/a\.ch\/x/);
});
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q -k "beschriftung or dreissig"`
Expected: FAIL — `AttributeError: module 'build' has no attribute 'pruefe_text'` bzw. Vergleich gegen die alte Zeichenketten-Form

- [ ] **Step 3: `pruefe_text` und die Spaltenpaare in `build.py`**

Bei `LINK_SPALTEN` (Zeile 72) ergänzen:

```python
TEXT_SPALTEN = ["Text1", "Text2", "Text3"]
# Adresse und Beschriftung gehoeren zusammen: sie werden gemeinsam gelesen,
# gemeinsam geprueft und rutschen beim Zusammenschieben gemeinsam auf.
LINK_PAARE = list(zip(LINK_SPALTEN, TEXT_SPALTEN))
TEXT_MAX_LAENGE = 30
```

Nach `pruefe_link` einfügen:

```python
def pruefe_text(roh) -> tuple[str | None, str | None]:
    """Prüft die Beschriftung einer Bezugsquelle.

    Liefert (text, None) oder (None, Meldung). Kein `http`: die Domain steht
    nicht mehr im Knopf, darum fiele eine Beschriftung, die eine Adresse
    vortäuscht, kaum auf.
    """
    text = str(roh or "").strip()
    if len(text) > TEXT_MAX_LAENGE:
        return None, f"Beschriftung ist zu lang (höchstens {TEXT_MAX_LAENGE} Zeichen)"
    if "<" in text or ">" in text:
        return None, "Beschriftung darf keine spitzen Klammern enthalten"
    if "http" in text.lower():
        return None, "Beschriftung darf keine Adresse enthalten"
    return text, None
```

- [ ] **Step 4: Lesen und Zusammenbauen umstellen**

`optional_header` (Zeile 229):

```python
        optional_header=["Von", "Ergaenzt"] + LINK_SPALTEN + TEXT_SPALTEN,
```

Den Link-Block im Skill-Aufbau (Zeile 294-308) ersetzen:

```python
        # Luecken werden zusammengeschoben: wer den ersten von zwei Links
        # entfernt, soll die uebrigen nicht von Hand aufruecken muessen. Die
        # Beschriftung wandert dabei mit ihrer Adresse mit.
        links = []
        for spalte, textspalte in LINK_PAARE:
            roh_url, roh_text = rec[spalte], rec[textspalte]
            if not roh_url:
                if roh_text:
                    errors.append(
                        f"Blatt 'Skills', Zeile {rec['_row']}, Spalte "
                        f"'{textspalte}': Beschriftung ohne Adresse in "
                        f"'{spalte}'."
                    )
                continue
            url, meldung = pruefe_link(roh_url)
            if meldung:
                errors.append(
                    f"Blatt 'Skills', Zeile {rec['_row']}, Spalte '{spalte}': "
                    f"{meldung}."
                )
                continue
            beschriftung, meldung = pruefe_text(roh_text)
            if meldung:
                errors.append(
                    f"Blatt 'Skills', Zeile {rec['_row']}, Spalte "
                    f"'{textspalte}': {meldung}."
                )
                continue
            if any(vorhanden["u"] == url for vorhanden in links):
                continue
            links.append({"u": url, "t": beschriftung})
```

Der Eintrag `"links": links` im Skill-Wörterbuch bleibt unverändert — nur sein Inhalt hat jetzt die neue Form.

- [ ] **Step 5: Die beiden Verbraucher nachziehen**

`worker/index.js`, `quellen` (Zeile 88-92):

```js
export function quellen(liste) {
  if (!liste || !liste.length) {
    return "—";
  }
  // Der Datenstand wird 300 Sekunden zwischengespeichert: direkt nach einer
  // Veroeffentlichung kann hier noch die alte Form (blosse Zeichenketten)
  // ankommen. Darum beide Formen lesen.
  return liste
    .map((eintrag) => {
      const url = typeof eintrag === "string" ? eintrag : eintrag.u;
      const text = typeof eintrag === "string" ? "" : eintrag.t;
      return "`" + zelle(url) + "`" + (text ? " " + zelle(text) : "");
    })
    .join("<br>");
}
```

`template-vorschlag.html`, `originalUebernehmen` (Zeile 487):

```js
  linksSetzen((s.links||[]).map(function(l){ return l.u||l; }));
```

Das Formular schickt weiterhin nur Adressen — Beschriftungen pflegt allein die betreuende Person in der Excel.

- [ ] **Step 6: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Run: `cd worker && node --test`
Expected: beide PASS

- [ ] **Step 7: Committen**

```bash
git add build.py worker/index.js worker/index.test.js template-vorschlag.html tests/test_build.py
git commit -m "Beschriftung: Text-Spalten und neue Datenform fuer Bezugsquellen"
```

> Die Seiten werden hier **noch nicht** neu gebaut — `template.html` kennt die neue Form erst nach Task 3. Ein Neubau dazwischen erzeugte eine Seite, die auf `s.links[i]` als Zeichenkette zugreift und nichts anzeigt.

---

### Task 2: Symbole beim Bauen einbetten

**Files:**
- Create: `assets/favicons/.gitkeep`
- Modify: `build.py` (`FAVICON_DIR`, `gastgeber`, `lade_favicons`, `_render`, `render`, `main`)
- Modify: `template.html` (zweiter Platzhalter)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `links[i]["u"]` aus Task 1.
- Produces: `build.FAVICON_DIR`, `build.gastgeber(url) -> str`, `build.lade_favicons(data) -> dict[str, str]`. In `template.html` steht `var ICONS = {…}` — eine Tabelle Hostname → `data:`-URI.

**Warum eine eigene Tabelle statt eines Feldes je Link:** 49 der heutigen Links zeigen auf `skills-box.ch`. Läge das Symbol am Link, stünde dieselbe Bilddatei 49-mal in der Seite. Die Tabelle trägt jedes Symbol genau einmal.

**Warum nur in `template.html` und nicht in `skills-daten.json`:** Worker und Formular brauchen die Symbole nicht; sie würden die Datei nur aufblähen, die der Worker bei jeder Einreichung holt.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_build.py` anhängen:

```python
def test_favicon_wird_eingebettet(mappe, monkeypatch, tmp_path):
    ordner = tmp_path / "favicons"
    ordner.mkdir()
    # Kleinstes gueltiges PNG (1x1, transparent) - als base64, damit man es
    # nicht Byte fuer Byte pruefen muss.
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    (ordner / "a.ch.png").write_bytes(png)
    monkeypatch.setattr(build, "FAVICON_DIR", ordner)
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + ["https://a.ch/x", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    icons = build.lade_favicons(build.load_data())
    assert list(icons) == ["a.ch"]
    assert icons["a.ch"].startswith("data:image/png;base64,")


def test_fehlendes_favicon_bricht_den_build_nicht(mappe, monkeypatch, tmp_path):
    """Wer eine Bezugsquelle bei einem neuen Haendler eintraegt, darf damit
    nicht die ganze Website blockieren."""
    leer = tmp_path / "leer"
    leer.mkdir()
    monkeypatch.setattr(build, "FAVICON_DIR", leer)
    pfad = mappe(LINK_HEADER, [SKILLS_ROW + ["https://a.ch/x", "", ""]])
    monkeypatch.setattr(build, "XLSX", pfad)
    assert build.lade_favicons(build.load_data()) == {}


def test_gastgeber_entfernt_www():
    assert build.gastgeber("https://www.skills-box.ch/products/x") == "skills-box.ch"
    assert build.gastgeber("kein link") == ""


def test_vorlage_hat_den_icons_platzhalter():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    assert build.PLACEHOLDER_ICONS in vorlage
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q -k "favicon or gastgeber or icons"`
Expected: FAIL — `AttributeError: module 'build' has no attribute 'lade_favicons'`

- [ ] **Step 3: `build.py` erweitern**

`import base64` bei den Importen ergänzen. Bei den Pfadkonstanten:

```python
FAVICON_DIR = ROOT / "assets" / "favicons"
PLACEHOLDER_ICONS = "var ICONS = /*__BUILD_ICONS__*/{};"
```

Nach `pruefe_text` einfügen:

```python
def gastgeber(url: str) -> str:
    """Hostname ohne führendes www. — der Schlüssel der Symboltabelle."""
    try:
        return (urlsplit(url).hostname or "").removeprefix("www.")
    except ValueError:
        return ""


def lade_favicons(data: dict) -> dict:
    """Symbol je Hostname als data:-URI.

    Fehlt eine Datei, kommt der Hostname schlicht nicht vor und der Knopf zeigt
    später den Hostnamen statt eines Bildes. Der Build darf daran NICHT
    scheitern: sonst legte eine neue Bezugsquelle bei einem unbekannten Händler
    die ganze Website lahm.
    """
    hosts = {
        gastgeber(link["u"])
        for stufe in data.values()
        for kat in stufe["kategorien"]
        for skill in kat["skills"]
        for link in skill["links"]
    }
    icons = {}
    for host in sorted(h for h in hosts if h):
        try:
            roh = (FAVICON_DIR / f"{host}.png").read_bytes()
        except OSError:
            # Deckt beides ab: gar nicht vorhanden, und vorhanden aber nicht
            # lesbar (gesperrte Datei, oder jemand hat versehentlich einen
            # Ordner mit diesem Namen angelegt). Ein einzelnes kaputtes Symbol
            # darf die Website nicht lahmlegen.
            continue
        icons[host] = "data:image/png;base64," + base64.b64encode(roh).decode("ascii")
    return icons
```

- [ ] **Step 4: `_render` auf mehrere Platzhalter umstellen**

`_render` nimmt bisher genau einen Platzhalter. Die Signatur wird zu einer Liste, damit die Skillsliste zwei Blöcke bekommt:

```python
def _render(template_path, output_path, ersetzungen):
    """Setzt mehrere Platzhalter in eine Vorlage ein.

    `ersetzungen` ist eine Liste von (Platzhalter, Muster, Daten).
    """
    if not template_path.exists():
        raise BuildError(f"Vorlage nicht gefunden: {template_path.name}")
    html = template_path.read_bytes().decode("utf-8-sig")  # evtl. BOM entfernen
    for platzhalter, muster, daten in ersetzungen:
        if platzhalter not in html:
            raise BuildError(
                f"Platzhalter nicht in {template_path.name} gefunden. "
                f"Die Vorlage muss '{platzhalter}' enthalten."
            )
        payload = json.dumps(daten, ensure_ascii=False, separators=(", ", ": "))
        # Ausgabecodierung fuer den <script>-Block: sonst beendet ein </script>
        # im Freitext das Skriptelement und der Rest wird als Markup ausgefuehrt.
        payload = (
            payload.replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
        )
        html = html.replace(platzhalter, muster % payload, 1)
    # gleiche Datei-Konvention wie das Original: UTF-8 mit BOM
    output_path.write_bytes(b"\xef\xbb\xbf" + html.encode("utf-8"))


def render(data: dict, icons: dict):
    _render(
        TEMPLATE,
        OUTPUT,
        [
            (PLACEHOLDER, "var DATA = %s;", data),
            (PLACEHOLDER_ICONS, "var ICONS = %s;", icons),
        ],
    )


def render_vorschlag(data: dict):
    _render(
        TEMPLATE_VORSCHLAG,
        OUTPUT_VORSCHLAG,
        [(PLACEHOLDER_VORSCHLAG, "var DATEN = %s;", data)],
    )
```

In `main` den Aufruf anpassen:

```python
        data = load_data()
        render(data, lade_favicons(data))
```

- [ ] **Step 5: Platzhalter in `template.html`**

Direkt unter `var DATA = /*__BUILD_DATA__*/{};` einfügen:

```js
var ICONS = /*__BUILD_ICONS__*/{};
```

- [ ] **Step 6: Ordner anlegen**

```bash
mkdir -p assets/favicons
```

Und `assets/favicons/.gitkeep` als leere Datei anlegen, damit der Ordner auch ohne Symbole im Repo existiert — sonst schlägt der erste Lauf auf einem frischen Checkout mit einem verwirrenden Pfadfehler fehl.

- [ ] **Step 7: Tests laufen lassen**

`import base64` oben in `tests/test_build.py` ergänzen, falls noch nicht vorhanden.

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Expected: PASS

- [ ] **Step 8: Committen — ohne `docs/`**

```bash
git add build.py template.html tests/test_build.py assets/favicons/.gitkeep
git commit -m "Beschriftung: Symbole beim Bauen einbetten"
```

> **Hier wird bewusst nicht gebaut.** `openModal` liest die Links noch als
> Zeichenketten; mit der neuen Objektform stünde `[object Object]` auf den
> Knöpfen. Task 3 stellt die Anzeige um und baut dann neu. `docs/` ist bis
> dahin einen Commit hinterher — das ist der kleinere Übelstand gegenüber
> einer eingecheckten, kaputten Seite.

---

### Task 3: Anzeige im Detail-Dialog

**Files:**
- Modify: `template.html` (CSS bei `.modal-links-liste a`; `symbol`-Funktion; `openModal`-Linkblock Zeile 449-460)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `s.links[i].u`, `s.links[i].t` (Task 1) und `ICONS` (Task 2).

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_build.py` anhängen:

```python
def test_dialog_zeigt_symbol_und_beschriftung():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    block = ohne_umbrueche(js_funktion(vorlage, "openModal"))
    # Ohne Beschriftung faellt der Knopf auf den Hostnamen zurueck.
    assert "l.t||gastgeber(l.u)" in block
    # Die Domain steht nicht mehr im Text - der title haelt die Zusicherung
    # aufrecht, dass man das Ziel vor dem Klick sieht.
    assert "a.title=l.u;" in block
    assert "a.rel='noopener noreferrer nofollow ugc';" in block
    # Symbol ist Schmuck, die Beschriftung traegt die Bedeutung.
    assert "img.alt='';" in block


def test_symbol_schlaegt_in_der_icons_tabelle_nach():
    vorlage = build.TEMPLATE.read_bytes().decode("utf-8-sig")
    rumpf = ohne_umbrueche(js_funktion(vorlage, "symbol"))
    assert "ICONS[new URL(u).hostname.replace(/^www\\./,'')]" in rumpf
    assert "catch" in rumpf
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_build.py -q -k "dialog_zeigt or symbol_schlaegt"`
Expected: FAIL

- [ ] **Step 3: CSS ergänzen**

Nach der Regel `.modal-links-liste a{…}` einfügen:

```css
.modal-links-icon{width:16px;height:16px;border-radius:3px;flex-shrink:0;object-fit:contain}
```

- [ ] **Step 4: `symbol` einfügen**

Direkt nach `gastgeber` (Zeile 434-439):

```js
/* Das Symbol kommt aus der beim Bauen eingebetteten Tabelle, nie vom Haendler:
   ein Bild von coop.ch wuerde beim Oeffnen dieses Dialogs an Coop melden, dass
   jemand genau diesen Skill angeschaut hat. */
function symbol(u){
  try{ return ICONS[new URL(u).hostname.replace(/^www\./,'')]||''; }
  catch(e){ return ''; }
}
```

- [ ] **Step 5: Den Linkblock in `openModal` ersetzen**

```js
  mLinksListe.textContent='';
  (s.links||[]).forEach(function(l){
    var a=document.createElement('a');
    a.href=l.u;
    a.target='_blank';
    a.rel='noopener noreferrer nofollow ugc';
    /* Die Domain steht nicht mehr im Text – der title haelt die Zusicherung
       aufrecht, dass man vor dem Klick sieht, wo man landet. */
    a.title=l.u;
    var bild=symbol(l.u);
    if(bild){
      var img=document.createElement('img');
      img.src=bild;
      img.alt='';
      img.className='modal-links-icon';
      a.appendChild(img);
    } else {
      a.appendChild(document.createTextNode('↗ '));
    }
    a.appendChild(document.createTextNode(l.t||gastgeber(l.u)));
    mLinksListe.appendChild(a);
  });
  mLinks.hidden = !(s.links && s.links.length);
```

Der Pfeil `↗` bleibt als Rückfall, wenn kein Symbol da ist — sonst stünde dort nackter Text ohne Hinweis, dass er hinausführt.

- [ ] **Step 6: Tests, Bauen, Ansehen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Run: `uv run build.py`

Dann von Hand ansehen — ohne Symboldateien muss der Dialog wie bisher aussehen (Pfeil + Hostname):

```bash
cd docs && python -m http.server 8734 --bind 127.0.0.1
```

`http://127.0.0.1:8734/skillsliste.html` öffnen, einen Skill mit Bezugsquellen antippen.

- [ ] **Step 7: Committen**

```bash
git add template.html tests/test_build.py docs/
git commit -m "Beschriftung: Symbol und Beschriftung im Detail-Dialog"
```

---

### Task 4: `tools/favicon_holen.py`

**Files:**
- Create: `tools/favicon_holen.py`
- Test: `tests/test_favicon_holen.py`

**Interfaces:**
- Produces: `zielpfad(domain) -> Path`, `symbol_adressen(domain, html) -> list[str]`, `main()`.

Das Skript ist **bewusst von `build.py` getrennt**: `build.py` muss offline und per Doppelklick laufen. Dasselbe Muster wie beim Plakat-Vorschaubild.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

`tests/test_favicon_holen.py` neu anlegen — **ohne Netzwerkzugriff**, geprüft wird nur die reine Seite:

```python
"""Prueft die reine Seite des Favicon-Helfers - ohne Netzwerk."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import favicon_holen as fh


def test_zielpfad_entfernt_www():
    assert fh.zielpfad("www.coop.ch").name == "coop.ch.png"
    assert fh.zielpfad("coop.ch").name == "coop.ch.png"


def test_adressen_beginnen_mit_dem_standardort():
    adressen = fh.symbol_adressen("coop.ch", "")
    assert adressen[0] == "https://coop.ch/favicon.ico"


def test_adressen_lesen_die_link_angabe_der_seite():
    html = '<link rel="apple-touch-icon" href="/static/icon-180.png">'
    adressen = fh.symbol_adressen("coop.ch", html)
    assert "https://coop.ch/static/icon-180.png" in adressen


def test_absolute_angabe_bleibt_absolut():
    html = '<link rel="icon" href="https://cdn.coop.ch/i.png">'
    assert "https://cdn.coop.ch/i.png" in fh.symbol_adressen("coop.ch", html)


def test_ohne_domain_beendet_sich_das_skript_verstaendlich(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["favicon_holen.py"])
    with pytest.raises(SystemExit):
        fh.main()
    assert "Domain" in capsys.readouterr().out
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest python -m pytest tests/test_favicon_holen.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'favicon_holen'`

- [ ] **Step 3: Das Skript anlegen**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""
Symbol eines Haendlers holen
============================

Legt assets/favicons/<domain>.png an (32x32), damit build.py es einbetten kann.

Aufruf:  uv run tools/favicon_holen.py www.coop.ch

Bewusst getrennt von build.py: der Build muss offline und per Doppelklick
laufen. Dieses Skript wird einmal je Haendler von Hand gestartet.

Manche Shops sperren automatische Abrufe aus (Coop antwortet mit 403). Dann
meldet das Skript das und nennt den Weg von Hand - es ist kein Ausfall,
sondern der Normalfall bei einem Teil der Haendler.
"""

import io
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
ZIEL = ROOT / "assets" / "favicons"
KANTE = 32
ZEITLIMIT = 15
USER_AGENT = "toolbox-favicon (+https://github.com/stayingclean/toolbox)"

LINK_TAG = re.compile(
    r'<link[^>]+rel=["\'][^"\']*icon[^"\']*["\'][^>]*>', re.IGNORECASE
)
HREF = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)


def zielpfad(domain: str) -> Path:
    return ZIEL / f"{domain.removeprefix('www.')}.png"


def symbol_adressen(domain: str, html: str) -> list:
    """Kandidaten fuer das Symbol, bester zuerst.

    Zuerst der Standardort, dann was die Seite selbst angibt - manche Shops
    liefern unter /favicon.ico nichts Brauchbares mehr.
    """
    basis = f"https://{domain}/"
    adressen = [basis + "favicon.ico"]
    for tag in LINK_TAG.findall(html or ""):
        treffer = HREF.search(tag)
        if treffer:
            adressen.append(urljoin(basis, treffer.group(1)))
    return adressen


def hole(adresse: str) -> bytes:
    anfrage = urllib.request.Request(
        adresse, headers={"user-agent": USER_AGENT}
    )
    with urllib.request.urlopen(anfrage, timeout=ZEITLIMIT) as antwort:
        return antwort.read()


def main():
    if len(sys.argv) < 2:
        print("Aufruf: uv run tools/favicon_holen.py <Domain>")
        print("Beispiel: uv run tools/favicon_holen.py www.coop.ch")
        raise SystemExit(1)

    domain = sys.argv[1].strip().removeprefix("https://").removeprefix("http://").strip("/")
    ZIEL.mkdir(parents=True, exist_ok=True)
    ziel = zielpfad(domain)

    seite = ""
    try:
        seite = hole(f"https://{domain}/").decode("utf-8", "ignore")
    except (urllib.error.URLError, OSError, ValueError):
        pass  # Ohne Startseite bleibt der Standardort - das genuegt meistens.

    from PIL import Image

    for adresse in symbol_adressen(domain, seite):
        try:
            roh = hole(adresse)
            bild = Image.open(io.BytesIO(roh))
        except Exception:
            continue
        bild = bild.convert("RGBA").resize((KANTE, KANTE), Image.LANCZOS)
        bild.save(ziel, "PNG", optimize=True)
        print(f"✅ {ziel.relative_to(ROOT).as_posix()} ({ziel.stat().st_size} Byte)")
        print("   Jetzt build.bat ausfuehren, damit es eingebettet wird.")
        return

    print(f"❌ Kein Symbol von {domain} zu holen.")
    print()
    print("   Das ist bei einem Teil der Haendler normal - sie sperren")
    print("   automatische Abrufe aus. Von Hand geht es so:")
    print()
    print(f"   1. https://{domain}/ im Browser oeffnen")
    print("   2. Das Symbol im Reiter speichern (oder aus der Seite kopieren)")
    print(f"   3. Als PNG hier ablegen: {ziel.relative_to(ROOT).as_posix()}")
    print("   4. build.bat ausfuehren")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest python -m pytest tests/test_favicon_holen.py -q`
Expected: PASS

- [ ] **Step 5: Die sieben Symbole tatsächlich holen**

```bash
uv run tools/favicon_holen.py www.skills-box.ch
uv run tools/favicon_holen.py www.coop.ch
uv run tools/favicon_holen.py www.migros.ch
uv run tools/favicon_holen.py www.galaxus.ch
uv run tools/favicon_holen.py www.denner.ch
uv run tools/favicon_holen.py www.aldi-suisse.ch
uv run tools/favicon_holen.py www.lidl.ch
```

**Was scheitert, scheitert** — im Bericht festhalten, welche Händler das Skript ausgesperrt haben. Diese Dateien legt die betreuende Person von Hand ab; der Build läuft auch ohne sie.

Dann `uv run build.py` und die Seite ansehen: Händler mit Symbol zeigen es, die übrigen weiterhin `↗ hostname`.

- [ ] **Step 6: Committen**

```bash
git add tools/favicon_holen.py tests/test_favicon_holen.py assets/favicons/ docs/
git commit -m "Beschriftung: Hilfsskript fuer Haendler-Symbole"
```

---

### Task 5: Excel-Werkzeuge nachziehen

**Files:**
- Modify: `tools/seed_excel.py` (Kopfzeile, Zeilen, Breiten)
- Modify: `tools/vorschlaege_holen.py` (`SPALTEN`, `SPALTEN_AENDERUNG`, `zeile_ersetzen`)
- Test: `tests/test_build.py`, `tests/test_vorschlaege_holen.py`

**Interfaces:**
- Consumes: `build.LINK_PAARE` (Task 1) per Import.

**Die heikle Stelle dieser Aufgabe:** Eine Ergänzung ersetzt die Link-Spalten vollständig. Bliebe `Text1` dabei stehen, während `Link1` auf ein anderes Produkt zeigt, **beschriebe die Beschriftung das falsche Ding** — und niemand sähe es, weil im Knopf nur die Beschriftung steht. Darum wird `Text_i` geleert, **aber nur wenn sich `Link_i` tatsächlich ändert**. Bei einer Ergänzung, die die Links unangetastet lässt, bleiben die Beschriftungen erhalten.

- [ ] **Step 1: Die fehlschlagenden Tests schreiben**

An `tests/test_build.py`:

```python
def test_seed_excel_kennt_die_textspalten():
    quelle = (build.ROOT / "tools" / "seed_excel.py").read_text(encoding="utf-8")
    assert '"Link1", "Text1", "Link2", "Text2", "Link3", "Text3"' in quelle
    assert 'l.get("t"' in quelle
```

An `tests/test_vorschlaege_holen.py` (ans Dateiende, nach `AENDERUNG`):

```python
PAAR_KOPF = KOPF + ["Link1", "Text1", "Link2", "Text2", "Link3", "Text3"]


def test_aenderung_leert_die_beschriftung_wenn_der_link_wechselt(tmp_path):
    """Sonst beschriebe die alte Beschriftung ein anderes Produkt - und das
    faellt niemandem auf, weil im Knopf nur sie steht."""
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(PAAR_KOPF)
    ws.append(["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.", "",
               "Max", "", "https://alt.ch/1", "Alter Artikel", "", "", "", ""])
    wb.save(pfad)

    vh.in_excel_uebernehmen(pfad, [{**AENDERUNG, "links": ["https://neu.ch/1"]}], [])

    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    zeile = dict(zip([c.value for c in ws2[1]], [c.value for c in ws2[2]]))
    assert zeile["Link1"] == "https://neu.ch/1"
    assert zeile["Text1"] in (None, "")


def test_aenderung_behaelt_die_beschriftung_bei_gleichem_link(tmp_path):
    """Wer nur den Tipp ergaenzt, soll die gepflegten Beschriftungen behalten."""
    pfad = tmp_path / "skills_daten.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Skills"
    ws.append(PAAR_KOPF)
    ws.append(["Hoch", "Ablenkung", "🎧", "Musik hören", "Ein Lied auflegen.", "",
               "Max", "", "https://alt.ch/1", "Igelball", "", "", "", ""])
    wb.save(pfad)

    vh.in_excel_uebernehmen(pfad, [{**AENDERUNG, "links": ["https://alt.ch/1"]}], [])

    ws2 = openpyxl.load_workbook(pfad)["Skills"]
    zeile = dict(zip([c.value for c in ws2[1]], [c.value for c in ws2[2]]))
    assert zeile["Text1"] == "Igelball"


def test_fehlende_textspalten_werden_angelegt(tmp_path):
    pfad = mappe_mit_kopf(tmp_path, KOPF)
    vh.in_excel_uebernehmen(pfad, [], [{**BEISPIEL, "links": ["https://a.ch/x"]}])
    kopf = [c.value for c in openpyxl.load_workbook(pfad)["Skills"][1]]
    for name in ("Link1", "Text1", "Link2", "Text2", "Link3", "Text3"):
        assert name in kopf
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl python -m pytest tests/test_vorschlaege_holen.py -q -k "beschriftung or textspalten"`
Expected: FAIL

- [ ] **Step 3: `tools/seed_excel.py` erweitern**

Kopfzeile:

```python
    ws.append(["Stufe", "Kategorie", "Emoji", "Titel", "Beschreibung", "Tipp",
               "Von", "Ergaenzt",
               "Link1", "Text1", "Link2", "Text2", "Link3", "Text3"])
```

In der Zeilen-Schleife den Link-Ausdruck ersetzen:

```python
                        # Adresse und Beschriftung paarweise, auf drei aufgefuellt
                        *[
                            wert
                            for paar in (list(s.get("links", [])) + [{}, {}, {}])[:3]
                            for wert in (paar.get("u", ""), paar.get("t", ""))
                        ],
```

Spaltenbreiten:

```python
    style_sheet(ws, 14, [9, 18, 8, 26, 60, 55, 16, 16,
                         40, 18, 40, 18, 40, 18], emoji_col=3)
```

- [ ] **Step 4: `tools/vorschlaege_holen.py` erweitern**

Den Import um `LINK_PAARE` erweitern:

```python
from build import LINK_PAARE, LINK_SPALTEN, pruefe_link  # noqa: E402
```

**Nur `SPALTEN` bekommt die Textspalten** (neue Zeilen; `bereinigt` liefert dort
`""`, denn Beschriftungen kommen nie aus einem Vorschlag):

```python
    ("Text1", "text1"),
    ("Text2", "text2"),
    ("Text3", "text3"),
```

**`SPALTEN_AENDERUNG` bekommt sie ausdrücklich NICHT.** Diese Liste wird bei
einer Änderung Spalte für Spalte geschrieben — stünden die Textspalten darin,
würden sie bei *jeder* Übernahme mit `""` überschrieben, und die bedingte
Leerung unten wäre wirkungslos.

Damit die Spalten auf dem Änderungsweg trotzdem entstehen, wird der
`spalten_sichern`-Aufruf in `in_excel_uebernehmen` erweitert:

```python
        # Die Textspalten werden hier nur ANGELEGT, nicht geschrieben - siehe
        # SPALTEN_AENDERUNG. Ohne sie liefe der Zugriff weiter unten in einen
        # ValueError, sobald eine Mappe sie noch nicht hat.
        neue_spalte = spalten_sichern(
            ws, kopf, SPALTEN_AENDERUNG + [(t, t.lower()) for _, t in LINK_PAARE]
        )
```

In `zeile_ersetzen`, **vor** der bestehenden Schreibschleife über
`SPALTEN_AENDERUNG`, die Beschriftungen behandeln:

```python
    # Wechselt eine Adresse, wird ihre Beschriftung falsch: sie beschriebe dann
    # ein anderes Produkt, und das faellt niemandem auf, weil im Knopf nur die
    # Beschriftung steht. Bleibt die Adresse gleich, bleibt sie erhalten.
    for linkspalte, textspalte in LINK_PAARE:
        alt = ws.cell(row=treffer[0], column=kopf.index(linkspalte) + 1).value
        alt = str(alt).strip() if alt is not None else ""
        if alt != e.get(linkspalte.lower(), ""):
            ws.cell(row=treffer[0], column=kopf.index(textspalte) + 1).value = ""
```

> `e` ist die von `bereinigt` erzeugte Fassung; die Adressen stehen dort unter
> `link1`/`link2`/`link3`. `LINK_SPALTEN` heisst `Link1` — daher `.lower()`.

- [ ] **Step 5: Tests laufen lassen, grün bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Expected: PASS

- [ ] **Step 6: `seed_excel` gegenprüfen**

> **`seed_excel.py` überschreibt `skills_daten.xlsx`.** Vorher `git status` prüfen; zurückholen mit `git checkout -- skills_daten.xlsx`.

```bash
uv run tools/seed_excel.py && uv run build.py && git diff --stat skills_daten.xlsx docs/
```

Erwartung: `docs/` bleibt unverändert. **Wichtig:** Die heutigen Beschriftungen sind leer, daher beweist der Lauf nur, dass nichts anderes kaputtgeht. Danach `git checkout -- skills_daten.xlsx`.

- [ ] **Step 7: Committen**

```bash
git add tools/seed_excel.py tools/vorschlaege_holen.py tests/
git commit -m "Beschriftung: Excel-Werkzeuge kennen die Text-Spalten"
```

---

### Task 6: Dokumentation

**Files:**
- Modify: `CLAUDE.md`, `ANLEITUNG.md`

- [ ] **Step 1: `CLAUDE.md`**

Im Bezugsquellen-Abschnitt ergänzen:

```markdown
Neben jeder Link-Spalte steht eine **`Text*`-Spalte** mit der Beschriftung des
Knopfes (höchstens 30 Zeichen, ohne `http`). Bleibt sie leer, zeigt der Knopf
den Hostnamen. Die Spaltenzahl im Blatt `Skills` ist damit **vierzehn**.

**Die Beschriftung pflegt nur die Betreuung.** Das Formular sendet ausschliesslich
Adressen — ohne Domain im Knopftext fiele eine irreführende Beschriftung kaum auf.

**Wechselt bei einer Übernahme die Adresse, wird ihre Beschriftung geleert**
(`vorschlaege_holen.py`, `zeile_ersetzen`). Sonst beschriebe sie ein anderes
Produkt, und das sähe niemand.

### Symbole der Händler

`assets/favicons/<hostname>.png` (32 × 32, Hostname ohne `www.`). `build.py`
bettet sie als `data:`-URI ein — **einmal je Hostname** in der Tabelle `ICONS`,
nicht je Link: 49 der heutigen Links zeigen auf denselben Shop.

**Fehlt eine Datei, gibt es kein Symbol und der Build läuft weiter.** Diese
Eigenschaft muss jeder Umbau erhalten: sonst legte eine Bezugsquelle bei einem
unbekannten Händler die ganze Website lahm.

**Die Symbole werden nie vom Händler geladen.** Ein `<img src="https://coop.ch/…">`
meldete beim Öffnen eines Skill-Dialogs an Coop, dass jemand genau diesen Skill
angeschaut hat — ohne Klick. Neues Symbol holen: `uv run tools/favicon_holen.py <domain>`.
```

- [ ] **Step 2: `ANLEITUNG.md`**

Beim Bezugsquellen-Abschnitt einfügen:

```markdown
### Beschriftung der Knöpfe

Neben jeder Link-Spalte steht eine **Text-Spalte** (`Text1` zu `Link1` und so
weiter). Was du dort einträgst, steht auf dem Knopf:

| Link1 | Text1 | Knopf zeigt |
|---|---|---|
| `https://www.skills-box.ch/products/igelball` | `Igelball` | 🟧 Igelball |
| `https://www.skills-box.ch/products/igelball` | *(leer)* | ↗ skills-box.ch |

Höchstens **30 Zeichen**, und keine Internetadresse hineinschreiben.

Das lohnt sich vor allem, wenn ein Skill **mehrere Links zum selben Shop** hat —
sonst stehen dort zweimal dieselben Wörter, und niemand weiss, welcher Knopf
wohin führt.

**Wichtig:** Trägst du einen Text ein, ohne daneben eine Adresse zu haben, hält
`build.bat` an und sagt es dir. Das ist Absicht — eine Beschriftung ohne Ziel
wäre sonst nie aufgefallen.
```

- [ ] **Step 3: Alles laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Run: `cd worker && node --test`
Expected: beide PASS

- [ ] **Step 4: Committen**

```bash
git add CLAUDE.md ANLEITUNG.md
git commit -m "Beschriftung: Dokumentation"
```

---

## Nach der Umsetzung

Die Beschriftungen sind zunächst alle leer — die Anzeige verhält sich also wie
vorher, nur mit Symbolen. Das Befüllen der 17 Skills mit gleichnamigen Knöpfen
ist eine eigene, inhaltliche Arbeit und **nicht Teil dieses Plans**.

Der Worker muss neu veröffentlicht werden, sobald die neue `skills-daten.json`
online ist — `quellen()` liest zwar beide Formen, aber die Beschriftungen
erscheinen im Issue erst mit der neuen Fassung.
