# Projekt: Sammlung veröffentlichter HTML-Seiten (GitHub Pages)

Statische Website unter **https://stayingclean.github.io/toolbox/**.
Das Repo dient als **Sammlung eigenständiger HTML-Seiten**, die nach und nach
(häufig mit Claudes Hilfe aus bestehenden Vorlagen/Dokumenten digitalisiert)
veröffentlicht werden — z. B. die interaktive Skillsliste und die Budgetvorlage.

Deploy über GitHub Actions (`.github/workflows/deploy.yml`) — veröffentlicht wird
**nur der Ordner `docs/`**. Pages-Quelle ist auf „GitHub Actions" gestellt.

## Aufbau

- **Quelle bleibt im Wurzelverzeichnis**, das **Ergebnis** liegt in `docs/`.
- `docs/index.html` = Startseite (`/toolbox/`) = Übersicht (Hub, verlinkt alle Seiten).
- `docs/skillsliste.html` = die generierte Skillsliste.
- `docs/budgetvorlage.html` = eigenständige Budget-Seite (neutrale Vorlage).
- `docs/flyer-editor.html` = Flyer-Editor (self-contained, Bilder eingebettet).
- `docs/asrs-v1-1.html` = ASRS v1.1 (ADHS-Selbstbeurteilung, WHO – frei nutzbar).
- `docs/skill-vorschlagen.html` = Formular zum Einreichen neuer Skills (generiert).
- `docs/skills-daten.json` = Datenstand für Formular und Worker (generiert).
- `docs/plakat.html` = Plakat zur Skillsliste zum Herunterladen (PNG und PDF in
  A5/A4/A3). Das PDF baut die Seite selbst; die Bildpunkte des PNG wandern dabei
  unverändert ins PDF. Das Plakat liegt in **zwei** Dateien daneben:
  `docs/plakat-skillsliste.png` in voller Auflösung (3508 × 4961 px, 300 dpi auf
  A3) für Download und PDF, und `docs/plakat-vorschau.jpg` (~360 KB) nur für die
  Anzeige — sonst lüde jeder Seitenaufruf 14,9 MB. Diese drei Zahlen gelten fürs
  heutige Plakat und sind beim Austausch mit anzupassen.

  **Beim Austausch des Plakats muss die Vorschau neu erzeugt werden:**

  ```
  uv run --with pillow python -c "from PIL import Image; q=Image.open('docs/plakat-skillsliste.png'); q.resize((1200, round(1200*q.height/q.width)), Image.LANCZOS).convert('RGB').save('docs/plakat-vorschau.jpg', quality=80, optimize=True, progressive=True)"
  ```

  Der Auflösungshinweis auf der Seite rechnet sich von selbst neu, und
  `pytest tests` prüft, ob die neue Datei weiterhin verlustfrei ins PDF
  durchgereicht werden kann und ob die Vorschau zum Original passt. Ausserdem
  meldet `pytest tests`, falls `width`/`height` am Vorschaubild in
  `docs/plakat.html` nicht mehr zur neuen Vorschau passen — die beiden Werte
  müssen dann von Hand nachgezogen werden.

Die Übersicht ist **nach Themen gruppiert** (`<section class="group">` je Thema, z. B.
„Werkzeuge", „ADHS").

## Formulare / Fragebögen

- Speichern-Konvention: **„Als HTML speichern"** (Antworten im eingebetteten
  JSON-Block, öffnet gefüllt) **plus JSON-Export/-Import**. Kein localStorage
  (der Benutzer speichert bewusst als Datei).
- **Urheberrecht:** Viele Testinstrumente sind geschützt. Nur **frei lizenzierte**
  Instrumente dürfen öffentlich (z. B. WHO ASRS v1.1 mit Quellenangabe). Geschützte
  Roh-Formulare liegen in **`neue_docs/`** und sind per `.gitignore` **ausgeschlossen**
  (kommen nicht ins öffentliche Repo, bis die Rechte vorliegen).

## Neue HTML-Seite veröffentlichen

Wenn eine neue (oft digitalisierte) HTML-Seite dazukommt:

1. Die fertige HTML-Datei in **`docs/`** ablegen → online unter `/toolbox/<datei>.html`.
2. Sämtliche personen-/organisationsspezifischen Angaben entfernen (neutralisieren),
   da `docs/` **öffentlich** publiziert wird.
3. **CSS muss in der Datei eingebettet bleiben** (kein externes Stylesheet), damit
   die Seite auch lokal ohne Server/Internet funktioniert.
4. Die Fusszeile muss den Urheber-Credit und den Kaffee-Link enthalten (siehe
   Konvention unten).
5. In `docs/index.html` (Übersicht) eine Karte ergänzen (Link + Kurzbeschreibung).

## Skillsliste pflegen (nicht von Hand editieren!)

`docs/skillsliste.html` wird **generiert** — nicht direkt bearbeiten.

