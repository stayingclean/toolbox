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

## Anonymität

Der Worker schreibt weder IP-Adresse noch Browserkennung ins Issue und in kein
Log — `[observability] enabled = false` in `wrangler.toml` schaltet die Workers
Logs bewusst ab, statt sich auf eine Voreinstellung zu verlassen. Für die
Ratenbegrenzung wird die IP nur als Hashwert mit einer Stunde Gültigkeit
gehalten.

**Eine Ausnahme, die genannt sein muss:** Die IP-Adresse geht als `remoteip` an
Cloudflares eigene Turnstile-Prüfung. Das ist derselbe Anbieter, der die
Verbindung ohnehin terminiert und die IP damit ohnehin sieht; sie verlässt den
Weg der Anfrage also nicht, wird aber an dieser Stelle bewusst mitgeschickt.

## Prüflogik

Die reinen Prüffunktionen stehen in `validate.js`, die reinen Anteile des
Workers in `index.js`; beide werden mit `(cd worker && node --test)` geprüft.
Sie kennen die gültigen Stufen und Kategorien nicht selbst, sondern lesen sie aus
`docs/skills-daten.json` — diese Datei erzeugt `build.py` bei jedem Build mit.

`validate.js` ist die Prüfinstanz für Einreichungen **über das Formular**. Weil
das Vorschlags-Repo öffentlich ist und jede Person mit GitHub-Konto dort von Hand
ein Issue eröffnen kann, prüft `tools/vorschlaege_holen.py` zusätzlich die
Herkunft (nur Issues des Bot-Kontos) und alle Felder noch einmal.
