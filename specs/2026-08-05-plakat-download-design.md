# Plakat zur Skillsliste zum Herunterladen

**Datum:** 2026-08-05
**Branch:** `feature/plakat-download`

## Ziel

Das bestehende Plakat („Gemeinsam Skills stärken", mit QR-Codes zur Skillsliste und
zum Vorschlagsformular) soll auf der Toolbox öffentlich zum Herunterladen stehen —
als **PNG** und als **PDF in A5, A4 oder A3**. Der Link gehört in die Gruppe
**Skills** der Übersicht.

## Entscheidungen

Diese Punkte wurden im Gespräch festgelegt und begrenzen den Umfang bewusst:

- **Kein Editor.** Ursprünglich stand eine abgespeckte Fassung des Flyer-Editors zur
  Debatte. Verworfen: Der Plakattext steckt im Bild und wäre ohnehin nicht änderbar
  gewesen; eine schlichte Download-Seite leistet, was gebraucht wird.
- **Kein HTML-Download.** Nur PNG und PDF.
- **PDF als echte Datei**, nicht über den Druckdialog. Ein Klick, fertige Datei,
  exaktes Papierformat — ohne dass Randeinstellungen im Dialog das Ergebnis
  verderben können.
- **Das Bild bleibt eine eigene Datei** und wird zur Laufzeit geladen, nicht in die
  HTML eingebettet. Eine höher aufgelöste Fassung wird nachgereicht und ersetzt
  einfach die Datei; an der Seite ist dann nichts zu ändern.

## Ausgangslage: Auflösung

Die vorhandene Datei misst **1054 × 1492 px**. Das Seitenverhältnis passt zum
A-Format (0,7064 gegenüber 0,7071 — ein Unterschied von 0,1 %), die Auflösung
reicht aber nur für rund 127 dpi auf A4 und 90 dpi auf A3. Für sauberen Druck bis
A3 braucht es etwa 3500 × 4960 px.

Die Seite wird deshalb so gebaut, dass sie mit **jeder** Bildgrösse richtig
arbeitet und dem Benutzer ehrlich sagt, was das aktuelle Bild hergibt. Die
höher aufgelöste Datei kommt später und wird nur ausgetauscht.

## Dateien

| Datei | Art | Zweck |
|---|---|---|
| `docs/plakat-skillsliste.png` | neu | Das Plakat, aus `neue_docs/` kopiert. Austauschbar. |
| `docs/plakat.html` | neu | Die Download-Seite. CSS eingebettet, Fusszeile mit Credit und Kaffee-Link. |
| `docs/index.html` | geändert | Neue Karte in der Gruppe „Skills". |
| `tests/test_plakat.py` | neu | Prüft Seite und PDF-Erzeugung. |
| `tests/plakat_pdf_treiber.mjs` | neu | Node-Treiber, der den PDF-Kern aus der HTML zum Testen ausführt. |

## Die Seite `docs/plakat.html`

Aufbau von oben nach unten:

1. Kurzer Titel und ein, zwei Sätze, worum es geht.
2. **Vorschau** des Plakats (das Bild selbst, in der Breite begrenzt).
3. **Download-Bereich** mit vier Knöpfen: `PNG`, `PDF A5`, `PDF A4`, `PDF A3`.
   Drei getrennte PDF-Knöpfe statt Auswahlfeld plus Knopf — ein Klick statt zwei.
4. **Auflösungshinweis**, zur Laufzeit aus der tatsächlichen Bildgrösse gerechnet.
5. Fusszeile nach der Konvention aus `CLAUDE.md`.

Gestaltung übernimmt die Farben und Typografie der Übersicht (`docs/index.html`),
damit die Seite dazugehört. Schriften werden allerdings **nicht** von Google
geladen — Systemschriften genügen, und die Seite bleibt ohne Internet ansehnlich.

### PNG-Knopf

Ein gewöhnlicher Link mit `download`-Attribut auf `plakat-skillsliste.png`. Kein
JavaScript, keine Umrechnung: Ein Pixelbild hat kein Papierformat, das entscheidet
erst der Drucker. Der Benutzer bekommt die Datei so, wie sie ist.

### PDF-Knöpfe

Beim Klick baut die Seite das PDF selbst und legt es als Download ab. Keine fremde
Bibliothek, alles im Browser.

**Weg A — PNG-Daten unverändert durchreichen (Regelfall).**