1. Inhalte in **`skills_daten.xlsx`** ändern (Blätter `Skills`, `Stufen`, `Kategorien`).
   Das Blatt `Skills` hat acht Spalten; `Von` und `Ergaenzt` nennen die beiden
   Beitragenden und dürfen leer bleiben. `build.py` liest sie **tolerant** —
   fehlen die Spalten ganz, baut eine ältere Mappe weiter (`optional_header`).
2. **`build.bat`** doppelklicken (bzw. `uv run build.py`) → erzeugt `docs/skillsliste.html`
   aus `template.html` + Excel.
3. Das Layout/Design steckt in `template.html` (nur die Datenzeile ist ein Platzhalter).
4. `tools/seed_excel.py` erzeugt die Excel reproduzierbar neu aus `docs/skillsliste.html`
   (nur Erst-Einrichtung/Reset).

Details für Nicht-Techniker: `ANLEITUNG.md`.

**Die Stufen-Namen `Hoch`, `Mittel`, `Tief` sind hart verdrahtet** und stehen an
sechs Stellen, die alle gleich lauten müssen:

- `build.py` → `STUFE_KEY` (Anzeigename → interner Schlüssel `hoch`/`mittel`/`tief`)
- `worker/validate.js` → `STUFEN`
- `tools/vorschlaege_holen.py` → `STUFEN`
- `tools/seed_excel.py` → `STUFE_DISPLAY`
- `template-vorschlag.html` → `var STUFEN = [["hoch","Hoch"], …]`
- die Dropdown-Prüfung in `skills_daten.xlsx` selbst — feste Formel
  `"Hoch,Mittel,Tief"` (gesetzt in `tools/seed_excel.py`, `add_stufe_dropdown`)

