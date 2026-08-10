# Beschriftete Bezugsquellen mit Shop-Symbol

**Datum:** 2026-08-07
**Baut auf:** `specs/2026-08-06-bezugsquellen-design.md` (Stufe 1, PR #7)

## Ziel

Ein Bezugsquellen-Knopf soll zeigen, **was** dort zu holen ist, nicht nur bei
welchem Händler. Statt

```
[ ↗ skills-box.ch ]  [ ↗ skills-box.ch ]  [ ↗ coop.ch ]
```

soll dort stehen

```
[ 🟧 Igelball ]  [ 🟧 Massage ]  [ 🟥 Peperoncini ]
```

## Warum das nötig wurde

Stufe 1 leitet die Aufschrift aus dem Hostnamen ab. Mit leeren Link-Spalten sah
das gut aus. Sobald echte Daten drin waren, zeigte sich: **17 von 44 Skills
haben zwei oder drei Knöpfe mit derselben Aufschrift**, meist `skills-box.ch` —
verschiedene Produkte im selben Shop. Bei „Handmuskeln anspannen" stehen drei
identische nebeneinander. Das ist kein Randfall, sondern jeder dritte Skill.

Ein erster Gedanke war, den Suchbegriff bzw. Pfad automatisch anzuhängen. Die
Messung im echten Dialog ergab: das passt (496 px am Desktop, 322 px am Handy,
nichts läuft über), erzeugt aber Aufschriften wie
`galaxus.ch · wittner maelzel serie 810k metronom zubehoer instrumente` — 69
Zeichen, am Handy zweizeilig. Galaxus hängt Kategoriewörter an den Slug.

Daraus entstand die bessere Lösung: eine **freiwillige, von Hand gepflegte
Beschriftung**, dazu ein Symbol für den Händler.

## Entscheidungen

- **Symbol + Beschreibung**, ohne Domain im Text. Kürzeste Knöpfe, gut lesbar.
- **Die Symbole werden beim Bauen eingebettet**, nicht zur Laufzeit geladen.
- **Die Beschriftung schreibt nur die betreuende Person in der Excel.** Besucher
  reichen weiterhin nur Adressen ein.
- Ohne Beschriftung bleibt es beim Hostnamen wie in Stufe 1.

## Datenmodell

### Excel, Blatt `Skills`

Drei Spalten kommen dazu, **paarweise verschränkt**, damit Adresse und Text beim
Pflegen nebeneinanderstehen:

```
… | Ergaenzt | Link1 | Text1 | Link2 | Text2 | Link3 | Text3
```

Das Einschieben zwischen die bestehenden Link-Spalten ist gefahrlos: `build.py`,
`tools/vorschlaege_holen.py` und `tools/seed_excel.py` arbeiten alle über den
**Spaltennamen**, nie über die Position.

`Text*` ist freiwillig, höchstens **30 Zeichen**, ohne spitze Klammern und ohne
`http` — eine Adresse in der Beschriftung wäre irreführend, gerade weil die
Domain nicht mehr im Text steht. `build.py` prüft das wie die Links und bricht
mit Blatt, Zeile und Spalte ab.

Ein `Text*` ohne zugehörigen `Link*` ist ein Fehler und bricht den Build ab —
sonst stünde eine Beschriftung ohne Ziel in der Mappe und niemand sähe es.

### In `skills-daten.json` und der Skillsliste

`links` wird von einer Liste von Zeichenketten zu einer Liste von Objekten:

```json
"links": [{"u": "https://www.skills-box.ch/products/igelball", "t": "Igelball"}]
```

`t` ist leer, wenn keine Beschriftung gepflegt ist.

**Der Formwechsel kostet zwei Zeilen an anderer Stelle** — das ist bewusst so
und nicht umgangen:

- `worker/index.js`, `quellen()` — baut die Bezugsquellen-Zelle im Issue
- `template-vorschlag.html` — füllt beim Ergänzen die Link-Liste vor

Die naheliegende Alternative wäre eine **zweite, parallele Liste** `linkTexte`
gewesen, die diese beiden Stellen unberührt liesse. Verworfen: zwei Listen, die
nur über den Index zusammengehören, laufen früher oder später auseinander, und
das fällt niemandem auf. Zwei Einzeiler sind der ehrlichere Preis.

## Symbole

`assets/favicons/<hostname>.png`, 32 × 32, Hostname ohne führendes `www.`:

```
assets/favicons/skills-box.ch.png
assets/favicons/coop.ch.png
assets/favicons/migros.ch.png
…
```

`build.py` bettet sie als `data:image/png;base64,…` ein. Die sieben heutigen
Dateien wiegen zusammen wenige Kilobyte.

**Fehlt eine Datei, gibt es kein Symbol und der Build läuft weiter.** Das ist
die wichtigste Eigenschaft dieses Teils: Wer eine Bezugsquelle bei einem neuen
Händler einträgt, darf damit nicht die ganze Website blockieren.

Ein Hilfsskript `tools/favicon_holen.py <domain>` holt und verkleinert ein
Symbol. Es ist **bewusst von `build.py` getrennt**, das offline und per
Doppelklick laufen muss — dasselbe Muster wie beim Plakat-Vorschaubild, das
`CLAUDE.md` schon dokumentiert.

**Das Skript wird nicht bei allen Händlern durchkommen.** Coop hat einen
serverseitigen Abruf bei der Link-Prüfung mit `403 Forbidden` beantwortet;
dieselben Bot-Sperren gelten fürs Favicon. Das Skript muss darum verständlich
melden, wenn es nicht geht, und den Weg von Hand nennen: Seite im Browser
öffnen, Symbol speichern, unter dem erwarteten Namen ablegen. Ein Fehlschlag
ist ein Hinweis, kein Abbruch — die sieben Dateien sind eine einmalige
Einrichtung, keine laufende Aufgabe.

## Anzeige

```
Bezugsquellen
[ 🟧 Igelball ]  [ 🟧 Massage ]  [ 🟥 Peperoncini ]  [ 🟦 galaxus.ch ]

Von Besuchern vorgeschlagen · keine Empfehlung, keine Provision
```

- Ohne `t` steht der Hostname da wie in Stufe 1.
- Das Symbol ist ein `<img>` mit leerem `alt` — es ist Schmuck, die Beschriftung
  daneben trägt die Bedeutung. Ein Vorlesegerät soll nicht „Bild" sagen.
- **Jeder Link bekommt `title` mit der vollständigen Adresse.** Damit bleibt das
  Ziel ablesbar, obwohl die Domain nicht mehr im Text steht — die Zusicherung
  aus Stufe 1 („man sieht vor dem Klick, wo man landet") wäre sonst verloren.
- `rel="noopener noreferrer nofollow ugc"` bleibt unverändert.

## Ausdrücklich nicht Teil davon

- **Kein Laden der Symbole vom Händler.** Ein `<img src="https://www.coop.ch/…">`
  würde beim Öffnen eines Skill-Dialogs an Coop melden, dass jemand genau diesen
  Skill angeschaut hat — ohne Klick, ohne Absicht. Auf einer Seite über
  Suchtdruck-Bewältigung ist das ein echtes Leck, und es ist derselbe Grund, aus
  dem Stufe 1 die Erreichbarkeitsprüfung im Browser verworfen hat.
- **Keine Beschriftung aus dem Formular.** Ohne sichtbare Domain fiele eine
  irreführende Beschriftung („Gratis Gutschein") kaum auf.
- **Kein automatisches Ableiten aus dem Pfad.** Gemessen und verworfen: bei
  Galaxus kommen dabei 69 Zeichen Slug-Salat heraus.