Ein PNG speichert seine Bildpunkte als zlib-Strom über zeilenweise gefilterte
Rohdaten. PDF liest genau dasselbe Format: `FlateDecode` mit
`DecodeParms << /Predictor 15 /Colors n /BitsPerComponent 8 /Columns Breite >>`.
Die Bilddaten wandern also Byte für Byte aus dem PNG ins PDF — verlustfrei, ohne
Neuberechnung. Für die beiden QR-Codes ist das der entscheidende Punkt: harte
Schwarz-Weiss-Kanten sind genau das, woran eine JPEG-Kompression sichtbar
knirscht.

Ablauf:

1. `fetch()` holt die PNG-Datei als `ArrayBuffer`.
2. Die Datei wird in ihre Chunks zerlegt. Aus `IHDR` kommen Breite, Höhe,
   Bittiefe, Farbtyp und Interlace-Kennzeichen; alle `IDAT`-Blöcke werden in der
   vorgefundenen Reihenfolge aneinandergehängt und ergeben den vollständigen
   zlib-Strom.
3. Weg A gilt für **Bittiefe 8, Farbtyp 0 (Graustufen) oder 2 (RGB), ohne
   Interlace**. Alles andere fällt auf Weg B.
4. Das PDF wird aus sechs Objekten zusammengesetzt: Katalog, Seitenbaum, Seite,
   Bild-XObject, Inhaltsstrom, Querverweistabelle.

Weg A rührt kein Canvas an und kann darum auch nicht an dessen
Sicherheitsbeschränkungen scheitern.

**Weg B — Rückfallebene.**

Ist die Bilddatei ein Typ, den Weg A nicht abdeckt (Palettenfarben, Transparenz,
Interlace, 16 Bit), zeichnet die Seite das Bild in ein Canvas und bettet es als
JPEG mit Qualität 0,92 ein (`/DCTDecode`). Etwas weicher, aber brauchbar — und der
Benutzer merkt nur, dass es funktioniert. Weg B ist ausdrücklich Rückfall, nicht
Regelfall: Ein neu eingesetztes Plakat sollte ein 8-Bit-RGB-PNG ohne Interlace
sein, damit Weg A greift.

**Seitenmasse.** In PDF-Punkten (1 pt = 1/72 Zoll), gerundet auf drei
Nachkommastellen:

| Format | mm | pt |
|---|---|---|
| A5 | 148 × 210 | 419,528 × 595,276 |
| A4 | 210 × 297 | 595,276 × 841,890 |
| A3 | 297 × 420 | 841,890 × 1190,551 |

**Platzierung.** Das Bild wird **unter Wahrung des Seitenverhältnisses** so gross
wie möglich auf die Seite gelegt und zentriert. Beim heutigen Bild bleibt dadurch
ein Rand von 0,1 % — rund 0,2 mm auf A4, mit blossem Auge nicht zu sehen, also
praktisch randlos. Der Verzicht aufs Verzerren ist Absicht: Ein künftiges Plakat
mit abweichendem Seitenverhältnis wird dann sauber eingepasst statt gestaucht.

**Dateinamen** der Downloads: `plakat-skillsliste-a5.pdf`, `-a4.pdf`, `-a3.pdf`.

### Auflösungshinweis

Sobald das Bild geladen ist, rechnet die Seite aus `naturalWidth` die effektive
Auflösung für jedes Format aus (`Pixel ÷ Zoll`) und zeigt sie beim jeweiligen
Knopf an, etwa „127 dpi". Formate unter 150 dpi werden zusätzlich sichtbar als
knapp gekennzeichnet; verboten wird nichts — wer ein A3 mit 90 dpi drucken will,
darf das, soll es aber vorher wissen.

Der Hinweis rechnet sich beim Austausch der Bilddatei von selbst neu. Es gibt
keine Zahl, die von Hand nachzupflegen wäre.

## Fehlerfälle

