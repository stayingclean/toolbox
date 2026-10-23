# Mitlaufende Anleitung in der Budgetvorlage

**Datum:** 2026-10-23
**Betrifft:** `docs/budgetvorlage.html` (eigenständige Seite, kein Generat)
**Punkt:** 7 aus `plans/2026-10-22-budget-offene-arbeiten.md`
**Mitlesen:** `specs/2026-10-21-budget-anpassungen-design.md` (Anpassungen),
`plans/2026-10-22-budget-abarbeitungsplan.md` (Welle 4)

## Ziel

> «Die Anleitung oben auf der Seite hilft dort nicht.» Gewünscht: mitlaufend, so
> dass die Angaben beim Erfassen sichtbar bleiben — und inhaltlich erweitert um
> den Ablauf mit den Anpassungen (warum, was und weshalb eingetragen wird).
> Ausdrücklich mitgefragt: **Was geschieht auf einem zu schmalen Bildschirm?**

Der Befund stimmt. Der Kasten `.info-box` steht als erstes Element in `<main>`
(Zeilen 2150–2156) und ist nach dem ersten Scrollen weg. Gelesen wird er also
genau dann, wenn man noch nichts tut; gebraucht wird er, während man in der
Zeile «Krankenkasse» steht — 2000 Zeilen Formular weiter unten.

Dazu kommt ein inhaltlicher Rückstand: Der Absatz über die Anpassungen
(Zeile 2153) wurde beim Umbau von gestern nur notdürftig nachgezogen. Er nennt
den Weg («Pfeil, + Anpassung erfassen») und die Darstellung, aber kein Wort
dazu, **warum** man eine Anpassung erfasst statt den Betrag zu überschreiben,
und **weshalb** das Datum den Unterschied macht. Genau das ist der Teil, den
eine Fachperson im Gespräch erklären muss.

## Was heute dasteht

| Stelle | Zeilen | Inhalt |
|---|---|---|
| `.info-box` CSS | 922–950 | Kasten mit linkem Balken, `margin-bottom: 2rem` |
| `.info-box` Markup | 2150–2156 | `<h2>` plus vier `<p>` |
| Druck | 1212–1214 | `.sticky-head, .toolbar, .footer, .info-box, …{display:none!important}` |
| `.sticky-head` CSS | 148–159 | `position: sticky; top: 0; z-index: 90` |
| `.sticky-head` Markup | 2053–2146 | Werkzeugleiste, Versionsleiste, Vorschau-Leiste |
| `springeZuZeile` | 4035–4052 | zieht `kopf.offsetHeight` vom Scrollziel ab (4041) |
| `.adj-wrap` / `.adj-panel` | 1888–1934, 2113–2117 | das bereits bewährte Überlagerungs-Panel |
| Panel-Verdrahtung | 5455–5470 | Klick ausserhalb (`composedPath`), Escape |
| Test | `tests/test_budget.py:866` | liest `<div class="info-box">` und prüft zwei Wendungen |

Drei Dinge daraus sind für den Entwurf bindend:

1. **`.sticky-head` ist der einzige klebende Block der Seite.** Der Kommentar
   bei Zeile 148 sagt auch, warum: Zwei einzeln klebende Leisten mit je `top: 0`
   legten sich übereinander, «Öffnen» und «Speichern» waren nicht mehr
   klickbar. Ein weiterer klebender Block darf diesen Fehler nicht wiederholen.
2. **Zeile 4041 ist die einzige Stelle, die eine Höhe misst.** `offsetHeight`
   auf `.sticky-head`, zur Laufzeit, bei jedem Sprung neu. Alles, was **innerhalb**
   von `.sticky-head` liegt, zählt dort automatisch mit. Alles daneben zählt nicht
   mit — und das Sprungziel läge unter dem neuen Block.
3. **Der Druck ist versorgt, solange der Block drinnen liegt.** `.sticky-head`
   steht in derselben Verbergen-Liste wie `.info-box`. Ein Block in der
   Kopfleiste druckt also von selbst nicht mit, ohne eine neue Regel.

### Wie hoch die Kopfleiste heute ist

Aus dem CSS gerechnet, **nicht im Browser gemessen** (auf diesem Rechner ist
kein Chrome installiert, siehe «Offen aus den Prüfungen» im Arbeitsplan):

- **Breit:** Werkzeugleiste ≈ 57 px (`padding: .75rem` doppelt, `.status`
  `min-height: 32px`, 1 px Rahmen) plus Versionsleiste ≈ 47 px
  (`padding: .55rem` doppelt) — zusammen **gut 100 px**.
- **Schmal (375 px):** beide Leisten haben `flex-wrap: wrap` (Zeilen 177, 1396).
  Die Werkzeugleiste bricht in Status plus drei bis vier Knopfzeilen um, die
  Versionsleiste in zwei bis drei. Zusammen **gegen 250 px und mehr** — also
  rund 40 % eines 600 px hohen Fensters, bevor überhaupt eine Tabellenzeile
  sichtbar ist.

Das ist der harte Rahmen für die ganze Frage. Auf dem Telefon ist kein Platz für
eine weitere dauerhaft klebende Zeile; auf dem Bildschirm ist genug Platz für
eine, aber nicht für vier.

## Varianten

### A — Klebender Hinweisstreifen in `.sticky-head`, Volltext als Überlagerung

Eine dritte, einzeilige Leiste als letztes Kind von `.sticky-head` (vor
Zeile 2146). Sie trägt die zwei Sätze, die man **beim Tippen** braucht, und
einen Knopf «Anleitung». Der Knopf öffnet ein Panel mit dem vollen Text, das
sich — wie `.adj-panel` — **über** den Seiteninhalt legt statt ihn zu schieben.

