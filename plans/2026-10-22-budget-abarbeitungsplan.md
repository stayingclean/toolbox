# Budgetvorlage — Abarbeitungsplan für die offenen Arbeiten

**Stand:** 2026-10-22
**Grundlage:** `plans/2026-10-22-budget-offene-arbeiten.md` (Punkte 1–9 und die
offenen Prüfungen)
**Branch:** `budget-anpassungen-stichtag`, nichts gepusht
**Tests:** 435 grün — `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`

---

## Die Strategie in vier Sätzen

1. **Zuerst löschen, dann umbauen, dann erweitern.** Punkt 1 (nie mehr drucken)
   entfernt rund 50 Zeilen Druck-CSS und vier Tests. Wird er zuerst erledigt,
   muss der Umbau aus Punkt 3 diese Regeln nicht noch einmal mitziehen.
2. **Alle Entwurfsfragen in einem Zug entscheiden**, bevor eine Zeile Code
   fällt — vier Entscheide, unten aufgelistet. Sie sind der eigentliche
   Engpass, nicht das Tippen.
3. **Punkte 2 und 3 sind ein einziger Umbau**, nicht zwei. Die Anpassung wird
   eine Tabellenzeile; damit ist «über oder unter dem Kommentar» von selbst
   beantwortet und «versteckt bis eingeblendet» ist nur noch ein Schalter.
4. **Punkte 7, 8 und 9 parallel entwerfen, aber seriell einbauen.** Alles liegt
   in *einer* Datei mit 5184 Zeilen: zwei Sessions, die gleichzeitig in
   `docs/budgetvorlage.html` schreiben, erzeugen Konflikte in jedem Hunk. Die
   Sessions liefern darum je einen Entwurf in `specs/`; eingebaut wird hier,
   nacheinander.

---

## Welle 0 — Die Entscheide (mit dem Benutzer durchgegangen am 2026-10-22)

### D1 — Der Pfeil zeigt den Kommentar, ein Knopf darin erfasst die Anpassung ✔ entschieden

Zwei Klarstellungen des Benutzers, die eine frühere Fassung dieses Abschnitts
ersetzen:

1. **Der Kommentar erscheint immer, sobald die Position aufgeklappt ist** — so
   wie vor dem Umbau. Nachgesehen auf `master`: dort enthält der
   Aufklappbereich ausschliesslich Beschriftung und Textfeld (`comment-panel`),
   nichts weiter. Genau dahin geht es zurück.
2. **Die Anpassungsfelder (Datum, Betrag jährlich/monatlich) erscheinen erst
   auf Klick**, über einen Knopf **im aufgeklappten Bereich**.

Deshalb ist es nur ein Knopf und keine zwei: Der Pfeil bleibt der Pfeil, und
der neue Knopf steckt im Aufklappbereich, nicht in der Zeile.

Aufbau einer aufgeklappten Position:

| Zeile | Inhalt |
|---|---|
| Positionszeile | Name, Jährlich, Monatlich, Total / Jahr — unverändert |
| Kommentarbereich | Beschriftung und Textfeld, **immer** sichtbar beim Aufklappen; darin der Knopf «Anpassung erfassen», solange es keine gibt |
| Anpassungszeile | Eigene Tabellenzeile, spaltenbündig: Datum in der Beschriftungsspalte, «Neu jährlich» und «Neu monatlich» unter den erfassten Beträgen, Unterschied in Spalte 4 (D2) |

**Damit sind Punkt 2 und Punkt 3 beide erfüllt, ohne Widerspruch:** die
Anpassung steht *unterhalb* des Kommentars (Punkt 2) und trotzdem
spaltenbündig unter den Zahlen der Position (Punkt 3) — eine Tabellenzeile
behält ihre Spalten, auch wenn eine andere Zeile dazwischen liegt.

**Regeln, die in den Entwurf gehören:**

- **Zugeklappt:** der Punkt am Pfeil zeigt, dass eine Anpassung hinterlegt ist
  (bestehendes CSS, Zeile 503). Die Zahlen sieht man zugeklappt nicht — wer
  alle Anpassungen auf einmal sehen will, nimmt die Anpassungsliste in der
  Kopfleiste (`#adjustmentsBtn`).
- **Aufgeklappt mit bestehender Anpassung:** die Anpassungszeile ist sofort da,
  der Knopf entfällt.
