# Altbau IFC-Viewer

Veröffentlicht unter `docs/altbau/`. Statischer Viewer mit **That Open Fragments 3.4.7** und Three.js, lokal gebündelt, ohne CDN, Tracking oder Backend. `model.ifc` ist die herunterladbare IFC4-Datei. `model.frag` wird daraus mit dem That-Open-IFC-Importer erzeugt und für schnelleres Laden im Browser verwendet. Der Browser benötigt keinen IFC-Konverter und lädt nur die optimierte Darstellung.

2’249 Elemente mit stabilen IFC-GUIDs, Namen, Farben, rekonstruierten Bauteilklassen und Eigenschaftensatz zur Herkunft. Vier `IfcBuildingStorey` (UG, EG, 1OG, 2OG). Dachobjekte gehören räumlich zum 2OG und zusätzlich zur `IfcGroup` Dach; sie sind im Viewer separat schaltbar. `elements.json` ordnet dieselben GUIDs den fünf Sichtbarkeitsgruppen zu. Ein Klick zeigt Name, IFC-Klasse, Geschoss und Rekonstruktionsstatus.

Längeneinheit im IFC: Meter, entsprechend den Blender-Koordinaten; Blender zeigt Zentimeter an. Geometrie als triangulierte Flächen, keine parametrischen Wandaufbauten oder vollständig ausgearbeitete BIM-Fachplanung. Bauteilklassen sind aus Objektnamen abgeleitet; unklare Teile bleiben `IfcBuildingElementProxy`. Die Datei ist eine Rekonstruktion aus Plänen und Fotos, kein vermessenes Bestandsmodell. Foto- und Interpretationsdetails sind gekennzeichnet. Prozedurale Blender-Materialien werden durch Grundfarben angenähert. Fotos, DXF-Quellen und Blender-Arbeitsdatei werden nicht mitveröffentlicht.

Quellcode und festgeschriebene Abhängigkeiten liegen in `altbau-src/`. Zum Bauen dort `npm ci` und `node build.mjs` ausführen. Nach einem Austausch von `docs/altbau/model.ifc` mit passenden GUIDs und `elements.json`: `node convert.mjs`. `altbau-viewer.html` spiegelt die veröffentlichte HTML-Datei; sie benötigt die benachbarten Modell- und JavaScript-Dateien und einen HTTP-Server.

Geprüft: IFC4-Schema ohne Fehler; alle 2’249 GUIDs im Fragments-Modell; tatsächliche Sichtbarkeit aller Geschossobjekte; Desktop- und Mobilansicht; Bauteilauswahl; IFC-Download. Abhängigkeiten und Lizenztexte stehen unter `docs/altbau/vendor/`.

Zum lokalen Prüfen: `python -m http.server 8080 --directory docs` und `/altbau/` öffnen. Änderungen werden über den bestehenden Pages-Workflow veröffentlicht.
