# Grafische Übersicht der Anpassungen und freier Versionsvergleich

**Datum:** 2026-10-23
**Betrifft:** `docs/budgetvorlage.html` (eigenständige Seite, kein Generat)
**Dateiformat:** v5 bleibt — es kommt kein Feld dazu
**Deckt ab:** Punkt 8 und Punkt 9 aus `plans/2026-10-22-budget-offene-arbeiten.md`
**Mitlesen:** `specs/2026-10-21-budget-anpassungen-design.md` (verbindlich),
`plans/2026-10-22-budget-abarbeitungsplan.md` (Welle 4, Session B)

Beide Punkte stehen in einem Entwurf, weil sie dieselbe Fläche betreffen (die
Übersicht unter dem Formular) und dasselbe Werkzeug brauchen (einen Balken, der
eine Zahl zeigt). Getrennt entworfen entstünden zwei Diagrammsprachen auf einem
Blatt.

---

## Die Lage: Web zuerst, eine Bibliothek wäre erlaubt

**Nachtrag 2026-10-23, nach einer Rückfrage des Benutzers.** Eine frühere
Fassung dieses Abschnitts begann mit «die Seite läuft per `file://` ohne Server
und ohne Internet, also keine Bibliothek». Das war **zu streng formuliert** und
ist seit dem Entscheid des Benutzers überholt. Was wirklich gilt:

- **Die Budgetvorlage wird über die URL benutzt**, nicht als herumgeschickte
  Kopie. Herunterladen führte bei den Beratenden zu auseinanderlaufenden
  Ständen des Werkzeugs; dagegen hilft keine Sorgfalt in der Datei, nur eine
  Adresse. `CLAUDE.md`, Abschnitt «Neue HTML-Seite veröffentlichen», Punkt 3 ist
  entsprechend nachgezogen.
- **Die Seite speichert `.json`, nicht HTML** (`saveFile`, Zeile 5428;
  `defaultFilename` → `budget-JJJJ-MM-TT.json`). Werkzeug und Daten sind
  getrennt; kein ausgefülltes Budget steckt je in einer HTML-Datei. Die
  Konvention «Als HTML speichern» in `CLAUDE.md` gilt den Fragebögen, nicht
  dieser Seite.
- **Netzunabhängig war die Seite ohnehin nie.** Zeilen 7–9 laden Inter und
  Playfair Display von Google Fonts, die Fusszeile holt den Avatar von
  `github.com`. Ohne Netz zeichnet sie in Georgia und System-Sans — und das hat
  nie jemand als Fehler gemeldet.
- **Ohne Netz gibt es die Seite gar nicht.** Wer offline arbeiten muss, lädt sie
  vorher herunter; nur für diese Person stellt sich die Frage, was dann fehlt.

**Was damit geht:**

- Alles aus HTML und CSS, alles aus handgeschriebenem SVG.
- Schriften von aussen (die Seite tut es schon) und ein gemeinsames Stylesheet
  über mehrere Seiten.

**Was weiterhin nicht geht:**

- **Eine fremde Bibliothek.** Der Benutzer hat das am 2026-10-23 ausdrücklich
  bestätigt: erlaubt wäre sie seit dem Web-Entscheid, gewollt ist sie nicht.
  Käme je eine, dann mitgeliefert in `docs/vendor/` oder eingebettet, mit
  festgelegter Version — **nie vom CDN**: jeder Aufruf meldete einem Dritten,
  dass jemand diese Seite öffnet, hier also, dass jemand ein Budget bearbeitet.
  Dasselbe Argument steht in `CLAUDE.md` bei den Händler-Symbolen der
  Skillsliste («Die Symbole werden nie vom Händler geladen»).
- **Zwei Fassungen der Seite**, eine mit und eine ohne Diagramme. Technisch
  möglich (`if (location.protocol !== 'file:')`), aber zwei Verhalten müssten
  beide entworfen, gebaut und geprüft werden, und die Rückfallebene muss man
  ohnehin bauen — ist sie gut, braucht es die Bibliothek nicht.

### Was der Entscheid an der Abwägung ändert

Er nimmt dem stärksten Argument gegen eine Bibliothek die Grundlage: «200 KB
fremder Code in jeder weitergegebenen Datei» zählt nicht mehr, wenn der Browser
die Seite einmal von der URL lädt und im Cache behält. Das
Drittanbieter-Argument bleibt, wäre aber durch Mitliefern erledigt.

**Der Benutzer hat trotzdem bei «keine fremden Bibliotheken» bleiben wollen**
(2026-10-23). Die Abwägung unten steht darum nicht mehr zur Wahl — sie steht
hier, damit nachvollziehbar bleibt, was erlaubt gewesen wäre und warum es
niemandem fehlt.

**Dieser Entwurf bleibt trotzdem bei CSS** — aus einem Grund, der nichts mit
Offline zu tun hat: alle drei Diagramme sind Balken mit Textbeschriftung, und
genau dort verliert eine Bibliothek. Die verbreiteten zeichnen auf ein
`<canvas>`: für einen Screenreader leer, im Ausdruck ein Bild statt Text, und
die Zahlen müssten zweimal gesetzt werden — einmal im Diagramm, einmal als Text
daneben. Die Konfiguration wäre etwa so lang wie die fünfzig Zeilen CSS, die sie
ersetzt.

**Wann eine Bibliothek sich lohnen würde** (dann aber bewusst, nicht nebenbei):
eine echte Zeitachse oder Verlaufskurve statt Sprüngen zwischen Stichtagen;
viele Reihen auf einmal (fünf Versionen × elf Kategorien); Hover-Tooltips auf
dichten Daten; ein Diagramm als PNG für einen Bericht. Nichts davon steht in
Punkt 8 oder 9. Auswahlkriterium wäre dann **SVG-Ausgabe statt Canvas, klein,
MIT**, mit genau festgelegter Version — die Namen und Grössen gehören zum
Zeitpunkt der Wahl nachgeschaut, nicht aus diesem Entwurf übernommen.