- **Höhe:** +1 Zeile (≈ 34 px) dauerhaft; der offene Volltext kostet **nichts**,
  weil er überlagert. `kopf.offsetHeight` ändert sich beim Auf- und Zuklappen
  darum nicht.
- **Ort:** innerhalb von `.sticky-head` — Zeile 4041 stimmt von selbst, der
  Druck auch.
- **Muster:** `.adj-panel` gibt es schon, samt Klick-ausserhalb über
  `composedPath` (5457–5463) und Escape (5464–5470). Nichts davon ist neu zu
  erfinden.
- **Gegen:** Die Seite hat dann drei klebende Leisten. Auf schmalem Schirm muss
  der Streifen seinen Text abgeben (siehe unten) — dort bleibt nur der Knopf.

### B — Schwebender Helfer unten rechts

Ein runder Knopf wie der Toast (fixiert, `bottom: 1.5rem; right: 1.5rem`),
der ein Panel aufklappt.

- **Für:** kostet keine Kopfhöhe, rührt Zeile 4041 nicht an, funktioniert auf
  jeder Breite gleich.
- **Gegen:** Der Benutzer hat «die Angaben bleiben sichtbar» verlangt, nicht
  «erreichbar». Ein zugeklappter Knopf zeigt nichts. Dazu kollidiert die Ecke
  mit dem Toast (`z-index: 200`, Zeile 1139 ff.) — beim Speichern läge die
  Meldung auf dem Knopf. Und ein frei schwebender Knopf über einem Formular ist
  auf dem Telefon genau dort, wo der Daumen tippt.

### C — Hinweise an den Spaltenköpfen

`<thead>` je Tabelle klebend machen und die Spaltenregel («jährlich **oder**
monatlich») dort hinschreiben.

- **Für:** Die Angabe steht genau dort, wo sie gilt, und kostet keine eigene
  Zeile.
- **Gegen:** Ein klebendes `thead` braucht `top: <Höhe der Kopfleiste>` — also
  genau die Zahl, die heute nur `springeZuZeile` zur Laufzeit misst. Diese Höhe
  wäre ab dann in CSS **und** in JS nötig und müsste bei jedem Umbruch der
  Werkzeugleiste neu gesetzt werden (`ResizeObserver` oder Scroll-Handler). Das
  ist der Preis, den der Kommentar bei Zeile 148 gerade vermeidet. Ausserdem
  passt der Ablauf der Anpassung (vier Schritte) in keinen Spaltenkopf — C kann
  höchstens die halbe Frage beantworten.

### D — Hinweis an der Stelle des Geschehens (Ergänzung, keine Variante)

Ein kurzer Satz im Kommentarbereich, direkt neben «+ Anpassung erfassen»
(`makeCommentRow`, 3551–3566). Er ist genau dann auf dem Schirm, wenn jemand
eine Anpassung beginnt — unabhängig von jeder Kopfleiste und von jeder
Fensterbreite.

- **Für:** billig, immer am richtigen Ort, trägt auf dem Telefon die Last,
  die der Streifen dort nicht tragen kann.
- **Gegen:** erklärt nur die Anpassung, nicht die Spaltenregel; und er darf
  nicht mitdrucken (eine neue Regel in der Druckliste, oder er steht im
  bereits nicht druckenden Teil).

## Empfehlung

> **Überholt durch «Nachtrag 2: Wohin der Knopf gehört» weiter unten.** A wurde
> gebaut und dann verworfen: der Streifen macht die Kopfleiste zu gross. Was
> hier steht, bleibt als Begründung stehen, warum C und B ausfielen — die gilt
> weiter.

**A als Träger, D als Ergänzung.** C fällt wegen der Höhen-Rechnung weg, B
wegen «sichtbar statt erreichbar».

Konkret:

1. **Ein Streifen `.hilfe-leiste`** als letztes Kind von `.sticky-head`, mit
   dem Kurztext und dem Knopf `#hilfeBtn` («Anleitung», `aria-expanded`).
2. **Ein Panel `#hilfePanel`** im Muster von `.adj-panel`: `position: absolute`
   unter dem Streifen, `max-height: min(60vh, 32rem)`, `overflow-y: auto`,
   Schatten, `hidden` als Grundzustand. Es **überlagert**, es schiebt nicht.
   Darin steht der Volltext.
3. **Der Volltext wohnt nur noch dort.** Der Kasten `.info-box` in `<main>`
   fällt weg; sein Inhalt wandert ins Panel und behält die Klasse
   `info-box` als innere Hülle — so bleibt das CSS (922–950) gültig, die
   Druckregel braucht keine Änderung, und `tests/test_budget.py:866` findet
   weiterhin `<div class="info-box">`. Zwei Fassungen desselben Textes an zwei
   Orten wären der Fehler, den dieses Projekt schon bei den Aufgabenlisten
   gemacht hat.
4. **In der Vorschau ist der Streifen weg** (`body.mode-preview .hilfe-leiste
   { display: none }`, wie `.adj-add-btn` bei Zeile 664). Dort wird nichts
   erfasst, also braucht es keine Erfassungshilfe — und die Vorschau-Leiste
   bekommt die Höhe, die der Streifen abgibt. Das löst nebenbei den
   Escape-Streit: Panel und Vorschau können nicht gleichzeitig offen sein, der
   bekannte Doppeleffekt von Escape (Arbeitsplan, «Zurückgestellte
   Kleinigkeiten») wiederholt sich nicht.
