# Worker: Skill-Vorschläge entgegennehmen

Nimmt das Formular `docs/skill-vorschlagen.html` entgegen, prüft die Eingaben
und legt daraus ein Issue in `stayingclean/skills-suggestions` an.

## Erneut veröffentlichen

    cd worker
    npx wrangler deploy

## Secrets (nur einmalig bzw. bei Ablauf)

| Secret | Woher |
| --- | --- |
| `GITHUB_TOKEN` | GitHub → Fine-grained token, nur `skills-suggestions`, Issues: Read and write |
| `TURNSTILE_SECRET` | Cloudflare → Turnstile → Widget `toolbox-skill-vorschlag` |
| `RATE_SALT` | beliebige Zufallszeichenfolge, `python -c "import secrets; print(secrets.token_hex(32))"` |

Setzen mit `npx wrangler secret put <NAME>`.

## Notbremse

Bei Missbrauch: im Repo `skills-suggestions` unter Settings die Issues
abschalten. Der Worker antwortet dann mit einem Fehler, die Formularseite
zeigt die Fehlermeldung an. Die Toolbox selbst ist nicht betroffen.

## Prüflogik

Die reinen Prüffunktionen stehen in `validate.js` und werden mit
`(cd worker && node --test)` geprüft. Sie kennen die gültigen Stufen und Kategorien
nicht selbst, sondern lesen sie aus `docs/skills-daten.json` — diese Datei
erzeugt `build.py` bei jedem Build mit.
