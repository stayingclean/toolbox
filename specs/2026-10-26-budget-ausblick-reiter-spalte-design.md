# Ausblick als Treppe, Anpassungen am Reiter, Spalte «Total / Jahr» weg

**Datum:** 2026-10-26
**Betrifft:** `docs/budgetvorlage.html` (eigenständige Seite, kein Generat)
**Dateiformat:** v5 bleibt — es kommt kein Feld dazu, keines fällt weg
**Deckt ab:** Diagramm A aus dem Gespräch vom 2026-10-26, die Hervorhebung von
Versionen mit Anpassungen, Punkt 10 aus `plans/2026-10-22-budget-offene-arbeiten.md`
**Mitlesen:** `specs/2026-10-21-budget-anpassungen-design.md` (verbindlich für
Stände und Stichtage), `specs/2026-10-23-budget-grafik-und-vergleich-design.md`
(Diagrammsprache, Auswertung)

Drei Teile, die nichts voneinander brauchen, aber dieselbe Datei ändern. Sie
werden darum nacheinander gebaut, jeder für sich fertig und grün (siehe
«Reihenfolge» am Ende).

---

## 1. Ausblick: was am Monatsende bleibt, als Treppe auf der Zeitachse

### Wozu

Die Zusammenfassung zeigt heute für jeden Stichtag eine Zeile, die Auswertung
dieselben Stände als liegende Balken («Stand für Stand»). Beides beantwortet
«wie viel bleibt in welchem Stand», keines «wann und wie lange». Wer eine
Version mit mehreren datierten Anpassungen vor sich hat, soll am Ende der
Version auf einen Blick sehen, wie sich der Monatsüberschuss über die Zeit
entwickelt — wann er sinkt, wie lange eine Delle dauert, wo er danach steht.

### Entscheide des Benutzers (2026-10-26)

- **Form: Treppe (Diagramm A).** Gewählt aus vier Skizzen (Treppe,
  Monatssäulen, Wasserfall, Zeitstrahl).
- **Verstrichene Daten erscheinen links von «heute».** Die Achse beginnt beim
  frühesten Datum, der Teil vor heute ist grau, ab der Heute-Linie folgt der
  Ausblick. Der Anfang der Linie sind die **erfassten Werte** — genau wie der
  Stand «heute» in der Zusammenfassung. Es wird nichts stillschweigend
  eingerechnet.
- **Ort: am Ende der Version**, unter den Stand-Zeilen der Zusammenfassung —
  **im selben Abschnitt** (`.summary-section`), nicht als eigener. Grund ist
  der Druck (nächster Punkt): im Ausdruck beginnt jeder `.section` auf einem
  neuen Blatt (`page-break-before: always`).
- **Auf Papier bildet die Treppe mit der Zusammenfassung einen Block**
  (Entscheid nach der Prüfung, 2026-10-26). Kein zusätzliches Blatt; passen
  beide nicht mehr auf die Seite, beginnen sie gemeinsam auf einer neuen
  (`.summary-section` hat schon `page-break-inside: avoid`).
- **Druck: ein eigenes Häkchen «Ausblick drucken»** in der Werkzeugleiste,
  neben «Kommentare drucken» und «Private Notiz drucken». **Nicht
  vorgewählt.**
- **«Stand für Stand» in der Auswertung bleibt**, unverändert. Die Treppe
  ersetzt es nicht.

### Verhältnis zu einem früheren Entscheid

`specs/2026-10-23-budget-grafik-und-vergleich-design.md` schliesst unter den
Nicht-Zielen aus: «Keine Zeitachse mit Monatsraster. Die Stände sind Sprünge,
keine kontinuierliche Entwicklung; eine Linie dazwischen behauptete eine
anteilige Jahresrechnung.» Die Zeitachse ist mit diesem Entscheid des Benutzers
überholt. **Der Grund dahinter gilt weiter und bindet die Treppe:** sie springt
an jedem Stichtag senkrecht, es gibt **keine schräge Linie** zwischen zwei
Ständen und keine Zwischenwerte. Im alten Entwurf ist dazu ein Nachtrag mit
Verweis hierher einzufügen.