5. **Der Hinweis aus D** als `<p class="adj-add-hinweis">` neben dem Knopf
   «+ Anpassung erfassen».

Nicht umgesetzt wird: ein gemerkter Auf/Zu-Zustand. `CLAUDE.md` schliesst
`localStorage` für diese Seite aus (der Benutzer speichert bewusst als Datei),
und in der Budget-Datei hat ein Oberflächen-Zustand nichts zu suchen — er wäre
im Dateiformat v6 das erste Feld, das nichts mit dem Haushalt zu tun hat. Das
Panel ist nach jedem Laden zu, der Streifen immer sichtbar.

## Antwort auf die schmale Breite

Die Frage ist berechtigt, und die ehrliche Antwort hat zwei Teile.

**Bis 768 px** (bestehender Umbruchpunkt, 1173): Der Streifen behält seine
Zeile, gibt aber Text ab. Zwei Sätze passen nicht in 375 px, ohne auf drei
Zeilen umzubrechen — und drei Zeilen Hilfe über einem Formular sind kein Dienst.
Darum trägt der Streifen zwei Texte im Markup:

```html
<p class="hilfe-text">
  <span class="hilfe-lang">…Langfassung…</span>
  <span class="hilfe-kurz">Jährlich oder monatlich – die andere Spalte rechnet sich.</span>
</p>
```

`display: none` schaltet zwischen ihnen, nicht JavaScript: `.hilfe-kurz` ist
breit verborgen, `.hilfe-lang` ab 768 px abwärts. Kein `text-overflow:
ellipsis`, denn ein abgeschnittener Hinweis ist schlechter als ein kurzer.

**Unter 560 px** (neuer Umbruchpunkt): Der Text fällt ganz weg, es bleibt der
Knopf — als rundes «?» ohne Beschriftung, der in die **Versionsleiste**
einrückt, statt eine eigene Zeile zu belegen. Die Kopfleiste wächst auf dem
Telefon damit um **null Pixel**.

Damit ist die Zusage dort schwächer: «immer sichtbar» wird zu «einen Tipp
entfernt». Das ist eine bewusste Entscheidung und keine Lücke. Der Grund steht
oben: Die Kopfleiste belegt auf 375 px schon gegen 250 px; eine weitere
dauerhafte Textzeile nähme dem Formular den Platz, den die Hilfe erklären soll.
Was auf dem Telefon den Dienst übernimmt, ist **D** — der Hinweis im
Kommentarbereich ist genau dann auf dem Schirm, wenn jemand eine Anpassung
beginnt, und braucht dafür keine klebende Zeile.

Das Panel wird auf schmaler Breite eine Vollbreiten-Lage, wörtlich nach dem
Muster von `.adj-panel` bei 640 px (1937–1941):

```css
@media (max-width: 640px) {
    #hilfePanel { left: 0.75rem; right: 0.75rem; width: auto; max-width: none; }
}
```

Dazu, weil die Kopfleiste dort selbst schon hoch ist: `max-height:
calc(100dvh - 12rem)` statt `60vh`, mit `dvh` aus demselben Grund wie beim
Modal (Zeile 1101) — die einfahrende Adressleiste macht `vh` zu einer
Lüge. Bleibt zu wenig übrig, scrollt das Panel in sich; die Seite darunter
bleibt stehen.

**Noch zu prüfen, sobald ein Browser zur Hand ist** (dieselbe Liste wie im
Arbeitsplan): ob der Knopf in der Versionsleiste bei 320 px noch neben «Neue
Version» und «Vorschau» Platz findet, oder ob die Leiste dort auf eine weitere
Zeile umbricht — dann wäre nichts gewonnen und der Knopf gehörte stattdessen
neben den Titel in `.toolbar-actions`.

## Der Text

Ausformuliert, in der Sprache der Seite. Der Kurztext steht im Streifen, der
Rest im Panel.

### Streifen, breit (`.hilfe-lang`)

> Jährlich **oder** monatlich eintragen — die andere Spalte rechnet sich.
> Anpassung: Zeile mit dem Pfeil aufklappen, dann «+ Anpassung erfassen».

### Streifen, schmal (`.hilfe-kurz`)

> Jährlich oder monatlich — die andere Spalte rechnet sich.

### Panel (`#hilfePanel`, innen `.info-box`)

