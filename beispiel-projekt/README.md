# Beispiel-Projekt: Wohnung und Stelle suchen

Fertiger Ordner nach der Anleitung «Mit Claude arbeiten» (stayingclean.github.io/toolbox/claude-anleitung/).
Alle Daten sind erfunden (Nadja Keller). Zum Testen:

1. Ordner an einen Ort **ausserhalb** eines Git-Repos kopieren, z. B. `Dokumente\Suche`.
2. Claude Desktop → Cowork → «Ordner hinzufügen» → diesen Ordner.
3. Erster Prompt: `Was steht an?`
   Beginnt die Antwort mit «Kompass», hat Claude CLAUDE.md automatisch gelesen.
4. Dann: `Führe den Auftrag 00_Auftraege/2026-09-16_wohnung-aarau.md aus, Schritte 1 und 2.`

## Aufbau

```
00_Auftraege/    pro Aufgabe eine Datei
01_Recherche/    Schritt 1–2: Funde (Claude)
02_Unterlagen/   Schritt 3: DEINE Unterlagen (Claude liest, schreibt nie hinein)
03_Entwuerfe/    Schritt 4–7: Word-Dateien zum Kommentieren (Claude)
04_Final/        Schritt 8: PDFs (Claude)
CLAUDE.md        nur für Claude: «Lies README.md und regeln.md»
README.md        diese Datei
regeln.md        der 8-Schritte-Ablauf, für alle Aufträge gleich
profil.md        Fakten der (fiktiven) Person
aufgaben.md      offene Punkte, Claude hakt ab
log.md           was wann passiert ist
```

Für andere KI-Anbieter: alle Dateien ausser CLAUDE.md hochladen und mit
«Lies README.md und regeln.md» beginnen.