---

## Was der Benutzer gesagt hat

**Punkt 8:** «Es gibt sehr viele Zahlen und nichts Grafisches. Wie könnte man
zum einen die Anpassungen, welche in der Version vorgenommen worden sind,
grafisch darstellen?»

**Punkt 9:** «Ein Button, der alle Versionen (auswählbar) vergleicht und die
Differenz anzeigt» — rechts neben der letzten Version.

Offen gelassen und in diesem Entwurf entschieden: Diagrammart, Anzahl
Diagramme, nur die Gesamtzahl oder auch die Kategorien, welche Versionen
auswählbar sind und wie die Differenz dargestellt wird.

---

## Was die Seite heute schon hat

**Zahlen, die fertig vorliegen** (Rechenkern zwischen
`/* == budget-kern:anfang == */`, Zeile 2727, und `/* == budget-kern:ende == */`,
Zeile 3106 — rein, ohne DOM, geprüft über `tests/budget_treiber.mjs`):

| Funktion | Zeile | liefert |
|---|---|---|
| `summen(schema, values)` | 3085 | Einnahmen, Ausgaben, Differenz — jährlich und monatlich |
| `stichtagListe(adjustments, heuteIso)` | 2946 | alle Stände in Reihenfolge: «heute», die Daten, «offen» |
| `werteFuerStand(values, adjustments, standKey)` | 2994 | Kopie der Werte mit den bis dahin eingelösten Anpassungen |
| `anpassungsGruppen(adjustments, staende, values)` | 3028 | je Stand die Einträge mit `altY/altM`, `neuY/neuM`, `deltaY/deltaM` und die Gruppensumme |
| `anpassungUnterschied(a, erfasstJaehrlich)` | 2760 | was eine Anpassung ausmacht |
| `anpassungWirkung(unterschied, istEinnahme)` | 2790 | `'gut'` / `'schlecht'` / `''` — **die Vorzeichenfrage ist beantwortet** |

**Was fehlt:** Summen je Kategorie gibt es im Kern **nicht**. `summen` teilt nur
in Einnahmen und Ausgaben; die Gruppensummen entstehen DOM-seitig in
`recomputeAll` als lokale Variable `groupTotals` (Zeile 4321) und sind von
aussen nicht erreichbar. Jedes Diagramm über Kategorien braucht also eine neue
Kernfunktion — das ist der Preis, der unten bei der Entscheidung gegen das
Kategoriendiagramm steht.

**Der Versionsvergleich existiert bereits.** `#versionsOverviewSection`
(Zeile 2423), sichtbar nur im Mehr-Versionen-Betrieb, enthält

- eine Tabelle aller Versionen mit Basis, Einnahmen/Jahr, Ausgaben/Jahr,
  Differenz/Jahr und Δ gegenüber der Basis, die aktive hervorgehoben
  (`renderVersionsOverview`, Zeile 4644),
- darunter die Stand-Zeilen derselben Version (Zeile 4694),
- darunter «Unterschiede pro Position» (`#versionsDetailBlock`, Zeile 2446;
  `renderVersionsDetail`, Zeile 4722) — die aktive Version gegen **ihre eigene
  Basis** (`basedOn`), nicht gegen eine wählbare.

**Punkt 9 ist damit eine Ergänzung, kein Neubau.** Es fehlen genau zwei Dinge:
die **freie Wahl** der zwei verglichenen Versionen, und ein **Einstieg** dort,
wo der Benutzer ihn sucht. Eine zweite Vergleichsansicht entsteht nicht — siehe
«Der bestehende Abschnitt wird umgebaut» weiter unten.

---

## Entscheidungen auf einen Blick

1. **Werkzeug: Balken aus HTML und CSS**, kein SVG — und keine Bibliothek,
   obwohl eine seit dem Web-Entscheid erlaubt wäre.
2. **Drei Diagramme, alle dieselbe Bauart:** die Stände der aktiven Version, die
   Rangliste der Anpassungen, die Versionen im Vergleich.
3. **Keine Kategorien** in diesem Schritt, mit begründetem Rückweg.
4. **Gerechnet wird im Kern**, gezeichnet im DOM: drei neue Kernfunktionen,
   testbar über `tests/budget_treiber.mjs`.
5. **Der bestehende Vergleichsabschnitt wird umgebaut**, der neue Knopf springt
   dorthin. Es gibt weiterhin genau eine Vergleichsansicht.
6. **Die Diagramme ersetzen die Vorschau nicht.** Die Schreibsperre in
   `captureFormToActiveVersion` bleibt (Antwort auf D4).
7. **Die Diagramme drucken mit** — mit Rahmen, damit sie in Graustufen lesbar
   bleiben.

---

## Werkzeugwahl: drei Varianten

### Variante A — Balken aus HTML und CSS *(empfohlen)*

Je Datenpunkt eine Zeile: Beschriftung, eine Spur (`.balken-spur`), darin ein
absolut gesetzter Balken mit `left` und `width` in Prozent, dazu die Zahl als
Text. Die Nulllinie ist ein 1px-Strich in der Spur, dessen Position dieselbe
Rechnung liefert.

- **Dafür:** Skaliert von 320 px bis Desktop ohne zweites Layout. Die Schrift
  bleibt echte Schrift in echter Grösse — kein `viewBox`, der Text mitschrumpft.
  Die Zahl steht als Text neben dem Balken, also liest ein Screenreader Sinn und
  nicht «Grafik». Rund fünfzig Zeilen CSS, keine Koordinatenrechnung.
