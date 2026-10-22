# Anpassungen mit Stichtag und private Versionsnotiz

**Datum:** 2026-10-21
**Betrifft:** `docs/budgetvorlage.html` (eigenständige Seite, kein Generat)
**Dateiformat:** v4 → v5

## Ziel

Ein Budget soll zeigen, **wann** eine geplante Veränderung greift, nicht nur
**dass** sie geplant ist. Heute kann die Seite zwei Haushaltsstände
nebeneinanderstellen (Versionen), aber keinen Zeitpunkt festhalten.

Nach dem Umbau steht in der Beratung auf dem Bildschirm:

```
heute                     − 120.00 / Monat
ab 01.01.2027             +  29.00 / Monat
ab 01.04.2027             +  43.00 / Monat
mit allen Vorschlägen     + 113.00 / Monat
```

Dazu kommt eine private Notiz pro Version, die nicht mitgedruckt wird.

## Woher das kommt

Rückmeldung aus der Sozialberatung, sinngemäss: Budgetverbesserungen treten oft
verzögert ein. Ein gekündigtes Handyabo läuft bis zum Ende der Kündigungsfrist
weiter. Und ein Vorschlag der Fachperson ist noch kein Entschluss. Gewünscht
wurde «ein weiteres Feld pro Betrag, wo man Anpassungen einträgt und je nachdem
auch zeitlich anpasst», damit man schwarz auf weiss sieht, wie viel mehr
möglich wäre.

Zwei Fälle also — «steht fest, wirkt später» und «noch nicht entschieden». Im
Gespräch mit der auftraggebenden Person wurde geklärt: **das ist dasselbe
Feld.** Steht ein Datum dabei, gilt das Erste; steht keines dabei, das Zweite.

## Was die Seite heute kann

- **Versionen** mit Reitern, `basedOn`-Verkettung, Vergleichstabelle unten
  («Versions-Übersicht»), Löschen und Umbenennen.
- **Kommentar je Position je Version**, im aufklappbaren Bereich unter der
  Zeile. Der Chevron-Knopf färbt sich, wenn ein Kommentar vorliegt. **Nur bei
  den Ausgaben** — `EXPANDABLE_GROUPS` umfasst die Ausgabengruppen; die Gruppe
  `einnahmen` hat heute weder Chevron noch Aufklappbereich noch Kommentar.
- **Checkbox «Kommentare drucken»** in der Werkzeugleiste; ohne Häkchen bleiben
  die aufgeklappten Bereiche im Ausdruck weg (`body.print-comments`).
- Speichern als HTML mit eingebettetem JSON, dazu JSON-Export/-Import.
- Werte je Zeile als `jaehrlich` **und** `monatlich`, mit der Regel: jährlich
  gewinnt, sonst monatlich × 12.

### Eine Warnung aus der Geschichte

Bis Dateiformat v3 gab es eine **«Reduktion»** je Zeile — ein Abzug, mit
Kommentar, im selben Aufklappbereich. Format v4 hat sie **absichtlich
abgeschafft** und durch die Versionen ersetzt; der Ladecode zerlegt alte
Dateien bis heute in «Original» und «Nach Reduktion».

Dieser Entwurf holt sie **nicht** zurück. Der Unterschied: die Reduktion war
ein Abzug ohne Zeitangabe und konkurrierte damit direkt mit den Versionen. Die
Anpassung hier ist ein **Zielbetrag mit Stichtag** und drückt genau das aus,
was eine Version nicht kann — das Datum. Wer beim Umbau auf den alten Code
stösst, soll ihn in Ruhe lassen: die Migration alter Dateien bleibt, wie sie
ist, und erzeugt weiterhin zwei Versionen, keine Anpassungen.

## Entscheidungen

- **Ein Feld für beide Fälle.** Zielbetrag plus freiwilliges Datum.
- **Zielbetrag, nicht Differenz.** «neu 0.00» ist eindeutig, «minus 60.00»
  verlangt Kopfrechnen und bricht, sobald der Ausgangsbetrag sich ändert.
