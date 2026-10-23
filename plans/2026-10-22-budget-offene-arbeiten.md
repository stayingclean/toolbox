# Budgetvorlage — offene Arbeiten

**Stand:** 2026-10-22
**Branch:** `budget-anpassungen-stichtag`, 18 Commits, **nichts gepusht, kein PR**
**Tests:** 435 grün (`uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`)

Diese Datei ist die Übergabe an eine neue Sitzung. Sie hält fest, was bereits
steht, was der Benutzer beim Ausprobieren angemerkt hat, und was aus den
Prüfungen offen geblieben ist.

## Was bereits steht

Alles in `docs/budgetvorlage.html` — eine Datei, eingebettetes CSS, Vanilla-JS,
kein Build, kein Generat.

- **Anpassung je Position und Version:** Zielbetrag (`jaehrlich` / `monatlich`)
  plus freiwilliges ISO-Datum `ab`. Mit Datum heisst «steht fest, wirkt
  später», ohne Datum «noch offen». `null` ist leer, `0` ist ein gültiger
  Zielbetrag («Abo fällt weg»). Eine Anpassung **ohne Betrag kann es nicht
  geben** — das Datumsfeld bleibt gesperrt, bis ein Betrag dasteht.
- **Rechenkern** zwischen `/* == budget-kern:anfang == */` und
  `/* == budget-kern:ende == */`: rein, ohne `SCHEMA`, `state` oder DOM.
  `tests/budget_treiber.mjs` schneidet ihn aus der ausgelieferten Datei heraus
  und führt ihn in Node aus — dasselbe Muster wie der PDF-Kern von
  `docs/plakat.html`. Die Exportliste liest der Treiber selbst aus dem Kern.
- **Stände** zu Stichtagen als Zusatzzeilen unter `#differenceRow`:
  heute / ab 01.01.2027 / … / mit allen Vorschlägen, kumulativ.
- **`#adjustmentsBtn`** in der Kopfleiste öffnet die Liste aller Anpassungen,
  nach Datum gruppiert; gesprungen wird über den Positionsnamen.
- **«Neue Version aus diesem Stand»** je Datumsgruppe. Der Dialog listet jede
  Position mit alt/neu und einem Häkchen (standardmässig gesetzt);
  Abgewähltes wird nicht eingelöst und bleibt als Anpassung stehen.
- **`#previewBtn`**: gesperrte Vorschau des ganzen Budgets zu einem Stand, mit
  Schreibsperre in `captureFormToActiveVersion`.
- **Private Notiz je Version**, druckt nur mit eigenem Häkchen.
- Dateiformat **v5**; v1–v4 laden unverändert weiter.

**Mitlesen:**
`specs/2026-10-21-budget-anpassungen-design.md` (verbindlich, mit zwei
Nachträgen vom 2026-10-22), `plans/2026-10-22-budget-anpassungen.md` und das
Protokoll der Umsetzung in
`.superpowers/sdd/2026-10-22-budget-anpassungen/progress.md` (git-ignoriert;
enthält jede Entscheidung, jede zurückgestellte Kleinigkeit und die
Begründungen).

---

## Punkte des Benutzers

Reihenfolge wie eingereicht. **Punkt 1 kehrt eine getroffene Entscheidung um**,
die Punkte 2–4 betreffen denselben Bereich und gehören zusammen angeschaut.

### 1. Anpassungen sollen nie gedruckt werden

> «Sie bieten nur eine Möglichkeit zum Erfassen von Zahlen für eine weitere
> Version.»

**Das ändert eine Entscheidung aus dem Entwurf.** Heute drucken die
Anpassungsfelder zusammen mit der Checkbox «Kommentare drucken» mit, und die
Zeilenmarkierung druckt nur dann ebenfalls (Abschnitt «Drucken» im Entwurf,
umgesetzt in Task 7). Neu: gar nicht mehr, unabhängig von jeder Checkbox.

Zu beachten: Die Zeilenmarkierung `has-adjustment` und ihr `beforeprint`-Teil
fallen damit auch weg. Den Entwurf nachziehen, nicht nur das CSS.

### 2. Anpassungen sind im aufgeklappten Bereich zu prominent

Gewünscht: versteckt, über einen Knopf oder eine Checkbox einblendbar — und
**unterhalb** des Kommentars statt darüber.