### Was gezeichnet wird

Eine Linie, ein Wert: **«bleibt pro Monat»** (`diffM`), dieselbe Zahl wie in
den Stand-Zeilen der Zusammenfassung. Keine Linien für Einnahmen oder
Ausgaben.

Die Daten liefert `standVerlauf` (bestehend, im Rechenkern): «heute» (=
erfasste Werte), je Datum ein Stand mit allen Anpassungen bis einschliesslich
diesem Tag, am Schluss «offen» (alle Anpassungen, auch die ohne Datum). Neu zu
rechnen ist nichts, neu ist nur die Lage auf der Zeitachse.

- **Waagrecht:** die Zeit. Die Linie hat bis zum ersten Datum den Wert «heute»
  (erfasst), springt an jedem Datum auf den Wert dieses Stands und läuft nach
  dem letzten Datum bis zum rechten Ende der **Zeitskala** weiter.
- **Heute-Linie:** senkrecht, gestrichelt, beschriftet «heute». Was links davon
  liegt, ist gedämpft (grau); rechts davon in der Linienfarbe. Liegt kein Datum
  in der Vergangenheit, steht die Heute-Linie am linken Rand.
- **Ein Datum, das heute ist, gilt als eingetreten** — wie in `stichtagListe`
  (`faellig = d <= heuteIso`). Sein Punkt liegt auf der Heute-Linie und zählt
  zum grauen Teil. (Mein Entscheid nach der Prüfung: eine Regel für Treppe,
  Reiter und Stand-Zeilen.)
- **Stufen:** an jedem Datum ein Punkt. Grün, wenn der Überschuss dort steigt,
  rot, wenn er sinkt (dieselbe Lesart wie `.adj-delta.ist-gut`/`ist-schlecht`).
  Daneben die Veränderung pro Monat (`+18`, `−42`) und, wenn an diesem Datum
  genau eine Position wirkt, ihr Name; bei mehreren «2 Positionen». Die ganze
  Liste steht im `title` des Punkts.
- **Zahlen an der Linie:** der Anfangswert links und der Endwert rechts.
  Dazwischen nur die Veränderungen, keine absoluten Werte (die stehen in den
  Stand-Zeilen direkt darüber).
- **Anpassungen ohne Datum (Vorschläge):** gibt es welche, steht rechts
  **neben** der Zeitskala ein eigener, schmaler Streifen — durch eine Lücke
  abgesetzt, ohne Monatsbeschriftung, unten beschriftet «ohne Datum». Darin ein
  gestricheltes, graues Stück auf der Höhe von «offen», beschriftet «mit
  Vorschlägen» und dem Wert. Vorschläge haben keinen Zeitpunkt; stünden sie
  auf der Zeitskala, behauptete die Grafik einen. Ohne Vorschläge fehlt der
  Streifen. (Mein Entscheid nach der Prüfung.)
- **Klickziele:** jeder Stufenpunkt (Vorschau dieses Datums), das
  gestrichelte Stück (Vorschau «offen») und der Anfangswert links (Vorschau
  «heute»). Hervorgehoben wird in der Vorschau das Ziel des gezeigten Stands.
- **Null:** die senkrechte Achse schliesst **immer 0** ein, die Nulllinie ist
  kräftiger als die übrigen Rasterlinien. Ein Fehlbetrag ist so sofort als
  solcher zu sehen. (Anders als «Der Weg» in der Auswertung, der einen
  Ausschnitt zeigt — dort geht es um den Abstand zweier Linien, hier um
  Überschuss oder Fehlbetrag.)
- **Ein Klick auf ein Klickziel** (siehe oben) öffnet die Vorschau dieses
  Stands (`enterPreview`), wie ein Klick auf einen Balken in «Stand für
  Stand». Die Ziele sind mit der Tastatur erreichbar.