- **Dagegen:** Nur Rechtecke. Keine Linie über die Zeit, keine verbundene
  Treppe, keine Achse mit Teilstrichen.

### Variante B — handgeschriebenes SVG

- **Dafür:** Alles zeichenbar — Wasserfall mit Verbindungsstücken, Linie über
  die Stichtage, echte Achse.
- **Dagegen:** Das `viewBox`-Problem. Mit fester Zeichenfläche und
  `width: 100%` schrumpft die Beschriftung auf einem Telefon mit; ohne `viewBox`
  müssen alle x-Werte aus `clientWidth` in Pixeln gerechnet und bei jeder
  Fensterbreite neu gesetzt werden. Dazu Koordinatenrechnung für jedes
  Diagramm und mehr Code, der nichts zeigt, was Variante A nicht zeigt.

### Variante C — Bibliothek, mitgeliefert oder eingebettet

- **Dafür:** Hover-Tooltips, Animation, Zoom. Das Grössenargument von früher
  zählt nicht mehr.
- **Dagegen:** Nichts aus Punkt 8 oder 9 verlangt eines der drei Merkmale — und
  die verbreiteten Bibliotheken zeichnen auf ein `<canvas>`: nichts für einen
  Screenreader, im Ausdruck ein Bild statt Text, die Zahlen zweimal zu setzen.
  Für Balken mit Textbeschriftung ist das ein Rückschritt, kein Fortschritt.

### Empfehlung

**Variante A.** Jedes Diagramm, das hier etwas aussagt, ist ein Balken an einer
Nulllinie: «wie viel bleibt am Monatsende» für mehrere Stände, Versionen oder
Positionen. Das ist genau der Fall, in dem CSS dem SVG überlegen ist, weil die
Beschriftung Text bleibt. Zeigt eine spätere Erweiterung, dass es eine echte
Zeitachse braucht, kommt **ein** Diagramm in SVG dazu — nicht eine Bibliothek.

---

## Punkt 8: welche Diagramme, und wie viele

Die Frage des Benutzers lautet ausdrücklich nach den **Anpassungen**, nicht nach
der Struktur des Budgets. Darum:

### Variante 1 — nur die Stände

Ein Diagramm: je Stand ein Balken der Differenz pro Monat. Alle Zahlen liegen
vor. **Zu wenig:** Es zeigt, *dass* sich etwas bewegt, aber nicht, *was* sich
bewegt. Bei acht Anpassungen bleibt die Frage «woher kommen die 113 Franken»
unbeantwortet.

### Variante 2 — Stände und Rangliste *(empfohlen)*

Zwei Diagramme: die Stände (die Gesamtzahl) und darunter je angepasste Position
ein Balken mit dem, was sie ausmacht (die Herkunft). Zusammen beantworten sie
«wie viel» und «woher», und beide rechnen aus Zahlen, die der Kern heute schon
liefert.

### Variante 3 — dazu ein Kategorien-Balken

Zusätzlich ein gestapelter Balken: Einnahmen gegen die Ausgaben nach Kategorien,
vorher und nachher. **Nicht in diesem Schritt**, aus drei Gründen:

1. Er braucht eine neue Kernfunktion für die Gruppensummen (siehe oben), also
   mehr neue Fläche als die beiden anderen Diagramme zusammen.
2. Er beantwortet eine andere Frage als Punkt 8 («wohin geht mein Geld» statt
   «was machen meine Anpassungen») und macht aus der Erfassungsseite eine
   Auswertungsseite. Das ist eine Entscheidung des Benutzers, nicht des
   Umsetzenden.
3. Elf Kategorien von sehr verschiedener Grösse ergeben keinen brauchbaren
   Kreis — die Miete nimmt mehr als die Hälfte, sechs Kategorien werden zu
   Haaren. Als sortierter Balken wiederholte er weitgehend die
   Subtotal-Zeilen, die ohnehin in den Tabellen stehen.

**Der Rückweg, falls der Benutzer die Kategorien doch will:** eine Kernfunktion
`gruppenSummen(schema, values)` → `{ [groupId]: { jaehrlich, monatlich } }`, die
`recomputeAll` (Zeile 4321) gleich mitbenutzt statt ihre eigene Rechnung zu
führen, und **ein** gestapelter Balken, nicht elf einzelne. Kein Kreisdiagramm.

**Entschieden ist damit auch die Teilfrage «nur die Gesamtzahl oder auch die
einzelnen Kategorien»: Gesamtzahl und einzelne Positionen, keine Kategorien.**
Die Position ist die Einheit, in der der Benutzer die Anpassung erfasst hat; die
Kategorie ist eine Zwischenstufe, die in seiner Frage nicht vorkommt.

---

## Diagramm 1 — «Was die Anpassungen über die Zeit ausmachen»

**Ort:** eine neue `<section class="section grafik-section" id="grafikSection">`
**direkt nach** der Zusammenfassung (nach Zeile 2418), vor
`#versionsOverviewSection`. Nicht in die Zusammenfassung hinein: die
Summentabelle hat ihre eigenen Druckregeln, und ein eigener Abschnitt lässt sich
als Ganzes ein- und ausblenden.

**Sichtbar, sobald es mindestens eine Anpassung gibt** — dasselbe Tor, an dem
heute `#adjustmentsBtn` und `#previewBtn` hängen (`renderAdjustmentList`,
Zeile 4187, `anzahl === 0`). Auf einer frisch geöffneten Seite steht kein leeres
Diagramm.

**Je Stand ein Balken**, in der Reihenfolge von `stichtagListe`: «heute», die
Daten aufsteigend, «mit allen Vorschlägen». Der Wert ist die **Differenz pro
Monat** — das ist die Zahl, über die in der Beratung gesprochen wird; der
Jahreswert steht im `title` des Balkens und in der Tabelle darüber.

