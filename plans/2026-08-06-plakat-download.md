# Plakat zum Herunterladen — Implementierungsplan

> **Für agentische Bearbeiter:** ERFORDERLICHE UNTER-SKILL: `superpowers:subagent-driven-development`
> (empfohlen) oder `superpowers:executing-plans`, um diesen Plan Aufgabe für Aufgabe
> umzusetzen. Die Schritte tragen Kästchen (`- [ ]`) zum Abhaken.

**Ziel:** Eine Seite `docs/plakat.html`, auf der das Plakat zur Skillsliste als PNG
und als PDF in A5, A4 oder A3 heruntergeladen werden kann, verlinkt aus der Gruppe
„Skills" der Übersicht.

**Architektur:** Eine einzelne, in sich geschlossene HTML-Seite. Das Plakat bleibt
eine **eigene Bilddatei** und wird zur Laufzeit geladen, nicht eingebettet — eine
höher aufgelöste Fassung ersetzt später nur diese Datei. Das PDF baut die Seite
selbst: Die Bildpunkte des PNG wandern **unverändert** in das PDF (`FlateDecode`
mit `Predictor 15` liest genau das Format, in dem ein PNG seine Daten ohnehin
speichert). Der PDF-Kern besteht aus reinen Funktionen ohne DOM, `fetch` oder
Canvas und wird darum in Node getestet, nicht im Browser.

**Tech Stack:** HTML, CSS und JavaScript (ES5-Stil wie im übrigen Repo), keine
Bibliotheken. Tests in pytest, die den JavaScript-Kern über Node ausführen;
Gegenprüfung des erzeugten PDFs mit `pypdf`.

## Global Constraints

Diese Vorgaben gelten für **jede** Aufgabe, auch wo sie nicht wiederholt werden:

- **Sprache:** Alle Bezeichner, Kommentare, Commit-Nachrichten und Texte auf
  Deutsch — wie im übrigen Repo. Kommentare erklären *warum*, nicht *was*.
- **CSS eingebettet:** Kein externes Stylesheet, keine externe Schriftquelle
  (auch nicht `fonts.googleapis.com`). Die Seite muss lokal ansehnlich bleiben.
- **Fusszeile:** Jede Seite in `docs/` trägt Urheber-Credit und Kaffee-Link nach
  der Konvention in `CLAUDE.md`. Wortlaut und Struktur exakt übernehmen.
- **Keine fremden Bibliotheken** im ausgelieferten Code.
- **Commits** am Ende jeder Aufgabe, mit `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
  als letzter Zeile. Umlaute in Commit-Nachrichten umschreiben (`ae`, `oe`, `ue`),
  wie im bestehenden Verlauf.
- **Tests laufen** über `uv run --with pytest --with openpyxl --with pypdf pytest tests -v`
  (ab Task 2 zusätzlich `--with pillow`). Der Basislauf vor Beginn: 81 bestandene Tests.
- **Papierformate:** genau A5 (148 × 210 mm), A4 (210 × 297 mm), A3 (297 × 420 mm).
- **Dateiname der Bilddatei:** `docs/plakat-skillsliste.png`, überall gleich.
- **Download-Namen:** `plakat-skillsliste.png`, `plakat-skillsliste-a5.pdf`,
  `plakat-skillsliste-a4.pdf`, `plakat-skillsliste-a3.pdf`.

---

## Dateien im Überblick

| Datei | Art | Verantwortung |
|---|---|---|
| `docs/plakat-skillsliste.png` | neu | Das Plakat in voller Auflösung (3508 × 4961 px, 14,9 MB): PNG-Download und Quelle fürs PDF. Austauschbar; nichts im Code hängt an seinen Massen. |
| `docs/plakat-vorschau.jpg` | neu | Verkleinerte Vorschau (~360 KB) — nur für die Anzeige, damit ein Seitenaufruf nicht 14,9 MB lädt. |
| `docs/plakat.html` | neu | Die ganze Seite: Gestaltung, PDF-Kern, Bedienung. Eine Datei, weil sie in sich geschlossen sein muss. |
| `tests/plakat_pdf_treiber.mjs` | neu | Schneidet den PDF-Kern aus der HTML und führt ihn in Node aus. Die einzige Brücke zwischen Testlauf und Browser-Code. |
| `tests/test_plakat.py` | neu | Prüft den PDF-Kern (Masse, Verlustfreiheit, Einpassung, Lesbarkeit) und die statischen Eigenschaften der Seite. |
| `docs/index.html` | ändern | Dritte Karte in der Gruppe „Skills". |
| `CLAUDE.md` | ändern | Die neue Seite in der Aufbau-Liste nennen, samt Befehl zum Neuerzeugen der Vorschau. |
| `test.bat` | ändern | `--with pypdf` (Task 1) und `--with pillow` (Task 2) ergänzen. |

Der PDF-Kern steht in `docs/plakat.html` zwischen zwei Marker-Kommentaren:

```js
/* == pdf-kern:anfang == */
/* == pdf-kern:ende == */
```

Diese Marker sind **Vertrag** — der Testtreiber schneidet genau dazwischen. Sie
dürfen weder umbenannt noch dupliziert werden.

---

## Task 1: Bilddatei und PDF-Kern

Der heikelste Teil zuerst, und zwar prüfbar: Nach dieser Aufgabe erzeugt der Kern
aus der echten Bilddatei drei PDFs, deren Masse und Bilddaten nachgerechnet sind.

**Files:**
- Create: `docs/plakat-skillsliste.png` (Kopie aus `neue_docs/`)
- Create: `docs/plakat.html` (Grundgerüst mit dem Kern; die Oberfläche folgt in Task 2)
- Create: `tests/plakat_pdf_treiber.mjs`
- Create: `tests/test_plakat.py`
- Modify: `test.bat`

**Interfaces:**
- Consumes: nichts.
- Produces: In `docs/plakat.html` global im Skript-Block verfügbar —
  - `PngNichtTauglich(grund)` — Fehlertyp mit `name === 'PngNichtTauglich'`
  - `pngLesen(bytes: Uint8Array) → { breite, hoehe, bittiefe, farbtyp, interlace, daten: Uint8Array }`
  - `pdfAusPng(pngBytes: Uint8Array, breiteMm: number, hoeheMm: number) → Uint8Array`
  - `pdfAusJpeg(jpegBytes: Uint8Array, breitePx, hoehePx, breiteMm, hoeheMm) → Uint8Array`
  - `pdfBauen(bild, breiteMm, hoeheMm) → Uint8Array` (intern; von den beiden oberen benutzt)

- [ ] **Schritt 1: Bilddatei nach `docs/` kopieren**

```bash
cp "neue_docs/staying clean QR Code-Skillsliste.png" docs/plakat-skillsliste.png
```

Prüfen, dass sie angekommen ist und den erwarteten Typ hat:

```bash
uv run --with pillow python -c "from PIL import Image; im=Image.open('docs/plakat-skillsliste.png'); print(im.size, im.mode)"
```

Erwartet: `(1055, 1491) RGB`

Die Datei wird später gegen eine höher aufgelöste ausgetauscht. Kein Test darf
sich auf `1055 × 1491` festnageln — die Masse werden überall aus der Datei
gelesen.

- [ ] **Schritt 2: Testtreiber `tests/plakat_pdf_treiber.mjs` schreiben**

```js
/* Schneidet den PDF-Kern aus docs/plakat.html heraus und fuehrt ihn in Node
   aus. So wird genau der Code geprueft, der spaeter im Browser laeuft -- keine
   Kopie, die auseinanderlaufen koennte.

   Aufruf: node plakat_pdf_treiber.mjs <html> <png> <breiteMm> <hoeheMm> <ziel> */