### Wann sie erscheint

- Genau dann, wenn die aktive Version **mindestens eine Anpassung mit Betrag**
  hat — dasselbe Tor wie `#adjustmentsBtn`, `#previewBtn` und `renderGrafik`.
- Gibt es nur Vorschläge ohne Datum, steht eine flache Linie ab heute und
  rechts das gestrichelte Stück. Die Achse reicht dann von heute ein halbes
  Jahr weit.
- In der Auswertung ist sie unsichtbar wie alle Abschnitte des Formulars.
- Sie folgt der aktiven Version und jeder Änderung an Beträgen oder
  Anpassungen (Aufruf aus `recomputeAll`, wie `renderGrafik`).

### Druck

- Neues Häkchen `#chkPrintAusblick`, Beschriftung «Ausblick drucken», **nicht
  gesetzt** beim Laden. Es setzt eine Klasse auf `body` (`print-ausblick`), wie
  die beiden bestehenden Häkchen. Es wird nirgends gespeichert.
- Ohne Häkchen erscheint die Treppe nicht auf dem Blatt; mit Häkchen steht
  sie unter den Stand-Zeilen, im selben Block wie die Zusammenfassung (siehe
  «Entscheide»), mit den Farben (`print-color-adjust: exact`).
- Ist das Häkchen gesetzt, die Version aber ohne Anpassung, druckt nichts —
  die Treppe ist dann ohnehin verborgen.

### Nicht-Ziele

- Keine Monatssäulen, keine Summe «bis dann zusammen» (Diagramm B).
- Keine schrägen Linien, keine anteilige Rechnung innerhalb eines Monats.
- Keine Linien für Einnahmen und Ausgaben.
- Kein Export als Bild.
- Keine Bibliothek: handgeschriebenes SVG wie «Der Weg».

### Dem Bauenden überlassen

- **Zeitspanne der Achse.** Vorgabe: von einem Monatsanfang vor dem frühesten
  Punkt (frühestes Datum oder heute) bis deutlich hinter das letzte Datum,
  sodass der letzte Stand sichtbar «läuft»; mindestens ein halbes Jahr.
- **Beschriftung der Zeitachse.** Monatsnamen, solange es lesbar bleibt, bei
  langen Spannen Quartale oder Jahre; der Jahreswechsel muss erkennbar sein.
- **Rasterlinien der senkrechten Achse.** Vorhandene Hilfen im Kern
  (`achsenBereich`, der Linienabstand) dürfen benutzt oder erweitert werden,
  solange 0 eingeschlossen ist.
- **Überlappende Beschriftungen** (zwei Daten dicht beieinander): auflösen,
  ohne Information zu verlieren — der `title` am Punkt trägt sie immer.
- **Neuzeichnen bei Breitenänderung** wie bei «Der Weg» (ResizeObserver).
- **Farben** aus den Variablen der Seite (`--color-*`). Die Budgetvorlage
  steht seit Commit `57de428` in `MIGRIERT` von `tests/test_tokens.py` (ihre
  `--color-*` hängen als Aliase an `tokens.css`); der Test meldet neue
  Hex-Werte dort **nicht** — sie wegzulassen, ist Sorgfalt des Bauenden.
- **Wie viel davon im Rechenkern liegt.** Bedingung: die Geometrie (Lage der
  Punkte auf der Zeitachse, Achsenbereich, Ticks) ist reine Rechnung zwischen
  den Kern-Markern und in `tests/test_budget.py` geprüft. Gezeichnet wird
  ausserhalb.

---

## 2. Versionen mit Anpassungen: die Zahl am Reiter

### Entscheid des Benutzers (2026-10-26)

Eine kleine Marke mit der **Anzahl der Anpassungen** im Versionsreiter, gewählt
aus «Zahl», «Punkt», «gestrichelter Rand».