- **Aufgeklappt ohne Anpassung:** nur der Knopf. Klick → leere Anpassungszeile,
  Fokus in «Neu jährlich».
- **Leer verlassen:** die Zeile verschwindet wieder. Das ist die bestehende
  Regel «eine Anpassung ohne Betrag kann es nicht geben» (Commit `9bba8ef`),
  nur sichtbar gemacht.
- **Zuklappen** schliesst Kommentar und Anpassungszeile zusammen; eine
  eingetragene Anpassung bleibt natürlich gespeichert.

### D2 — Spalte 4 der Anpassungszeile zeigt den Unterschied ✔ entschieden

**Entschieden:** Die Anpassungszeile zeigt in der vierten Spalte den
Unterschied. Die Spalte selbst bleibt, wie sie ist — die Frage, ob sie in den
Positionszeilen überhaupt etwas beiträgt, liegt als **Punkt 10** und wird
nicht in diesem Umbau beantwortet.

Die Herleitung, weil sie den Entscheid trägt:

Rückfrage des Benutzers: «Warum gibt es eigentlich jetzt schon drei Spalten?
Die Zahl jährlich steht ja immer in der ersten und letzten Spalte.»

**Der Benutzer hat recht, und zwar genau.** Nachgesehen in
`docs/budgetvorlage.html`:

- «Jährlich» und «Monatlich» sind **zwei Eingabefelder**, die sich gegenseitig
  füllen: wer monatlich tippt, bekommt jährlich gerechnet und umgekehrt
  (`handleAmountInput`, Zeile ~4975).
- «Total / Jahr» ist **gerechnet**: `const rowTotal = y || (m * 12)` (Zeile
  4039).

Da beide Felder immer gefüllt sind, ist die vierte Spalte in einer
Positionszeile **immer dieselbe Zahl wie die zweite**. Sie verdient ihren Platz
nur in den Subtotal-Zeilen und in der Zusammenfassung, wo sie die Jahressumme
trägt. (Eine Ausnahme bliebe eine von Hand geschriebene oder sehr alte Datei,
in der nur der Monatswert steht — dann ist das Jahresfeld leer und die vierte
Spalte zeigt die Rechnung.)

Die Spalte trägt in einer Positionszeile also nichts bei, was nicht schon
dasteht — und ist damit für die Anpassungszeile frei: dort steht der
Unterschied (`−1 200`, grün/rot). Das ist genau das Kopfrechnen, das Punkt 3
loswerden will, und es kostet nichts.

Was mit der Spalte selbst geschieht (anders belegen, oder in der Erfassung
weglassen und nur bei den Subtotalen führen), ist **Punkt 10** in
`plans/2026-10-22-budget-offene-arbeiten.md` — eigener Umbau, betrifft jede
Zeile der Seite und den Ausdruck.

### D3 — Kommentare in die neue Version ✔ entschieden

- **Eingelöste Positionen:** Kommentar wandert mit und ist **im Dialog
  bearbeitbar**.
- **Alle übrigen Kommentare:** wandern mit, **ohne** Bearbeitungsmöglichkeit —
  gesteuert über **eine Checkbox** im Dialog («Übrige Kommentare übernehmen»).

Das ist mehr als heute (`createVersion`, Zeile ~3184, kopiert `comments`
bewusst nicht) und berührt das Dateiformat nicht; v5 bleibt.

### D4 — Vorschau-Modus: später entscheiden ✔ entschieden

Erst nach dem Entwurf aus Welle 4 (Punkt 8). Fällt die Vorschau weg, fällt die
Schreibsperre in `captureFormToActiveVersion` mit — die riskanteste Stelle des
Umbaus. Dort zeigt sich, ob Stand-Knöpfe in der neuen Übersicht sie wirklich
ersetzen.

---

## Welle 1 — Löschen und Kleinigkeiten ✔ erledigt am 2026-10-22

Zwei Commits (`5c81329` Punkt 1 mit Tests und Entwurf, `ee09cfa` Punkt 6 und
die vier Kleinigkeiten), 438 Tests grün. Die Anpassungsfelder sind im Druck
nicht mehr erreichbar — **auf Papier gegengeprüft ist das noch nicht**, der
nächste Ausdruck zeigt es.