- **Keine anteilige Jahresrechnung.** Die Seite rechnet nicht aus, was das
  laufende Jahr anteilig kostet. Sie zeigt diskrete Stände zu Stichtagen. So
  redet die Beratung, und so bleiben die Zahlen prüfbar.
- **«heute» heisst: keine einzige Anpassung angewendet.** Auch dann nicht, wenn
  ihr Datum bereits verstrichen ist. Ein Budget, das sich über Nacht selbst
  umschreibt, kann niemand mehr nachvollziehen; ob die Einsparung wirklich
  eingetroffen ist, weiss nur die Fachperson. Verstrichene Stichtage werden
  stattdessen als «fällig seit …» markiert.
- **Die Stände bauen aufeinander auf.** Der Stand zum 01.04. enthält alles, was
  am 01.01. schon gegriffen hat.
- **Höchstens eine Anpassung je Position und Version.** Eine Kette («sinkt erst,
  fällt dann weg») lässt sich mit Versionen abbilden und ist den Aufwand im
  Formular nicht wert.
- **Anpassungen gehören zur Version**, wie die Kommentare. «Aktuell» und «Nach
  Umzug» haben je eigene.
- **Einnahmen bekommen Anpassungen ebenso wie Ausgaben.** «Neue Stelle ab
  01.03.» oder «Unterhaltsbeiträge fallen weg» verändern die Differenz genauso
  stark wie ein gekündigtes Abo. Dafür brauchen die Einnahmen-Zeilen erstmals
  einen Aufklappbereich — siehe unten.
- **Die Vorschau ist keine Version.** Sie wird gerechnet, nicht gespeichert,
  und lässt sich nicht bearbeiten.
- **Die private Notiz gehört ebenfalls zur Version**, nicht zum Budget als
  Ganzem.

## Datenmodell

Ein Versionsobjekt bekommt zwei Felder dazu:

```js
{
  id, name, basedOn, createdAt,
  values:   { "rowId.jaehrlich": number, "rowId.monatlich": number },
  comments: { rowId: string },

  adjustments: {                      // NEU — rowId → Anpassung
    telefon: { jaehrlich: null, monatlich: 0, ab: "2027-01-01" }
  },
  privateNote: ""                     // NEU — private Notiz zur Version
}
```

### Die Falle: leer ist nicht null

In `values` bedeutet leer dasselbe wie 0; überall im bestehenden Code steht
`version.values[key] || 0`. **Für `adjustments` gilt das nicht.** «neu 0.00»
ist der häufigste Fall überhaupt — das Abo fällt weg. Leer muss deshalb `null`
sein und von 0 unterscheidbar bleiben. Wer hier `|| 0` schreibt, macht aus
jeder leeren Anpassung eine Nullsetzung und streicht stillschweigend Positionen
aus dem Budget.

Eine Anpassung **gilt als vorhanden**, wenn `jaehrlich` oder `monatlich` eine
Zahl ist (0 eingeschlossen).

**Nachtrag vom 2026-10-22: eine Anpassung ohne Betrag kann es nicht geben.**
Ursprünglich war ein `ab` ohne Betrag erlaubt und wurde als «unvollständig»
markiert. Das ist gestrichen — eine Anpassung, die nichts anpasst, ist keine.
Umgesetzt wird das als **Sperre, nicht als Aufräumen**: das Datumsfeld bleibt
gesperrt, solange keiner der beiden Beträge eine Zahl enthält. So entsteht der
Zustand gar nicht erst, statt dass die Seite ihn hinterher stillschweigend
wegräumt. Werden beide Beträge geleert, fällt das Datum mit und der Eintrag
verschwindet.

Die 0 bleibt davon unberührt und bleibt ein gültiger Zielbetrag. «Abo
gekündigt, kostet ab 01.01. nichts mehr» ist der Anlass dieses ganzen
Vorhabens; ohne die 0 liesse er sich nicht ausdrücken.

Für die Rechnung gilt dieselbe Regel wie bei `values`: jährlich gewinnt, sonst
monatlich × 12.

`ab` ist ein ISO-Datum `YYYY-MM-DD` oder `null`. `null` heisst «noch offen».

### Beim Anlegen einer Version

