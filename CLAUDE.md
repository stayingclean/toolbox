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
- `docs/neutral_flyer.html` = Flyer-Editor (self-contained, Bilder eingebettet).
- `docs/asrs-v1-1.html` = ASRS v1.1 (ADHS-Selbstbeurteilung, WHO – frei nutzbar).
- `docs/skill-vorschlagen.html` = Formular zum Einreichen neuer Skills (generiert).
- `docs/skills-daten.json` = Datenstand für Formular und Worker (generiert).

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
4. Die Fusszeile muss den Urheber-Credit enthalten (siehe Konvention unten).
5. In `docs/index.html` (Übersicht) eine Karte ergänzen (Link + Kurzbeschreibung).

## Skillsliste pflegen (nicht von Hand editieren!)

`docs/skillsliste.html` wird **generiert** — nicht direkt bearbeiten.

1. Inhalte in **`skills_daten.xlsx`** ändern (Blätter `Skills`, `Stufen`, `Kategorien`).
2. **`build.bat`** doppelklicken (bzw. `uv run build.py`) → erzeugt `docs/skillsliste.html`
   aus `template.html` + Excel.
3. Das Layout/Design steckt in `template.html` (nur die Datenzeile ist ein Platzhalter).
4. `tools/seed_excel.py` erzeugt die Excel reproduzierbar neu aus `docs/skillsliste.html`
   (nur Erst-Einrichtung/Reset).

Details für Nicht-Techniker: `ANLEITUNG.md`.

## Skill-Vorschläge von aussen

Besucher können über `docs/skill-vorschlagen.html` anonym neue Skills einreichen.
Der Weg: Formular → Cloudflare Worker (`worker/`) → Issue in
`stayingclean/skills-suggestions`.

**Freigeben und übernehmen:**

1. Im Vorschlags-Repo das Issue anschauen und Label `freigegeben` setzen
   (oder `abgelehnt` mit einer kurzen Begründung als Kommentar).
2. **`vorschlaege.bat`** doppelklicken → übernimmt alle freigegebenen Vorschläge
   in `skills_daten.xlsx`, schliesst die Issues und baut die Skillsliste neu.
3. Ergebnis anschauen, dann committen und pushen. **Nichts geht ohne Push online.**

Die Formularseite ist generiert (`template-vorschlag.html` + `build.py`) — nicht
direkt bearbeiten. Sie ist die einzige Seite in `docs/`, die Internet braucht
(Spam-Schutz und Absenden); das CSS bleibt trotzdem eingebettet.

Der Worker liegt in `worker/`, wird aber **nicht** veröffentlicht. Details und
Notbremse: `worker/README.md`.

## Konvention: Fusszeile mit Urheber-Credit

**Jede HTML-Seite in `docs/` MUSS in der `<footer>` den Urheber-Credit enthalten**
(Avatar der GitHub-Organisation + „Erstellt von stayingclean", verlinkt auf die Org):

```html
<a class="footer-credit" href="https://github.com/stayingclean" target="_blank" rel="noopener">
  <img class="footer-avatar" src="https://github.com/stayingclean.png?size=80"
       alt="stayingclean" loading="lazy" width="28" height="28">
  <span>Erstellt von stayingclean</span>
</a>
```

Dazu dieses CSS (Farben/Abstände an das jeweilige Theme der Seite anpassen):

```css
.footer-credit{display:inline-flex;align-items:center;gap:8px;margin-top:12px;
  color:var(--muted);text-decoration:none;transition:color .15s ease}
.footer-credit:hover{color:var(--accent)}            /* bzw. Akzentfarbe der Seite */
.footer-avatar{width:28px;height:28px;border-radius:50%;
  border:1px solid var(--border);object-fit:cover;display:block}
```

- Avatar kommt direkt von `https://github.com/stayingclean.png` (aktualisiert sich
  automatisch, wenn das Organisations-Logo geändert wird).
- Bei der Skillsliste steht der Credit in **`template.html`** (nicht in der
  generierten `docs/skillsliste.html`), sonst direkt in der jeweiligen HTML-Datei.