Was dabei anders kam als geplant: Die vier Kleinigkeiten stehen in **einem**
Commit statt in vieren; keine trägt für sich einen. Die Ersatzregel
`.modal .einloesen-text` ist mitgegangen, weil sie nur den Abstand nachbesserte,
den `.modal p` dem Hinweis genommen hatte.

### 1.1 Punkt 1: Anpassungen drucken nie mehr

Zu entfernen in `docs/budgetvorlage.html`:

- Druck-CSS, Zeilen ~1237–1282: die beiden `body.print-comments …
  .has-adjustment`-Regeln, `body.print-comments … .adj-block { display: block }`,
  die `.adj-input`-Druckfarben und die vier Regeln zur Zeilenmarkierung.
- `.adj-block { display: none }` bleibt — **ohne** die Gegenregel.
- Die Zeilenmarkierung auf dem Bildschirm (Zeilen 516–530) bleibt; sie
  verschwindet erst mit Welle 2, falls der Umbau sie ersetzt.
- `beforeprint`-Teil um Zeile 5072: `hatAnpassung` / `has-adjustment` setzen
  entfällt.

Mitzuziehen:

- **Tests** `tests/test_budget.py` Zeilen 178–179, 759, 764–774 — vier
  Textsuchen, die das genaue Gegenteil festnageln. Sie werden umgedreht:
  «`.adj-block` druckt nie, auch nicht mit `print-comments`».
- **Entwurf** `specs/2026-10-21-budget-anpassungen-design.md`, Abschnitt
  «Drucken»: Entscheid umkehren, Begründung des Benutzers zitieren.

### 1.2 Punkt 6: Checkbox im Dialog zentrieren

`.einloesen-liste .radio-option { align-items: flex-start; }` (Zeile 1764) ist
die Ursache. Richtig ist nicht `center` für alles — der Name kann zweizeilig
werden, das Datum steht darunter. Statt dessen: `align-items: flex-start`
behalten und der Checkbox `align-self: center` geben, oder die erste Textzeile
und die Checkbox über eine gemeinsame Zeilenhöhe ausrichten.

### 1.3 Zurückgestellte Kleinigkeiten (vier Einzeiler)

- `anpassungHatInhalt` → `anpassungHatBetrag` (Kern, alle Aufrufe, Exportliste,
  `tests/budget_treiber.mjs`-Nutzungen).
- `istIsoDatum` härten: `new Date(s).toISOString().slice(0, 10) === s`, Test
  mit `2027-02-31`.
- `.modal p` schlägt `.modal-hint` — Spezifität korrigieren.
- `100vh` am Modal → `100dvh`.

---

## Welle 2 — Punkte 2 + 3 ✔ erledigt am 2026-10-23

Commit `d8162d9`, 443 Tests grün, im Browser gegengeprüft (Spalten bündig auf
den Pixel, Datum überlebt den Feldwechsel, leere Zeile verschwindet, Zuklappen
nimmt beide Zeilen mit, Einlösen und Rückweg stimmen).

Zwei Dinge kamen beim Bauen dazu, die unten nicht standen:

- **In der Vorschau bietet der Knopf nichts an** (`body.mode-preview
  .adj-add-btn { display: none }`). Dort sind alle Felder gesperrt; der Knopf
  hätte eine Zeile geöffnet, in die man nichts schreiben kann.
- **Der Satz in der Anleitung oben nennt jetzt den Knopf.** Er beschrieb den
  alten Ablauf. Punkt 7 schreibt den Kasten ohnehin neu, bis dahin stimmt er
  wenigstens.

Noch offen aus dieser Welle: der **erste echte Ausdruck mit der neuen Zeile**.
`.adj-row` druckt nie, das sichert ein Test — auf Papier gesehen hat es
niemand.

### Was geplant war

Der grosse Umbau. **Zuerst ein Nachtrag im Entwurf**
(`specs/2026-10-21-budget-anpassungen-design.md`, Abschnitte «Anzeige: die
Zeile» und «Drucken»), dann Code.

Zielbild nach D1: **nach** der Kommentarzeile eine
`<tr class="adj-row" data-adj-for="…">` mit vier Zellen — Datumsfeld in der
Beschriftungsspalte, «Neu jährlich» und «Neu monatlich» spaltenbündig zu den
erfassten Beträgen, in der vierten Spalte der Unterschied (D2). Der Block
`.adj-block` verschwindet aus dem Kommentarbereich; dieser enthält wieder nur
Beschriftung und Textfeld — plus den Knopf «Anpassung erfassen».

