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
| **Von** | Name der Person, die den Skill vorgeschlagen hat (darf leer sein). |
| **Ergaenzt** | Name der Person, die den Skill später ergänzt hat (darf leer sein). Die Spalte heisst wirklich so – **ohne Umlaut**. |

> **Zu `Von` und `Ergaenzt`:** Beide Namen erscheinen auf der Webseite, wenn man
> einen Skill antippt – als Zeile „Vorgeschlagen von … · Ergänzt von …". Sie
> werden normalerweise automatisch gefüllt, wenn du Vorschläge von anderen
> übernimmst (siehe unten). Von Hand musst du hier nichts eintragen.

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

> ⛔ **Die drei Stufen heissen `Hoch`, `Mittel` und `Tief`. Diese Namen bitte
> nicht ändern** – sonst funktioniert das Einreichungsformular auf der Website
> nicht mehr, ohne dass man es merkt. Die Namen sind an mehreren Stellen fest
> hinterlegt, und nur eine davon meldet sich: `build.bat` bricht dann mit einer
> Fehlermeldung ab.
>
> Was du gefahrlos ändern kannst, ist die **Bezeichnung** in der Spalte daneben
> (z. B. „Hohe Anspannung") – die steht auf der Webseite. Genauso Bereich, Icon,
> Einleitungstext und Farben.

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
- ⛔ Die Stufen-Namen **`Hoch`, `Mittel`, `Tief`** nicht umbenennen (siehe oben).
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

   **Es gibt zwei Arten von Vorschlägen.** Beginnt der Titel mit `[Änderung]`,
   will jemand einen **bestehenden** Skill verbessern, statt einen neuen
   anzulegen. Im Eintrag stehen dann zwei Spalten nebeneinander: links, was heute
   in der Liste steht, rechts der Vorschlag. Du siehst also auf einen Blick, was
   sich ändern würde. Entschieden wird gleich wie sonst.

   Bei einer Änderung bleiben Stufe und Kategorie so, wie sie sind – geändert
   werden nur Emoji, Titel, Beschreibung und Tipp. Der ursprüngliche Name in der
   Spalte `Von` bleibt ebenfalls stehen; die ergänzende Person kommt zusätzlich
   in die Spalte `Ergaenzt`. Auf der Webseite steht danach „Vorgeschlagen von …
   · Ergänzt von …".
3. **Übernehmen:** Doppelklick auf **`vorschlaege.bat`**. Das Fenster zeigt, was
   übernommen wurde, und baut die Skillsliste neu. Änderungen ersetzen die
   bestehende Zeile in der Excel, neue Skills kommen unten dazu.
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

**Wenn im Fenster steht, eine Änderung liesse sich nicht zuordnen:** Der Skill,
der geändert werden sollte, steht nicht mehr unter diesem Titel in der Excel —
meistens, weil er zwischendurch umbenannt oder gelöscht wurde. **Es ist nichts
kaputt:** Es wurde nichts gespeichert und kein Eintrag geschlossen. Nimm dem
betroffenen Eintrag auf GitHub das Kennzeichen `freigegeben` weg und starte
`vorschlaege.bat` noch einmal — die übrigen Vorschläge werden dann wie gewohnt
übernommen.

**Wenn im Fenster steht, eine Änderung passe auf mehrere Zeilen:** Derselbe Titel
kommt in `skills_daten.xlsx` zweimal in derselben Stufe und Kategorie vor, und
das Programm rät nicht, welche der beiden gemeint ist. Auch hier wurde nichts
gespeichert und nichts geschlossen. Öffne die Excel, lösche die doppelte Zeile
oder gib ihr einen anderen Titel, speichere und starte `vorschlaege.bat` erneut.
Welcher Titel es ist, steht in der Meldung.

**Eine Änderung an einem gerade erst neu aufgenommenen Skill geht noch nicht.**
Kam ein Skill im selben Durchlauf frisch dazu und liegt gleichzeitig eine
Änderung dafür vor, wird die Änderung gemeldet und bleibt offen. Die Meldung sagt
dann, den Skill gebe es nicht (mehr) — das stimmt hier so nicht, gemeint ist: er
ist noch nicht in der gebauten Liste. Kein Fehler und nichts zu reparieren:
Sobald der Durchlauf fertig ist, genügt ein zweiter Doppelklick auf
`vorschlaege.bat`, dann wird auch die Änderung übernommen.