> ## So füllen Sie die Vorlage aus
>
> **Beträge**
> Tragen Sie jeden Betrag entweder in die **Jahres-** oder in die
> **Monatsspalte** ein — die andere Spalte rechnet sich daraus (Jahresbetrag
> ÷ 12 bzw. Monatsbetrag × 12). Subtotale und Gesamtsummen folgen automatisch.
> Beträge in **CHF**, Dezimalstellen mit Komma oder Punkt.
>
> **Anpassungen — was dort hineingehört**
> Eine Anpassung ist der Betrag, den eine Position **künftig** haben soll, nicht
> der, den sie heute hat. Die erfassten Zahlen bleiben darum stehen; daneben
> steht, was möglich wäre. So sieht man im Gespräch, was ein Vorschlag bringt,
> ohne dass die Aufnahme des heutigen Haushalts überschrieben wird.
>
> **Anpassungen — wie Sie eine erfassen**
> 1. Zeile mit dem **Pfeil** am Anfang aufklappen. Darunter erscheint das Feld
>    für den Kommentar.
> 2. Dort auf **«+ Anpassung erfassen»** klicken.
> 3. Die Anpassung steht nun als eigene Zeile direkt unter dem Kommentar,
>    spaltengleich zu den Beträgen: links das Datum, daneben der neue Jahres-
>    oder Monatsbetrag, rechts der Unterschied zum erfassten Wert.
> 4. Ohne Betrag gibt es keine Anpassung. Das Datum lässt sich erst setzen,
>    wenn ein neuer Betrag dasteht, und eine Zeile ohne Betrag verschwindet
>    wieder, sobald Sie sie verlassen.
>
> **Anpassungen — weshalb das Datum**
> **Mit** Datum heisst: steht fest, wirkt ab dann — ein gekündigtes Abo läuft
> bis zum Ende der Frist weiter. **Ohne** Datum heisst: noch offen, ein
> Vorschlag, über den niemand entschieden hat. Die Zusammenfassung unten zeigt
> darum für jeden Stichtag einen eigenen Stand, zuletzt den Stand **mit allen
> Vorschlägen**. «Vorschau» in der Versionsleiste zeigt dasselbe für das ganze
> Budget — gerechnet, nicht erfasst; dort wird nichts geschrieben.
>
> Anpassungen werden **nie gedruckt**. Sie sind das Feld zum Erfassen; auf
> Papier gehört der Stand, nicht das Formular.
>
> **Weitere Budget-Version**
> Eine weitere Version brauchen Sie für einen **grundsätzlich anderen
> Haushalt** — nach einem Umzug, nach einer Trennung. Über «Neue Version»
> übernehmen Sie die Werte einer bestehenden Version, auf Wunsch samt den
> Anpassungen, die bis zu einem Stichtag fällig sind; die Kommentare lassen
> sich im selben Dialog gleich anpassen. «Versionsvergleich» unten zeigt die
> Differenzen auf einen Blick.

Was gegenüber heute dazukommt, ist der ganze Mittelteil: «was dort
hineingehört» (das Warum), die vier Schritte (das Was) und «weshalb das Datum»
(das Weshalb). Der heutige Absatz 2153 presst das in drei Sätze und lässt den
Grund weg.

Zwei Wendungen sind **nicht** frei wählbar: `tests/test_budget.py:866` prüft
auf «direkt in der Zeile» und «grundsätzlich anderen Haushalt» in den ersten
2500 Zeichen nach `<div class="info-box">`. Die zweite steht oben. Die erste
fehlt im neuen Text — er sagt es ausführlicher. Entweder nimmt Schritt 3 die
Wendung auf («Die Anpassung steht direkt in der Zeile, …»), oder der Test wird
mitgeändert. **Empfohlen:** den Test mitändern und auf die neuen Wendungen
prüfen («künftig haben soll», «Mit Datum», «nie gedruckt») — er soll den Inhalt
festnageln, nicht eine Formulierung.

### Hinweis bei «+ Anpassung erfassen» (D)

> Neuer Betrag für eine weitere Version — die erfasste Zahl bleibt stehen.

## Einbaustellen in `docs/budgetvorlage.html`

Zeilennummern nach dem heutigen Stand (Commit `5c8468c`).

| Zeilen | Was zu tun ist |
|---|---|
| 148–159 | Beim Kommentar zu `.sticky-head` festhalten, dass jetzt **drei** Leisten darin liegen und warum keine davon einzeln klebt. |
| 922–950 | `.info-box` bleibt als Klasse; `margin-bottom: 2rem` fällt weg (steht im Panel, nicht in `<main>`), `font-size` evtl. auf 0.92rem. |
| **neu, nach 950** | `.hilfe-leiste`, `.hilfe-text`, `.hilfe-lang`, `.hilfe-kurz`, `#hilfeBtn`, `#hilfePanel` — Panel nach dem Muster von `.adj-panel` (1918–1934). |
| 1173–1199 | im 768-px-Block: `.hilfe-lang {display:none}`, `.hilfe-kurz {display:inline}`. |
| **neu, bei 1199** | neuer Block `@media (max-width: 560px)`: `.hilfe-text {display:none}`, Knopf als rundes «?» in der Versionsleiste. |
| 1212–1214 | **nichts ändern.** `.sticky-head` und `.info-box` stehen beide schon in der Verbergen-Liste; der Streifen druckt dadurch von selbst nicht mit. Gegenprüfen, nicht umschreiben. |
| 1937–1941 | Vorbild für den 640-px-Block des Panels; dort oder daneben die Regel für `#hilfePanel` ergänzen. |
| 664 | Vorbild für `body.mode-preview .hilfe-leiste { display: none }`. |
| 2146 | **Einfügestelle:** Streifen und Panel als letztes Kind von `.sticky-head`, direkt vor `</div><!-- /sticky-head -->`. |
| 2150–2156 | Der Kasten `.info-box` verschwindet aus `<main>`; sein Inhalt (neu gefasst, siehe oben) wandert ins Panel. |
| 3551–3566 | in `makeCommentRow` den Hinweis aus D neben `.adj-add-btn` einhängen; er darf nicht drucken. |
| 4035–4052 | `springeZuZeile`: beim Sprung auch das Hilfe-Panel schliessen (neben `closeAdjustmentsPanel()`, 4036) — sonst liegt die Überlagerung genau über der Zeile, zu der gesprungen wurde. **Zeile 4041 bleibt unverändert**: der Streifen liegt in `.sticky-head`, `offsetHeight` zählt ihn mit. |
| 5455–5470 | Vorbild für die Verdrahtung: Knopf schaltet um, Klick ausserhalb über `composedPath`, Escape schliesst und gibt den Fokus an den Knopf zurück. |
| 5489–5499 | Prüfen, nicht ändern: Die Escape-Weiche der Vorschau braucht keinen Zweig für das Hilfe-Panel, **solange** der Streifen in der Vorschau verborgen ist und das Panel beim Betreten der Vorschau geschlossen wird. Beides gehört zum Einbau. |
| 4104, 4140 | dort schaltet die Vorschau die Felder; dieselbe Stelle schliesst das Hilfe-Panel beim Betreten. |
| `tests/test_budget.py:866` | Test auf die neuen Wendungen umstellen (siehe oben) und einen zweiten dazu: der Streifen liegt **innerhalb** von `.sticky-head`. |

