# Flyer «Toolbox» — Quellen

Hier liegt, was der **Flyer-Editor** (`docs/flyer-editor.html`) braucht, um den
Toolbox-Flyer wieder herzustellen. Das Ergebnis selbst wird nicht
veröffentlicht: der Ordner liegt im Wurzelverzeichnis, nicht in `docs/`.

## Die Hintergrundbilder — das Einzige, was sich nicht nachbauen lässt

- `Flyer-Hintergrund Detailliert.jpg` (1055 × 1491 px)
- `Flyer-Hintergrund Einfach.jpg` (1055 × 1491 px)

Dieselbe Werkzeugkiste vor Bergen, einmal ausgemalt und einmal flächig. Im
Editor kommen sie über **Hintergrund → Vorderseite** bzw. **Rückseite** hinein;
er liest die Datei und bettet sie als `data:`-URI ein. Beide sind A-Format
hochkant (Verhältnis 0,708), passen also ohne Zuschnitt auf A5 und A4.

**Im Editor stecken sie nicht.** Dort sind nur die beiden Seiten des
Beispiel-Flyers («Zeit für das Wesentliche») und das Logo eingebettet. Ohne die
zwei Dateien hier lässt sich der Toolbox-Flyer darum nicht wieder herstellen.

## Die fertigen Flyer

- `flyer_a5_detailliert.pdf`, `flyer_a5_einfach.pdf` (je 148 × 210 mm)

Derselbe Flyer mit je einem der beiden Hintergründe. Der Text steckt als echter
Text darin, nicht als Bild — er lässt sich also herauskopieren, falls der
Aufbau einmal von Hand nachgezogen werden muss.

## Was fehlt

Der Editor kann sich selbst als **`flyer-bearbeitet.html`** speichern — mit
Text, Positionen und eingebettetem Hintergrund, weiter bearbeitbar. Diese Datei
gibt es bis jetzt nicht. Solange sie fehlt, sind Textstand und Anordnung nur in
den PDFs festgehalten, und wer etwas ändern will, baut den Flyer im Editor neu
auf. Wird sie einmal gespeichert, gehört sie hierher — dann sind die PDFs bloss
noch Ergebnis.

## Was bewusst nicht hier liegt

Die A4-Querbogen (zwei A5 nebeneinander zum Drucken und Schneiden) und die
PNG-Fassungen der beiden A5-Seiten. Beides erzeugt der Editor auf Knopfdruck
neu — Formatwahl «A4 Querformat» bzw. der Bild-Export —, und zusammen wären es
weitere 6 MB im Repo.