Nur `build.py` prüft die Namen und bricht mit einer Meldung ab („erlaubt sind nur
Hoch, Mittel oder Tief"). Die anderen fünf Stellen haben **keine** solche Sperre:
Wird eine davon vergessen, laufen Formular, Worker und Übernahme-Skript
auseinander, ohne dass irgendetwas fehlschlägt.

## Skill-Vorschläge von aussen

Besucher können über `docs/skill-vorschlagen.html` anonym neue Skills einreichen.
Der Weg: Formular → Cloudflare Worker (`worker/`) → Issue in
`stayingclean/skills-suggestions`.

Das Formular hat **zwei Reiter**: „Neuer Skill" und „Bestehenden ergänzen". Eine
Ergänzung ändert Emoji, Titel, Beschreibung und Tipp eines vorhandenen Skills;
**Stufe und Kategorie bleiben**, weil sie zusammen mit dem ursprünglichen Titel
den Schlüssel bilden, über den `vorschlaege.bat` die Zeile in der Excel
wiederfindet. Der Issue-Titel beginnt dann mit
`[Änderung]`, der Rumpf zeigt „Bisher" und „Neu" nebeneinander
(`worker/index.js`, `issueRumpfAenderung`).

Beide Beitragenden werden genannt: die Spalte `Von` bleibt beim ursprünglichen
Vorschlag stehen, die Spalte `Ergaenzt` nennt die ergänzende Person. Der
Detail-Dialog der Skillsliste setzt daraus „Vorgeschlagen von A · Ergänzt von B"
zusammen (`template.html`, `openModal`). Im JSON-Block des Issues heisst das
Namensfeld bei einer Änderung `erg` statt `von`; im Formular ist es dasselbe
Eingabefeld.

**Freigeben und übernehmen:**

1. Im Vorschlags-Repo das Issue anschauen und Label `freigegeben` setzen
   (oder `abgelehnt` mit einer kurzen Begründung als Kommentar).
2. **`vorschlaege.bat`** doppelklicken → übernimmt alle freigegebenen Vorschläge
   in `skills_daten.xlsx`, schliesst die Issues und baut die Skillsliste neu.
   Änderungen ersetzen eine bestehende Zeile, neue Skills werden angehängt.
3. Ergebnis anschauen, dann committen und pushen. **Nichts geht ohne Push online.**

**Die Reihenfolge im Übernahme-Skript ist Absicht — nicht „aufräumen":** Der
ganze Lauf schreibt in **einem** Durchgang (laden → ändern → **einmal**
speichern). Darin werden erst die Änderungen eingearbeitet, dann die neuen
Skills angehängt, und erst ganz am Ende wird gespeichert. Eine Änderung, die
sich nicht zuordnen lässt, bricht ab, **bevor** irgendetwas gespeichert ist.
Zwei getrennte Speichervorgänge hatten den Fehlerfall, dass der zweite
scheitert, nachdem der erste geschrieben hat: halb übernommene Mappe bei noch
offenen Issues — beim nächsten Lauf kämen die neuen Zeilen ein zweites Mal.
Zwei Abbruchgründe gibt es: Der zu ändernde Skill steht nicht mehr unter diesem
Titel in der Excel, oder derselbe Titel kommt in derselben Stufe und Kategorie
mehrfach vor (es wird bewusst nicht geraten).

Zugesicherte Eigenschaft, die jeder Umbau erhalten muss: **Bricht der Lauf ab,
ist nichts in die Excel geschrieben und kein Issue geschlossen** — der Lauf
lässt sich gefahrlos wiederholen. Genau darauf verweist `ANLEITUNG.md`.

**Eine Änderung an einem Skill, der im selben Lauf erst neu dazukommt, geht
nicht.** Der ursprüngliche Titel wird gegen `docs/skills-daten.json` geprüft, und
diese Datei schreibt erst `build.py` am Ende des Laufs neu. Solche Änderungen
werden abgelehnt, das Issue bleibt offen, nach dem nächsten Lauf klappt es. Kein
Fehler, aber überraschend — und die Meldung („steht nicht mehr in der Stufe …")
führt in diesem Fall in die Irre.

**Beobachtung für die Zukunft:** `worker/index.js` entscheidet allein an
`eingabe.art === "aenderung"`, welche Prüfung läuft. Ginge das Feld verloren,
liefe eine Änderung durch `pruefeVorschlag` und würde klaglos als **neuer** Skill
angelegt — die übrigen Felder passen auf beide Formen. Heute unerreichbar: das
Formular sendet `art` immer mit, und jedes Issue geht durch ein menschliches
Auge. Relevant, sobald je ein zweiter Client dazukommt.

Die Formularseite ist generiert (`template-vorschlag.html` + `build.py`) — nicht
direkt bearbeiten. Sie ist die einzige Seite in `docs/`, die Internet braucht
(Spam-Schutz und Absenden); das CSS bleibt trotzdem eingebettet.

Der Worker liegt in `worker/`, wird aber **nicht** veröffentlicht. Details und
Notbremse: `worker/README.md`.

## Konvention: Fusszeile mit Urheber-Credit und Kaffee-Link

**Jede HTML-Seite in `docs/` MUSS in der `<footer>` den Urheber-Credit und den
Kaffee-Link enthalten** (Avatar der GitHub-Organisation + „Erstellt von
stayingclean", verlinkt auf die Org; daneben der Hinweis auf Buy me a coffee):

```html
<div class="footer-links">
  <a class="footer-credit" href="https://github.com/stayingclean" target="_blank" rel="noopener">
    <img class="footer-avatar" src="https://github.com/stayingclean.png?size=80"
         alt="stayingclean" loading="lazy" width="28" height="28">
    <span>Erstellt von stayingclean</span>
  </a>
  <span class="footer-sep" aria-hidden="true">·</span>
  <a class="footer-coffee" href="https://buymeacoffee.com/stayingclean" target="_blank" rel="noopener">
    <span aria-hidden="true">☕</span><span>Kaffee spendieren</span>
  </a>
</div>
```

Dazu dieses CSS (Farben/Abstände an das jeweilige Theme der Seite anpassen):

```css
.footer-links{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin-top:12px}
.footer-credit{display:inline-flex;align-items:center;gap:8px;
  color:var(--muted);text-decoration:none;transition:color .15s ease}
.footer-credit:hover{color:var(--accent)}            /* bzw. Akzentfarbe der Seite */
.footer-avatar{width:28px;height:28px;border-radius:50%;
  border:1px solid var(--border);object-fit:cover;display:block}
.footer-coffee{display:inline-flex;align-items:center;gap:6px;
  color:var(--muted);text-decoration:none;transition:color .15s ease}
.footer-coffee:hover{color:var(--accent)}
@media (max-width:480px){.footer-sep{display:none}}  /* sonst baumelt das „·" nach dem Umbruch */
```

- Avatar kommt direkt von `https://github.com/stayingclean.png` (aktualisiert sich
  automatisch, wenn das Organisations-Logo geändert wird).
- **Kein Bild für den Kaffee-Link** — nur das Zeichen ☕. So bleibt jede Seite ohne
  Internet lauffähig, und der offizielle gelbe Button würde zu keinem Theme passen.
- Bei zentrierten Fusszeilen zusätzlich `justify-content:center` auf `.footer-links`.
- Bei der Skillsliste steht die Fusszeile in **`template.html`**, beim
  Vorschlagsformular in **`template-vorschlag.html`** (nicht in den generierten
  Seiten in `docs/`), sonst direkt in der jeweiligen HTML-Datei.
- **Ausnahme:** `docs/neutral_flyer.html` ist nur eine Weiterleitung auf
  `flyer-editor.html` (alter Link) und braucht keine Fusszeile.
- Beim Flyer-Editor steht die Fusszeile als `<footer class="site-credit">` am Ende
  von `<body>`, ausserhalb von `#sheets`. Dadurch erscheint sie im Editor und in der
  exportierten Ansicht-HTML, aber **nicht** im Bild-Export und **nicht** im Druck.