## Nachtrag 2026-10-23: nachgemessen und eingebaut

Der Einbau ist erfolgt; drei Dinge sind dabei anders gekommen als hier
entworfen, alle drei aus gemessenen Zahlen heraus.

**Der Knopf steht nicht im Streifen, sondern in der Versionsleiste**, bei
«Anpassungen» und «Vorschau». Nur so kann der Streifen unter 560 px ersatzlos
verschwinden, ohne den Zugang zur Anleitung mitzunehmen — der Entwurf wollte
den Knopf dort erst unterhalb der Grenze einrücken, was zwei Orte für dasselbe
Bedienelement bedeutet hätte. Der Streifen trägt jetzt nur noch den Text.

**Der Langtext weicht schon bei 960 px, nicht erst bei 768 px.** Gemessen: Bei
900 px bricht er auf zwei Zeilen um (46 px statt 28 px). Zwei Zeilen Hilfe über
einem Formular sind kein Dienst, also gilt die Kurzfassung ab 960 px abwärts.

**Die Versionsleiste musste mit.** Beim Messen kam heraus, dass
`.version-tabs` mit `min-width: 0` unter die Breite eines Reiters schrumpft:
Der Reiter «Hauptversion» lief aus seinem Kasten heraus und lag auf 375 px über
dem Knopf «Neue Version» — ein Fehler, der vor dieser Arbeit schon da war und
den der neue Knopf nur sichtbar gemacht hat. Jetzt gilt `min-width:
fit-content`; damit die Leiste deswegen nicht umbricht, zeigen «Neue Version»
unter 560 px nur noch das Pluszeichen und das Wort «Versionen:» gar nichts
(beides bleibt in `aria-label` und `title`).

**Die Höhen, jetzt gemessen statt gerechnet** (Kopfleiste gesamt):

| Breite | vorher | nachher |
|---|---|---|
| 1200 px | 160 px | 188 px |
| 560 px | 175 px | 203 px |
| 375 px | 277 px | **277 px** |

Auf dem Telefon kostet die Anleitung damit **null Pixel** — die Zusage des
Entwurfs hält, und die überlappende Schrift in der Versionsleiste ist
nebenbei weg. Breit kostet der Streifen 28 px.

**Geprüft wurde ausserdem:** Das Panel ändert die Höhe der Kopfleiste beim
Auf- und Zuklappen nicht (188 px in beiden Zuständen), Escape und Klick
ausserhalb schliessen es, der Sprung aus der Anpassungsliste schliesst es, und
in der Vorschau sind Streifen und Knopf weg.

## Nachtrag 2: Wohin der Knopf gehört (Rückmeldung 2026-10-23)

Die Rückmeldung nach dem Einbau: **Variante A fällt weg** — mit dem Streifen
wird die Kopfleiste zu gross. Gewünscht ist stattdessen **eine Hilfe für alle
Bildschirmbreiten**, mit dem Knopf entweder **oben rechts unter der
Kopfleiste** oder **unten links auf dem Bildschirm**.

### Erst gemessen: was der Streifen wirklich kostet

Gemessen im eingebauten Browser an der ausgelieferten Datei (`file://`),
Kopfleiste = `.sticky-head`, einmal wie heute und einmal mit verborgenem
Streifen:

| Fenster | Kopf heute | ohne Streifen | Streifen | Werkzeugleiste | Versionsleiste |
|---|---|---|---|---|---|
| 1185 × 800 | 188 px (24 %) | **159 px** | 29 px | 109 px | 50 px |
| 945 × 800 | 188 px | 159 px | 29 px | 109 px | 50 px |
| 753 × 800 | 232 px (29 %) | **203 px** | 29 px | 153 px | 50 px |
| 560 × 700 | 203 px | 203 px | 0 px | 153 px | 50 px |
| 375 × 667 | 233 px | 233 px | 0 px | 183 px | 50 px |

Drei Zahlen aus dieser Tabelle steuern alles Weitere:

1. **Der Streifen kostet 29 px von 188** — 15 %. Er wegzulassen bringt die
   Kopfleiste auf 159 px, nicht auf 100. Wer sie wirklich klein will, muss an
   die **Werkzeugleiste** (109 px breit, 183 px auf dem Telefon): zwei
   Druck-Häkchen und drei Knöpfe, die umbrechen. Das ist eine eigene Arbeit,
   nicht Punkt 7 — aber es ist der grössere Hebel.
2. **Der Knopf in der Versionsleiste kostet null.** Die Leiste ist 50 px hoch,
   mit und ohne ihn, auf jeder gemessenen Breite. Was teuer war, war nur der
   Streifen.
3. **Unter 560 px kostet der Streifen heute schon nichts** (dort verborgen).
   Die Rückmeldung betrifft also den breiten Schirm, und dort sitzt der Knopf
   schon heute an genau einer Stelle für alle Breiten.

Dazu die Seitenränder — wichtig für einen schwebenden Knopf. Abstand vom
Fensterrand bis zum Inhalt (`.section`, Seite ist 1100 px breit, zentriert):