- **«Neue Version» wie bisher** (`basedOn`): `adjustments` und `privateNote`
  werden **nicht** mitkopiert — gleich wie die Kommentare heute.
- **«Neue Version aus dem Stand ‹ab 01.01.2027›»** (neu, siehe unten):
  `values` sind die gerechneten Werte dieses Standes. Anpassungen mit einem
  Datum **bis und mit** diesem Stichtag sind darin aufgegangen und entfallen.
  Anpassungen mit späterem Datum **und** solche ohne Datum wandern unverändert
  mit — sonst verlöre man mit dem Einlösen des ersten Stichtags alle folgenden.
  Kommentare und private Notiz werden nicht mitkopiert.

  **Nachtrag vom 2026-10-22: der Dialog fragt, welche Positionen mitkommen.**
  Nicht jede Anpassung, die zu einem Stichtag gehört, ist auch wirklich
  eingetreten — die Krankenkasse hat zugestimmt, der Vermieter nicht. Der
  Dialog listet deshalb jede Position, die dieser Stand einlösen würde, mit
  ihrem alten und neuen Betrag und einem Häkchen, **standardmässig gesetzt**.
  Was angehakt bleibt, wandert in die Werte der neuen Version; was abgewählt
  wird, bleibt dort als Anpassung stehen, mit seinem Datum. Entschieden wird
  also an **einer** Stelle, im Moment des Drückens, und nichts davon muss
  gespeichert werden. Häkchen neben den Zeilen im Formular wurden erwogen und
  verworfen: zwei Orte für dieselbe Entscheidung ergeben zwei Stände, die sich
  widersprechen können.

  Der feste Hinweissatz im Dialog entfällt damit. Was mit den übrigen
  Anpassungen geschieht, zeigt die Liste selbst.

### Dateiformat

`FILE_FORMAT_VERSION` steigt von 4 auf 5. Beim Laden einer v4-Datei fehlen die
beiden Felder und werden zu `{}` und `''`. Ältere Dateien (v1–v3) laufen
unverändert durch die bestehende Migration.

## Die Stichtage

Aus den Anpassungen der aktiven Version entsteht eine Liste von Ständen:

1. **heute** — der erfasste Stand, keine Anpassung angewendet.
2. **je ein Stand pro verschiedenem `ab`-Datum**, aufsteigend sortiert. Jeder
   wendet alle Anpassungen an, deren Datum kleiner oder gleich ist.
3. **mit allen Vorschlägen** — zusätzlich alle Anpassungen ohne Datum. Dieser
   Stand erscheint nur, wenn es mindestens eine solche gibt.

Mehrere Positionen am selben Datum ergeben **einen** Stand.

## Anzeige: die Zusammenfassung unten

**Hier wird die Kernzusage eingelöst, nicht im Vorschau-Reiter.** Der
bestehende Block «Total Einnahmen / Total Ausgaben / Differenz: Einnahmen −
Ausgaben» bekommt zusätzliche Zeilen, sobald die aktive Version Anpassungen
hat:

```
Total Einnahmen                         3'800.00
Total Ausgaben                          3'920.00
Differenz: Einnahmen − Ausgaben         − 120.00
   ab 01.01.2027                        +  29.00
   ab 01.04.2027                        +  43.00
   mit allen Vorschlägen                + 113.00
```

Das steht bewusst **nicht** in der Versions-Übersicht. Die ist heute per
`isMultiVersion()` ausgeblendet, solange nur eine Version existiert — und genau
das ist der Regelfall, denn die Anpassungen sollen die Versionen für diesen
Zweck ja gerade ersetzen. Wer die Zahlen dorthin legte, lieferte sie im
häufigsten Fall gar nicht. Das Gate bleibt deshalb, wie es ist.

Die Stände erscheinen zusätzlich als eigene Zeilen in der Versions-Übersicht,
wo diese ohnehin sichtbar ist (ab zwei Versionen), abgesetzt von den echten
Versionen.

## Anzeige: die Zeile

Im bestehenden Aufklappbereich, **über** dem Kommentar:

```
ANPASSUNG DIESER POSITION
  [ Neu jährlich ]  [ Neu monatlich ]  [ Gilt ab (darf leer bleiben) ]
KOMMENTAR ZU TELEFON, HANDY, INTERNET
  [ Abo gekündigt, Frist läuft bis 31.12.2026.                       ]
```

