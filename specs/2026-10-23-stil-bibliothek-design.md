# Gemeinsamer Stil über die Seiten der Toolbox

**Datum:** 2026-10-23
**Betrifft:** alle Seiten in `docs/`, dazu `template.html` und
`template-vorschlag.html` als deren Quellen
**Stand:** **Entwurf im Werden.** Der Ist-Zustand ist erhoben und nachgeprüft,
die Randbedingungen stehen. Was noch fehlt, sind vier Entscheide des Benutzers —
Abschnitt «Offene Punkte» am Ende. Bis die beantwortet sind, ist dies **keine
Umsetzungsvorlage**.
**Mitlesen:** `CLAUDE.md`, Abschnitt «Neue HTML-Seite veröffentlichen» Punkt 3
(der Entscheid, der das hier erst erlaubt) und Abschnitt «Konvention: Fusszeile
mit Urheber-Credit und Kaffee-Link»

---

## Woher das kommt

Am 2026-10-23 hat der Benutzer entschieden, dass die Seiten **für den
Online-Gebrauch gerechnet** sind: benutzt werden sie über
`stayingclean.github.io/toolbox/`, nicht als herumgeschickte Kopien. Anlass war,
dass heruntergeladene Kopien der Budgetvorlage bei den Beratenden
auseinanderliefen — ein Versions-Chaos, das keine Sorgfalt in der Datei
verhindern kann, nur eine Adresse. `CLAUDE.md` Punkt 3 ist entsprechend neu
gefasst (Commit `a881290`, danach `0382932`).

Vorher stand dort «CSS muss eingebettet bleiben, damit die Seite lokal ohne
Internet funktioniert». Diese Begründung gilt nur noch für zwei Ausnahmen.
**Damit ist ein gemeinsames Stylesheet über mehrere Seiten überhaupt erst
erlaubt** — vorher war es durch die Regel ausgeschlossen.

Aus der Diskussion um diesen Entscheid ist die Frage entstanden, ob es nicht
Zeit wäre, CSS und JavaScript in eine Art interne Bibliothek zu fassen, damit
ein einheitliches Erscheinungsbild entsteht. Dieses Dokument ist die Antwort
darauf.

**Eine Vorgeschichte als Aufgabenbeschreibung gibt es nicht.** Gesucht wurde in
`docs/` (38 Dateien, keine einzige `.md`), in allen neun `specs/`, allen elf
`plans/`, `README.md`, `ANLEITUNG.md`, in `.superpowers/` (enthält nur das
Budget-Vorhaben vom 22.10.), in den Issues und PRs aller fünf Repos der
Organisation (toolbox: null Issues, 32 PRs, alle gemerged, keiner zum Thema), in
allen Remote-Branches (`stayingclean/toolbox` hat genau einen: `master`) und in
den Protokollen der übrigen Sitzungen. Die Aufgabe existierte nur als Gespräch.
Festgehalten ist sie erst hier.

---

## Ziel

Ein Besucher, der von der Übersicht zur Budgetvorlage und weiter zur Anleitung
klickt, soll **dieselbe Website** sehen — nicht drei Seiten, die sich zufällig
ähneln. Und wer eine neue Seite dazustellt, soll den Stil **übernehmen** können,
statt ihn aus einer bestehenden Datei abzuschreiben.

Das Abschreiben ist heute der Normalfall, und es ist schon schiefgegangen: die
Fusszeilen-Konvention, die `CLAUDE.md` als fertigen CSS-Block vorgibt, steht an
sechs Stellen und stimmt an keinen zwei davon überein (siehe unten).

---

## Der Ist-Zustand

Erhoben am 2026-10-23 am Stand `ec04785`. Jede Zahl unten ist aus den Dateien
gelesen, nicht geschätzt.

### Die Seiten und ihr CSS