### Verhalten

- **Gezählt** wird wie beim Knopf `#adjustmentsBtn`: Anpassungen mit Betrag in
  Zeilen, die die Seite kennt. Mit und ohne Datum, verstrichen oder nicht.
  Muss der Knopf und die Marke einmal auseinanderlaufen, ist das ein Fehler —
  beide holen die Zahl aus derselben Funktion.
- **Ohne Anpassung keine Marke.** Kein «0».
- **Für jede Version**, nicht nur die aktive.
- **Tooltip am Reiter** ergänzt: «3 Anpassungen, nächste ab 01.12.2026».
  «Nächste» ist das früheste Datum **nach** heute (ein Datum, das heute ist,
  gilt als eingetreten, siehe Teil 1). Gibt es keines: «alle Daten
  verstrichen», wenn datierte da sind. Gibt es Vorschläge ohne Datum, kommt
  «, 1 ohne Datum» dazu. Beispiele: «3 Anpassungen, nächste ab 01.12.2026,
  1 ohne Datum» · «2 Anpassungen, alle Daten verstrichen» · «1 Anpassung,
  ohne Datum». (Mein Entscheid nach der Prüfung.)
- **Barrierefrei:** die Zahl selbst ist für Screenreader verborgen, der Name
  des Reiters lautet stattdessen «Ab Januar, 3 Anpassungen».
- **Lebt mit:** trägt jemand in der aktiven Version eine Anpassung ein oder
  löscht sie, ändert sich die Zahl sofort. Dafür werden die Reiter **nicht**
  neu aufgebaut (das würfe Fokus und Klick-Handler weg), sondern nur die Marke
  nachgeführt.
- Die Versionsleiste druckt nicht; die Marke also auch nicht.

### Dem Bauenden überlassen

Aussehen der Marke im Rahmen des bestehenden Reiterstils (kleine runde Marke
in der Akzentfarbe der Seite). Die Zählfunktion gehört in den Rechenkern und
wird geprüft.

---

## 3. Punkt 10: Die Spalte «Total / Jahr» fällt weg

### Befund

`plans/2026-10-22-budget-offene-arbeiten.md`, Punkt 10, und die Herleitung in
`plans/2026-10-22-budget-abarbeitungsplan.md` unter D2: «Jährlich» und
«Monatlich» füllen sich gegenseitig, `rowTotal = y || (m * 12)` ist in jeder
Positionszeile dieselbe Zahl wie das Jahresfeld. **Nachgeprüft am 2026-10-26:
dasselbe gilt für die Zwischensummen** (`[data-period="total"]` bekommt
`yearly`) **und für «Total Fixkosten»** (`fixkostenY`). Echte Arbeit leistet die
Spalte nur in der Anpassungszeile, wo sie den Unterschied zeigt. Auf dem Blatt
bricht ihr Kopf «TOTAL / JAHR» zudem auf zwei Zeilen.

### Entscheid des Benutzers (2026-10-26)

**Die Spalte wird ganz gestrichen**, in der Erfassung wie im Druck.

**Und «Monatlich» und «Jährlich» tauschen die Plätze** (Benutzer, 2026-10-26,
nach Durchsicht der Pläne): die Budget-Tabellen haben danach drei Spalten in
der Folge **Position, Monatlich, Jährlich**. Grund: zusammengezählt werden die
Jahresbeträge, und die Summe gehört in die rechte Spalte, wo vorher «Total /
Jahr» stand — so steht die Zwischensumme wieder dort, wo man sie liest.

Der Tausch gilt überall, wo das Paar als Spalten steht: Kopfzeilen,
Positionszeilen, Anpassungszeilen, Zwischensummen, «Total Fixkosten» und —
**mein Entscheid**, damit die Seite eine Leserichtung hat — auch die
Zusammenfassung samt Stand-Zeilen. **Nicht** betroffen sind die Tabellen der
Auswertung (Wärmekarte, Vergleich): sie zeigen Monatsbeträge und
Unterschiede, keine Paare. Die Tastaturfolge folgt der Anzeige (erst
monatlich, dann jährlich); das gegenseitige Füllen der beiden Felder hängt am
`data-period`, nicht an der Lage, und bleibt.