Eine Zeile mit Anpassung bleibt **auch zugeklappt markiert** — linker Balken
und warmer Hintergrund in den vorhandenen Warnfarben (`--color-warning`,
`--color-warning-bg`). Nur so sieht man die Anpassungen beim Durchscrollen.

Der Chevron-Knopf zeigt heute schon durch Füllung an, dass ein Kommentar
vorliegt. Die Anpassung braucht ein eigenes, davon unterscheidbares Zeichen —
sonst stehen zwei Aussagen auf demselben Knopf.

Die angezeigte Zahl in «Total / Jahr» bleibt der **heutige** Betrag. Die
Anpassung ändert die Zeile nicht, sie steht daneben.

### Die Einnahmen bekommen den Aufklappbereich erst

`EXPANDABLE_GROUPS` entspricht heute den Ausgabengruppen. Die Gruppe
`einnahmen` wird aufgenommen, damit ihre Zeilen Chevron und Panel erhalten.

**Damit erhalten die Einnahmen beiläufig auch die Kommentarfunktion.** Das ist
gewollt und nicht zu verhindern, ohne das Panel künstlich zu halbieren — eine
Notiz wie «befristet bis Ende Jahr» gehört dort ohnehin hin. Der Kommentar
verhält sich in allem wie bei den Ausgaben, Druckverhalten eingeschlossen.

Zu prüfen ist, ob die Breiten der Einnahmen-Zeilen stimmen: der Chevron nimmt
links Platz weg, den sie bisher nicht abgeben mussten.

Eine Korrektur zum Bestand: Der Vergleich mit der `basedOn`-Version steht
**nicht** im Aufklappbereich, sondern als `title`-Tooltip auf dem
Chevron-Knopf (`refreshExpanderUI`). Im Panel stehen heute nur Beschriftung und
Textfeld. Es ist also schlicht Platz zu schaffen für die Anpassungsfelder —
**ein Inline-Vergleich im Panel ist nicht Teil dieses Entwurfs.**

## Anzeige: Reiter «Vorschau»

Rechts neben den echten Versionsreitern, abgesetzt, gestrichelt umrandet, ohne
Schliesskreuz:

```
Versionen:  (Aktuell)  (Nach Umzug)  |  (⏱ Vorschau)
Stand:  [heute] [ab 01.01.2027] [ab 01.04.2027] [mit allen Vorschlägen]
```

Dieser Reiter zeigt das **ganze Budget** zu einem Stand. Die blosse
Differenz steht schon unten in der Zusammenfassung; dafür muss hier niemand
hin.

- Erscheint nur, wenn die aktive Version mindestens eine Anpassung hat.
- **Der Vorschau-Reiter gehört nicht in die `role="tablist"` der Versionen.**
  Die aktive Version bleibt aktiv, während die Vorschau läuft — ein Reiter in
  derselben Gruppe behauptete das Gegenteil und brächte die Tastaturbedienung
  der bestehenden Leiste durcheinander. Er ist ein eigener Umschaltknopf
  daneben.
- Die Stand-Leiste erscheint **nur, solange die Vorschau offen ist**, und sie
  **schaltet um**; sie springt nicht im Formular herum.
- «heute» innerhalb der Vorschau ist das gesperrte Abbild der Version. So kann
  man zwischen Ausgangslage und Stichtagen hin und her, ohne die Vorschau zu
  verlassen.
- Verlassen wird sie über den Vorschau-Knopf selbst oder über einen
  Versionsreiter. Das gesperrte Formular braucht einen sichtbaren Weg zurück —
  ein Zustand, aus dem man nicht offensichtlich herausfindet, wäre das
  Schlimmste an dieser Funktion.
- Wird die aktive Version gewechselt, schliesst die Vorschau.

### Die Vorschau darf nichts zurückschreiben