| Seite | CSS | Quelle | Lädt Schrift |
|---|---:|---|---|
| `docs/index.html` | 146 Z. eingebettet | handgeschrieben | ja |
| `docs/budgetvorlage.html` | **2181 Z.** eingebettet | handgeschrieben | ja |
| `docs/skillsliste.html` | 183 Z. eingebettet | **generiert** aus `template.html` | ja |
| `docs/skill-vorschlagen.html` | 90 Z. eingebettet | **generiert** aus `template-vorschlag.html` | ja |
| `docs/plakat.html` | 119 Z. eingebettet | handgeschrieben | **nein** |
| `docs/flyer-editor.html` | 147 Z. eingebettet | handgeschrieben | **nein** |
| `docs/claude-anleitung/*.html` (6 Seiten hier, 8 aus ki-tasks) | 188 Z. **in `stil.css`** | handgeschrieben | ja |
| `docs/neutral_flyer.html` | — | Weiterleitung | — |
| `docs/altbau/` | — | fremder Viewer (`docs/altbau/vendor/`) | — |

Die Anleitung ist also **der einzige Ort, der es schon richtig macht**: ein
`stil.css` und ein `anleitung.js`, von vierzehn Seiten geteilt (sechs hier, acht
aus `stayingclean/ki-tasks`).

### Die Palette ist fast schon einheitlich — nur heissen die Dinge überall anders

Das ist der wichtigste Befund. Es muss **keine** Corporate Identity *erfunden*
werden; es gibt schon eine, sie ist nur nirgends aufgeschrieben.

| Bedeutung | index | budgetvorlage | skillsliste | vorschlagen | plakat | anleitung |
|---|---|---|---|---|---|---|
| Papier | `--bg`<br>`#FAF8F5` | `--color-bg-alt`<br>`#FAF8F5` | `--bg`<br>`#FAF8F5` | `--bg`<br>`#FAF8F5` | `--bg`<br>`#FAF8F5` | `--bg`<br>`#FAF8F5` |
| Karte | `--card`<br>`#FFFFFF` | `--color-surface`<br>`#ffffff` | `--surface`<br>`#FFFFFF` | `--card`<br>`#FFFFFF` | `--card`<br>`#FFFFFF` | `--card`<br>`#FFFFFF` |
| Akzent | `--accent`<br>`#008080` | `--color-primary`<br>`#008080` | `--active`<br>`#008080` | `--accent`<br>`#008080` | `--accent`<br>`#008080` | `--accent`<br>`#008080` |
| Akzent dunkel | `--accent-dark`<br>`#006666` | `--color-primary-dark`<br>`#006666` | `--active-2`<br>`#006666` | `--accent-dark`<br>`#006666` | `--accent-dark`<br>`#006666` | `--accent-dark`<br>`#006666` |
| Akzent zart | `--accent-tint`<br>`#E6F2F2` | `--color-primary-tint`<br>`#e6f2f2` | `--active-h`<br>`#E6F2F2` | `--accent-tint`<br>`#E6F2F2` | `--accent-tint`<br>`#E6F2F2` | `--accent-tint`<br>`#E6F2F2` |
| Fliesstext | `--text`<br>`#1C1C1C` | `--color-text`<br>**`#1a1a1a`** | `--text`<br>`#1C1C1C` | `--text`<br>`#1C1C1C` | `--text`<br>`#1C1C1C` | `--text`<br>`#1C1C1C` |
| Gedämpft | `--muted`<br>`#7A7268` | `--color-text-muted`<br>**`#6b7280`** | `--muted`<br>`#7A7268` | `--muted`<br>`#7A7268` | `--muted`<br>`#7A7268` | `--muted`<br>`#7A7268` |
| Linie | `--border`<br>`#E8E4DF` | `--color-border`<br>**`#e5e7eb`** | `--border`<br>`#E8E4DF` | `--border`<br>`#E8E4DF` | `--border`<br>`#E8E4DF` | `--border`<br>`#E8E4DF` |

Fünf der sechs Seiten haben **dieselben acht Farben**. Nur die Namen gehen drei
verschiedene Wege: `--accent` / `--color-primary` / `--active`, und
`--card` / `--color-surface` / `--surface`.

### Die Budgetvorlage fällt bei drei Farben heraus

Die drei fett markierten Werte oben sind keine Schreibvarianten, sondern andere
Farben — und zwar aus einem anderen System:

| | Toolbox (warm) | Budgetvorlage | Woher |
|---|---|---|---|
| Fliesstext | `#1C1C1C` | `#1a1a1a` | kaum sichtbar |
| Gedämpft | `#7A7268` warmes Grau | `#6b7280` **kühles Blaugrau** | Tailwind `gray-500` |
| Linie | `#E8E4DF` warmes Grau | `#e5e7eb` **kühles Blaugrau** | Tailwind `gray-200` |

`#7A7268` und `#E8E4DF` sind ins Beige gezogen und passen zum Papier `#FAF8F5`.
`#6b7280` und `#e5e7eb` sind ins Blau gezogen. Die Budgetvorlage wirkt dadurch
**kühler und technischer** als der Rest der Website. Das ist der einzige
Unterschied im Ist-Zustand, der einem Besucher auffallen *kann* — alles andere
ist Namensdurcheinander ohne sichtbare Folge.

Dazu kommen in der Budgetvorlage drei Signalfarben aus demselben fremden System:
`--color-success #059669`, `--color-warning #d97706`, `--color-danger #dc2626`.

### Signalfarben: drei Seiten, drei Antworten

| | warnend | Fläche dazu | bestätigend |
|---|---|---|---|
| anleitung | `--warn #B45309` | `--warn-tint #FFF4E5` | `--ok #2F7D3A`, `--ok-tint #EAF6EC` |
| plakat | `--warn #8A5A2B` | `--warn-tint #FBF1E4`, `--warn-border #EDD9BF` | — |
| budgetvorlage | `--color-warning #d97706` | `--color-warning-bg #fffbeb` | `--color-success #059669` |

Drei verschiedene Brauntöne für «Achtung» und zwei verschiedene Grüns für «gut».

### Abstände, Radien, Übergänge: drei Systeme, zwei Lücken

| | Radien | Übergänge |
|---|---|---|
| budgetvorlage | `--radius-sm/md/lg` = **4 / 8 / 12** px | `--transition-fast` 150 ms, `--transition-base` 250 ms |
| skillsliste | `--r/-sm/-xs` = **14 / 10 / 7** px | `--tr` **0.3 s** |
| index, vorschlagen, plakat, anleitung | *keine Variablen* — Werte stehen direkt in den Regeln | *keine* |

Die beiden Radien-Skalen haben nicht nur andere Werte, sondern **gegenläufige
Namen**: `sm` ist bei der Budgetvorlage 4 px, bei der Skillsliste ist das
Kleinste `xs` = 7 px und `sm` = 10 px. Wer die eine Seite kennt und an der
anderen arbeitet, greift zuverlässig falsch.

### Die Fusszeile: eine Vorlage, sechs Abschriften, keine zwei gleich

`CLAUDE.md` gibt den Block fertig vor. So ist er in den Dateien angekommen:

| | Lücke | Abstand oben | Rand des Avatars | Übergang | Schriftgrösse |
|---|---|---|---|---|---|
| `CLAUDE.md` (Vorlage) | `8px 14px` | `12px` | `1px` | `.15s ease` | — |
| `stil.css` | `8px 14px` | `12px` | `1px` | `.15s ease` | — |
| `template-vorschlag.html` | `8px 14px` | `12px` | `1px` | `.15s ease` | — |
| `template.html` | **`.5rem .9rem`** | **`.7rem`** | **`1.5px`** | **`var(--tr)`** = 0.3 s | **`.74rem`** |
| `index.html` | nur `:hover` und `.footer-sep` abgewandelt | | | | |
| `plakat.html` | dito | | | | |
| `budgetvorlage.html` | `:hover` zeigt auf `--color-primary-dark` statt `--accent` | | | | |
| `flyer-editor.html` | eigenes Thema: `.footer-sep{color:#3d5a3d}` (grün) | | | | |

Die Skillsliste ist also schon weggelaufen: anderer Avatar-Rand, andere Lücke,
doppelt so langsamer Übergang, eigene Schriftgrösse. Niemand hat das gemeldet,
weil es niemandem auffällt — und genau darum läuft es weiter auseinander.

### Drei verschiedene Schriftabrufe für dieselben zwei Schriften

Alle Seiten, die eine Schrift laden, laden **Inter** und **Playfair Display** —
aber in drei verschiedenen Schnittmengen:

| Abruf | Seiten |
|---|---|
| `Inter:400,500,600,700` + `Playfair:500,600,700` | `index.html`, `template-vorschlag.html`, `claude-anleitung/*` |
| `Inter:300,400,500,600,700` + `Playfair:400,500,600,700` | `budgetvorlage.html` |
| `Playfair:500,700` + `Inter:400,500,600,700` | `template.html` |

Drei verschiedene URLs heissen: drei verschiedene Cache-Einträge. Wer von der
Übersicht zur Budgetvorlage klickt, lädt die Schriften **neu**, obwohl es
dieselben sind. Die dritte Variante vertauscht zusätzlich die Reihenfolge der
Familien in der URL — auch das ergibt einen eigenen Cache-Eintrag.

`budgetvorlage.html` lädt zwei Gewichte, die sonst niemand holt: `Inter 300`
und `Playfair 400`. **`Inter 300` wird in der Datei nirgends benutzt**
(nachgeprüft: kein `font-weight: 300`) — es kann beim Vereinheitlichen
ersatzlos weg. `Playfair 400` ist noch zu prüfen; fällt es weg und wird doch
gebraucht, wird eine Überschrift dort schwerer.

---

## Randbedingungen aus dem Projekt

Diese vier stehen fest und sind **nicht** Teil der offenen Punkte.

### 1. Drei Seiten müssen in sich geschlossen bleiben

Für sie darf es **kein** `<link rel="stylesheet">` geben. Die Gründe sind
verschieden und alle drei dokumentiert:

- **`docs/skillsliste.html`** soll ohne Netz funktionieren, und die
  Händler-Symbole dürfen aus Datenschutzgründen nie vom Händler geladen werden
  (ein `<img src="https://coop.ch/…">` meldete Coop beim Öffnen eines Dialogs,
  dass jemand genau diesen Skill anschaut — ohne Klick). Daten, CSS und Symbole
  stecken darum als `data:`-URI in der Datei.
- **`docs/flyer-editor.html`** exportiert sich selbst per
  `document.documentElement.outerHTML`. Was nicht **im Dokument** steht, fehlt
  in der exportierten Datei. Dazu ein technischer Grund: der Bild-Export
  zeichnet die Seite über ein SVG mit `foreignObject` auf ein `<canvas>`; eine
  fremd geladene Ressource verunreinigt den Canvas und `toBlob()` wirft danach
  `SecurityError`. Der PNG-Export wäre nicht nur anders, er wäre kaputt.
- **`docs/plakat.html`** rendert PNG und PDF selbst. Eine erst später
  eintreffende Ressource ergäbe ein anderes Bild. Ein Test nagelt das fest:
  `tests/test_plakat.py`, `test_seite_laedt_nichts_von_aussen_ausser_dem_avatar`.

**Das heisst nicht, dass sie draussen bleiben müssen** — es heisst, dass der
Stil bei ihnen **hineingeschrieben** werden muss statt verlinkt. Beide
Generate (`skillsliste`, `skill-vorschlagen`) haben mit `build.py` schon einen
Weg dafür. `plakat.html` und `flyer-editor.html` haben keinen. Was daraus folgt,
ist offener Punkt 3.

### 2. Fremde Bibliotheken bleiben draussen

Bestätigt am 2026-10-23. Nicht mehr, weil sie offline fehlten, sondern weil
keine gebraucht wird. Hier geht es ausschliesslich um **eigenen Stil-Code** —
kein Tailwind, kein Bootstrap, keine CSS-Bibliothek, auch nicht mitgeliefert.

### 3. Eingebettetes CSS ist nicht per se schlecht

`CLAUDE.md` Punkt 3 sagt: eingebettet bleibt, wo es heute steht, weil es nichts
kostet — eine Datei, ein Abruf, kein Cache-Problem beim Deploy. «Ein eigenes
Stylesheet lohnt sich erst, wenn mehrere Seiten es teilen.» Das ist **ein
Argument für dieses Vorhaben**, nicht dagegen: geteilt wird hier gerade. Aber es
setzt den Maßstab — eine gemeinsame Datei muss sich an der Zahl der Seiten
rechtfertigen, die sie wirklich teilen.

### 4. Die Fusszeile bleibt Pflicht