```
heute                   ███████▌|                      − 120.00
ab 01.01.2027                  █|██                    +  29.00
ab 01.04.2027                  █|████                   +  43.00
mit allen Vorschlägen          █|██████████             + 113.00
                                ↑ Nulllinie
```

- **Farbe:** `--color-success` ab null, `--color-danger` darunter — dieselbe
  Zuordnung wie `.stand-row.positive` / `.negative` (Zeilen 907 und 913). Eine
  zweite Farblogik auf demselben Blatt wäre eine Falle.
- **Der Stand «heute» steht mit dabei**, nicht nur als Bezugspunkt. Ohne ihn
  fehlt der Vergleich, und er ist der einzige Balken, der eine erfasste und
  keine gerechnete Zahl zeigt.
- **Der gerade angezeigte Stand ist markiert**, wenn die Vorschau offen ist —
  dieselbe Klasse `is-preview` wie bei der Stand-Zeile (Zeile 901).
- **Ein Klick auf einen Balken öffnet die Vorschau zu diesem Stand.** Damit
  bekommt der Benutzer, was er mit den Stand-Knöpfen in der Übersicht gemeint
  hatte, ohne dass die Vorschau selbst verschwindet (siehe «Die Vorschau
  bleibt»). Der Balken ist dafür ein `<button>`, keine Zeile mit Click-Handler.

**Keine Treppe mit Verbindungsstücken.** Ein Wasserfall zeigt dasselbe, braucht
aber SVG und erklärt sich schlechter: die Balken an einer gemeinsamen Nulllinie
sagen unmittelbar «hier bin ich im Minus, dort im Plus», was in einem Budget die
eine Frage ist.

---

## Diagramm 2 — «Woher die Veränderung kommt»

Im gleichen Abschnitt unter Diagramm 1: je angepasste Position ein Balken mit
dem Unterschied pro Monat, nach Betrag absteigend.

```
Handyabo                   |████████████   − 45.00 / Monat
Hausrat­versicherung        |███████        − 28.00 / Monat
Lohn Person 2              |█████          + 20.00 / Monat
Vereinsbeitrag          ███|               +  8.00 / Monat
```

- **Vorzeichen und Farbe kommen aus `anpassungWirkung`** (Zeile 2790): bei einer
  Ausgabe ist weniger gut, bei einer Einnahme mehr. Die Klassen `ist-gut` und
  `ist-schlecht` gibt es bereits für die vierte Spalte der Anpassungszeile
  (gesetzt in `recomputeAll`, Zeile 4313) und werden hier wiederverwendet. **Wer
  hier das Vorzeichen allein nach dem Betrag einfärbt, lässt «+1'200.00» beim
  Lohn in Rot stehen** — genau der Fehler, den die Funktion verhindert.
- **Die Beschriftung ist der Positionsname** aus `rowAnzeigename` (Zeile 4004),
  und ein Klick springt zur Zeile über `springeZuZeile` (Zeile 4035) — wie in
  der Anpassungsliste der Kopfleiste, damit es nur eine Art gibt, von einer
  Anpassung zu ihrer Position zu kommen.
- **Höchstens acht Balken.** Darüber eine neunte Zeile «weitere N Positionen ·
  −12.00 / Monat». Zwanzig Balken wären eine zweite Tabelle, keine Grafik, und
  die Anpassungsliste in der Kopfleiste zeigt ohnehin alle.
- **Die Reihenfolge springt beim Tippen nicht.** `recomputeAll` läuft bei jedem
  Tastendruck; würde die Sortierung mitlaufen, wanderten die Balken unter dem
  Finger weg. Darum: die Breiten werden laufend nachgezogen, **neu sortiert wird
  erst, wenn kein Anpassungsfeld den Fokus hat** (`document.activeElement` ist
  kein `.adj-input`). Die Zeilen tragen dafür `data-row-id` und werden
  wiederverwendet statt neu gebaut.

---

## Punkt 9: der bestehende Abschnitt wird umgebaut

**Keine zweite Ansicht.** Der Knopf öffnet kein Fenster und baut keine zweite
Tabelle; er bringt den Benutzer an den Abschnitt, den es schon gibt, und dieser
Abschnitt lernt die freie Wahl.

### Der Knopf

`#compareBtn` in der Versionsleiste, **direkt rechts der Reiter** (nach
`#versionTabs`, Zeile 2105, vor `#addVersionBtn`, Zeile 2106) — genau dort, wo
der Benutzer ihn genannt hat, und er gehört dorthin, weil er auf die Reiter
wirkt, während «Neue Version» einen neuen anlegt.

- Beschriftung «⇄ Vergleichen», gestrichelte Umrandung wie «Neue Version» und
  «Vorschau»: er ist keine Version.
- **Nur im Mehr-Versionen-Betrieb sichtbar** (`isMultiVersion()`, Zeile 3184,
  geschaltet in `applyModeToUI`, Zeile 4574). Mit einer Version gibt es nichts
  zu vergleichen, und der Zielabschnitt ist dann selbst versteckt — ein Knopf,
  der ins Nichts führt, wäre schlimmer als keiner.
- **Er trägt keine Rolle `tab`.** Die Leiste selbst ist kein `tablist`, nur
  `#versionTabs` ist es (Kommentar bei Zeile 2098) — diese Trennung muss halten,
  sonst wären Knöpfe Kinder einer Reiterliste, ohne Reiter zu sein.
- **Verhalten beim Klick:** zum Abschnitt springen, die Höhe von `.sticky-head`
  abziehen und die Auswahl fokussieren — dasselbe Muster wie `springeZuZeile`
  (Zeile 4035), einschliesslich der kurzen Hervorhebung, damit sichtbar ist, wo
  man gelandet ist.

