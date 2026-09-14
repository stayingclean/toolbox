# Beispiel-Projekt: Arbeit und Wohnung suchen

Fertiger Ordner nach der Anleitung «Mit Claude arbeiten» (docs/claude-anleitung/).
Alle Daten sind erfunden (Nadja Keller). Zum Testen so verwenden:

1. Diesen Ordner an einen Ort **ausserhalb** des Repos kopieren, z. B. `Dokumente\Suche`.
2. Claude Desktop öffnen → Cowork → «Ordner hinzufügen» → den kopierten Ordner wählen.
3. Als ersten Prompt nur schreiben: `Hallo, was steht an?`

**Test, ob CLAUDE.md gelesen wird:** Die erste Antwort muss mit dem Wort
«Kompass» beginnen und die offenen Punkte aus aufgaben.md nennen. Beginnt sie
nicht mit «Kompass», wurde CLAUDE.md nicht automatisch gelesen. Dann im Prompt
ergänzen: `Lies zuerst CLAUDE.md.` Das Ergebnis bitte in der Anleitung
(md-dateien.html, Abschnitt CLAUDE.md) nachtragen.

4. Danach die Prompts aus der Anleitung der Reihe nach ausprobieren
   (Workflow Bewerbung → Prompt 1 usw.). Ergebnisse landen in inserate/,
   bewerbungen/ und wohnungen/.

Aufbau:

```
CLAUDE.md          eine Zeile: Lies regeln.md, plus der Kompass-Test
regeln.md          wie Claude arbeiten soll
profil.md          Fakten der (fiktiven) Person
kriterien.md       Stelle und Wohnung: Muss, Wunsch, Ausschluss
aufgaben.md        offene Punkte, von Claude nachgeführt
log.md             was wann passiert ist
unterlagen/        CHECKLISTE.md, später PDFs
inserate/          Suchergebnisse Stellen
bewerbungen/       je Bewerbung ein Unterordner
wohnungen/         Suchergebnisse und Bewerbungen Wohnung
```
