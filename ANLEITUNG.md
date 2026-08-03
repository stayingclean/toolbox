# Skillsliste pflegen — Anleitung

Diese Anleitung erklärt, wie man die Inhalte der Skillsliste ändert **ohne
Programmierkenntnisse**. Bearbeitet wird nur eine Excel-Datei; die fertige
Webseite wird danach per Doppelklick neu erzeugt.

## Überblick

| Datei | Wofür |
|---|---|
| **`skills_daten.xlsx`** | Hier werden die Inhalte bearbeitet (das ist die einzige Datei, die du anfasst). |
| **`build.bat`** | Doppelklick → erzeugt die Webseite neu. |
| Ordner **`docs/`** | Das **Ergebnis** (die fertige Webseite, `docs/skillsliste.html`). Wird automatisch erzeugt/überschrieben und online veröffentlicht — **nicht von Hand bearbeiten.** |
| `template.html`, `build.py`, Ordner `tools/` | Technik dahinter (für Entwickler) — bitte nicht verändern. |

> **Aufteilung:** Im Hauptordner liegt die **Quelle** (das, was du bearbeitest);
> im Ordner `docs/` liegt nur das fertige **Ergebnis**, das online geht.

## Einmalig: „uv“ installieren

Das Erzeugen der Webseite braucht das kleine Hilfsprogramm **uv** (nur **einmal**
installieren, danach nie wieder).

1. Windows-Startmenü → **PowerShell** öffnen.
2. Diesen Befehl einfügen und Enter drücken:

   ```powershell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. PowerShell schliessen. Fertig.

> Die allererste Ausführung von `build.bat` lädt danach noch ein kleines
> Zusatzpaket nach — das dauert wenige Sekunden und passiert nur einmal.

## So änderst du Inhalte

1. **`skills_daten.xlsx` in Excel öffnen.**
2. Änderungen vornehmen (siehe unten) und **speichern** (Format **Excel-Arbeitsmappe `.xlsx`** beibehalten — **nicht** als CSV speichern!).
3. **`build.bat` doppelklicken.** Es erscheint kurz ein schwarzes Fenster mit
   `✅ docs/skillsliste.html wurde neu erstellt.`
4. `docs/skillsliste.html` im Browser öffnen und prüfen.

### Das Blatt `Skills` (Haupt-Tabelle)

Jede Zeile ist ein Skill. Spalten:

| Spalte | Bedeutung |
|---|---|
| **Stufe** | `Hoch`, `Mittel` oder `Tief` (Auswahl per Klappliste in der Zelle). |
| **Kategorie** | Name der Kategorie, z. B. `Anti-Craving`. Muss im Blatt **Kategorien** existieren. |
| **Emoji** | Ein Emoji, z. B. 🌶️ (Emoji-Auswahl mit Tastenkombination **Windows-Taste + .** (Punkt)). |
| **Titel** | Kurzer Name des Skills. |
| **Beschreibung** | Der erklärende Text. |
| **Tipp** | Optionaler Zusatztipp (darf leer sein). Die Glühbirne **💡 wird automatisch** vorangestellt – also **nicht** selbst eintippen, nur den Text. |

> **Filtern/Sortieren:** In der Kopfzeile gibt es Filter-Pfeile. Damit lässt
> sich z. B. nur eine Stufe oder Kategorie anzeigen. Das ist nur eine
> Ansichtshilfe und ändert die Daten nicht.

- **Neue Skill hinzufügen:** einfach eine neue Zeile ausfüllen.
- **Skill entfernen:** die ganze Zeile löschen.
- **Reihenfolge ändern:** Zeilen verschieben — die Reihenfolge in Excel ist die
  Reihenfolge auf der Webseite (innerhalb derselben Stufe und Kategorie).

### Das Blatt `Stufen` (selten ändern)

Die drei Anspannungs-Stufen mit Überschrift, Bereich, Icon, Einleitungstext und
Farben. Die drei Zeilen (`Hoch`, `Mittel`, `Tief`) bitte **nicht löschen**.

### Das Blatt `Kategorien` (selten ändern)

Legt fest, welche Kategorie-Tabs es je Stufe gibt, in welcher **Reihenfolge** und
mit welchem **Icon**.

- **Neue Kategorie:** zuerst hier eine Zeile anlegen (Stufe + Name + Icon),
  danach kann sie im Blatt `Skills` verwendet werden.

## Wenn etwas nicht stimmt

`build.bat` prüft die Daten und sagt **genau**, was zu korrigieren ist — z. B.:

```
❌ Build abgebrochen – bitte folgendes in skills_daten.xlsx korrigieren:
   • Blatt 'Skills', Zeile 12: Kategorie 'Bewegun' existiert in Stufe 'Mittel' nicht ...