### Die Auswahl

Unter der Einleitung des Abschnitts (Zeile 2425) eine Zeile:

> **Vergleichen:** [ Version A ▾ ] **mit** [ Version B ▾ ]

Zwei `<select>` mit allen Versionen. **Vorbelegt mit dem, was heute gilt:** A =
die Basis der aktiven Version (`basedOn`), B = die aktive Version. Damit zeigt
der Abschnitt ohne jede Bedienung genau das, was er heute zeigt — niemand
verliert eine Ansicht, und die Wahl ist ein Angebot, keine Pflicht.

- **Hat die aktive Version keine Basis** (Wurzelversion), ist A die erste andere
  Version in der Liste. Heute versteckt sich der Detailblock in diesem Fall
  ganz (Zeile 4736) — mit freier Wahl gibt es immer ein Paar, und die leere
  Aussage heisst künftig «keine Unterschiede» statt «nichts zu sehen». **Das ist
  eine bewusste Änderung am bestehenden Verhalten** und gehört in den
  Prüfdurchgang.
- **A und B gleich** ist erlaubt und ergibt «keine Unterschiede». Keine Sperre:
  eine Auswahl, die sich wehrt, ist mühsamer als ein leeres Ergebnis, das sich
  erklärt.
- **Die Wahl wird nicht gespeichert.** Sie steht nicht in der Datei (v5 bleibt
  unverändert) und überlebt kein Neuladen — sie ist eine Blickrichtung, kein
  Inhalt.
- Umbenennen oder Löschen einer Version baut die beiden Listen neu auf; eine
  gelöschte gewählte Version fällt auf die Vorbelegung zurück.

### Diagramm 3 — die Versionen als Balken

Über der Tabelle, denn das Bild ordnet die Zahlen, die darunter stehen: je
Version ein Balken der Differenz pro Monat, in der Reihenfolge der Reiter, die
beiden gewählten mit einem Abzeichen «A» und «B» und stärkerem Rand.

Das ist die Antwort auf «alle Versionen (auswählbar) vergleichen» im
Wortsinn — alle stehen da, zwei sind gewählt. Zusätzlich kommen die Stand-Zeilen
der aktiven Version als Balken dazu? **Nein** — sie stehen in Diagramm 1 und
in der Tabelle; dreimal dieselbe Zahl ist keine Übersicht.

### Die Differenz

**Paarweise, nicht als Matrix.** Die Differenz ist zwischen zwei Zahlen
definiert; eine Tabelle mit einer Spalte je Version und einer Δ-Spalte je Paar
ist bei vier Versionen unlesbar und auf einem Telefon gar nicht darstellbar. Die
Gesamtzahlen aller Versionen nebeneinander liefert die bestehende Tabelle, das
Bild liefert Diagramm 3 — die *Position für Position*-Differenz braucht ein
Paar.

Dargestellt wird sie, wo sie heute steht: in «Unterschiede pro Position»
(`#versionsDetailBlock`). Geändert wird nur die Herkunft der zwei Seiten —
`renderVersionsDetail` (Zeile 4722) bekommt A und B als Argumente statt
`getBaselineVersion()` und `getActiveVersion()` zu rufen. Die Spaltenköpfe
nehmen schon heute die Namen auf (`#detailColBasis`, `#detailColActive`,
Zeile 4745), die Zeilen zeigen bereits Δ/Jahr und Δ/Monat mit Vorzeichen und
Farbe. **Dort ist fast nichts zu bauen, nur umzuhängen.**

### Was unverändert bleibt

Die Tabelle aller Versionen (Zeile 4659 ff.) samt «Δ vs. Basis» bleibt, wie sie
ist. Die Spalte beschreibt eine Eigenschaft jeder Version (ihr Verhältnis zu
`basedOn`) und nicht das gewählte Paar; sie durch «Δ vs. A» zu ersetzen nähme
eine Angabe weg, die sonst nirgends steht. Die Stand-Zeilen darunter
(Zeile 4694) bleiben ebenfalls.

---

## Neu im Rechenkern

Alle drei Diagramme rechnen **im Kern** und werden damit über
`tests/budget_treiber.mjs` echt geprüft; im DOM bleibt nur das Zusammensetzen
der Zeilen. Der Treiber liest seine Funktionsliste selbst aus dem Quelltext
(Zeile 28 in `tests/budget_treiber.mjs`) — neue Kernfunktionen brauchen dort
keine Änderung.

```js
// 1. Die Stände mit ihren Summen — eine Quelle für drei Anzeigen.
standVerlauf(schema, values, adjustments, heuteIso)
// → [{ key, ab, faellig, einnahmenY, einnahmenM, ausgabenY, ausgabenM,
//      diffY, diffM, deltaY, deltaM }]
//   deltaY/deltaM: gegenüber dem Stand «heute». «heute» selbst hat 0.

// 2. Die Rangliste der Anpassungen, gekappt und aufsummiert.
anpassungsRangliste(adjustments, staende, values, einnahmeRowIds, maxAnzahl)
// → { eintraege: [{ rowId, deltaY, deltaM, wirkung }], restAnzahl, restDeltaM }
//   Sortiert nach |deltaM| absteigend, bei Gleichstand nach rowId, damit das
//   Ergebnis nicht von der Schlüsselreihenfolge des Objekts abhängt.

// 3. Die Geometrie eines Balkensatzes, in Prozent der Spur.
balkenAnteile(werte)
// → { nullBei, balken: [{ von, breite }] }
//   Die Spanne umfasst immer die Null, darum ist nullBei stets definiert.
//   Alle Werte gleich oder alle 0: breite 0, kein Sprung auf 100 %.
```