Heute stehen sie bewusst über dem Kommentar (Entwurf, «Anzeige: die Zeile»).
Die Umkehrung ist eine bewusste Änderung, kein Versehen beim Umbau.

### 3. Anpassungszahlen in denselben Spalten wie die Position

> «Man würde also das Datum am Anfang der Zeile eingeben und die Zahlen daneben
> eintragen. So sieht man die Anpassungen unterhalb der eigentlichen Zahlen.»

Also: die Anpassung wird eine eigene Zeile direkt unter der Position, spaltenbündig
zu «Jährlich» / «Monatlich», mit dem Datum in der Beschriftungsspalte. Das macht
den Vergleich alt/neu ohne Kopfrechnen sichtbar.

Hängt eng mit Punkt 2 zusammen: Ist die Anpassung eine eigene Tabellenzeile,
stellt sich die Frage «über oder unter dem Kommentar» neu. Beide Punkte in
einem Zug entwerfen.

### 4. Kommentare im Dialog mitbearbeiten

> «Ob und wann man die Möglichkeit haben sollte die Kommentare für die neue
> Version anzupassen. Ich würde vorschlagen, dass man im Dialog die Kommentare
> mit einfügt und der User darin die Anpassungen vornehmen kann.»

Heute werden `comments` beim Anlegen einer Version **nicht** mitkopiert — gleich
wie `adjustments` und `privateNote`. Der Dialog zeigt sie nicht.

Zu klären: Sollen die Kommentare der eingelösten Positionen in die neue Version
mitwandern, und soll man sie dort gleich anpassen können? Das würde den Dialog
von einer Auswahl zu einem kleinen Formular machen.

### 5. «Neue Version» aus der Kopfleiste und «aus diesem Stand» zusammenführen

> «Ich würde vorschlagen, dass sich die ‹Neue Version› aus der Kopfzeile den
> gleichen Dialog aufruft wie der Dialog vom Button ‹Anpassungen›, damit wir
> den gleichen Workflow haben, wenn eine Version Anpassungen enthält.»

Heute sind es zwei Wege durch **dasselbe Modal**: `#addVersionBtn` öffnet es
ohne Liste, `neueVersionAusStand(standKey)` mit Liste. Der Dialog ist also schon
einer, die Einstiege sind zwei.

**Der Befund dahinter stimmt und ist der wichtigere Teil:** Es fehlt ein Weg,
*alle* Anpassungen in eine neue Version zu übernehmen. `stichtagListe` hängt
den Stand «offen» nur an, wenn mindestens eine Anpassung **ohne** Datum
existiert. Haben alle Anpassungen ein Datum, gibt es keine Gruppe «Ohne Datum»
und damit keinen Knopf «alles». Erreichbar ist es nur mittelbar: die **späteste**
Datumsgruppe löst alles ein, was bis dahin fällig ist — also alle. Das weiss
aber niemand, der es nicht gebaut hat.

### 6. Checkbox im Dialog nicht vertikal zentriert

Kleinigkeit im CSS der Einlöse-Liste (`.einloesen-*`).

### 7. Die Anleitung oben auf der Seite hilft dort nicht

Gewünscht: mitlaufend, so dass die Angaben immer sichtbar bleiben — und
inhaltlich erweitert um den neuen Ablauf mit den Anpassungen (warum, was und
weshalb eingetragen wird).

Ausdrücklich mitgefragt: **Was geschieht auf einem zu schmalen Bildschirm?**
Die Antwort gehört in den Entwurf, nicht erst in den Code.

Zu beachten: `.info-box` wird im Druck ausgeblendet; die klebende
`.sticky-head` trägt bereits Werkzeugleiste und Versionsleiste, und
`springeZuZeile` rechnet mit ihrer Höhe. Ein zusätzlicher mitlaufender Block
beeinflusst beides.

### 8. Die Übersicht einer Version grafisch verbessern

> «Es gibt sehr viele Zahlen und nichts Grafisches. Wie könnte man zum einen
> die Anpassungen, welche in der Version vorgenommen worden sind, grafisch
> darstellen?»

### 9. Versionen vergleichen, rechts neben der letzten Version

