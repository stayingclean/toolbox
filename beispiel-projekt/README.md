# Beispiel-Projekt: Wohnung und Stelle suchen

Fertiger Ordner nach der Anleitung «Mit Claude arbeiten» (stayingclean.github.io/toolbox/claude-anleitung/).
Alle Daten sind erfunden (Nadja Keller). Zum Testen:

1. Ordner an einen Ort **ausserhalb** eines Git-Repos kopieren, z. B. `Dokumente\Suche`.
2. Claude Desktop → Cowork → «Ordner hinzufügen» → diesen Ordner.
3. Erster Prompt: `Was steht an?`
   Beginnt die Antwort mit «Kompass», hat Claude CLAUDE.md automatisch gelesen.
4. Dann: `Führe den Auftrag auftraege/2026-09-16_wohnung-aarau.md aus, Schritte 1 und 2.`

## Aufbau

```
CLAUDE.md        nur für Claude: «Lies README.md und regeln.md»
README.md        diese Datei
regeln.md        der 8-Schritte-Ablauf, für alle Aufträge gleich
profil.md        Fakten der (fiktiven) Person
aufgaben.md      offene Punkte, Claude hakt ab
log.md           was wann passiert ist
_Dokumente/      DEINE Unterlagen (Claude liest, schreibt nie hinein)
auftraege/       pro Aufgabe eine Datei
recherche/       Schritt 1–2: Funde (Claude)
entwuerfe/       Schritt 4–7: Word-Dateien zum Kommentieren (Claude)
final/           Schritt 8: PDFs (Claude)
```

Für andere KI-Anbieter: alle Dateien ausser CLAUDE.md hochladen und mit
«Lies README.md und regeln.md» beginnen.