**`standVerlauf` ersetzt zwei bestehende Schleifen.** Dieselbe Rechnung steht
heute zweimal fast gleich da: in `recomputeAll` für die Stand-Zeilen der
Zusammenfassung (Zeile 4369) und in `renderVersionsOverview` für die
Stand-Zeilen der Übersicht (Zeile 4694). Mit dem Diagramm käme eine dritte dazu.
**Das ist der eigentliche Gewinn dieses Umbaus für den Code** — eine Quelle für
drei Anzeigen, und der Unterschied «in der Vorschau aus den erfassten Werten
rechnen» steckt dann an einer Stelle statt an dreien.

**`anpassungsRangliste` braucht die Einnahmen-Zeilen als Argument**, weil der
Kern `SCHEMA` nicht kennt (Kommentar bei Zeile 2717). Die Liste kommt aus
`SCHEMA.einnahmen.map(r => r.id)` am Aufrufort. Ohne sie wäre `anpassungWirkung`
im Kern nicht aufrufbar, und das Vorzeichen landete wieder im DOM-Code.

**Nicht zur dritten Fassung werden:** `computeTotalsForVersion` (Zeile 3192)
rechnet dasselbe wie `summen` (Zeile 3085) — eine alte Doppelung aus der Zeit
vor dem Kern. Diagramm 3 nimmt **`summen(SCHEMA, v.values)`**, nicht die
DOM-Fassung. Die beiden zusammenzuführen ist ein eigener, kleiner Umbau; dieser
Entwurf vergrössert die Doppelung wenigstens nicht.

---

## Die Vorschau bleibt — Antwort auf D4

Der Benutzer hatte vorgeschlagen, die Stände als Knöpfe in die Übersicht zu
legen und den Vorschau-Knopf nur noch dorthin springen zu lassen. Fiele die
gesperrte Vorschau damit weg, fiele die Schreibsperre in
`captureFormToActiveVersion` (Zeile 3242) mit — die riskanteste Stelle des
ganzen Umbaus.

**Die Übersicht ersetzt die Vorschau nicht.** Die Begründung ist inhaltlich,
nicht ängstlich: Diagramm 1 zeigt je Stand **eine** Zahl, die Differenz pro
Monat. Die Vorschau zeigt **das ganze Budget** zu diesem Stand — rund sechzig
Positionen mit ihren eingelösten Beträgen, die Subtotale, die Gruppensummen. Das
ist die Ansicht, mit der man in einer Beratung Zeile für Zeile durchgeht, und
kein Diagramm trägt sie.

**Was vom Vorschlag übrig bleibt und gebaut wird:** die Balken von Diagramm 1
sind Knöpfe und öffnen die Vorschau zum angeklickten Stand. Der Benutzer bekommt
den Einstieg, den er wollte, an der Stelle, an der er ihn wollte; der
Vorschau-Knopf in der Leiste bleibt als zweiter Weg stehen (er ist der
Tastaturweg, und er funktioniert auch, wenn der Abschnitt weit unten liegt).

**Damit ist D4 entschieden: die Vorschau und ihre Schreibsperre bleiben.** Wer
sie später doch abschaffen will, braucht zuerst einen Ersatz für die
Positionsansicht, nicht für die Stände.

---

## Schmale Breite

Die Frage hat sich bei Punkt 7 gestellt und gilt hier genauso.

- **Bis 768 px** (bestehende Abfrage, Zeile 1173) bleibt die Zeile dreiteilig:
  Beschriftung, Spur, Zahl. Die Beschriftung bekommt `min-width: 0` und
  `overflow-wrap`, damit ein langer Positionsname bricht statt die Spur zu
  quetschen.
- **Unter 480 px** (bestehende Abfrage, Zeile 1070) wird die Zeile zweizeilig:
  Beschriftung und Zahl in einer Zeile, die Spur darunter über die ganze Breite.
  Ein Balken von 40 % einer 120 px breiten Spur sagt nichts mehr; über die volle
  Breite sagt er wieder etwas.
- Die Spur hat eine Mindesthöhe (`14px`) und der Balken eine Mindestbreite
  (`2px`, sobald der Wert nicht 0 ist), damit eine kleine Anpassung nicht
  unsichtbar wird.
- **Die beiden `<select>` der Auswahl brechen untereinander**, mit dem Wort
  «mit» als eigene Zeile. Sie werden nicht zu einem Zeilenumbruch mitten im Satz
  gezwungen.

---

## Drucken

**Die Diagramme drucken mit.** Auf dem Blatt, das in einer Beratung oder bei
einer Stiftung landet, sind sie das Beste, was die Seite zu bieten hat — und das
Gegenmittel gegen den Befund aus Welle 5 («rund 60 leere Kästchen lassen das
Blatt wie ein Formular wirken»).

Dafür nötig:

- `print-color-adjust: exact` auf den Balkenfarben, sonst drucken sie weiss
  (dasselbe Mittel wie bei `.total-display`, Zeile 1306).
- **Jeder Balken bekommt einen 1px-Rahmen** in der dunkleren Variante seiner
  Farbe. Auf einem Schwarzweissdrucker bleibt damit die Länge lesbar, auch wenn
  grün und rot zum selben Grau werden. Das Vorzeichen steht ohnehin als Text
  daneben.
- `page-break-inside: avoid` je `<figure>`, wie bei `.versions-overview-section`
  (Zeile 1309). Ein halber Balkensatz über dem Seitenumbruch ist schlimmer als
  eine halbleere Seite.