Die Reihenfolge im `<tbody>` ist damit: Positionszeile, Kommentarzeile
(`.expander-row`, `colSpan=4`), Anpassungszeile. Beide Zusatzzeilen hängen am
selben Aufklapp-Zustand.

**Die Stellen, und was dort schiefgehen kann:**

- `makeExpanderRow` / `renderRows` (ab Zeile 3345): neue Zeile bauen, `.adj-block`
  aus dem Panel entfernen.
- **Falle: die neue Zeile darf kein `data-row-id` tragen.** `$(`tr[data-row-id="…"]`)`
  steht an drei Stellen (3465, 3770, 5074) und nimmt den ersten Treffer. Ein
  zweiter Treffer pro Position wäre ein stiller Fehler. Darum `data-adj-for`.
- `zeilenIdVon` (3558) kennt nur `.expander-row` und `tr[data-row-id]`. Lernt sie
  die neue Zeile nicht, ist `bleibtInZeile` in `handleAdjInputBlur` immer falsch —
  **und das Datum fällt beim Wechsel zwischen den Anpassungsfeldern weg.** Genau
  der Fehler, den Commit `5b143b5` behoben hat. Ein Kerntest dazu existiert
  (`datumNachVerlassen`), er deckt diese DOM-Seite aber nicht ab.
- `refreshExpanderUI` (3429): `aufklapp.querySelector('.adj-ab')` und
  `.adj-datum-hinweis` (3475, 3481) zeigen ins alte Panel — neu suchen.
- `readAdjustmentFieldsFromDom` (3513) sucht global über `data-row-id` /
  `data-adj` und funktioniert unverändert weiter. Diese Attribute an den Inputs
  darum unbedingt behalten.
- Sichtbarkeit nach D1: `setRowExpanded` schaltet künftig **zwei** Zeilen statt
  einer. Die Anpassungszeile zeigt sich beim Aufklappen nur, wenn eine
  Anpassung besteht; sonst steht im Kommentarbereich der Knopf «Anpassung
  erfassen», der sie erzeugt und den Fokus in «Neu jährlich» setzt. Leer
  verlassen verschwindet sie wieder.
- CSS: `.has-adjustment`-Markierung (516–530) und der Punkt am Pfeil (503–514)
  werden überflüssig oder ändern die Bedeutung; `springeZuZeile` /
  `adj-sprung` (1920, 3768) muss die Anpassungszeile mit einblenden, sonst
  springt die Anpassungsliste ins Leere.
- Schmale Breite: `label-cell: 40 %` unter 768 px (Zeile 1102) — das Datumsfeld
  muss dort hineinpassen. Diese Prüfung steht ohnehin auf der Liste.
- Druck: `.adj-row` kommt zu den ausgeblendeten Zeilen. Ist Welle 1 erledigt,
  ist das eine Zeile CSS statt eines Regelwerks.

---

## Welle 3 — Punkte 5 + 4 ✔ erledigt am 2026-10-23

Commit `3b443e0`, 448 Tests grün, im Browser durchgespielt.

Anders als geplant: Nicht `stichtagListe` hat den Stand «alle» bekommen,
sondern `einloesbareEintraege` lässt «offen» immer zu. Der Unterschied ist
wichtig — ein zusätzlicher Stand hätte in der Zusammenfassung eine zweite
Zeile mit denselben Zahlen erzeugt, sobald jede Anpassung ein Datum trägt.

Dazugekommen: Die Grundlage steht im Dialog jetzt **über** der Liste (sie
bestimmt, was darunter steht), und das Häkchen «Übrige Kommentare
übernehmen» beginnt jedes Mal gesetzt.

### Was geplant war

### 3.1 Punkt 5: ein Weg, *alle* Anpassungen einzulösen

Der billigste Teil mit dem grössten Nutzen, und er lässt sich **echt testen**:
`stichtagListe` liegt im Rechenkern, den `tests/budget_treiber.mjs` in Node
ausführt.