> «Ein Button, der alle Versionen (auswählbar) vergleicht und die Differenz
> anzeigt.»

Offen gelassen und bewusst als Frage gestellt: welche Diagrammart, wie viele
Diagramme, nur die Gesamtzahl oder auch die einzelnen Kategorien.

**Harte Randbedingung für 8 und 9:** Die Seite muss per `file://` ohne Server
und ohne Internet laufen, und das CSS bleibt eingebettet (`CLAUDE.md`). Eine
Diagrammbibliothek von einem CDN ist damit ausgeschlossen. Was bleibt:
handgeschriebenes SVG oder CSS. Das ist gut machbar, aber es begrenzt den
Ehrgeiz — und es gehört vor dem Entwerfen ausgesprochen.

**Nachtrag 2026-10-22, zwei Rückfragen des Benutzers:** Lässt sich der Import
einer Bibliothek mit einer `if`-Abfrage umgehen (lokal ohne, online mit
Diagrammen), und lässt sich eine Bibliothek auf einer GitHub Page überhaupt
verwenden? Beantwortet in `plans/2026-10-22-budget-abarbeitungsplan.md`,
Welle 4, Session B — kurz: ja, beides; empfohlen ist trotzdem SVG von Hand,
und falls doch eine Bibliothek, dann in die Datei eingebettet statt vom CDN
und ohne zwei Fassungen.

**Nachtrag 2026-10-23 — die «harte Randbedingung» oben gilt nicht mehr so.**
Der Benutzer hat entschieden, dass die Budgetvorlage über die URL benutzt wird
und nicht als heruntergeladene Kopie; heruntergeladene Stände liefen bei den
Beratenden auseinander. Dazu zwei Befunde: die Seite speichert `.json` und
nicht HTML (Werkzeug und Daten sind getrennt), und sie lädt schon heute
Schriften von Google Fonts, war also nie netzunabhängig. Eine Bibliothek wäre
damit erlaubt gewesen; der Benutzer hat am selben Tag **bestätigt, dass fremde
Bibliotheken draussen bleiben** — käme je eine, dann mitgeliefert in
`docs/vendor/` oder eingebettet, nie vom CDN. Zur Offline-Fähigkeit gehört
neben der Skillsliste auch der **Flyer-Editor**: er exportiert sich selbst als
HTML-Datei, die auf einer Festplatte weiter funktionieren muss.
Die Empfehlung für die drei Diagramme bleibt CSS, nun aber mit
anderer Begründung (Balken mit Textbeschriftung; Canvas verliert bei Ausdruck
und Screenreader). Ausgeführt in
`specs/2026-10-23-budget-grafik-und-vergleich-design.md`, Abschnitt «Die Lage:
Web zuerst»; `CLAUDE.md` Punkt 3 ist nachgezogen.

### 10. Die vierte Spalte «Total / Jahr» wiederholt in jeder Position die zweite

Aus einer Rückfrage des Benutzers am 2026-10-22 entstanden: «Warum gibt es
eigentlich jetzt schon drei Spalten? Die Zahl jährlich steht ja immer in der
ersten und letzten Spalte.» Das stimmt — «Jährlich» und «Monatlich» füllen sich
gegenseitig, und `rowTotal = y || (m * 12)` (Zeile 4039) ergibt damit in einer
Positionszeile immer denselben Wert wie das Jahresfeld. Ihren Zweck hat die
Spalte nur in den Subtotal-Zeilen und in der Zusammenfassung.

Dieser Punkt ist **nicht** Teil des Anpassungs-Umbaus: er betrifft jede Zeile
der Seite und den Ausdruck. Die Herleitung steht in
`plans/2026-10-22-budget-abarbeitungsplan.md` unter D2.

---

## Offen aus den Prüfungen

### Noch nie von einem Menschen gesehen

- **Der echte Ausdruck.** Auf dem Rechner ist kein Chrome oder Edge installiert
  und der eingebaute Browser hat keine Druckvorschau; geprüft wurde durch
  Umschreiben von `@media print` auf `@media all` und Lesen der berechneten
  Stile. Mit Punkt 1 fällt ein Teil davon ohnehin weg. Zu prüfen bleibt: Steht
  die Kennzeichnung «Stand ab … — gerechnet, nicht erfasst» wirklich oben auf
  Seite 1? Sind die gerechneten Zahlen aus der Vorschau in ihrer gedämpften
  Farbe auf Papier lesbar? Unterscheiden sich die Stand-Zeilen ohne
  Hintergrundgrafiken noch voneinander?