Urheber-Credit und Kaffee-Link in jeder Seite in `docs/`, Ausnahme
`neutral_flyer.html` (Weiterleitung). Kein Bild für den Kaffee-Link, nur ☕.
Ändert sich durch dieses Vorhaben nichts — ausser dass der CSS-Block dann
hoffentlich nur noch an einer Stelle steht.

---

## Was ich daraus ableite (meine Einschätzung, nicht entschieden)

Das Folgende ist **mein Vorschlag**, damit die offenen Punkte unten etwas haben,
woran sie sich reiben können. Der Benutzer hat dem nicht zugestimmt.

1. **Der Kern ist eine Token-Datei, nicht eine Komponenten-Bibliothek.** Der
   Ist-Zustand zeigt: die Farben stimmen schon, die Namen nicht. Eine Liste von
   Variablen mit festgelegten Namen löst den grössten Teil des Problems und
   kostet fast nichts. Komponenten (Knopf, Karte, Dialog) sind die viel grössere
   Arbeit und der viel grössere Eingriff — die Budgetvorlage allein hat 2181
   Zeilen CSS, die dann umgeschrieben würden.
2. **Die Tokens gehören in eine Datei, die sowohl verlinkt als auch eingebettet
   werden kann.** Sonst gibt es zwei Wahrheiten für die drei geschlossenen
   Seiten.
3. **Die drei Abweichungen der Budgetvorlage sind der einzige sichtbare
   Schaden.** Sie zu beheben ist eine Änderung an einer Seite, die im Einsatz
   ist — das ist ein Entscheid des Benutzers, kein Aufräumen.
4. **Ein Test ist hier mehr wert als sonst.** Alle Auseinanderlauf-Stellen in
   diesem Projekt haben eines gemeinsam: keine Sperre meldet sie
   (`CLAUDE.md` sagt das an vier Stellen über die Stufen-Namen, die Linkregeln,
   die Höchstzahl drei und die Seitenliste der Anleitung). Dieselbe Falle gilt
   hier: eine Seite, die ihre eigene Farbe setzt, fällt niemandem auf.

---

## Entscheide des Benutzers, 2026-10-23

### 1. Umfang: nur Tokens

Farben, Schriften, Abstände, Radien, Übergänge — mit festgelegten Namen. **Keine
Komponenten, kein geteiltes JavaScript.** Begründung aus dem Ist-Zustand: die
Farben stimmen schon, nur die Namen gehen drei Wege. Komponenten wären der viel
grössere Eingriff bei viel kleinerem Gewinn.

Damit bleibt `docs/claude-anleitung/anleitung.js` das, was es ist: die Logik
jener Anleitung, kein Vorbild für eine Bibliothek.

### 2. Reichweite: Bestand ja — aber zwei Dateien bleiben unangetastet

> «Mit Bestand, aber die Dateien, welche in Claude erwähnt werden (Editor,
> Skillsliste) nicht anfassen. Die Budget-Liste separat umbauen»

| Seite | |
|---|---|
| `docs/index.html` | migrieren |
| `docs/skill-vorschlagen.html` (über `template-vorschlag.html`) | migrieren |
| `docs/claude-anleitung/stil.css` | migrieren |
| `docs/plakat.html` | migrieren — **mit Vorbehalt, siehe unten** |
| `docs/budgetvorlage.html` | **eigener Umbau**, getrennt von diesem |
| `docs/skillsliste.html` | **nicht anfassen** |
| `docs/flyer-editor.html` | **nicht anfassen** |

Die Budgetvorlage getrennt zu halten ist richtig: 2181 Zeilen CSS, Druck-Layout,
gerade erst umgebaut, 435 Tests. Sie gehört in einen eigenen Schritt mit eigenem
Commit, damit ein Fehler dort nicht die übrigen vier Seiten mitnimmt.

### 3. Verteilung: `<link>` statt Einbetten

> «Plakat mit ref, FlyerEditor nur, wenn sichergestellt ist, dass beim Download
> der CSS Dabei ist. Vorschlagformular mit ref»

- **Vorschlagsformular: `<link>`.** Unproblematisch — es ist die einzige Seite
  in `docs/`, die ohnehin Internet braucht (Spam-Schutz und Absenden).
  **Nachzuziehen:** `CLAUDE.md` sagt im Abschnitt «Skill-Vorschläge von aussen»
  noch «das CSS bleibt trotzdem eingebettet».