Heute hängt `stichtagListe` den Stand «offen» nur an, wenn mindestens eine
Anpassung **ohne** Datum existiert. Neu: ein Stand «alle Anpassungen», sobald es
überhaupt eine Anpassung gibt — unabhängig davon, ob alle ein Datum haben. Die
Einstiege (`#addVersionBtn` und `neueVersionAusStand`) bleiben wie sie sind; der
Dialog ist schon einer, es fehlte nur dieser Stand.

### 3.2 Punkt 4: Kommentare im Dialog mitbearbeiten

Nach D3, also zwei Dinge in einem: je eingelöster Position ein kleines
Textfeld mit dem bisherigen Kommentar (bearbeitbar), und **eine** Checkbox
«Übrige Kommentare übernehmen» für alle anderen.

Betrifft `createVersion` (Zeile ~3184, `comments` werden heute bewusst nicht
kopiert — der Kommentar dort nachziehen), das Füllen der Einlöse-Liste und das
Auslesen der Häkchen. Dateiformat bleibt v5, es kommt kein Feld dazu.

Zu beachten: Der Dialog wird damit höher. `100vh` → `100dvh` aus Welle 1.3 ist
dann keine Kleinigkeit mehr, sondern Voraussetzung.

---

## Welle 4 — Punkte 7, 8, 9: parallel entwerfen, seriell einbauen

Zwei Sessions, die **nur `specs/`** schreiben und nicht `docs/`. Jede liefert
einen Entwurf, der die offenen Fragen beantwortet; der Einbau geschieht danach
hier, eine Welle nach der anderen.

**Session A — Punkt 7: mitlaufende Anleitung.** Zu beantworten: Was geschieht
auf einem zu schmalen Bildschirm (ausdrücklich mitgefragt)? Wie verträgt sich
ein weiterer klebender Block mit `.sticky-head`, die schon Werkzeug- und
Versionsleiste trägt, und mit `springeZuZeile`, das mit ihrer Höhe rechnet?
Inhaltlich erweitert um den Ablauf mit den Anpassungen. `.info-box` ist im Druck
ausgeblendet und bleibt es.

**Session B — Punkte 8 + 9: grafische Übersicht und Versionsvergleich.** Beide
betreffen dieselbe Fläche und brauchen dasselbe Werkzeug, darum ein Entwurf.
**Harte Randbedingung, die im Entwurf oben stehen muss:** die Seite läuft per
`file://` ohne Server und ohne Internet, das CSS bleibt eingebettet — keine
Diagrammbibliothek von einem CDN, also handgeschriebenes SVG oder CSS. Zu
entscheiden: Diagrammart, Anzahl Diagramme, nur die Gesamtzahl oder auch die
Kategorien, und welche Versionen der Vergleich auswählbar macht.

#### Es gibt schon einen Versionsvergleich — Punkt 9 ist eine Ergänzung, kein Neubau

Beim Nachsehen aufgefallen und für den Entwurf wichtig: Die Seite hat bereits
einen Abschnitt **«Versionsvergleich»** (`#versionsOverviewSection`, Zeile
2316), der nur im Mehr-Versionen-Betrieb sichtbar ist. Er enthält

- eine Tabelle aller Versionen mit Basis, Einnahmen/Jahr, Ausgaben/Jahr,
  Differenz/Jahr und **Δ gegenüber der Basis**, die aktive hervorgehoben,
- darunter «Unterschiede pro Position» (`#versionsDetailBlock`) gegenüber der
  Basis der aktiven Version.

Was Punkt 9 dem hinzufügt, ist damit genau benennbar: **frei wählbare**
Versionen statt immer «gegen die eigene Basis», und ein **Einstieg** dort, wo
der Benutzer ihn erwartet — ein Knopf rechts neben der letzten Version, statt
eines Abschnitts weit unten, den man erst im Mehr-Versionen-Betrieb überhaupt
sieht. Der Entwurf soll prüfen, ob der bestehende Abschnitt umgebaut oder der
Knopf nur dorthin springen soll; eine zweite Vergleichsansicht neben der
bestehenden darf nicht entstehen.

#### Zwei Rückfragen des Benutzers zur Bibliothek (2026-10-22)

**«Kann man den Import einer Bibliothek mit einer IF-Abfrage umgehen — eine
lokale Fassung ohne Diagramme, eine Online-Fassung mit?»**