- **Die beiden `<select>` drucken nicht.** Sie wären zwei leere Kästchen — genau
  der Eindruck, den Punkt 11 bemängelt. Statt dessen druckt eine Textzeile
  «Vergleich: ‹A› gegen ‹B›», befüllt im bestehenden `beforeprint`-Handler
  (Zeile 5439), nach dem Muster der Druckfassung des Kommentars (Zeile 3546)
  und der privaten Notiz.
- **Ungeprüft auf Papier.** Auf diesem Rechner gibt es keine Druckvorschau; der
  erste echte Ausdruck gehört in Welle 5, zusammen mit den anderen offenen
  Papierfragen.

---

## Barrierefreiheit und Bewegung

- Jedes Diagramm ist eine `<figure>` mit `<figcaption>` als Titel.
- **Die Zahl ist Text, der Balken ist Dekoration.** Die Spur trägt
  `aria-hidden="true"`; was ein Screenreader liest, ist «Handyabo, −45.00 pro
  Monat». Deshalb braucht es kein `role="img"` mit einer künstlich
  zusammengesetzten Beschreibung — und deshalb ist CSS hier dem SVG auch in
  dieser Hinsicht voraus.
- **Keine Übergänge auf der Balkenbreite.** `recomputeAll` läuft bei jedem
  Tastendruck; eine `transition` auf `width` liesse die Balken dauernd kriechen.
  Das ist nicht nur eine Frage von `prefers-reduced-motion` (Abfrage bei
  Zeile 2032), sondern bei dieser Aufruffrequenz schlicht falsch.
- Die Balken-Knöpfe von Diagramm 1 sind echte `<button>` und damit
  tastaturerreichbar; die Reihenfolge entspricht der Stichtagsreihenfolge.

---

## Fallen, die der Einbau treffen wird

1. **In der Vorschau stehen gerechnete Werte im Formular.** `recomputeAll`
   nimmt darum `basisWerte = (state.previewStand && active) ? active.values :
   formWerte` (Zeile 4367). **Die Diagramme müssen dieselbe Quelle benutzen.**
   Wer vom Formular weiterrechnet, zeigt in der Vorschau überall ein Delta von 0
   und den Zielbetrag als Istwert — der Fehler sieht aus wie «es gibt keine
   Anpassungen mehr».
2. **Versionsnamen sind Benutzereingaben.** In den Diagrammbeschriftungen und
   in den `<option>` der Auswahl gehört `escapeHtml` (Zeile 5099) davor, so wie
   es die Übersichtstabelle schon tut (Zeile 4673).
3. **`renderVersionsOverview` ruft `captureFormToActiveVersion`** (Zeile 4655),
   damit die aktive Zeile die laufenden Eingaben zeigt. Diagramm 3 hängt am
   selben Aufruf und braucht keinen zweiten; ein zusätzlicher wäre harmlos, aber
   die Schreibsperre ist zu wichtig, um sie an mehr Stellen zu streifen als
   nötig.
4. **Der Detailblock ändert sein Leerverhalten** (siehe «Die Auswahl»): aus
   «versteckt, weil Wurzelversion» wird «sichtbar mit der Aussage ‹keine
   Unterschiede›». Die Tests, die das heutige Verstecken festnageln, müssen
   mitgezogen werden.
5. **`springeZuZeile` rechnet mit der Höhe von `.sticky-head`** (Zeile 4040).
   Der neue Knopf macht die Leiste nicht höher, solange er in dieselbe Zeile
   passt; wird die Leiste auf schmalen Schirmen zweizeilig, stimmt der Abstand
   weiterhin, weil `offsetHeight` gemessen und nicht angenommen wird. Kommt
   Punkt 7 (mitlaufende Anleitung) dazu, ist dies die Stelle, die beide Umbauten
   gemeinsam betreffen.
6. **Zwei Sessions, eine Datei.** Punkt 7 wird parallel entworfen und fasst
   dieselbe `.sticky-head` und dieselben Druckregeln an. Eingebaut wird seriell,
   eine Welle nach der anderen.

---

## Ausdrücklich nicht Teil davon

- **Kein Kategorien- oder Kreisdiagramm** (Begründung oben, mit Rückweg).
- **Keine Zeitachse mit Monatsraster.** Die Stände sind Sprünge, keine
  kontinuierliche Entwicklung; eine Linie dazwischen behauptete eine anteilige
  Jahresrechnung, die der Entwurf vom 2026-10-21 bewusst nicht macht.
- **Kein Export des Diagramms** als Bild. Wer es weitergeben will, druckt die
  Seite oder gibt die Datei weiter.
- **Keine gespeicherte Auswahl** im Dateiformat. v5 bleibt unverändert.
- **Punkt 10** (die vierte Spalte «Total / Jahr») bleibt ein eigener Umbau.
- **Keine Zusammenführung von `computeTotalsForVersion` und `summen`** — nur die
  Feststellung, dass die neue Rechnung `summen` nimmt.

---

## Die Stellen in `docs/budgetvorlage.html`

Zeilennummern vom Stand dieses Entwurfs (5554 Zeilen, Branch
`budget-anpassungen-stichtag`).

### Markup

| Zeile | was |
|---|---|
| 2105 / 2106 | `#versionTabs` endet, `#addVersionBtn` beginnt — **dazwischen** kommt `#compareBtn` |
| 2388–2418 | Zusammenfassung mit `#differenceRow` (2409) und `#summaryStands` (2416) — bleibt unverändert |
| nach 2418 | **neu:** `<section id="grafikSection" hidden>` mit Diagramm 1 und Diagramm 2 |
| 2423 | `#versionsOverviewSection` beginnt |
| 2425–2428 | Einleitung des Abschnitts — **darunter** die Auswahl A/B und Diagramm 3 |
| 2429–2444 | Tabelle aller Versionen — unverändert |
| 2446–2464 | `#versionsDetailBlock` — Spaltenköpfe 2453/2454 nehmen schon Namen auf |