```

Korrigiere die genannte Zeile, speichere und starte `build.bat` erneut.

## Hinweis zu Emoji-Farben in Excel

Die Emoji-Spalten sind auf die Schriftart **Segoe UI Emoji** gestellt, damit
Excel sie farbig anzeigt. Je nach Excel-Version werden Emoji im Tabellenblatt
trotzdem **schwarz-weiss** dargestellt – das ist nur eine Anzeige-Eigenheit von
Excel. Die Emoji sind korrekt gespeichert und erscheinen auf der **Webseite
immer farbig**.

## Wichtige Regeln (kurz)

- ✅ Nur **`skills_daten.xlsx`** bearbeiten.
- ✅ Immer als **`.xlsx`** speichern (niemals als CSV — das zerstört die Emoji!).
- ⛔ Blatt-Namen und die **Kopfzeile** (erste Zeile) nicht umbenennen.
- ⛔ Den Ordner `docs/` sowie `template.html`, `build.py` nicht von Hand ändern.

## Veröffentlichen

Nach dem Bauen liegt das fertige Ergebnis im Ordner `docs/`. Beim Hochladen
(Push) der Änderungen wird `docs/` automatisch via GitHub Pages online gestellt —
am Vorgehen ändert sich für dich nichts.

## Vorschläge von anderen übernehmen

Auf der Website gibt es die Seite „Skill vorschlagen". Wer dort etwas einträgt,
landet als Eintrag in einer Liste, die nur du freigeben kannst.

1. **Anschauen:** Öffne https://github.com/stayingclean/skills-suggestions/issues
   (auf dem Handy geht die GitHub-App). Jeder Eintrag ist ein Vorschlag.
2. **Entscheiden:** Rechts unter „Labels" wählst du
   - `freigegeben` → soll in die Skillsliste
   - `abgelehnt` → nicht übernehmen (schreib kurz dazu, warum)
   - `in Prüfung` → du schaust es dir später nochmal an
3. **Übernehmen:** Doppelklick auf **`vorschlaege.bat`**. Das Fenster zeigt, was
   übernommen wurde, und baut die Skillsliste neu.
4. **Veröffentlichen:** Schau `docs/skillsliste.html` an. Wenn es passt, wie
   gewohnt committen und pushen. Vorher ist online nichts verändert.

Wenn im Fenster steht „Keine freigegebenen Vorschläge offen", hast du gerade
nichts freigegeben — dann ist alles in Ordnung.

**Wenn im Fenster steht, ein Issue habe nicht geschlossen werden können:** Öffne
das genannte Issue (die Nummer steht in der Meldung, z. B. `#12`) auf GitHub und
schliesse es von Hand mit dem Knopf „Close issue". Der Vorschlag steht dann
bereits in der Excel — bleibt das Issue offen, wird er beim nächsten Doppelklick
auf `vorschlaege.bat` ein zweites Mal übernommen und erscheint doppelt in der
Skillsliste.

Steht im Fenster, ein Vorschlag sei **nicht übernommen** worden (mit einer
Begründung wie „Unbekannte Kategorie" oder „stammt von …, nicht vom Formular"),
bleibt das Issue absichtlich offen — da ist nichts zu tun ausser es anzuschauen
und gegebenenfalls das Label `abgelehnt` zu setzen.