Technisch geht das: `if (location.protocol !== 'file:')` und das `<script>` erst
dann in den `<head>` hängen, danach nur zeichnen, wenn die Bibliothek wirklich
da ist (`typeof Chart !== 'undefined'`). Vier Gründe, es trotzdem nicht zu tun:

1. **Zwei Fassungen heissen zwei Verhalten**, die beide entworfen, gebaut und
   geprüft werden müssen — und die *schlechtere* bekäme gerade der, der die
   Datei herunterlädt und behält. Genau dafür ist die Budgetvorlage gemacht:
   eine Datei, zum Weitergeben.
2. **Die Rückfallebene muss ohnehin gebaut werden.** Ist sie gut, braucht es
   die Bibliothek nicht; ist sie schlecht, ist die lokale Fassung schlecht. Die
   Arbeit fällt also in jedem Fall an, die Bibliothek kommt obendrauf.
3. **Ein CDN sieht mit.** Jeder Aufruf der Seite meldet dem CDN, dass jemand
   sein Budget ansieht. Dasselbe Argument steht in `CLAUDE.md` schon bei den
   Händler-Symbolen der Skillsliste («Die Symbole werden nie vom Händler
   geladen»).
4. **Für Balken und Linien reichen rund hundert Zeilen SVG.** Eine Bibliothek
   zahlt sich erst bei Hover-Tooltips, Zoom und Animation aus — und nichts
   davon steht in Punkt 8 oder 9.

**«Kann man die Bibliothek auf einer GitHub Page verwenden?»**

Ja, auf drei Wegen:

- **(a) Vom CDN.** Läuft auf der Page, braucht Internet beim Ansehen, Nachteil 3
  oben.
- **(b) Mitgeliefert**, z. B. `docs/vendor/chart.min.js`, relativ eingebunden.
  Läuft auf der Page *und* per `file://` — aber nur, wenn jemand den ganzen
  Ordner herunterlädt. Wer bloss `budgetvorlage.html` speichert, hat keine
  Diagramme. Der Deploy veröffentlicht `docs/` vollständig, von dieser Seite
  wäre es kein Problem.
- **(c) Eingebettet**, die minifizierte Bibliothek direkt in die HTML-Datei —
  dasselbe Muster, mit dem `build.py` die Händler-Symbole als `data:`-URI in die
  Skillsliste legt. Eine Datei, offline, mit Diagrammen. Preis: rund 200 KB
  fremder Code in jeder weitergegebenen Datei, dazu der Lizenztext (Chart.js ist
  MIT, der Hinweis muss mitgehen).

**Empfehlung für den Entwurf:** handgeschriebenes SVG. Zeigt sich dort, dass
eine Bibliothek wirklich nötig ist, dann **(c) einbetten** — nicht (a), und
keine zwei Fassungen.

---

## Welle 5 — Prüfen, was noch nie ein Mensch gesehen hat

### Der Ausdruck ist jetzt gesehen (2026-10-22)

Der Benutzer hat gedruckt: 12 Seiten A4 aus `file://`, mit gesetztem Häkchen
«Kommentare drucken». Die Datei liegt als
`Budgetvorlage-Ausdruck-Anpassungen.pdf` im Projektordner und ist über
`.gitignore` **vom Repo ausgeschlossen** — sie enthält echte Zahlen, `docs/`
ist öffentlich.

Was das Blatt zeigt:

- **Punkt 1 ist bestätigt.** Die Anpassung druckt als vollständiges leeres
  Formular: Überschrift «ANPASSUNG DIESER POSITION», die Beschriftungen «Neu
  jährlich», «Neu monatlich», «Gilt ab (darf leer bleiben)» und drei gerahmte
  Felder (Seite 2). Bei einer Anpassung ohne Datum steht auf dem Papier sogar
  der Platzhalter **`tt.mm.jjjj`** (Seite 3). Das sieht aus wie ein
  Formular zum Ausfüllen, nicht wie eine Aussage.