| Fall | Verhalten |
|---|---|
| Bild lädt nicht (Datei fehlt, offline) | Vorschau zeigt einen Hinweis statt eines kaputten Bildes, die PDF-Knöpfe werden ausgegraut, der PNG-Link bleibt nutzbar. |
| Seite lokal per Doppelklick geöffnet (`file://`) | Browser verbieten dort das Auslesen lokaler Dateien per Skript, `fetch()` scheitert. Die Seite sagt das klar an („PDF-Erzeugung braucht die Seite im Web") statt stumm zu scheitern. Online ist das kein Thema. |
| PNG-Typ passt nicht zu Weg A | Weg B greift; keine Meldung nötig. |
| Auch Weg B scheitert | Verständliche Meldung im Hinweisbereich, kein stiller Abbruch. |

Die Regel aus `CLAUDE.md` („auch lokal ohne Server/Internet funktionieren")
bezieht sich auf eingebettetes CSS statt externer Stylesheets. Das hält die Seite
ein: Sie ist lokal vollständig lesbar, Vorschau und PNG-Link funktionieren, nur
die PDF-Erzeugung ruht — und sagt warum.

## Änderung an der Übersicht

In `docs/index.html`, Gruppe `group--skills`, eine dritte Karte:

```html
<a class="card card--skills" href="plakat.html">
  <span class="name">Plakat</span>
  <span class="meta">Zum Aufhängen – als PNG oder PDF in A5, A4, A3</span>
</a>
```

Die Gruppe verwendet ein zweispaltiges Raster; die dritte Karte rutscht in die
zweite Zeile. Das ist in Ordnung und braucht keine Sonderbehandlung.

## Prüfung

Der PDF-Kern wird als **reine Funktion** geschrieben —
`pngZuPdf(pngBytes, breiteMm, hoeheMm) → Uint8Array` — ohne Zugriff auf DOM,
`fetch` oder Canvas. Nur der Aufrufdrumherum kennt die Seite. Damit ist der
heikelste Teil ausserhalb des Browsers prüfbar.

In `docs/plakat.html` wird dieser Teil zwischen zwei Marker-Kommentare gesetzt:

```js
/* == pdf-kern:anfang == */
…
/* == pdf-kern:ende == */
```

`tests/test_plakat.py` schneidet den Abschnitt heraus, lässt ihn über
`tests/plakat_pdf_treiber.mjs` in Node laufen und prüft das Ergebnis:

- **Seitenmasse:** Die `MediaBox` jedes erzeugten PDFs entspricht dem Format in
  Punkten (Toleranz 0,01 pt).
- **Bildmasse:** `/Width` und `/Height` im XObject entsprechen den Pixelmassen der
  Quelldatei.
- **Verlustfreiheit:** Der Flate-Strom im PDF ist Byte für Byte gleich den
  aneinandergehängten `IDAT`-Blöcken der Quelldatei. Das ist die eigentliche
  Zusicherung von Weg A.
- **Seitenverhältnis:** Die Skalierung im Inhaltsstrom passt das Bild ein, ohne es
  zu verzerren, und zentriert es.
- **Lesbarkeit:** Die Querverweistabelle stimmt (Objekt-Byteversätze), und das PDF
  lässt sich von einem unabhängigen Leser öffnen.

Dazu ein paar statische Prüfungen der Seite selbst: Fusszeile mit Credit und
Kaffee-Link vorhanden, kein externes Stylesheet, keine externe Schriftquelle, die
Karte in `docs/index.html` verweist auf `plakat.html`, und die Bilddatei liegt in
`docs/`.

Zum Schluss eine Sichtprüfung im echten Browser: Seite öffnen, alle vier Downloads
auslösen, die drei PDFs ansehen.

## Was bewusst nicht dazugehört

- Kein Editor, keine Textfelder, kein Austausch des Hintergrunds.
- Keine PNG-Varianten in mehreren Grössen — die Originaldatei genügt.
- Keine Formate ausser A5, A4, A3.
- Kein Hochskalieren des Bildes, um Auflösung vorzutäuschen.

## Offene Punkte

- Die **höher aufgelöste Bilddatei** wird nachgereicht. Bis dahin steht die
  aktuelle 1054 × 1492 px grosse Fassung in `docs/`, und der Auflösungshinweis
  sagt ehrlich, wofür sie reicht. Der Austausch ist ein reiner Dateitausch.
- Mit `docs/plakat-skillsliste.png` wandert erstmals eine Datei aus `neue_docs/`
  ins öffentliche Verzeichnis. Das Plakat ist Eigengestaltung der Organisation und
  enthält keine personen- oder organisationsspezifischen Angaben ausser den beiden
  QR-Codes, die auf die Toolbox selbst zeigen — die Veröffentlichung ist damit
  unbedenklich.