| Fenster | Rand links/rechts | letzte Spalte «Total / Jahr» |
|---|---|---|
| 1425 px | 187 px | endet 220 px vor dem Rand |
| 1185 px | 67 px | endet 100 px vor dem Rand |
| 1009 px | 24 px | endet 57 px vor dem Rand |
| 375 px | 12 px | **ragt 103 px über den Rand hinaus** |

### Die drei Platzierungen im Vergleich

#### E — Streifen weg, Knopf bleibt, wo er ist (Versionsleiste)

Die Zeile `.hilfe-leiste` entfällt samt ihren zwei Texten; der Knopf
«Anleitung» bleibt in der Versionsleiste bei «Anpassungen» und «Vorschau»,
das Panel bleibt wie es ist.

- **Für:** Kopfleiste 159 px statt 188 px. Dieselbe Hilfe, derselbe Ort, dasselbe
  Verhalten auf **jeder** Breite — genau das, was gewünscht war. Kostet null
  zusätzliche Pixel (gemessen). Überlagert nie Inhalt, liegt nie im Daumenbereich,
  kollidiert mit nichts. Der Knopf läuft mit, weil die Versionsleiste klebt.
  Druck, Escape, Klick-ausserhalb, Vorschau und der Sprung aus der
  Anpassungsliste sind **bereits gebaut und geprüft** — es wird nur gelöscht,
  nichts erfunden. Kleinster Eingriff von allen dreien.
- **Gegen:** Der Knopf ist der vierte in einer Reihe («Versionen», Reiter,
  «Neue Version», «Anpassungen», «Anleitung», «Vorschau»). Wer Hilfe sucht,
  sucht sie dort vielleicht nicht — ein «?» am Bildschirmrand ist die
  bekanntere Geste. Und der immer sichtbare Satz ist weg (siehe unten).

#### F — Schwebend oben rechts, an der Unterkante der Kopfleiste

Ein rundes «?», das unter der Kopfleiste zu schweben scheint. **Mechanik, die
funktioniert:** `position: absolute; bottom: -1.2rem; right: 1rem` als Kind von
`.sticky-head`. Dann hängt er an deren Unterkante, wandert mit, wenn die
Werkzeugleiste umbricht, und zählt **nicht** in `offsetHeight` mit (ausserhalb
des Flusses) — `springeZuZeile` (Zeile 4041) bleibt unangetastet und die
Kopfleiste schrumpft auf 159 px.

- **Für:** Kopfleiste wie bei E (159 px), aber der Knopf ist frei und fällt auf.
  Gleiches Verhalten auf allen Breiten. Braucht **keine** gemessene Höhe —
  anders als ein `position: fixed; top: <Kopfhöhe>`, das dieselbe Zahl in CSS
  bräuchte, die heute nur `springeZuZeile` zur Laufzeit kennt (das ist der
  Grund, weshalb Variante C ausfiel). Er sitzt oben, also dort, wo das Auge
  nach einer Erklärung sucht, und das Panel klappt nach unten auf — wie heute.
- **Gegen:** Ab 1180 px abwärts liegt er **über** dem Inhalt: beim Rand von
  24 px (1009 px Fenster) genau über der Spalte «Total / Jahr», also über
  Zahlen. Nur ab etwa 1180 px passt er in den Seitenrand. Auf dem Telefon
  schwebt er über der Tabelle, die dort ohnehin schon seitlich überläuft. Er
  verdeckt beim Scrollen wechselnde Zeilen — und zwar immer dieselbe Stelle,
  was bei einem Formular heisst: irgendwann die Zeile, die man gerade braucht.
  Dazu neue Mechanik: ein Element, das aus `.sticky-head` herausragt, deren
  `z-index: 90` nach unten weitergibt.

#### G — Schwebend unten links, fixiert

`position: fixed; bottom: 1.5rem; left: 1.5rem`, das Gegenstück zum Toast.

- **Für:** Kostet keine Kopfhöhe, gleiche Lage auf allen Breiten, kollidiert
  **nicht** mit dem Toast (der sitzt unten rechts, `z-index: 200`). Bleibt beim
  seitlichen Scrollen stehen — auf dem Telefon, wo die Tabelle überläuft, ein
  echter Vorteil. Die bekannteste Geste von allen dreien.
- **Gegen (gemessen):** Am Seitenende bleiben unter dem Urheber-Credit nur
  **32 px**, und der Credit beginnt bei x = 24 px — ein Knopf im Band
  24…60 px **liegt auf dem Avatar und dem Link «Erstellt von stayingclean»**.
  Den `CLAUDE.md` verlangt auf jeder Seite, klickbar. Abhilfe: `padding-bottom`
  am Fuss oder den Knopf ausblenden, wenn der Fuss im Blick ist
  (`IntersectionObserver` — Maschinerie für eine Zierde). Weiter: unten links
  liegt über der Beschriftungsspalte, also über den Namen der Positionen; auf
  dem Telefon im Daumenbereich; und das Panel müsste nach **oben** aufklappen,
  was eine zweite Panel-Lage bedeutet (heute `top: calc(100% + 0.4rem)`).
  «Oben rechts unter der Kopfleiste» und «unten links» sind nicht gleich teuer.

### Alle Varianten nebeneinander

| | Kopfhöhe breit | gleich auf allen Breiten | immer sichtbarer Text | überlagert Inhalt | neue Mechanik | Aufwand |
|---|---|---|---|---|---|---|
| **A** (heute) | 188 px | nein (Text fällt bei 960/560) | ja, breit | nein | gebaut | gebaut |
| **B** unten rechts | 159 px | ja | nein | ja | Toast-Kollision | mittel |
| **C** Spaltenköpfe | 159 px | ja | ja, nur die Spaltenregel | nein | Kopfhöhe in CSS **und** JS | hoch |
| **D** im Kommentar | 159 px | ja | ja, nur beim Aufklappen | nein | gebaut | gebaut |
| **E** Versionsleiste | **159 px** | **ja** | nein | **nein** | **keine** | **löschen** |
| **F** oben rechts | 159 px | ja | nein | ab ~1180 px abwärts | ragt aus `.sticky-head` | klein |
| **G** unten links | 159 px | ja | nein | ja, plus Fuss | Panel nach oben, Fuss | mittel |

