# Projekt: Sammlung veröffentlichter HTML-Seiten (GitHub Pages)

Statische Website unter **https://eraschle.github.io/skills/**.
Das Repo dient als **Sammlung eigenständiger HTML-Seiten**, die nach und nach
(häufig mit Claudes Hilfe aus bestehenden Vorlagen/Dokumenten digitalisiert)
veröffentlicht werden — z. B. die interaktive Skillsliste und die Budgetvorlage.

Deploy über GitHub Actions (`.github/workflows/deploy.yml`) — veröffentlicht wird
**nur der Ordner `docs/`**. Pages-Quelle ist auf „GitHub Actions" gestellt.

## Aufbau

- **Quelle bleibt im Wurzelverzeichnis**, das **Ergebnis** liegt in `docs/`.
- `docs/index.html` = Startseite (`/skills/`) = die generierte Skillsliste.
- `docs/uebersicht.html` = generischer Hub, der alle Seiten verlinkt.
- `docs/budgetvorlage.html` = eigenständige Budget-Seite (neutrale Vorlage).

## Neue HTML-Seite veröffentlichen

Wenn eine neue (oft digitalisierte) HTML-Seite dazukommt:

1. Die fertige HTML-Datei in **`docs/`** ablegen → online unter `/skills/<datei>.html`.
2. Sämtliche personen-/organisationsspezifischen Angaben entfernen (neutralisieren),
   da `docs/` **öffentlich** publiziert wird.
3. **CSS muss in der Datei eingebettet bleiben** (kein externes Stylesheet), damit
   die Seite auch lokal ohne Server/Internet funktioniert.
4. Die Fusszeile muss den Urheber-Credit enthalten (siehe Konvention unten).
5. In `docs/uebersicht.html` eine Karte ergänzen (Link + Kurzbeschreibung).

## Skillsliste pflegen (nicht von Hand editieren!)

`docs/index.html` wird **generiert** — nicht direkt bearbeiten.

1. Inhalte in **`skills_daten.xlsx`** ändern (Blätter `Skills`, `Stufen`, `Kategorien`).
2. **`build.bat`** doppelklicken (bzw. `uv run build.py`) → erzeugt `docs/index.html`
   aus `template.html` + Excel.
3. Das Layout/Design steckt in `template.html` (nur die Datenzeile ist ein Platzhalter).
4. `tools/seed_excel.py` erzeugt die Excel reproduzierbar neu aus `docs/index.html`
   (nur Erst-Einrichtung/Reset).

Details für Nicht-Techniker: `ANLEITUNG.md`.

## Konvention: Fusszeile mit Urheber-Credit

**Jede HTML-Seite in `docs/` MUSS in der `<footer>` den Urheber-Credit enthalten**
(Avatar vom GitHub-Account + „Erstellt von Erich Raschle", verlinkt aufs Profil):

```html
<a class="footer-credit" href="https://github.com/eraschle" target="_blank" rel="noopener">
  <img class="footer-avatar" src="https://github.com/eraschle.png?size=80"
       alt="Erich Raschle" loading="lazy" width="28" height="28">
  <span>Erstellt von Erich Raschle</span>
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

- Avatar kommt direkt von `https://github.com/eraschle.png` (aktualisiert sich
  automatisch, wenn das GitHub-Profilbild geändert wird).
- Bei der Skillsliste steht der Credit in **`template.html`** (nicht in der
  generierten `docs/index.html`), sonst direkt in der jeweiligen HTML-Datei.