### Was daraus folgt

- **Kopfzeilen:** jedes `<th>Total / Jahr</th>` fällt weg.
- **Positionszeilen, Zwischensummen, «Total Fixkosten»:** die vierte Zelle
  fällt weg, ebenso die Stellen in `recomputeAll`, die sie füllen.
  `rowTotal` selbst bleibt, solange etwas damit rechnet (der Unterschied der
  Anpassungszeile).
- **Die Zwischensumme verliert ihre hervorgehobene Zahl.** Bisher trug die
  vierte Zelle die kräftige Marke (`.subtotal-row .total-display`, weisse
  Schrift auf Akzentfarbe). Die Zeile bleibt durch Hintergrund und Linie
  darüber erkennbar; ob die Jahreszahl die Marke übernimmt, entscheidet der
  Bauende am Bildschirm — **mein Vorschlag: nein**, beide Zahlen gleich fett,
  damit «Jährlich» und «Monatlich» gleich gewichtet bleiben.
- **Anpassungszeile:** der Unterschied (`.adj-delta`, grün/rot) wandert in die
  erste Zelle, hinter das Datum, in Klammern. Er bleibt der **Jahresbetrag**
  (`anpassungUnterschied`, wie bisher und wie in der gewählten Vorschau
  «+600.00» bei 18'000 → 18'600), trägt aber jetzt selbst die Einheit, weil
  kein Spaltenkopf mehr «/ Jahr» sagt: «ab 01.01.2027 (+600.00 / Jahr)».
  (Mein Entscheid nach der Prüfung — ohne Einheit stünde die Zahl neben der
  Spalte «Monatlich» und läse sich als Monatsbetrag.) Die Zeile hat danach
  ebenfalls drei Zellen.
- **Kommentarzeile:** `colSpan = 4` wird 3.
- **Breiten:** die frei werdende Breite geht an die Positionsspalte und die
  Betragsspalten, auch in der schmalen Ansicht (`max-width`-Block mit
  `label-cell: 40 %`). Ob dabei der bekannte seitliche Überlauf auf 375 px
  verschwindet, wird nachgemessen und im Abschlussbericht erwähnt, ist aber
  nicht Ziel.
- **Texte, die von «rechts» oder vom Total sprechen**, werden nachgezogen: der
  `title` der Anpassungsfelder («Rechts steht der Unterschied»), der
  Hilfetext («rechts der Unterschied zum erfassten Wert») und jeder weitere
  Treffer bei der Suche nach «Total / Jahr», «rechts» und «vierte Spalte».
- **Zusammenfassung:** hat schon nur zwei Zahlenspalten, bleibt unverändert.
- **Dateiformat:** die Spalte war gerechnet, nichts davon steht in der Datei.

### Nicht-Ziele

- Die Spalte wird nicht anders belegt (kein Anteil in Prozent, keine
  Veränderung zur Basis).
- Punkt 11 (Rahmen der Betragsfelder im Druck) bleibt ein eigener Punkt.

---

## 4. Alte Dateien laden weiter, und alles funktioniert danach

### Auftrag des Benutzers (2026-10-26)

«Es muss sichergestellt werden, dass nach dem Umbau alles funktioniert und
JSON von einer älteren Version noch eingelesen werden können.»

### Was das heisst

- Das Dateiformat bleibt v5, `SUPPORTED_VERSIONS` bleibt `{1, 2, 3, 4, 5}`.
  Keine der drei Wellen ändert `serialize`, `hydrate`, `isValidPayload` oder
  die Migration der Formate v1–v3 (`classifyLegacyKey`, `splitLegacyValues`,
  `buildLegacyVersions`).