- **Flyer-Editor: fällt damit heraus.** Die Bedingung des Benutzers ist mit
  einem `<link>` **nicht erfüllbar** — Begründung unten. Deckt sich mit
  Entscheid 2.
- **Plakat: `<link>`** — vom Benutzer am 2026-10-23 bestätigt, samt Auftrag,
  Test und `CLAUDE.md` nachzuziehen. **Beides erledigt**, siehe unten.

#### Warum der Flyer-Editor kein `<link>` haben kann

Die Seite exportiert sich selbst (`docs/flyer-editor.html`, Zeilen 1228 und
1325: `'<!DOCTYPE html>\n' + document.documentElement.outerHTML`). Ein
`<link rel="stylesheet" href="…">` wandert dabei als **Tag** mit, nicht als
Inhalt. Liegt die exportierte Datei auf einer Festplatte, zeigt der relative
Pfad ins Leere und der Flyer verliert sein Aussehen — genau der Fall, den die
Bedingung ausschliesst.

Dazu kommt der Bild-Export: die Seite verpackt sich als XHTML in ein SVG
`<foreignObject>` (Zeilen 1234–1251) und lässt den Browser das zeichnen. Ein SVG
in einem `<img>` ist isoliert; von aussen verwiesene Stile werden dort gar nicht
geladen. Das Bild käme also unformatiert heraus.

Erfüllbar wäre die Bedingung nur, indem `build.py` die Tokens beim Bauen
**hineinschreibt** — dann würde der Flyer-Editor neu ein Generat. Das
widerspricht Entscheid 2 («nicht anfassen»), also bleibt er aussen.

#### Warum das Plakat ein `<link>` haben könnte — und was dem entgegensteht

**Der in `CLAUDE.md` genannte Grund hält nicht.** Dort steht, das Plakat lade
keine Schrift, weil «sie rendert PNG und PDF selbst, und eine erst später
eintreffende Schrift ergäbe ein anderes Bild». Nachgeprüft am Code:

- Das Plakat **rendert sich nicht selbst**. Es liefert eine fertige Bilddatei
  aus (`docs/plakat-skillsliste.png`, 3508 × 4961 px) und holt sie per `fetch`
  (Zeile 479).
- `pdfAusPng` reicht die **Bildpunkte unverändert** ins PDF durch. Der Kern sagt
  es selbst (Zeile 192): «Reine Funktionen: kein DOM, kein fetch, kein Canvas.»
- Die Rückfallebene `pdfAusJpeg` benutzt ein Canvas, zeichnet darauf aber
  `drawImage(bild, 0, 0)` (Zeile 517) — **die Bilddatei**, nicht die Seite.

Das Aussehen der Seite hat also **keinen Einfluss** auf PNG oder PDF. Ein
Stylesheet verunreinigt ein Canvas auch nicht (nur gezeichnete Bilder und Medien
tun das) — anders als beim Flyer-Editor, der wirklich das DOM zeichnet.

**Was dem entgegenstand, war kein technischer Grund, sondern zwei Texte** —
beide sind am 2026-10-23 nachgezogen:

- **`tests/test_plakat.py`.** Die alte Fassung verbot `rel="stylesheet"`
  rundweg und begründete das mit «sonst sähe die Seite ohne Internet anders
  aus» — die Offline-Begründung, die der Entscheid vom 2026-10-23 für diese
  Seite abgelöst hat. An ihre Stelle treten zwei Tests, die die **echte**
  Zusicherung festnageln statt der falsch begründeten:
  - `test_seite_laedt_nichts_von_aussen_ausser_dem_avatar` prüft jetzt, was die
    Seite **lädt** (`src`, und `href` an einem `<link>`), nicht wohin sie
    verlinkt. Ein `<a href="https://buymeacoffee.com/…">` ist ein Ziel für
    einen Klick und meldet niemandem etwas; die alte Textsuche hätte das nie
    unterschieden.
  - `test_eine_stilvorlage_der_seite_kaeme_aus_demselben_ordner` verlangt, dass
    ein `<link rel="stylesheet">` einen **relativen** Pfad trägt. Heute hat die
    Seite keine Stilvorlage, der Test ist also leer — und wacht ab dem Tag, an
    dem eine dazukommt.

  Gegengeprüft an sieben erfundenen Fällen: Stilvorlage vom CDN,
  protokollrelativ (`//cdn…`), vom Wurzelpfad (`/stil.css`), Google Fonts und
  ein fremdes Bild werden alle gefangen; der Avatar und eine eigene Vorlage
  daneben gehen durch. 37 Tests in `tests/test_plakat.py` grün.
