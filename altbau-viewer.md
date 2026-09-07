# Altbau IFC-Viewer

Veröffentlicht unter `docs/altbau/`. Statischer Viewer mit **That Open Components 3.4.8, Components Front 3.4.3 und Fragments 3.4.7**, lokal gebündelt, ohne CDN, Tracking oder Backend. `model.ifc` ist die herunterladbare IFC4-Datei. `model.frag` wird daraus mit dem That-Open-IFC-Importer erzeugt und für schnelleres Laden im Browser verwendet. Der Browser benötigt keinen IFC-Konverter und lädt nur die optimierte Darstellung.

## CAD-Arbeitsplatz

Links liegt die Toolbox, oben die Ansichtsleiste, rechts der ein-/ausklappbare Inspektor und unten die Statusleiste. Auf kleinen Displays liegt der Inspektor unter dem Modellbereich. Werkzeugwahl öffnet den passenden Bereich.

Ein Klick auf **Schnitt** erstellt einen horizontalen Schnitt in der Modellmitte. Horizontal/Längs X/Quer Y ersetzt die Richtung des aktiven Schnitts; weitere Ebenen werden ausdrücklich über «Weiterer Schnitt» hinzugefügt. Der Schieber umfasst die Modellausdehnung. Die Zahl in cm beschreibt die Entfernung ab Modellkante in Richtung der Schnittnormalen, keine absolute IFC-Höhenkote. «Andere Seite» kehrt die Schnittrichtung um, «Mittig» zentriert sie, «Alle entfernen» entfernt sämtliche Ebenen. Flächenklick und Schnittgriffe liegen unter «Erweiterte Werkzeuge».

## Werkzeuge

- Modell: Geschosse/Dach schalten, Suche nach Name/IFC-Klasse/GUID, Filter nach Geschoss/Klasse, Mehrfachauswahl.
- Properties: Attribute und vorhandene Property-Sets direkt aus den IFC-Fragmentdaten; Hervorheben, Fokussieren, Ausblenden/Isolieren, transparente Umgebung, JSON-Export der gewählten Objekte. Bei Mehrfachauswahl zeigt die Tabelle das zuletzt gewählte Objekt.
- Messen: Länge (cm, m, mm), Fläche (m²), Winkel (Grad), Punkt-/Kantenfang, ganze Kanten messen. Zwei Klicks für Länge, drei für Winkel; Flächen mit Enter/Abschliessen beenden. Einzelne oder alle Messungen löschen, als JSON speichern und wieder laden.
- Ansicht: Perspektive, Orthogonalprojektion, Grundriss und Seitenansichten, mehrere Schnitte per Flächenklick oder Gebäudeachse, Schnittverschiebung, Umkehrung und Griffe. Raster, Hintergrund, Vollbild und PNG-Screenshot mit Massbeschriftungen.
- Begehen: First-Person-Modus, Start auf einer modellierten Bodenfläche des gewählten Geschosses oder per Klick, 1,65 m Augenhöhe, W/A/S/D/Pfeile und mobile Bewegungstasten, R/F für Höhe. Freie Navigation ohne Kollisionen/Schwerkraft; keine barrierefreie oder baurechtliche Wegprüfung.
- Ansichten als JSON speichern/laden: Kamera, sichtbare GUIDs und Schnitte. Messungen separat speichern. Kein automatisches Speichern und keine Änderung an der IFC-Datei.

Die Berechnung, Geometrie und grafischen Massobjekte stammen aus That Open. Für zuverlässige Klick-/Touch-Eingaben werden die Koordinaten jedes Klicks separat erfasst und die Raycasts sequentiell verarbeitet; die asynchrone Vorschau des Pakets wird dafür nicht als Datenquelle verwendet. Schnitte werden auch an den Fragments-Worker übergeben, damit abgetrennte Geometrie nicht auswählbar bleibt.

Das ist ein Gebäudebetrachter mit den für dieses Modell nutzbaren BIM-Werkzeugen, keine Oberfläche für jede Entwickler-API des SDK. Fachfunktionen ohne passende Modelldaten (z. B. Infrastrukturtrassen oder IDS-Prüfregeln) sind nicht eingebaut. Es werden keine fehlenden Eigenschaften, Materialschichten oder Mengen erfunden.

2’249 Elemente mit stabilen IFC-GUIDs, Namen, Farben, rekonstruierten Bauteilklassen und Eigenschaftensatz zur Herkunft. Vier `IfcBuildingStorey` (UG, EG, 1OG, 2OG). Dachobjekte gehören räumlich zum 2OG und zusätzlich zur `IfcGroup` Dach; sie sind im Viewer separat schaltbar. `elements.json` ordnet dieselben GUIDs den fünf Sichtbarkeitsgruppen zu. Ein Klick zeigt Name, IFC-Klasse, Geschoss und Rekonstruktionsstatus.

Längeneinheit im IFC: Meter, entsprechend den Blender-Koordinaten; Blender zeigt Zentimeter an. Geometrie als triangulierte Flächen, keine parametrischen Wandaufbauten oder vollständig ausgearbeitete BIM-Fachplanung. Bauteilklassen sind aus Objektnamen abgeleitet; unklare Teile bleiben `IfcBuildingElementProxy`. Die Datei ist eine Rekonstruktion aus Plänen und Fotos, kein vermessenes Bestandsmodell. Foto- und Interpretationsdetails sind gekennzeichnet. Prozedurale Blender-Materialien werden durch Grundfarben angenähert. Fotos, DXF-Quellen und Blender-Arbeitsdatei werden nicht mitveröffentlicht.

Quellcode und festgeschriebene Abhängigkeiten liegen in `altbau-src/`: `main.mjs` koordiniert Welt, Auswahl, Navigation und Schnitte; `properties.mjs` liest zyklussicher IFC-Daten; `measurements.mjs` verwaltet Messungen; `files.mjs` prüft Importe; `viewer.html` enthält Oberfläche und CSS. Zum Bauen dort `npm ci` und `npm run build` ausführen. Der Build aktualisiert `docs/altbau/` und den HTML-Spiegel im Repository-Root. Nach einem Austausch von `docs/altbau/model.ifc` mit passenden GUIDs und `elements.json`: `node convert.mjs`. Die Seite benötigt einen HTTP-Server und die benachbarten Modell-/JavaScript-Dateien.

Tests in `altbau-src/`: `npm test`; einmalig `npx playwright install chromium --only-shell`, danach `npm run test:browser`. Für den zusätzlichen Klicktest `INTERACTIVE=1` als Umgebungsvariable setzen. `CAD=1` prüft die Toolbox und vereinfachte Schnittführung. `VIEWER_URL` prüft eine veröffentlichte URL. Screenshots werden in `altbau-src/test-output/` abgelegt und nicht veröffentlicht. Tests prüfen reale IFC-Sichtbarkeit, Property-Sets, Isolation, Schnitte, Perspektivwechsel, Begehung, Touch-Bewegung, JSON-Rundläufe, ungültige Dateien, bekannte Messwerte sowie direkte Messklicks.

Geprüft: IFC4-Schema ohne Fehler; alle 2’249 GUIDs im Fragments-Modell; tatsächliche Sichtbarkeit aller Geschossobjekte; Desktop- und Mobilansicht; Bauteilauswahl; IFC-Download. Abhängigkeiten und Lizenztexte stehen unter `docs/altbau/vendor/`.

Zum lokalen Prüfen: `python -m http.server 8080 --directory docs` und `/altbau/` öffnen. Änderungen werden über den bestehenden Pages-Workflow veröffentlicht.