- **Das wird nicht nur behauptet, sondern geprüft — am echten Ladeweg der
  Seite.** Diese Funktionen liegen in der IIFE der Seite und nicht im
  Rechenkern; der Node-Treiber erreicht sie nicht, ein jsdom-Gerüst ist ein
  eigenes Vorhaben (`plans/2026-10-22-budget-offene-arbeiten.md`,
  «Testlücke mit System»). Darum eine **Ladeprüfung im Browser**:
  - Je eine Beispieldatei pro Format v1, v2, v3, v4, v5 unter
    `tests/fixtures/budget/` — fiktive Zahlen, keine echten Daten. v2 und v3
    mit Reduktionen (werden zu «Original» + «Nach Reduktion»), v4 mit zwei
    Versionen und `basedOn`, v5 mit Anpassungen (datiert, verstrichen, ohne
    Datum, eine nur aus Datum ohne Betrag, eine in einer unbekannten Zeile),
    Kommentaren und privater Notiz.
  - Ein Prüfskript, das in der Seite läuft: es ersetzt
    `window.showOpenFilePicker`/`showSaveFilePicker` durch Attrappen, öffnet
    jede Beispieldatei über den Knopf «Öffnen» (also über `isValidPayload`
    und `hydrate`), liest für jede Version die angezeigten Summen der
    Zusammenfassung und speichert über «Speichern» in die Attrappe. Ergebnis:
    je Datei die Versionen mit ihren Summen und der gespeicherte Datenteil
    (ohne Zeitstempel und zufällige IDs).
  - **Vorher/Nachher:** das Ergebnis wird **vor Welle 1** am unveränderten
    Stand als Sollwert festgehalten (`tests/fixtures/budget/erwartet.json`)
    und **nach jeder Welle** wiederholt. Es muss gleich bleiben — keine der
    drei Wellen ändert eine Zahl oder ein gespeichertes Feld.
- Python-Tests halten fest, dass die Beispieldateien vorhanden und gültig
  sind, dass Format und unterstützte Versionen unverändert bleiben und dass
  der Sollwert zu jeder Beispieldatei einen Eintrag hat.
- **«Alles funktioniert»** heisst darüber hinaus: die ganze Testsuite grün
  (`pytest tests`), und nach jeder Welle die Browserprüfung aus deren Plan
  mit Screenshots, Konsole ohne Fehler.

---

## Reihenfolge und Schnitt

Vier Wellen, nacheinander, jede für sich grün und committed — sie ändern
dieselbe Datei, aber nicht dieselben Stellen, und jede ist für sich brauchbar
und prüfbar.

0. **Ladeprüfung und Sollwert.** Vor jeder Änderung an der Seite, damit der
   Sollwert vom unveränderten Stand stammt.
1. **Zahl am Reiter.** Klein, eine Kernfunktion, ein Renderschritt.
2. **Spalte «Total / Jahr» und Spaltentausch.** Berührt jede Tabelle und den Druck; vor der
   Treppe, damit deren Druckprüfung schon das neue Tabellenbild sieht.
3. **Treppe.** Der grösste Teil: Kern für die Geometrie, SVG, Häkchen, Druck.

## Nachzuziehen ausserhalb der Seite

- `plans/2026-10-22-budget-offene-arbeiten.md`: Punkt 10 als erledigt
  markieren, mit Verweis hierher.
- `specs/2026-10-23-budget-grafik-und-vergleich-design.md`: Nachtrag zur
  Zeitachse (siehe oben).
- `CLAUDE.md`, Abschnitt zu `tokens.css`: am 2026-10-26 nachgeprüft, nichts
  nachzuziehen. Der Stand, auf dem dieser Zweig aufsetzt (`ed9e2ed`),
  beschreibt die Budgetvorlage schon mit ihrer Alias-Schicht (seit `57de428`
  in `MIGRIERT`) und nennt keine Zahl von Tests mehr.