### Empfehlung

**E, und F nur, wenn der Knopf auffallen soll.** G nicht — die 32 px über dem
Urheber-Credit sind gemessen, und der Ausweg wäre ein `IntersectionObserver`
für eine Zierde.

Der Grund für E vor F: Beide bringen dieselben 159 px. E überlagert nichts und
besteht aus Löschen; F überlagert ab 1180 px abwärts Zahlen in der Tabelle und
bringt dafür Auffälligkeit. Ein Knopf, der über dem Betrag liegt, den man gerade
lesen will, ist in einem Formular teurer als einer, den man beim ersten Mal
suchen muss — zumal er in der Versionsleiste **neben** den beiden Knöpfen steht,
die man ohnehin benutzt.

Wird F doch gewählt, dann mit `right: max(1rem, calc((100vw - 1100px) / 2 -
3rem))`: So sitzt er auf breiten Schirmen im Seitenrand und rückt erst heran,
wenn keiner mehr da ist. Das Überlagern bleibt schmal, verschwindet aber nicht.

### Was dabei aufgegeben wird — und was es ersetzt

Mit dem Streifen fällt der **immer sichtbare Satz** weg, auf jeder Breite. Die
Zusage aus Punkt 7 («die Angaben bleiben sichtbar») wird damit überall zu
«einen Klick entfernt» — vorher galt das nur unter 560 px. Das ist die
bewusste Gegenleistung für 29 px und für eine Oberfläche, die auf jeder Breite
gleich aussieht.

Zwei Dinge tragen diesen Verlust:

- **D ist schon eingebaut** — «Neuer Betrag für eine weitere Version – die
  erfasste Zahl bleibt stehen» steht neben «+ Anpassung erfassen» und erscheint
  genau dann, wenn jemand eine Anpassung beginnt.
- **Die Spaltenregel liesse sich in die Spaltenköpfe holen** (C in klein, ohne
  klebendes `thead`): aus `<th>Jährlich</th>` wird `<th>Jährlich <span
  class="th-hint">oder monatlich</span></th>`, einmal je Tabelle. Kostet keine
  Kopfhöhe, steht genau über der Spalte, die sie erklärt, und braucht keine
  gemessene Höhe. Das ist der einzige Satz des Streifens, der wirklich
  dauerhaft sichtbar sein muss — empfohlen als Zugabe zu E.

### Einbaustellen für E

Zeilennummern nach Commit `e99d958` (Stand mit eingebautem Streifen).

| Zeilen | Was zu tun ist |
|---|---|
| 983–1002 | `.hilfe-leiste` und `.hilfe-text` löschen; `.hilfe-wrap`, `.hilfe-btn`, `#hilfePanel` bleiben. |
| 1004 | `.hilfe-kurz { display: none }` löschen. |
| 1055–1057 | `body.mode-preview`: nur noch `.hilfe-wrap` verbergen. |
| 1314 | im 768-px-Block die `.hilfe-leiste`-Polsterung löschen. |
| 1317–1324 | der ganze 960-px-Block entfällt (er schaltete nur Lang auf Kurz). |
| 1336–1340 | im 560-px-Block `.hilfe-leiste { display: none }` löschen. Der Rest des Blocks bleibt: rundes «?», «Neue Version» ohne Wort, `.version-bar-label` verborgen — das sind Korrekturen an der Versionsleiste, nicht am Streifen. |
| 2355–2367 | Streifen-Markup samt Kommentar löschen (er ist das letzte Kind von `.sticky-head`). |
| 1212 ff. | Druckliste: nichts zu tun, `.sticky-head` deckt alles ab. |
| — | **Nicht anfassen:** `.hilfe-btn` in der Versionsleiste (2293–2298), `#hilfePanel` (2299 ff.), `toggleHilfePanel`/`closeHilfePanel` (4247–4259), die Verdrahtung (5714–5726), der Aufruf in `springeZuZeile` und beim Betreten der Vorschau. |
| `tests/test_budget.py` | den Test, der den Streifen in `.sticky-head` nachweist, auf den Knopf umstellen (der Knopf, nicht der Streifen, ist ab jetzt die Zusage). |

Für F zusätzlich: `.hilfe-wrap` aus der Versionsleiste (2293) nach `.sticky-head`
verschieben, dort `position: absolute; bottom: -1.2rem; right: …`, und
`.sticky-head` einen eigenen `z-index`-Kontext lassen (sie hat ihn bei
Zeile 155 schon).

### Nebenfund, nicht aus dieser Arbeit

Auf 375 px ist die Seite **seitlich scrollbar**: `scrollWidth` 546 px bei
375 px Fensterbreite, die Budget-Tabelle ist 445 px breit und läuft aus ihrer
Sektion heraus (die letzte Spalte endet 103 px hinter dem rechten Rand). Das
hat mit der Anleitung nichts zu tun und ist älter als sie, trifft aber jede
Überlegung zu einem schwebenden Knopf auf dem Telefon. Gehört als eigener Punkt
in `plans/2026-10-22-budget-offene-arbeiten.md`.

## Nachtrag 3: entschieden und gebaut (2026-10-23)

