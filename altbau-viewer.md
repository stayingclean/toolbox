# Altbau 3D-Viewer

Veröffentlicht unter `docs/altbau/`. Statischer Three.js-Viewer mit lokal eingebundener Bibliothek (0.180.0, MIT), ohne CDN, Tracking oder Backend. GLB-Modell nach Geschoss und Material gebündelt. Geschosse sind über `Floor_UG`, `Floor_EG`, `Floor_OG1`, `Floor_OG2`, `Floor_Dach` adressiert. Fotos, DXF-Quellen und Blender-Arbeitsdatei werden nicht mitveröffentlicht. Prozedurale Blender-Materialien sind im Web durch Grundfarben angenähert.

Zum lokalen Prüfen: `python -m http.server 8080 --directory docs` und `/altbau/` öffnen. Änderungen werden über den bestehenden Pages-Workflow veröffentlicht.