import { readFileSync, writeFileSync } from 'node:fs';

const [, , htmlPfad, pngPfad, breiteMm, hoeheMm, zielPfad] = process.argv;

const ANFANG = '/* == pdf-kern:anfang == */';
const ENDE = '/* == pdf-kern:ende == */';

const html = readFileSync(htmlPfad, 'utf8');
const ab = html.indexOf(ANFANG);
const bis = html.indexOf(ENDE);
if (ab < 0 || bis < 0) {
  console.error('Die Marker des PDF-Kerns stehen nicht in ' + htmlPfad + '.');
  process.exit(2);
}

const kern = new Function(
  html.slice(ab, bis) + '\nreturn { pngLesen, pdfAusPng, pdfAusJpeg };'
)();

const png = new Uint8Array(readFileSync(pngPfad));
const pdf = kern.pdfAusPng(png, Number(breiteMm), Number(hoeheMm));
writeFileSync(zielPfad, Buffer.from(pdf));
```

- [ ] **Schritt 3: Die fehlschlagenden Tests schreiben**

`tests/test_plakat.py`:

```python
"""Prüft den PDF-Kern aus docs/plakat.html und die statischen Eigenschaften
der Plakat-Seite.

Der Kern wird nicht nachgebaut, sondern aus der ausgelieferten HTML
herausgeschnitten und in Node ausgeführt (tests/plakat_pdf_treiber.mjs).
Geprüft wird damit genau der Code, der im Browser läuft.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SEITE = ROOT / "docs" / "plakat.html"
BILD = ROOT / "docs" / "plakat-skillsliste.png"
TREIBER = ROOT / "tests" / "plakat_pdf_treiber.mjs"

MM_ZU_PT = 72 / 25.4
FORMATE = {"a5": (148, 210), "a4": (210, 297), "a3": (297, 420)}

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="Node wird gebraucht, um den PDF-Kern auszuführen",
)


def idat_bytes(png: bytes) -> bytes:
    """Hängt alle IDAT-Blöcke aneinander — der zlib-Strom des Bildes."""
    pos, teile = 8, []
    while pos + 8 <= len(png):
        laenge = int.from_bytes(png[pos : pos + 4], "big")
        art = png[pos + 4 : pos + 8]
        if art == b"IDAT":
            teile.append(png[pos + 8 : pos + 8 + laenge])
        elif art == b"IEND":
            break
        pos += 8 + laenge + 4
    return b"".join(teile)


def png_masse(png: bytes) -> tuple[int, int]:
    return (
        int.from_bytes(png[16:20], "big"),
        int.from_bytes(png[20:24], "big"),
    )


def objekt_strom(pdf: bytes, nummer: int) -> bytes:
    """Liest den Datenstrom eines PDF-Objekts anhand seiner /Length."""
    start = pdf.index(f"{nummer} 0 obj".encode())
    treffer = re.search(rb"/Length (\d+)", pdf[start : start + 800])
    assert treffer, f"Objekt {nummer} hat kein /Length"
    laenge = int(treffer.group(1))
    ab = pdf.index(b"stream\n", start) + len("stream\n")
    return pdf[ab : ab + laenge]


@pytest.fixture(scope="module")
def pdfs(tmp_path_factory):
    """Erzeugt einmal je Format ein PDF aus der echten Bilddatei."""
    ziel = tmp_path_factory.mktemp("plakat")
    ergebnis = {}
    for name, (breite, hoehe) in FORMATE.items():
        pfad = ziel / f"plakat-{name}.pdf"
        lauf = subprocess.run(
            ["node", str(TREIBER), str(SEITE), str(BILD),
             str(breite), str(hoehe), str(pfad)],
            capture_output=True, text=True,
        )
        assert lauf.returncode == 0, lauf.stderr
        ergebnis[name] = pfad.read_bytes()
    return ergebnis


def test_marker_umschliessen_den_kern():
    text = SEITE.read_text(encoding="utf-8")
    assert text.count("/* == pdf-kern:anfang == */") == 1
    assert text.count("/* == pdf-kern:ende == */") == 1
    assert text.index("/* == pdf-kern:anfang == */") < text.index("/* == pdf-kern:ende == */")


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_seitenmass_entspricht_dem_papierformat(pdfs, name):
    breite_mm, hoehe_mm = FORMATE[name]
    treffer = re.search(rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", pdfs[name])
    assert treffer, "keine MediaBox gefunden"
    assert float(treffer.group(1)) == pytest.approx(breite_mm * MM_ZU_PT, abs=0.01)
    assert float(treffer.group(2)) == pytest.approx(hoehe_mm * MM_ZU_PT, abs=0.01)


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_bildmasse_stammen_aus_der_datei(pdfs, name):
    breite, hoehe = png_masse(BILD.read_bytes())
    kopf = pdfs[name][:2000]
    assert f"/Width {breite}".encode() in kopf
    assert f"/Height {hoehe}".encode() in kopf


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_bilddaten_wandern_unveraendert_ins_pdf(pdfs, name):
    """Die eigentliche Zusicherung von Weg A: kein Neukodieren."""
    assert objekt_strom(pdfs[name], 4) == idat_bytes(BILD.read_bytes())


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_bild_wird_eingepasst_und_zentriert(pdfs, name):
    breite_px, hoehe_px = png_masse(BILD.read_bytes())
    breite_mm, hoehe_mm = FORMATE[name]
    seite_b, seite_h = breite_mm * MM_ZU_PT, hoehe_mm * MM_ZU_PT

    inhalt = objekt_strom(pdfs[name], 5).decode("latin-1")
    treffer = re.search(r"([\d.]+) 0 0 ([\d.]+) ([\d.]+) ([\d.]+) cm", inhalt)
    assert treffer, f"keine Platzierungsmatrix in: {inhalt!r}"
    bild_b, bild_h, x, y = (float(g) for g in treffer.groups())

    # nicht verzerrt
    assert bild_b / bild_h == pytest.approx(breite_px / hoehe_px, rel=1e-4)
    # so gross wie möglich: eine der beiden Kanten stösst an den Seitenrand
    assert min(seite_b - bild_b, seite_h - bild_h) == pytest.approx(0, abs=0.01)
    # und nirgends grösser als die Seite
    assert bild_b <= seite_b + 0.01 and bild_h <= seite_h + 0.01
    # zentriert
    assert x == pytest.approx((seite_b - bild_b) / 2, abs=0.01)
    assert y == pytest.approx((seite_h - bild_h) / 2, abs=0.01)


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_querverweistabelle_zeigt_auf_die_objekte(pdfs, name):
    """Stimmen die Byteversätze nicht, öffnen strenge Leser die Datei nicht."""
    pdf = pdfs[name]
    ab = int(re.search(rb"startxref\n(\d+)", pdf).group(1))
    assert pdf[ab : ab + 4] == b"xref"
    zeilen = pdf[ab:].split(b"\n")
    for nummer in range(1, 6):
        versatz = int(zeilen[2 + nummer].split()[0])
        marke = f"{nummer} 0 obj".encode()
        assert pdf[versatz : versatz + len(marke)] == marke


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_ein_unabhaengiger_leser_oeffnet_das_pdf(pdfs, name, tmp_path):
    pypdf = pytest.importorskip("pypdf")
    pfad = tmp_path / f"{name}.pdf"
    pfad.write_bytes(pdfs[name])
    leser = pypdf.PdfReader(str(pfad))
    assert len(leser.pages) == 1
    breite_mm, hoehe_mm = FORMATE[name]
    assert float(leser.pages[0].mediabox.width) == pytest.approx(
        breite_mm * MM_ZU_PT, abs=0.01
    )


def test_bilddatei_passt_zu_weg_a():
    """Farbtyp 2 (RGB), 8 Bit, kein Interlace — sonst griffe die Rückfallebene."""
    png = BILD.read_bytes()
    assert png[:8] == bytes([137, 80, 78, 71, 13, 10, 26, 10])
    assert png[24] == 8, "Bittiefe ist nicht 8"
    assert png[25] in (0, 2), "Farbtyp ist weder Graustufen noch RGB"
    assert png[28] == 0, "PNG ist interlaced"
```

- [ ] **Schritt 4: Lauf, der scheitern muss**

```bash
uv run --with pytest --with openpyxl --with pypdf pytest tests/test_plakat.py -v
```

Erwartet: **Fehlschlag** — `docs/plakat.html` gibt es noch nicht, also findet der
Treiber die Marker nicht und `test_marker_umschliessen_den_kern` scheitert an der
fehlenden Datei. Genau das bestätigt, dass die Tests wirklich auf den Kern
schauen und nicht ins Leere greifen.

- [ ] **Schritt 5: `docs/plakat.html` mit dem PDF-Kern anlegen**

Nur das Gerüst und der Kern; Gestaltung und Bedienung kommen in Task 2.

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Plakat – Toolbox</title>
</head>
<body>
<script>
(function(){
  "use strict";

/* == pdf-kern:anfang == */
/* Baut aus einer Bilddatei ein einseitiges PDF im gewuenschten Papierformat.

   Reine Funktionen: kein DOM, kein fetch, kein Canvas. Nur so laesst sich der
   heikelste Teil ausserhalb des Browsers pruefen (tests/test_plakat.py).

   Weg A (pdfAusPng) reicht die Bildpunkte des PNG unveraendert ins PDF durch:
   Ein PNG speichert sie als zlib-Strom ueber zeilenweise gefilterte Rohdaten,
   und PDF liest mit FlateDecode + Predictor 15 genau dasselbe Format. Kein
   Neukodieren, kein Qualitaetsverlust -- das zaehlt vor allem fuer die beiden
   QR-Codes, deren harte Schwarz-Weiss-Kanten unter JPEG sichtbar leiden.

   Weg B (pdfAusJpeg) ist die Rueckfallebene fuer PNG-Typen, die Weg A nicht
   abdeckt; die JPEG-Bytes erzeugt dann die Seite per Canvas. */

  var MM_ZU_PT = 72 / 25.4;

  /* Wird geworfen, wenn die PNG-Datei nicht zu Weg A passt. Die Seite faengt
     genau diesen Fall ab und weicht auf Weg B aus. */
  function PngNichtTauglich(grund) {
    this.name = 'PngNichtTauglich';
    this.message = grund;
  }
  PngNichtTauglich.prototype = Object.create(Error.prototype);

  function latin1(text) {
    var bytes = new Uint8Array(text.length);
    for (var i = 0; i < text.length; i++) bytes[i] = text.charCodeAt(i) & 0xFF;
    return bytes;
  }

  function runde(wert) { return Math.round(wert * 1000) / 1000; }

  /* PNG in seine Chunks zerlegen. Liefert Masse, Typ und den vollstaendigen
     zlib-Strom: alle IDAT-Bloecke in der vorgefundenen Reihenfolge
     aneinandergehaengt ergeben genau ihn. */
  function pngLesen(bytes) {
    var signatur = [137, 80, 78, 71, 13, 10, 26, 10];
    if (bytes.length < 8) throw new PngNichtTauglich('Datei zu kurz fuer ein PNG.');
    for (var i = 0; i < 8; i++) {
      if (bytes[i] !== signatur[i]) throw new PngNichtTauglich('Keine PNG-Datei.');
    }
    var sicht = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    var pos = 8, kopf = null, bloecke = [], gesamt = 0;
    while (pos + 8 <= bytes.length) {
      var laenge = sicht.getUint32(pos);
      var art = String.fromCharCode(bytes[pos + 4], bytes[pos + 5],
                                    bytes[pos + 6], bytes[pos + 7]);
      var daten = pos + 8;
      if (art === 'IHDR') {
        kopf = {
          breite: sicht.getUint32(daten),
          hoehe: sicht.getUint32(daten + 4),
          bittiefe: bytes[daten + 8],
          farbtyp: bytes[daten + 9],
          interlace: bytes[daten + 12]
        };
      } else if (art === 'IDAT') {
        bloecke.push(bytes.subarray(daten, daten + laenge));
        gesamt += laenge;
      } else if (art === 'IEND') {
        break;
      }
      pos = daten + laenge + 4;            // + 4 Byte CRC
    }
    if (!kopf) throw new PngNichtTauglich('PNG ohne IHDR-Block.');
    if (!bloecke.length) throw new PngNichtTauglich('PNG ohne Bilddaten.');
    var strom = new Uint8Array(gesamt), k = 0;
    for (var j = 0; j < bloecke.length; j++) {
      strom.set(bloecke[j], k);
      k += bloecke[j].length;
    }
    kopf.daten = strom;
    return kopf;
  }

  /* Setzt das PDF byteweise zusammen. `bild` beschreibt das eingebettete Bild:
     { breite, hoehe, daten, filter: 'Flate'|'DCT', farbraum, farben } */
  function pdfBauen(bild, breiteMm, hoeheMm) {
    var teile = [], laenge = 0, versatz = [];

    function schreibe(stueck) {
      var bytes = (typeof stueck === 'string') ? latin1(stueck) : stueck;
      teile.push(bytes);
      laenge += bytes.length;
    }
    function objekt(nummer, woerterbuch, strom) {
      versatz[nummer] = laenge;
      schreibe(nummer + ' 0 obj\n' + woerterbuch + '\n');
      if (strom) { schreibe('stream\n'); schreibe(strom); schreibe('\nendstream\n'); }
      schreibe('endobj\n');
    }

    var seiteB = runde(breiteMm * MM_ZU_PT);
    var seiteH = runde(hoeheMm * MM_ZU_PT);

    /* Einpassen unter Wahrung des Seitenverhaeltnisses, dann zentrieren. Beim
       heutigen Plakat bleibt dadurch ein Rand von 0,07 % -- unsichtbar. Der
       Verzicht aufs Verzerren ist Absicht: ein kuenftiges Plakat mit anderem
       Seitenverhaeltnis wird sauber eingepasst statt gestaucht. */
    var skala = Math.min(seiteB / bild.breite, seiteH / bild.hoehe);
    var bildB = runde(bild.breite * skala);
    var bildH = runde(bild.hoehe * skala);
    var x = runde((seiteB - bildB) / 2);
    var y = runde((seiteH - bildH) / 2);

    var inhalt = 'q\n' + bildB + ' 0 0 ' + bildH + ' ' + x + ' ' + y + ' cm\n/Im0 Do\nQ\n';

    var bildWb = '<< /Type /XObject /Subtype /Image'
      + ' /Width ' + bild.breite + ' /Height ' + bild.hoehe
      + ' /ColorSpace /' + bild.farbraum
      + ' /BitsPerComponent 8';
    if (bild.filter === 'Flate') {
      bildWb += ' /Filter /FlateDecode'
        + ' /DecodeParms << /Predictor 15 /Colors ' + bild.farben
        + ' /BitsPerComponent 8 /Columns ' + bild.breite + ' >>';
    } else {
      bildWb += ' /Filter /DCTDecode';
    }
    bildWb += ' /Length ' + bild.daten.length + ' >>';

    schreibe('%PDF-1.4\n');
    /* Binaerkennung: vier Bytes ueber 127, an denen Werkzeuge die Datei als
       binaer erkennen. Bewusst als Escape-Folgen -- woertliche Zeichen ergaeben
       nur dann E2 E3 CF D3, wenn jedes Werkzeug die Quelldatei als UTF-8 liest. */
    schreibe('%\u00E2\u00E3\u00CF\u00D3\n');
    objekt(1, '<< /Type /Catalog /Pages 2 0 R >>');
    objekt(2, '<< /Type /Pages /Kids [3 0 R] /Count 1 >>');
    objekt(3, '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ' + seiteB + ' ' + seiteH + ']'
            + ' /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>');
    objekt(4, bildWb, bild.daten);
    objekt(5, '<< /Length ' + inhalt.length + ' >>', latin1(inhalt));

    var xrefAb = laenge;
    var xref = 'xref\n0 6\n0000000000 65535 f \n';
    for (var n = 1; n <= 5; n++) {
      var v = String(versatz[n]);
      while (v.length < 10) v = '0' + v;
      xref += v + ' 00000 n \n';
    }
    schreibe(xref);
    schreibe('trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n' + xrefAb + '\n%%EOF\n');

    var pdf = new Uint8Array(laenge), p = 0;
    for (var t = 0; t < teile.length; t++) { pdf.set(teile[t], p); p += teile[t].length; }
    return pdf;
  }

  /* Weg A: PNG-Bilddaten unveraendert durchreichen. */
  function pdfAusPng(pngBytes, breiteMm, hoeheMm) {
    var kopf = pngLesen(pngBytes);
    if (kopf.bittiefe !== 8) {
      throw new PngNichtTauglich('Bittiefe ' + kopf.bittiefe + ' statt 8.');
    }
    if (kopf.interlace !== 0) {
      throw new PngNichtTauglich('PNG ist interlaced.');
    }
    if (kopf.farbtyp !== 0 && kopf.farbtyp !== 2) {
      throw new PngNichtTauglich('Farbtyp ' + kopf.farbtyp + ' (weder Graustufen noch RGB).');
    }
    return pdfBauen({
      breite: kopf.breite,
      hoehe: kopf.hoehe,
      daten: kopf.daten,
      filter: 'Flate',
      farbraum: kopf.farbtyp === 0 ? 'DeviceGray' : 'DeviceRGB',
      farben: kopf.farbtyp === 0 ? 1 : 3
    }, breiteMm, hoeheMm);
  }

  /* Weg B: fertige JPEG-Bytes einbetten (die Seite erzeugt sie per Canvas). */
  function pdfAusJpeg(jpegBytes, breitePx, hoehePx, breiteMm, hoeheMm) {
    return pdfBauen({
      breite: breitePx,
      hoehe: hoehePx,
      daten: jpegBytes,
      filter: 'DCT',
      farbraum: 'DeviceRGB',
      farben: 3
    }, breiteMm, hoeheMm);
  }
/* == pdf-kern:ende == */

})();
</script>
</body>
</html>
```

**Achtung beim Binärkommentar:** `'%âãÏÓ\n'` steht bewusst als
Escape-Folge da und **nicht** als wörtliches `%âãÏÓ`. Die Seite wird als UTF-8
ausgeliefert; wörtliche Zeichen kämen dort mehrbytig an, und `latin1()` würde
etwas anderes schreiben, als gemeint ist. Die Escape-Folge liefert genau die vier
Bytes `E2 E3 CF D3`.

- [ ] **Schritt 6: Tests laufen lassen — jetzt grün**

```bash
uv run --with pytest --with openpyxl --with pypdf pytest tests/test_plakat.py -v
```

Erwartet: alle Tests dieser Datei bestehen.

Falls nicht: **nicht die Tests anpassen**, sondern den Kern korrigieren. Die
Erwartungswerte sind gegen ein unabhängig gerendertes PDF geprüft worden — ein
Fehlschlag hier heisst, dass der Kern abweicht, nicht der Test.

- [ ] **Schritt 7: `test.bat` um `pypdf` ergänzen**

Aus:

```bat
uv run --with pytest --with openpyxl pytest tests -v
```

wird:

```bat
uv run --with pytest --with openpyxl --with pypdf pytest tests -v
```

- [ ] **Schritt 8: Gesamtlauf**

```bash
uv run --with pytest --with openpyxl --with pypdf pytest tests -v
```

Erwartet: die bisherigen 81 Tests plus die neuen, alle bestanden, 0 Fehler.

- [ ] **Schritt 9: Commit**

```bash
git add docs/plakat-skillsliste.png docs/plakat.html tests/plakat_pdf_treiber.mjs tests/test_plakat.py test.bat
git commit -m "$(cat <<'EOF'
PDF-Kern: PNG-Bildpunkte unveraendert ins PDF durchreichen

Ein PNG speichert seine Bildpunkte als zlib-Strom ueber zeilenweise
gefilterte Rohdaten, und PDF liest mit FlateDecode + Predictor 15 genau
dasselbe Format. Die IDAT-Bloecke wandern darum Byte fuer Byte ins PDF,
statt ueber ein Canvas neu kodiert zu werden. Die beiden QR-Codes sind
der Grund: harte Schwarz-Weiss-Kanten sind das, woran JPEG knirscht.

Der Kern kommt ohne DOM, fetch und Canvas aus. Er wird darum nicht
nachgebaut, sondern aus der ausgelieferten HTML herausgeschnitten und in
Node ausgefuehrt -- geprueft wird genau der Code, der im Browser laeuft.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Die Seite

Jetzt bekommt die Seite Gestalt: Vorschau, vier Download-Knöpfe, ehrlicher
Auflösungshinweis, saubere Fehlerfälle, Fusszeile.

**Files:**
- Create: `docs/plakat-vorschau.jpg` (verkleinerte Vorschau)
- Modify: `docs/plakat.html` (Kopf, `<style>`, Rumpf und Bedienlogik ergänzen; der Kern bleibt unangetastet)
- Modify: `tests/test_plakat.py` (statische Prüfungen anhängen)

**Interfaces:**
- Consumes: `pdfAusPng`, `pdfAusJpeg`, `PngNichtTauglich` aus Task 1.
- Produces: nichts für spätere Tasks.

### Zwei Dateien, nicht eine

Die Plakatdatei ist **14,9 MB** gross (3508 × 4961 px — 300 dpi auf A3). Als
Vorschau eingebunden lüde jeder Seitenaufruf diese 14,9 MB herunter, auch wenn
niemand etwas speichert. Darum liegt daneben eine verkleinerte Vorschau:

| Datei | Grösse | wofür |
|---|---|---|
| `docs/plakat-skillsliste.png` | 14,9 MB | PNG-Download **und** Quelle fürs PDF |
| `docs/plakat-vorschau.jpg` | ~360 KB | nur die Anzeige auf der Seite |

JPEG statt PNG, weil die Aquarell-Illustrationen als PNG selbst verkleinert noch
2,9 MB wögen — bei gleicher sichtbarer Qualität achtmal so viel.

Daraus folgen zwei Dinge, die man leicht übersieht:

1. **Der Auflösungshinweis darf nicht aus dem Vorschaubild rechnen** — der
   meldete 1200 px und damit unsinnige dpi-Werte. Die wahren Masse kommen per
   Teilabruf (HTTP-Range) aus den ersten 34 Bytes der grossen Datei; dort steht
   der IHDR-Block des PNG. Das kostet ein paar hundert Byte statt 14,9 MB.
2. **Weg B darf nicht das Vorschaubild ins Canvas zeichnen** — das ergäbe ein
   PDF mit 1200 px Vorlage. Weg B baut sich sein Bild aus den bereits geholten
   Bytes der grossen Datei.

- [ ] **Schritt 1: Vorschaubild erzeugen**

```bash
uv run --with pillow python -c "from PIL import Image; q=Image.open('docs/plakat-skillsliste.png'); q.resize((1200, round(1200*q.height/q.width)), Image.LANCZOS).convert('RGB').save('docs/plakat-vorschau.jpg', quality=80, optimize=True, progressive=True)"
```

Prüfen:

```bash
uv run --with pillow python -c "from PIL import Image; import os; im=Image.open('docs/plakat-vorschau.jpg'); print(im.size, round(os.path.getsize('docs/plakat-vorschau.jpg')/1024), 'KB')"
```

Erwartet: `(1200, 1697) 360 KB` (±40 KB — die genaue Grösse hängt an der
Pillow-Fassung).

Genau dieser Befehl gehört in Task 3 in die `CLAUDE.md`, damit die Vorschau nach
einem Austausch des Plakats reproduzierbar neu entsteht.

- [ ] **Schritt 2: Die statischen Tests schreiben (sie müssen erst scheitern)**

Zuerst im Kopf von `tests/test_plakat.py`, direkt nach der `BILD`-Zeile,
die Vorschau ergänzen:

```python
VORSCHAU = ROOT / "docs" / "plakat-vorschau.jpg"
```

Dann anhängen:

```python
def test_fusszeile_traegt_credit_und_kaffee_link():
    text = SEITE.read_text(encoding="utf-8")
    assert "https://github.com/stayingclean" in text
    assert "Erstellt von stayingclean" in text
    assert "https://buymeacoffee.com/stayingclean" in text
    assert "Kaffee spendieren" in text


def test_seite_laedt_nichts_von_aussen_ausser_dem_avatar():
    """CSS eingebettet, keine fremde Schriftquelle — sonst sähe die Seite
    ohne Internet anders aus. Der Avatar der Fusszeile ist die vereinbarte
    Ausnahme aus CLAUDE.md."""
    text = SEITE.read_text(encoding="utf-8")
    assert 'rel="stylesheet"' not in text
    assert "fonts.googleapis.com" not in text
    assert "fonts.gstatic.com" not in text


def test_seite_verweist_auf_beide_bilddateien():
    text = SEITE.read_text(encoding="utf-8")
    assert "plakat-skillsliste.png" in text, "die grosse Datei fehlt"
    assert "plakat-vorschau.jpg" in text, "die Vorschau fehlt"
    assert BILD.exists()
    assert VORSCHAU.exists()


def test_vorschau_ist_klein_genug_fuer_einen_seitenaufruf():
    """Die grosse Datei ist 14,9 MB. Die Vorschau existiert genau darum, dass
    nicht jeder Seitenaufruf sie herunterlädt."""
    assert VORSCHAU.stat().st_size < 1_000_000
    assert VORSCHAU.stat().st_size * 10 < BILD.stat().st_size


def test_vorschau_zeigt_dasselbe_wie_die_grosse_datei():
    """Nach einem Austausch des Plakats muss auch die Vorschau neu erzeugt
    werden. Ein abweichendes Seitenverhältnis verrät, dass das vergessen ging."""
    from PIL import Image

    with Image.open(BILD) as gross, Image.open(VORSCHAU) as klein:
        assert klein.width < gross.width, "Vorschau ist nicht verkleinert"
        assert klein.width / klein.height == pytest.approx(
            gross.width / gross.height, rel=0.01
        )


def test_alle_drei_pdf_knoepfe_stehen_auf_der_seite():
    text = SEITE.read_text(encoding="utf-8")
    for format_name in ("A5", "A4", "A3"):
        assert f'data-format="{format_name}"' in text


def test_lokaler_aufruf_wird_erklaert():
    """Als Datei geöffnet kann die Seite die Bilddatei nicht lesen. Das muss
    dastehen, statt still zu scheitern."""
    text = SEITE.read_text(encoding="utf-8")
    assert "file:" in text
```

Lauf:

```bash
uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_plakat.py -v
```

Erwartet: die fünf neuen Tests schlagen fehl, die aus Task 1 bestehen weiter.

- [ ] **Schritt 3: Kopf und Gestaltung ergänzen**

In `docs/plakat.html` den `<head>` ersetzen. Farben und Aufbau folgen
`docs/index.html`, damit die Seite dazugehört — aber mit Systemschriften statt
Google Fonts, damit sie auch ohne Internet gleich aussieht.

```html
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Plakat – Toolbox</title>
  <style>
    :root {
      --bg: #FAF8F5;
      --card: #FFFFFF;
      --border: #E8E4DF;
      --text: #1C1C1C;
      --muted: #7A7268;
      --accent: #008080;
      --accent-dark: #006666;
      --accent-tint: #E6F2F2;
      --warn: #8A5A2B;
      --warn-tint: #FBF1E4;
      --warn-border: #EDD9BF;
      --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                   Helvetica, Arial, sans-serif;
      --font-display: Georgia, "Times New Roman", serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--font-body);
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }
    /* Derselbe dezente Puls wie auf der Übersicht — hält die Seiten zusammen. */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      z-index: -1;
      pointer-events: none;
      background: radial-gradient(ellipse 80% 55% at 50% 0%, var(--accent-tint) 0%, transparent 68%);
      opacity: 0.3;
      animation: breathe 7s ease-in-out infinite;
    }
    @keyframes breathe {
      0%, 100% { opacity: 0.22; transform: scaleY(1); }
      50%      { opacity: 0.40; transform: scaleY(1.05); }
    }
    @media (prefers-reduced-motion: reduce) {
      body::before { animation: none; }
    }
    .wrap { max-width: 760px; margin: 0 auto; padding: 48px 20px 64px; }
    .zurueck { margin: 0 0 18px; }
    .zurueck a { color: var(--muted); text-decoration: none; font-size: 0.9rem; }
    .zurueck a:hover { color: var(--accent); }
    h1 {
      font-family: var(--font-display);
      font-size: 2rem; font-weight: 600; margin: 0 0 8px;
      letter-spacing: -0.01em; color: var(--accent-dark);
    }
    .sub { color: var(--muted); margin: 0; font-size: 1rem; }
    h2 {
      font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em;
      color: var(--muted); margin: 0 0 12px;
    }
    .vorschau { margin: 32px 0 0; padding: 0; }
    .vorschau img {
      display: block; width: 100%; height: auto;
      border: 1px solid var(--border); border-radius: 14px; background: var(--card);
    }
    .vorschau figcaption { margin-top: 8px; color: var(--muted); font-size: 0.82rem; }
    .fehlbild {
      display: none; padding: 28px; text-align: center;
      border: 1px dashed var(--border); border-radius: 14px;
      background: var(--card); color: var(--muted);
    }
    .downloads { margin-top: 32px; }
    .knoepfe { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
    @media (max-width: 620px) { .knoepfe { grid-template-columns: repeat(2, 1fr); } }
    .knopf {
      display: flex; flex-direction: column; gap: 4px;
      padding: 16px 18px; background: var(--card);
      border: 1px solid var(--border); border-radius: 14px;
      text-decoration: none; color: var(--text); font: inherit; text-align: left;
      cursor: pointer;
      transition: background 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
    }
    .knopf:hover:not(:disabled) {
      background: var(--accent-tint); border-color: var(--accent);
      transform: translateY(-2px);
    }
    .knopf:disabled { opacity: 0.45; cursor: default; }
    .knopf-name { font-weight: 600; font-size: 1.05rem; color: var(--accent-dark); }
    .knopf-meta { color: var(--muted); font-size: 0.8rem; }
    .knopf.knapp .knopf-meta { color: var(--warn); }
    .status {
      display: none; margin-top: 14px; padding: 12px 14px;
      border: 1px solid var(--warn-border); border-radius: 10px;
      background: var(--warn-tint); color: var(--warn); font-size: 0.88rem;
    }
    .status.sichtbar { display: block; }
    footer {
      margin-top: 48px; padding-top: 20px;
      border-top: 1px solid var(--border);
      color: var(--muted); font-size: 0.82rem;
    }
    .footer-links {
      display: flex; flex-wrap: wrap; align-items: center;
      gap: 8px 14px; margin-top: 12px;
    }
    .footer-credit {
      display: inline-flex; align-items: center; gap: 8px;
      color: var(--muted); text-decoration: none; transition: color 0.15s ease;
    }
    .footer-credit:hover { color: var(--accent); }
    .footer-avatar {
      width: 28px; height: 28px; border-radius: 50%;
      border: 1px solid var(--border); object-fit: cover; display: block;
    }
    .footer-coffee {
      display: inline-flex; align-items: center; gap: 6px;
      color: var(--muted); text-decoration: none; transition: color 0.15s ease;
    }
    .footer-coffee:hover { color: var(--accent); }
    @media (max-width: 480px) { .footer-sep { display: none; } }
  </style>
</head>
```

- [ ] **Schritt 4: Den Rumpf ergänzen**

Der `<body>` erhält den Inhalt **vor** dem bestehenden `<script>`-Block:

```html
<body>
  <div class="wrap">
    <p class="zurueck"><a href="index.html">← Übersicht</a></p>

    <header>
      <h1>Plakat zur Skillsliste</h1>
      <p class="sub">Zum Aufhängen — mit QR-Codes zur Skillsliste und zum
        Vorschlagsformular.</p>
    </header>

    <figure class="vorschau">
      <img id="plakat" src="plakat-vorschau.jpg" width="1200" height="1697"
           alt="Plakat „Gemeinsam Skills stärken“ mit zwei QR-Codes: einer führt zur Skillsliste, einer zum Formular für eigene Vorschläge.">
      <div class="fehlbild" id="fehlbild">
        Das Plakat konnte nicht geladen werden.
      </div>
      <figcaption id="masse"></figcaption>
    </figure>

    <section class="downloads">
      <h2>Herunterladen</h2>
      <div class="knoepfe">
        <a class="knopf" href="plakat-skillsliste.png"
           download="plakat-skillsliste.png">
          <span class="knopf-name">PNG</span>
          <span class="knopf-meta" id="pngMeta">Bilddatei</span>
        </a>
        <button class="knopf" type="button" data-format="A5">
          <span class="knopf-name">PDF A5</span>
          <span class="knopf-meta">148 × 210 mm</span>
        </button>
        <button class="knopf" type="button" data-format="A4">
          <span class="knopf-name">PDF A4</span>
          <span class="knopf-meta">210 × 297 mm</span>
        </button>
        <button class="knopf" type="button" data-format="A3">
          <span class="knopf-name">PDF A3</span>
          <span class="knopf-meta">297 × 420 mm</span>
        </button>
      </div>
      <p class="status" id="status" role="status"></p>
    </section>

    <footer>
      <div>Das Plakat darf frei ausgedruckt und aufgehängt werden.</div>
      <div class="footer-links">
        <a class="footer-credit" href="https://github.com/stayingclean" target="_blank" rel="noopener">
          <img class="footer-avatar" src="https://github.com/stayingclean.png?size=80" alt="stayingclean" loading="lazy" width="28" height="28">
          <span>Erstellt von stayingclean</span>
        </a>
        <span class="footer-sep" aria-hidden="true">·</span>
        <a class="footer-coffee" href="https://buymeacoffee.com/stayingclean" target="_blank" rel="noopener">
          <span aria-hidden="true">☕</span><span>Kaffee spendieren</span>
        </a>
      </div>
    </footer>
  </div>

  <!-- Der <script>-Block aus Task 1 bleibt unverändert stehen, wo er ist:
       direkt hier, nach </div> und vor </body>. -->
</body>
```

Der `<body>`-Inhalt wird also **vor** den bestehenden `<script>`-Block gesetzt,
der Block selbst nicht angefasst — der PDF-Kern samt seinen Markern bleibt Wort
für Wort, wie er ist.

- [ ] **Schritt 5: Die Bedienlogik ergänzen**

Innerhalb der bestehenden `(function(){ … })()`, **nach** `/* == pdf-kern:ende == */`
und vor dem schliessenden `})();`:

```js
  /* ---------- Bedienung ---------- */

  var BILD = 'plakat-skillsliste.png';   // die grosse Datei: Download und PDF
  var FORMATE = { A5: [148, 210], A4: [210, 297], A3: [297, 420] };
  var GUT_DPI = 150;                 // darunter wird der Druck sichtbar weich

  var plakat = document.getElementById('plakat');
  var status = document.getElementById('status');
  var knoepfe = [].slice.call(document.querySelectorAll('.knopf[data-format]'));
  var rohdaten = null;               // einmal geholt, dann behalten

  function melde(text) {
    status.textContent = text;
    status.classList.add('sichtbar');
  }
  function sperre() {
    knoepfe.forEach(function (knopf) { knopf.disabled = true; });
  }

  /* Die wahren Masse stehen im IHDR-Block, den ersten 34 Byte der grossen
     Datei. Ein Teilabruf holt genau die -- aus dem angezeigten Vorschaubild
     duerfen sie nicht kommen, das ist absichtlich klein und ergaebe unsinnige
     dpi-Werte. */
  function masseHolen() {
    var abbruch = new AbortController();
    return fetch(BILD, {
      headers: { Range: 'bytes=0-33' },
      signal: abbruch.signal
    }).then(function (antwort) {
      if (antwort.status !== 206) {
        // Server beachtet Range nicht: abbrechen, statt 14,9 MB zu laden.
        abbruch.abort();
        throw new Error('Teilabruf nicht möglich');
      }
      return antwort.arrayBuffer();
    }).then(function (puffer) {
      var sicht = new DataView(puffer);
      return { breite: sicht.getUint32(16), hoehe: sicht.getUint32(20) };
    });
  }

  /* Sagt ehrlich, was die Bilddatei hergibt. Rechnet sich beim Austausch der
     Datei von selbst neu -- keine Zahl von Hand nachpflegen. */
  function aufloesungZeigen(breite, hoehe) {
    if (!breite || !hoehe) return;
    document.getElementById('masse').textContent =
      breite + ' × ' + hoehe + ' Pixel';
    document.getElementById('pngMeta').textContent =
      'Bilddatei, ' + breite + ' × ' + hoehe + ' px';
    knoepfe.forEach(function (knopf) {
      var mm = FORMATE[knopf.getAttribute('data-format')];
      var dpi = Math.round(Math.min(breite / (mm[0] / 25.4), hoehe / (mm[1] / 25.4)));
      knopf.querySelector('.knopf-meta').textContent =
        mm[0] + ' × ' + mm[1] + ' mm · ' + dpi + ' dpi';
      knopf.classList.toggle('knapp', dpi < GUT_DPI);
      if (dpi < GUT_DPI) {
        knopf.title = 'Mit ' + dpi + ' dpi wird der Ausdruck in diesem Format '
                    + 'sichtbar weich. Gedruckt werden kann er trotzdem.';
      } else {
        knopf.removeAttribute('title');
      }
    });
  }

  function speichere(bytes, name) {
    var url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }));
    var verweis = document.createElement('a');
    verweis.href = url;
    verweis.download = name;
    document.body.appendChild(verweis);
    verweis.click();
    document.body.removeChild(verweis);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function bytesHolen() {
    if (rohdaten) return Promise.resolve(rohdaten);
    return fetch(BILD).then(function (antwort) {
      if (!antwort.ok) throw new Error('HTTP ' + antwort.status);
      return antwort.arrayBuffer();
    }).then(function (puffer) {
      rohdaten = new Uint8Array(puffer);
      return rohdaten;
    });
  }

  /* Rueckfallebene, nur noetig wenn die Datei kein 8-Bit-PNG ohne Interlace
     ist: das Bild aus den bereits geholten Bytes aufbauen und ueber ein Canvas
     als JPEG ausgeben. Ausdruecklich NICHT das angezeigte Vorschaubild -- das
     ergaebe ein PDF aus einer 1200-px-Vorlage. */
  function bildAusBytes(bytes) {
    return new Promise(function (erfuellen, ablehnen) {
      var url = URL.createObjectURL(new Blob([bytes], { type: 'image/png' }));
      var bild = new Image();
      bild.onload = function () { erfuellen({ bild: bild, url: url }); };
      bild.onerror = function () {
        URL.revokeObjectURL(url);
        ablehnen(new Error('Bilddatei ist nicht lesbar'));
      };
      bild.src = url;
    });
  }

  function jpegBytes(bild) {
    var flaeche = document.createElement('canvas');
    flaeche.width = bild.naturalWidth;
    flaeche.height = bild.naturalHeight;
    var stift = flaeche.getContext('2d');
    stift.fillStyle = '#ffffff';                 // JPEG kennt keine Transparenz
    stift.fillRect(0, 0, flaeche.width, flaeche.height);
    stift.drawImage(bild, 0, 0);
    var uri = flaeche.toDataURL('image/jpeg', 0.92);
    var roh = atob(uri.slice(uri.indexOf(',') + 1));
    var bytes = new Uint8Array(roh.length);
    for (var i = 0; i < roh.length; i++) bytes[i] = roh.charCodeAt(i);
    return bytes;
  }

  function erzeuge(format) {
    var mm = FORMATE[format];
    var name = 'plakat-skillsliste-' + format.toLowerCase() + '.pdf';
    status.classList.remove('sichtbar');
    bytesHolen().then(function (png) {
      try {
        speichere(pdfAusPng(png, mm[0], mm[1]), name);
        return null;
      } catch (fehler) {
        if (fehler.name !== 'PngNichtTauglich') throw fehler;
      }
      return bildAusBytes(png).then(function (geladen) {
        try {
          speichere(pdfAusJpeg(jpegBytes(geladen.bild), geladen.bild.naturalWidth,
                               geladen.bild.naturalHeight, mm[0], mm[1]), name);
        } finally {
          URL.revokeObjectURL(geladen.url);
        }
      });
    }).catch(function (fehler) {
      melde('Das PDF konnte nicht erzeugt werden ('
          + (fehler && (fehler.message || fehler.name) || 'unbekannter Fehler')
          + '). Das PNG lässt sich weiterhin herunterladen.');
    });
  }

  knoepfe.forEach(function (knopf) {
    knopf.addEventListener('click', function () {
      erzeuge(knopf.getAttribute('data-format'));
    });
  });

  plakat.addEventListener('error', function () {
    plakat.style.display = 'none';
    document.getElementById('fehlbild').style.display = 'block';
  });

  /* Als Datei geoeffnet duerfen Browser die Bilddatei nicht per Skript lesen.
     Das gleich sagen, statt den Benutzer in einen Fehlschlag laufen zu lassen. */
  if (location.protocol === 'file:') {
    sperre();
    melde('Diese Seite wurde als lokale Datei geöffnet. Browser erlauben hier '
        + 'nicht, die Bilddatei per Skript zu lesen — die PDF-Knöpfe ruhen '
        + 'deshalb. Auf stayingclean.github.io/toolbox/ funktionieren sie. '
        + 'Das PNG lässt sich auch hier herunterladen.');
  } else {
    masseHolen().then(function (masse) {
      aufloesungZeigen(masse.breite, masse.hoehe);
    }).catch(function () {
      /* Ohne Teilabruf bleiben die Knoepfe bei ihren Millimeterangaben. Lieber
         keine dpi-Zahl als eine erfundene -- die Knoepfe funktionieren
         weiterhin, das PDF haengt nicht an dieser Abfrage. */
    });
  }
```

Der Hinweis „Bilddatei fehlt" hängt jetzt nicht mehr an der Vorschau: Fällt nur
die Vorschau aus, ist bloss die Anzeige leer, die Downloads gehen weiter. Fällt
die grosse Datei aus, meldet sich der `catch` in `erzeuge` — dort, wo es zählt.

- [ ] **Schritt 6: `test.bat` um `pillow` ergänzen**

Die neuen Tests vergleichen Vorschau und Original, dafür braucht es Pillow. Aus:

```bat
uv run --with pytest --with openpyxl --with pypdf pytest tests -v
```

wird:

```bat
uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -v
```

- [ ] **Schritt 7: Tests laufen lassen**

```bash
uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -v
```

Erwartet: alles bestanden, auch die sieben neuen statischen Tests.

- [ ] **Schritt 8: Commit**

```bash
git add docs/plakat.html docs/plakat-vorschau.jpg tests/test_plakat.py test.bat
git commit -m "$(cat <<'EOF'
Plakat-Seite: Vorschau, vier Downloads, ehrlicher Aufloesungshinweis

Die grosse Plakatdatei ist 14,9 MB. Als Vorschau eingebunden lude sie
jeder Seitenaufruf herunter, auch ohne Download -- darum liegt daneben
eine verkleinerte JPEG-Vorschau von rund 360 KB. PNG als Vorschau waere
bei gleicher sichtbarer Qualitaet achtmal so gross: Aquarell ist nichts
fuer verlustfreie Kompression.

Daraus folgen zwei Dinge, die man leicht uebersieht. Der
Aufloesungshinweis darf nicht aus der Vorschau rechnen, sonst meldet er
1200 px; die wahren Masse holt ein Teilabruf aus den ersten 34 Byte der
grossen Datei, wo der IHDR-Block steht. Und die Canvas-Rueckfallebene
darf nicht die Vorschau zeichnen, sonst entstuende ein PDF aus einer
1200-px-Vorlage -- sie baut ihr Bild aus den geholten Bytes.

Unter 150 dpi wird ein Knopf markiert, aber nicht gesperrt: wer so
drucken will, darf das, soll es aber vorher wissen.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Verlinkung und Dokumentation

**Files:**
- Modify: `docs/index.html:167-175` (Gruppe „Skills")
- Modify: `CLAUDE.md` (Aufbau-Liste)
- Modify: `tests/test_plakat.py`

**Interfaces:**
- Consumes: die Seite aus Task 2.
- Produces: nichts.

- [ ] **Schritt 1: Die Tests schreiben**

An `tests/test_plakat.py` anhängen:

```python
def test_uebersicht_verlinkt_das_plakat_in_der_skills_gruppe():
    text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    ab = text.index('class="group group--skills"')
    bis = text.index("</section>", ab)
    gruppe = text[ab:bis]
    assert 'href="plakat.html"' in gruppe, "Karte steht nicht in der Skills-Gruppe"


def test_claude_md_nennt_die_neue_seite():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/plakat.html" in text
```

Lauf:

```bash
uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_plakat.py -v
```

Erwartet: die zwei neuen Tests schlagen fehl.

- [ ] **Schritt 2: Karte in `docs/index.html` ergänzen**

In der Gruppe `group--skills`, nach der Karte „Skill vorschlagen":

```html
        <a class="card card--skills" href="plakat.html">
          <span class="name">Plakat</span>
          <span class="meta">Zum Aufhängen – als PNG oder PDF in A5, A4, A3</span>
        </a>
```

Das Raster ist zweispaltig; die dritte Karte rutscht in die zweite Zeile. Das ist
in Ordnung und braucht keine Sonderbehandlung.

- [ ] **Schritt 3: `CLAUDE.md` ergänzen**

Im Abschnitt „Aufbau", nach der Zeile zu `docs/skills-daten.json`:

```markdown
- `docs/plakat.html` = Plakat zur Skillsliste zum Herunterladen (PNG und PDF in
  A5/A4/A3). Das PDF baut die Seite selbst; die Bildpunkte des PNG wandern dabei
  unverändert ins PDF. Das Plakat liegt in **zwei** Dateien daneben:
  `docs/plakat-skillsliste.png` in voller Auflösung (3508 × 4961 px, 300 dpi auf
  A3) für Download und PDF, und `docs/plakat-vorschau.jpg` (~360 KB) nur für die
  Anzeige — sonst lüde jeder Seitenaufruf 14,9 MB.

  **Beim Austausch des Plakats muss die Vorschau neu erzeugt werden:**

  ```
  uv run --with pillow python -c "from PIL import Image; q=Image.open('docs/plakat-skillsliste.png'); q.resize((1200, round(1200*q.height/q.width)), Image.LANCZOS).convert('RGB').save('docs/plakat-vorschau.jpg', quality=80, optimize=True, progressive=True)"
  ```

  Sonst nichts: Der Auflösungshinweis auf der Seite rechnet sich von selbst neu,
  und `pytest tests` prüft, ob die neue Datei weiterhin verlustfrei ins PDF
  durchgereicht werden kann und ob die Vorschau zum Original passt.
```

- [ ] **Schritt 4: Tests laufen lassen**

```bash
uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -v
```

Erwartet: alles bestanden.

- [ ] **Schritt 5: Commit**

```bash
git add docs/index.html CLAUDE.md tests/test_plakat.py
git commit -m "$(cat <<'EOF'
Uebersicht und CLAUDE.md nennen die Plakat-Seite

Die Karte steht in der Skills-Gruppe, weil das Plakat auf die Skillsliste
und das Vorschlagsformular fuehrt und damit dort hingehoert.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Sichtprüfung im Browser

Die Tests decken Masse und Bytes ab, aber nicht, ob die Seite gut aussieht und
sich richtig anfühlt. Das muss ein Mensch (oder ein Browser) sehen.

**Files:** keine Änderungen, ausser es fällt etwas auf.

- [ ] **Schritt 1: Lokalen Server starten**

`fetch` braucht http — genau darum ruhen die PDF-Knöpfe bei `file://`.

```bash
uv run python -m http.server 8765 --directory docs
```

- [ ] **Schritt 2: `http://localhost:8765/plakat.html` öffnen und prüfen**

- Vorschau erscheint, Bildmasse stehen darunter: `3508 × 4961 Pixel` — nicht
  `1200 × 1697`. Steht dort die Vorschaugrösse, kommt der Hinweis aus der
  falschen Datei.
- Vier Knöpfe; die PDF-Knöpfe zeigen mm **und** dpi: A5 600, A4 424, A3 300.
- **Kein** Knopf ist als knapp markiert (alle über 150 dpi).
- Im Netzwerk-Reiter der Entwicklerwerkzeuge: Der Seitenaufruf lädt rund 360 KB,
  nicht 14,9 MB. Die grosse Datei taucht erst beim Klick auf einen PDF-Knopf auf
  — davor nur ein winziger Teilabruf (Status 206).
- Fusszeile mit Avatar und Kaffee-Link.
- Auf schmalem Fenster (unter 620 px) rutschen die Knöpfe auf zwei Spalten.

- [ ] **Schritt 3: Alle vier Downloads auslösen**

Erwartet: `plakat-skillsliste.png`, `plakat-skillsliste-a5.pdf`,
`plakat-skillsliste-a4.pdf`, `plakat-skillsliste-a3.pdf` landen im
Download-Ordner. Die drei PDFs öffnen und ansehen: Plakat füllt die Seite,
nichts ist verzerrt oder abgeschnitten, beide QR-Codes sind scharf.

- [ ] **Schritt 4: QR-Codes prüfen**

Die beiden QR-Codes aus einem geöffneten PDF mit dem Telefon scannen. Erwartet:
der grosse führt zur Skillsliste, der kleine zum Vorschlagsformular. Führen sie
woandershin, gehört das gemeldet — dann stimmt die Bildvorlage nicht, nicht der
Code dieser Aufgabe.

- [ ] **Schritt 5: Den lokalen Fall prüfen**

`docs/plakat.html` per Doppelklick öffnen (also über `file://`). Erwartet: Seite
sieht vollständig aus, Vorschau da, PDF-Knöpfe ausgegraut, Hinweistext erklärt
warum, PNG-Link funktioniert.

- [ ] **Schritt 6: Server beenden und Ergebnis berichten**

Was auffällt, wird gemeldet, nicht stillschweigend repariert — ausser es ist ein
offensichtlicher Tippfehler.

---

## Nach dem Plan

- Die höher aufgelöste Bilddatei ist **während der Umsetzung eingetroffen** und
  ist bereits die Grundlage: 3508 × 4961 px, 8-Bit-RGB ohne Interlace — 600 dpi
  auf A5, 424 auf A4, 300 auf A3. Damit ist kein Format mehr knapp. Die
  `knapp`-Markierung bleibt trotzdem im Code: Sie greift beim nächsten
  Plakatwechsel wieder, falls die neue Vorlage kleiner ausfällt.
- Zum Schluss `superpowers:finishing-a-development-branch`, um den Branch
  zusammenzuführen. **Nichts geht ohne Push online.**