Das Missverständnis ist aufgelöst: Was gestört hat, war **der Text in der
Kopfleiste**, nicht der Zugang zur Anleitung. Ein «?» allein, ganz rechts
aussen, ist in Ordnung. Gebaut ist damit **E mit dem Knopf am äusseren Rand**:

- **Der Streifen ist weg** — CSS, Medienblöcke und Markup. An seiner Stelle
  steht ein Kommentar, der sagt, was dort stand und warum es nicht mehr steht.
- **Der Knopf ist auf jeder Breite dasselbe runde «?»** (1,8 rem), nicht mehr
  «Anleitung» breit und «?» schmal. `aria-label` und `title` tragen den Namen.
- **Er steht als Letztes in der Versionsleiste**, hinter «Vorschau», mit
  `margin-left: auto` am äusseren Rand. Dafür wanderte der Vorschau-Knopf im
  Markup vor den Hilfe-Knopf — damit Tab-Reihenfolge und Augenreihenfolge
  gleich bleiben (ein `order:` im CSS hätte sie auseinandergebracht).
- **Was dauernd sichtbar sein muss, steht jetzt im `title` der Felder selbst**
  — der Vorschlag des Benutzers, und er ist besser als der Streifen: der
  Hinweis erscheint dort, wo er gilt, und kostet null Pixel.

| Stelle | Tooltip |
|---|---|
| Betragsfeld (jährlich/monatlich) | «Jährlich oder monatlich eintragen – die andere Spalte rechnet sich.» |
| Pfeil der Zeile | «Aufklappen: Kommentar zu dieser Position, und ‹+ Anpassung erfassen› für einen künftigen Betrag» |
| Kommentarfeld | «Gilt nur für diese Budget-Version. Druckt mit, solange oben ‹Kommentare drucken› angehakt ist.» |
| Anpassungs-Betrag | «Betrag, den diese Position künftig haben soll – die erfasste Zahl oben bleibt stehen. Rechts steht der Unterschied. Druckt nie mit.» |
| Anpassungs-Datum | unverändert (`anpassungDatumHinweis`) |

Der Satz neben «+ Anpassung erfassen» (`.adj-add-hinweis`) bleibt sichtbar
stehen — ein Tooltip erscheint erst beim Zeigen, und genau dort lohnt der
Unterschied.

**Gemessen nach dem Umbau** (eingebauter Browser, `file://`, Kopfleiste =
`.sticky-head`):

| Fenster | vorher (mit Streifen) | jetzt | Versionsleiste |
|---|---|---|---|
| 1185 px | 188 px | **159 px** | 50 px |
| 753 px | 232 px | **203 px** | 50 px |
| 560 px | 203 px | 203 px | 50 px |
| 375 px | 233 px | 233 px | 50 px |
| 320 px | — | 263 px | 50 px |

Die Versionsleiste bleibt auf **jeder** dieser Breiten 50 px hoch: der Knopf
bricht nirgends auf eine zweite Zeile um, obwohl `margin-left: auto` ihn an den
Rand schiebt (eine Auto-Marge verbraucht nur freien Platz, sie erzwingt keinen
Umbruch).

**Ebenfalls geprüft:** Das Panel ändert die Kopfhöhe beim Auf- und Zuklappen
nicht (159 px in beiden Zuständen), öffnet 576 × 480 px mit 24 px Abstand zum
rechten Rand, schliesst auf Escape und auf Klick ausserhalb; auf 375 px wird es
351 px breit mit 12 px Rand und scrollt in sich; in der Vorschau ist der Knopf
weg; die vier Tooltips stehen an ihren Feldern. `pytest tests`: 456 grün (drei
Tests umgestellt, einer neu für die Tooltips).

**Was damit endgültig aufgegeben ist:** der dauerhaft sichtbare Satz über der
Tabelle. Er lebt jetzt in den Tooltips und — sichtbar, ohne Zeigen — im Satz
neben «+ Anpassung erfassen». Die Spaltenregel in die Spaltenköpfe zu holen,
ist damit nicht mehr nötig; wer sie doch will, findet den Vorschlag in
Nachtrag 2.

## Was dieser Entwurf offen lässt

- ~~**Die Höhen sind gerechnet, nicht gemessen.**~~ Erledigt, siehe Nachtrag.
- ~~**Die Stelle des «?»-Knopfs unter 560 px.**~~ Entschieden: Versionsleiste,
  und zwar auf jeder Breite.
- ~~**Die Wahl zwischen E und F.**~~ Entschieden: E mit dem Knopf am äusseren
  Rand, dazu Tooltips an den Feldern. Siehe Nachtrag 3.
- ~~**Ob die Spaltenregel in die Spaltenköpfe wandert.**~~ Nicht nötig, sie
  steht im `title` der Betragsfelder.
- **Der echte Ausdruck** ist weiterhin von keinem Menschen gesehen (gleiche
  Lücke wie im Arbeitsplan). Am Druck ändert dieser Umbau nichts:
  `.sticky-head` war und bleibt in der Verbergen-Liste.
- **Punkt 10** (die vierte Spalte «Total / Jahr») kann die Spaltenregel im
  Kurztext noch ändern. Fällt die Spalte, bleibt der Satz trotzdem richtig.
- **Der seitliche Überlauf auf 375 px** (Nebenfund in Nachtrag 2) ist nicht
  Teil von Punkt 7.
- **Die Anleitung bleibt eine Anleitung.** Kein geführter erster Durchlauf,
  keine Markierungen am Formular, kein «Schritt 1 von 4». Das war nicht
  gefragt, und es wäre ein eigenes Vorhaben.