### CSS

| Zeile | was |
|---|---|
| 885–918 | `.summary-table .stand-row …` — Farblogik und `is-preview`, die die Diagramme übernehmen |
| 1070 | `@media (max-width: 480px)` — zweizeilige Diagrammzeile |
| 1173 | `@media (max-width: 768px)` — Beschriftungsbreite |
| 1207 | `@media print` beginnt |
| 1306–1308 | `print-color-adjust: exact` als Vorlage |
| 1309 | `.versions-overview-section { page-break-inside: avoid }` — Vorlage fürs `<figure>` |
| 1632–1720 | Block des Versionsvergleichs — **hierher** die neuen Regeln für Balken, Spur, Auswahl |
| 2032 | `@media (prefers-reduced-motion: reduce)` |

### Rechenkern

| Zeile | was |
|---|---|
| 2727 | `/* == budget-kern:anfang == */` |
| 2790 | `anpassungWirkung` — die Vorzeichenregel für Diagramm 2 |
| 2946 | `stichtagListe` |
| 2994 | `werteFuerStand` |
| 3028 | `anpassungsGruppen` — Grundlage von `anpassungsRangliste` |
| 3085 | `summen` — Grundlage von `standVerlauf` und Diagramm 3 |
| vor 3106 | **neu:** `standVerlauf`, `anpassungsRangliste`, `balkenAnteile` |
| 3106 | `/* == budget-kern:ende == */` |

### JavaScript

| Zeile | was |
|---|---|
| 3184 | `isMultiVersion` — Tor für `#compareBtn` |
| 3192 | `computeTotalsForVersion` — **nicht** benutzen, siehe Doppelung |
| 3242 | die Schreibsperre in `captureFormToActiveVersion` — bleibt |
| 4004 | `rowAnzeigename` — Beschriftung in Diagramm 2 |
| 4012 | `deltaAnzeige` — Vorzeichen und Rundung, überall wiederverwenden |
| 4035 | `springeZuZeile` — Muster für den Sprung des Knopfes, und Ziel aus Diagramm 2 |
| 4187 | `renderAdjustmentList` — hier fällt die Entscheidung «es gibt Anpassungen»; dasselbe Tor für `#grafikSection` |
| 4280 | `recomputeAll` |
| 4360–4377 | die Stand-Zeilen der Zusammenfassung — gehen auf `standVerlauf` über |
| 4367 | `basisWerte` — die Vorschau-Falle |
| 4574 | `applyModeToUI` — Sichtbarkeit von `#compareBtn` |
| 4644 | `renderVersionsOverview` — Diagramm 3 und die Auswahl |
| 4694–4716 | die Stand-Zeilen der Übersicht — gehen ebenfalls auf `standVerlauf` über |
| 4722 | `renderVersionsDetail` — bekommt A und B als Argumente |
| 5099 | `escapeHtml` |
| 5439 | `beforeprint` — die Druckzeile der Auswahl |
| 5453 ff. | die Stelle, an der die Knöpfe der Versionsleiste verdrahtet werden |

---

## Tests

**Im Kern, echt geprüft** (`tests/test_budget.py`, Aufruf über `kern(...)`,
Zeile 42):

- `standVerlauf`: Reihenfolge, «heute» mit Delta 0, ein Stand je Datum, das
  verstrichene Datum als eigener Stand, keine Stände ohne Anpassung.
- `standVerlauf` gegen `summen(werteFuerStand(...))`: **dieselben Zahlen wie
  die Stand-Zeilen heute** — das ist der Test, der den Umbau der zwei Schleifen
  absichert.
- `anpassungsRangliste`: Sortierung, Kappung bei `maxAnzahl`, die Restsumme
  stimmt mit der Summe der weggelassenen Einträge, `wirkung` bei einer Einnahme
  umgekehrt wie bei einer Ausgabe.
- `balkenAnteile`: nur positive Werte, nur negative, gemischt, alle gleich, alle
  0, ein einziger Wert. `nullBei` liegt bei rein positiven Werten auf 0 und bei
  rein negativen auf 100.

**Als Textsuche** (schwächer, aber die einzige Möglichkeit für die DOM-Seite,
solange es kein jsdom-Gerüst gibt):

- `#compareBtn` steht zwischen `#versionTabs` und `#addVersionBtn`.
- `#grafikSection` steht zwischen Zusammenfassung und `#versionsOverviewSection`.
- Es gibt **keine** zweite Vergleichstabelle: `versions-detail-table` kommt
  genau einmal vor.
- `.balken-spur` trägt `aria-hidden`.
- Die Diagramme haben keine `transition` auf `width`.
- `@media print` blendet die `<select>` aus und lässt die Balken drucken.
- Die Diagramme nehmen `summen`, nicht `computeTotalsForVersion`.

**Umzuziehen:** die Tests, die das heutige Verstecken des Detailblocks bei einer
Wurzelversion festnageln.

---

## Dem Umsetzenden überlassen

- Die genauen Farben und Abstände der Balken, solange die Zuordnung
  grün = positiv / rot = negativ und `ist-gut` / `ist-schlecht` eingehalten wird.
- Ob die Beschriftung in Diagramm 2 links oder über dem Balken steht, solange
  die Regel «unter 480 px die Spur über die ganze Breite» gilt.
- Ob die acht Balken von Diagramm 2 eine Konstante oder eine Zahl im Aufruf
  sind.
- **Wenn das Wiederverwenden der Zeilen für die stabile Sortierung zu teuer
  wird:** statt nach Betrag nach der Reihenfolge in `SCHEMA` sortieren. Dann
  springt nichts, und das Diagramm liest sich wie das Formular — der grösste
  Balken fällt auch ohne Sortierung auf.