- **Die Einnahmen-Zeilen mit dem neuen Pfeil** bei schmaler Breite
  (`label-cell: 40 %` unter 768 px).
- **Das Anpassungs-Panel** auf schmalem Fenster und mit vielen Einträgen.

### Die Vorschau-Frage ist nie beantwortet worden

Der Benutzer hatte vorgeschlagen, die Stände als Knöpfe in die Übersicht zu
legen und den Vorschau-Knopf nur noch dorthin springen zu lassen. Auf die
Rückfrage, was sich beim Klick ändern soll, kamen andere Punkte dazwischen.

Die Frage lohnt sich: Fällt der gesperrte Vorschau-Modus weg, fällt die
riskanteste Stelle des ganzen Umbaus mit weg — die Schreibsperre in
`captureFormToActiveVersion`, die verhindert, dass gerechnete Zahlen die
erfassten überschreiben.

### Testlücke mit System

Der Rechenkern ist echt geprüft. Die **Brücke zwischen DOM und Kern** hängt
dagegen an Textsuchen: Schlüssel `rowId.period`, Klassennamen,
Sichtbarkeitsschaltungen, das Füllen der Einlöse-Liste und das Auslesen der
Häkchen. Eine Umbenennung in `recomputeAll` liesse alle 435 Tests grün und die
Stände still falsch rechnen.

Die ehrliche Antwort wäre ein jsdom-Gerüst für `docs/budgetvorlage.html`. Das
ist ein eigenes Vorhaben, kein Nebenbei — aber es ist der einzige strukturelle
Vorbehalt gegen den heutigen Stand.

### Zurückgestellte Kleinigkeiten

Vollständig mit Begründung in
`.superpowers/sdd/2026-10-22-budget-anpassungen/progress.md` (Zeilen mit
`minor (deferred)`). Die, die wahrscheinlich jemandem auffallen:

- **Escape wirkt in der Vorschau doppelt**: schliesst die Anpassungsliste *und*
  verlässt die Vorschau. Eine Korrektur schlug fehl, weil beide Handler am
  Dokument hängen und der erste das Panel versteckt, bevor der zweite nachsieht.
  Der Benutzer hat gesagt, damit kann er leben.
- **Pfeil-Klick hält das Datum nur in Chromium.** Safari und Firefox unter macOS
  fokussieren Knöpfe beim Klick nicht, dort fällt das Datum bei leerem Betrag
  trotzdem weg.
- `anpassungHatInhalt` prüft inzwischen nur noch den Betrag — der Name sagt
  nicht mehr, was er tut (`anpassungHatBetrag` wäre richtig).
- `100vh` am Modal ist auf Mobilgeräten mit einblendender Adressleiste zu hoch
  (`dvh`), und auf kleinen Schirmen entsteht ein verschachtelter Doppel-Scroll.
- `.modal p` schlägt `.modal-hint`: der Satz unter der Einlöse-Liste erscheint
  in Fliesstextfarbe statt gedämpft (Bestandsproblem).
- `istIsoDatum` lässt `2027-02-31` durch (`Date.parse` nimmt es an). Ergibt
  einen Stand mit unsinniger Überschrift, keine falschen Zahlen; über
  `<input type="date">` nicht erzeugbar. Härtung:
  `new Date(s).toISOString().slice(0, 10) === s`.

---

## Hinweise für die nächste Sitzung

- **Punkte 1, 2, 3 und 4 zuerst zusammen entwerfen**, nicht einzeln umsetzen.
  Sie betreffen alle denselben Bereich (die Zeile und ihren Aufklappbereich),
  und Punkt 3 verschiebt die Anpassung aus dem Panel in die Tabelle — danach
  stellen sich 1 und 2 anders.
- **Der Entwurf wird mitgeändert, nicht nur der Code.** Punkt 1 und Punkt 2
  kehren dort getroffene Entscheidungen um; bleibt der Entwurf stehen, widerlegt
  ihn die Seite.
- **Nichts ist gepusht.** Der Branch liegt lokal.