`captureFormToActiveVersion()` liest das Formular blind in die aktive Version
zurück und wird aus `serialize()`, `renderVersionsOverview()` und den
Eingabe-Handlern aufgerufen. Steht im Formular ein gerechneter Stand, würde der
nächste dieser Aufrufe die **erfassten Werte überschreiben** — stillschweigend
und unwiederbringlich. Das ist die einzige Stelle in diesem Entwurf, an der
eine falsche Annahme Daten der Fachperson vernichtet statt nur anders
auszusehen.

Deshalb verbindlich:

1. Beim Betreten der Vorschau wird **einmal** zurückgeschrieben (wie bei
   `switchVersion`), damit nichts Offenes verlorengeht.
2. Solange die Vorschau läuft, schreibt `captureFormToActiveVersion()`
   **nichts** — sie kehrt sofort zurück.
3. **Speichern und Exportieren laufen normal weiter** und schreiben die
   dahinterliegende Version unverändert. Kein Sprung, keine Sperre, keine
   Rückfrage: der gerechnete Stand steht ohnehin nicht in der Datei.

Wem das zu heikel ist, baut die Vorschau als eigene Darstellung statt als
umbefülltes Formular. Beide Wege sind zulässig, die drei Punkte oben gelten für
beide.

## Anzeige: Knopf «Anpassungen» in der Kopfleiste

Neben den Reitern, von überall im Formular erreichbar, ohne den Stand zu
wechseln:

```
(⏱ 4 Anpassungen)        ← klappt auf:

ab 01.01.2027   zwei Positionen · + 149.00
   Telefon, Handy, Internet        60.00 → 0.00      + 60.00
   Fitness-Abo                     89.00 → 0.00      + 89.00
ab 01.04.2027   eine Position · + 14.00
   Hausrat- / Haftpflicht          42.00 → 28.00     + 14.00
ohne Datum      noch offen · + 70.00
   Krankenkasse (Franchise)       410.00 → 340.00    + 70.00

   [ Neue Version aus diesem Stand ]   ← je Datumsgruppe einer
```

**Jede Datumsgruppe trägt ihren eigenen Knopf**, auch die Gruppe «ohne Datum».
Ein einzelner Knopf am Fuss müsste raten, welchen der drei Stichtage er meint.

Der Knopf öffnet das bestehende «Neue Version»-Modal mit vorausgefülltem Namen
(«Stand ab 01.01.2027»), damit die Fachperson ihn überschreiben kann. Als
`basedOn` wird die **Version gesetzt, aus der gerechnet wurde**. Das ist kein
Beiwerk: daran hängen die Spalte «Δ vs. Basis», der Chevron-Tooltip und die
Tabelle «Unterschiede pro Position». Mit dieser Basis listet jene Tabelle genau
die eingelösten Anpassungen auf — das ist der Zweck. `null` ergäbe eine
Wurzelversion ganz ohne Vergleich.

**Das Datum ist nur Überschrift.** Gesprungen wird über den Positionsnamen —
ein Eintrag, ein Ziel. Das war die ausdrückliche Rückmeldung: ein Klick auf ein
Datum könnte nicht sagen, zu welcher von mehreren Positionen er führt.

Ein Klick klappt die Zeile auf und scrollt sie in den sichtbaren Bereich. Weil
die Kopfleiste klebt (`.sticky-head`), muss der Sprung deren Höhe abziehen,
sonst landet die Zeile darunter.

Ein Stichtag, dessen Datum verstrichen ist, trägt den Zusatz «fällig seit …».

Der Knopf erscheint nur, wenn es Anpassungen gibt, und nennt ihre Anzahl.

## Private Notiz zur Version

Ein mehrzeiliges Feld beim Kopf des Budgets, deutlich als privat
gekennzeichnet, für Sinn und Zweck: warum dieses Budget entstanden ist, was die
Fachperson sich dabei gedacht hat. Es gehört zur **aktiven Version** und
wechselt mit ihr.

- Im Ausdruck **bleibt es weg**, ausser die neue Checkbox «Private Notiz
  drucken» ist gesetzt. Sie steht in der Werkzeugleiste neben «Kommentare
  drucken» und ist standardmässig **aus**.
- In der **gespeicherten Datei steht es drin** — ausdrücklich so entschieden.
  Die Notiz ist gegen das versehentliche Mitdrucken geschützt, nicht gegen das
  Weitergeben der Datei. Wer das Gegenteil annimmt, baut ein falsches
  Versprechen ein.