- **Die Stand-Zeilen drucken — aber sie sehen aus wie erfasste Zahlen.** Auf
  Seite 11 stehen «ab 22.10.2026» und «mit allen Vorschlägen» in denselben
  roten Rahmen und derselben Zahlengrösse wie die erfasste Differenz darüber.
  Die Frage aus der Übergabe ist damit anders beantwortet als vermutet: **gut
  lesbar ja, unterscheidbar nein.** Nichts auf dem Blatt sagt, dass diese zwei
  Zeilen gerechnet sind. Das gehört in Welle 2 oder 4 behoben — eine
  Kennzeichnung je Stand-Zeile, nicht nur Farbe.
- **Eine Bildschirm-Erklärung steht mit auf dem Papier:** «Datum schon
  verstrichen, in ‹heute› nicht eingerechnet». Auf Papier erklärt sie einen
  Zustand, den niemand mehr ändern kann.
- **Weiterhin ungeprüft:** ob «Stand ab … — gerechnet, nicht erfasst» oben auf
  Seite 1 steht. Diese Kennzeichnung gehört zum Ausdruck **aus der Vorschau**;
  gedruckt wurde die normale Ansicht. Dafür braucht es einen zweiten Ausdruck
  bei aktiver Vorschau.
- **Rückenwind für Punkt 10:** Der Spaltenkopf «TOTAL / JAHR» bricht auf dem
  Blatt auf zwei Zeilen — für eine Spalte, die in jeder Position dieselbe Zahl
  zeigt wie «JÄHRLICH» daneben (Seiten 2 und 9 gut zu sehen).
- **Neue Beobachtung (Punkt 11):** Jedes Betragsfeld druckt seinen Rahmen mit.
  Rund 60 leere Kästchen lassen das Blatt wie ein Formular wirken, nicht wie
  eine Aufstellung — und weil vor jeder Gruppe umbrochen wird, stehen 12 Seiten
  mit viel Weissraum. Beides zusammen entscheidet, wie das Budget bei einer
  Stiftung ankommt. Kein Fehler, aber eine Frage, die sich erst auf Papier
  stellt.
- **Kein Fehler:** Die fehlenden Abstände in «Miete(inkl. Nebenkosten)» und
  «PERSON 2Kleider» stehen nur in der Textauswertung der PDF; auf dem Blatt
  sind die Abstände da.

### Was weiterhin offen ist
- **Schmale Breite:** Einnahmen-Zeilen mit dem neuen Pfeil, und die
  Anpassungszeile aus Welle 2.
- **Das Anpassungs-Panel** in der Kopfleiste mit vielen Einträgen auf schmalem
  Fenster.
- **jsdom-Gerüst für `docs/budgetvorlage.html`:** ein eigenes Vorhaben, kein
  Nebenbei — und der einzige strukturelle Vorbehalt gegen den heutigen Stand.
  Es nagelt fest, was heute an Textsuchen hängt: Schlüssel `rowId.period`,
  Klassennamen, Sichtbarkeitsschaltungen, das Füllen der Einlöse-Liste, das
  Auslesen der Häkchen. **Welle 2 ist genau der Umbau, der diese Lücke
  ausnutzen könnte** — wer das Gerüst will, baut es davor, nicht danach.

---

## Reihenfolge auf einen Blick

| Welle | Inhalt | Aufwand | Braucht |
|---|---|---|---|
| 0 | Vier Entscheide | erledigt | D1, D3, D4 entschieden; D2 offen |
| 1 | Punkt 1, Punkt 6, vier Kleinigkeiten | ~1 h | nichts |
| 2 | Punkte 2 + 3 (Anpassung als Tabellenzeile) | ~halber Tag | D2 |
| 3 | Punkte 5 + 4 (Dialog) | ~halber Tag | nichts mehr |
| 4 | Punkte 7, 8, 9 — Entwürfe parallel, Einbau seriell | je ~halber Tag | Entwurf je Session |
| 5 | Ausdruck, schmale Breite, (jsdom) | offen | den Benutzer fürs Papier |

## Was dieser Plan bewusst auslässt

- **Escape wirkt in der Vorschau doppelt** — der Benutzer hat gesagt, damit kann
  er leben.
- **Pfeil-Klick hält das Datum nur in Chromium** (Safari und Firefox fokussieren
  Knöpfe beim Klick nicht). Mit Welle 2 wandert die Anpassung aus dem
  Aufklappbereich; danach stellt sich die Frage neu und ist vielleicht erledigt.
- **Nichts ist gepusht.** Der Branch liegt lokal, pro Welle ein oder mehrere
  Commits.