- **`CLAUDE.md` Punkt 3** nennt den alten «dritten Grund» jetzt ausdrücklich
  als falsch und führt die drei Code-Befunde auf.

### 4. Budgetvorlage: warme Farben

> «Budgetvorlage mit den warmen farben»

Entschieden am 2026-10-23, nach Ansicht der Vorschau mit beiden Varianten
nebeneinander:

| | heute | neu |
|---|---|---|
| `--color-text` | `#1a1a1a` | `#1C1C1C` |
| `--color-text-muted` | `#6b7280` | `#7A7268` |
| `--color-border` | `#e5e7eb` | `#E8E4DF` |

Es bleibt dabei, dass die Budgetvorlage **getrennt** umgebaut wird (Entscheid
2). Diese drei Zeilen gehören in jenen Schritt — sie sind zwar unabhängig vom
Rest, aber die Seite soll nur in einem Vorgang angefasst werden.

**Ehrlich dazu:** auf der echten Seite ist der Unterschied klein. Was den
Charakter trägt — das Teal `#008080`, die Playfair-Überschriften, die
Papierfarbe `#FAF8F5` — ist ohnehin schon identisch. Die kühlen Werte zeigen
sich nur in grösseren Flächen gedämpften Texts und in langen Linienzügen.
Angeglichen wird, weil es drei Zeilen kostet und die einzige echte Abweichung
beseitigt, nicht weil es dringend wäre.

Die drei Signalfarben der Budgetvorlage (`--color-success #059669`,
`--color-warning #d97706`, `--color-danger #dc2626`) stammen aus demselben
fremden System und sind mit diesem Entscheid **nicht** behandelt — sie gehören
in den Token-Satz, sobald festgelegt ist, wie die Signalfarben projektweit
heissen (heute drei Seiten, drei Antworten; siehe Ist-Zustand).

---

## Offen geblieben

Nichts, was den Plan blockiert. Zu entscheiden bleibt beim Bauen:

- **Wie die Signalfarben heissen und welche Werte gelten.** Heute drei
  Brauntöne für «Achtung» und zwei Grüns für «gut». Betrifft Anleitung, Plakat
  und Budgetvorlage.
- **Ob `Playfair 400` wegfällt.** `Inter 300` ist nachweislich unbenutzt und
  kann weg; bei `Playfair 400` ist es noch nicht nachgeprüft.

---

## Noch nicht behandelt

Bewusst offen gelassen, bis die vier Punkte oben beantwortet sind — sie hängen
alle davon ab:

- **Dunkles Thema.** Keine Seite hat heute eines. Wäre eine Token-Datei der
  natürliche Ort dafür, ist aber ein eigener Entscheid.
- **Druck.** `budgetvorlage`, `plakat` und `flyer-editor` haben je eigene
  `@media print`-Regeln. Ob die in die Bibliothek gehören, hängt an Punkt 1.
- **Was ein Test prüfen soll.** Naheliegend: keine Seite setzt eine Farbe, die
  nicht im Token-Satz steht; alle Seiten laden dieselbe Schrift-URL; der
  Fusszeilen-Block steht nur an einer Stelle. Der genaue Zuschnitt hängt an
  Punkt 1 und 2.
- **`docs/altbau/`** bleibt aussen vor: fremder Viewer mit eigenem `vendor/`.
- **Die acht Seiten aus `stayingclean/ki-tasks`.** Sie verweisen auf
  `stil.css`, das der Toolbox gehört. Ändert sich dessen Rolle, ändert sich
  etwas für ein zweites Repo — `CLAUDE.md`, Abschnitt «Anleitung
  `docs/claude-anleitung/` — zwei Repos, eine Seitenliste».