## Drucken

- Die Anpassungsfelder stehen im Aufklappbereich und drucken deshalb mit der
  bestehenden Checkbox «Kommentare drucken» mit. Die Zeilenmarkierung druckt
  nur dann ebenfalls — eine gelbe Zeile ohne Erklärung verwirrt.
- Die Vorschau-Leiste und der Anpassungen-Knopf drucken nie (wie `.version-bar`
  heute).
- Die Stichtag-Stände in der Versions-Übersicht drucken mit, wie die Übersicht
  heute schon. Dasselbe gilt für die neuen Stand-Zeilen in der
  Zusammenfassung — sie sind der Kern der Sache und gehören aufs Blatt.

### Einen gerechneten Stand drucken

Das ist **erlaubt** — die Klientin soll das Blatt mitnehmen können. Es braucht
dafür aber eine Kennzeichnung, die im Ausdruck steht und nicht zu übersehen
ist, im Blattkopf über dem Budget:

```
Stand ab 01.01.2027 — gerechnet, nicht erfasst
```

Ohne sie verliesse ein Budget-Ausdruck das Haus, dessen Zahlen nicht die
erfassten sind, und man sähe es ihm nicht an. Die Kennzeichnung erscheint nur
im Ausdruck eines Standes, nie beim normalen Budget.

## Ausdrücklich nicht Teil davon

- **Keine anteilige Jahresrechnung** und kein gemischtes Kalenderjahr.
- **Kein automatisches Anwenden** verstrichener Stichtage.
- **Keine Erinnerungen, keine Benachrichtigungen.** Die Seite läuft ohne Server
  und ohne Netz; sie kann nicht an einen Termin erinnern, an dem sie nicht
  geöffnet ist.
- **Keine Kette von Anpassungen** je Position.
- **Die Versionen bleiben.** Sie sind weiterhin für den grundsätzlich anderen
  Haushalt da (Umzug, Trennung, neue Stelle), nicht mehr für «was wäre, wenn
  ich das Abo künde».
- **Die Reduktions-Migration bleibt unverändert.**

## Randbedingungen aus dem Projekt

- Das CSS bleibt **in der Datei eingebettet**; die Seite muss ohne Server und
  ohne Internet laufen (`CLAUDE.md`).
- `docs/` wird öffentlich veröffentlicht: **keine echten Personendaten** in
  Beispielen oder Platzhaltern.
- Die Fusszeile mit Urheber-Credit und Kaffee-Link bleibt unangetastet.
- Alles bleibt in `docs/budgetvorlage.html`; die Seite wird nicht generiert.

## Nicht vergessen

Kleinigkeiten, die beim Umbau mitlaufen müssen und sonst durchrutschen:

- `SUPPORTED_VERSIONS` muss die 5 aufnehmen, nicht nur `FILE_FORMAT_VERSION`.
- Die Druckmarkierung setzt heute `has-comment` je Zeile; sie braucht das
  Gegenstück «hat Anpassung».
- Der Hinweistext in der `.info-box` sagt heute, Einsparungen modelliere man
  über weitere Budget-Versionen. Das stimmt nach dem Umbau nicht mehr.
- «Zurücksetzen» muss Anpassungen und private Notiz mitlöschen.
- **Für diese Seite gibt es keine Tests.** `tests/` deckt Build, Plakat,
  Anleitung und Vorschläge ab, nicht die Budgetvorlage. Geprüft wird von Hand;
  wer hier Tests anlegen will, baut das Gerüst mit.

## Dem Umsetzenden überlassen

- Ob die Vorschau das bestehende Formular umbefüllt (wie `switchVersion`) oder
  eine eigene Darstellung baut.
- Markup und Feinschliff des Anpassungs-Panels und des Kopfleisten-Knopfes.
- Die genaue Darstellung der gerechneten Stände in der Versions-Übersicht.
- Das Zeichen am Chevron-Knopf für «hat Anpassung».
- Format und Eingabehilfe des Datumsfelds (`<input type="date">` liegt nahe).
