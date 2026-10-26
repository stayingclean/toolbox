// Ladepruefung der Budgetvorlage: oeffnet die Beispieldateien aller fuenf
// Dateiformate (tests/fixtures/budget/v1.json ... v5.json) in der echten Seite,
// liest je Version die Summen ab und haelt fest, was die Seite beim Speichern
// daraus macht. Damit merkt eine spaetere Welle, wenn eine alte Datei nach dem
// Umbau anders rechnet oder beim Speichern etwas verliert.
//
// Laeuft im Browser, nicht in Node: geprueft wird die ausgelieferte Seite mit
// ihrem ganzen Oeffnen-und-Speichern-Weg, nicht ein herausgeschnittener Kern.
//
// So ausfuehren:
//   1. Lokalen Server starten: preview_start {name: "toolbox-statisch"}
//      (.claude/launch.json, `uv run python -m http.server <port>` aus der
//      Wurzel des Repos -- nicht aus docs/, die Beispieldateien liegen unter
//      tests/). Ist 8765 schon belegt, einen anderen Port nehmen; das Skript
//      arbeitet nur mit Pfaden ab der Wurzel.
//   2. Zu http://localhost:<port>/docs/budgetvorlage.html navigieren.
//   3. Den Inhalt dieser Datei per javascript_tool ausfuehren. Der Wert ist das
//      Ergebnis (die Datei ist ein einziger Ausdruck, darum kein Semikolon am
//      Schluss).
//
// Das Ergebnis muss tests/fixtures/budget/erwartet.json gleichen. Aendert eine
// Welle gewollt etwas am Gespeicherten, ist das ein Entscheid und kein
// Nachfuehren: erst entscheiden, dann den Sollwert neu aufnehmen.
//
// Was bewusst NICHT im Ergebnis steht:
// - die Stichtag-Zeilen (#summaryStands). Ob ein Stichtag schon vorbei ist,
//   haengt vom heutigen Datum ab; der Sollwert wuerde sonst mit dem Kalender
//   ungueltig. Gelesen werden nur die drei Hauptzeilen der Zusammenfassung,
//   und die rechnen aus den erfassten Werten.
// - savedAt und createdAt: die Seite setzt sie aus der Uhr (bei den alten
//   Formaten createdAt aus savedAt oder jetzt).
// - die Versions-IDs: die Migration der alten Formate wuerfelt sie neu. Sie
//   werden durch ihren Platz ersetzt ("#0", "#1"), ebenso basedOn und
//   activeVersionId -- so bleibt sichtbar, WORAUF verwiesen wird.
await (async () => {
    const VERSIONEN = ['v1', 'v2', 'v3', 'v4', 'v5'];
    const WARTEN_MS = 5000;

    // Wartet, bis die Bedingung gilt. Bei Zeitueberschreitung steht in der
    // Meldung, was der Toast der Seite gerade sagt -- dort meldet sie, warum
    // eine Datei nicht aufging.
    async function warteBis(bedingung, was) {
        const start = Date.now();
        while (!bedingung()) {
            if (Date.now() - start > WARTEN_MS) {
                const toast = document.querySelector('#toast');
                throw new Error(`Zeitueberschreitung: ${was}`
                    + (toast ? ` (Toast: «${toast.textContent}»)` : ''));
            }
            await new Promise((r) => setTimeout(r, 20));
        }
    }

    function reiter() {
        return [...document.querySelectorAll('#versionTabs .version-tab')];
    }

    // Wie viele Reiter die Datei ergeben muss. Die alten Formate teilt die
    // Seite in «Original» und «Nach Reduktion», sobald irgendeine Reduktion
    // erfasst war. Stimmt die Zahl nicht, laeuft das Warten in die
    // Zeitueberschreitung -- das ist dann bereits ein Befund.
    function erwarteteReiter(datei) {
        if (datei.version >= 4) return Math.max(datei.data.versions.length, 1);
        return Object.keys(datei.data.values || {}).some((k) => k.includes('.reduktion')) ? 2 : 1;
    }

    // Nur der erste tbody: der zweite (#summaryStands) haengt am Datum.
    function summen() {
        const tbody = document.querySelector('.summary-table > tbody:not(#summaryStands)');
        const zahl = (art, periode) => {
            const el = tbody.querySelector(`[data-summary="${art}"][data-period="${periode}"]`);
            // Anzeige ist 1'234.56 -- das Tausendertrennzeichen muss weg.
            return Number(el.textContent.replace(/'/g, ''));
        };
        return {
            einnahmenY: zahl('einnahmen', 'jaehrlich'),
            ausgabenY: zahl('ausgaben', 'jaehrlich'),
            diffY: zahl('differenz', 'jaehrlich'),
            diffM: zahl('differenz', 'monatlich'),
        };
    }

    function normalisiere(gespeichert) {
        const data = JSON.parse(JSON.stringify(gespeichert.data));
        const platz = new Map(data.versions.map((v, i) => [v.id, `#${i}`]));
        // Ein Verweis auf eine ID, die es nicht gibt, bliebe sonst still
        // unsichtbar; so steht er als Abweichung im Ergebnis.
        const ersetze = (id) => (id == null ? id : (platz.get(id) ?? `unbekannt:${id}`));
        data.versions.forEach((v) => {
            v.id = platz.get(v.id);
            v.basedOn = ersetze(v.basedOn);
            delete v.createdAt;
        });
        data.activeVersionId = ersetze(data.activeVersionId);
        return data;
    }

    async function pruefe(name) {
        const text = await (await fetch(`/tests/fixtures/budget/${name}.json`)).text();
        const datei = JSON.parse(text);

        // Attrappe fuer den Dateidialog. Die Seite behaelt den Griff nach dem
        // Oeffnen und schreibt beim Speichern ueber createWritable hinein --
        // genau dort fangen wir das Gespeicherte ab.
        let geschrieben = null;
        const teile = [];
        const griff = {
            kind: 'file',
            name: `${name}.json`,
            getFile: async () => new File([text], `${name}.json`, { type: 'application/json' }),
            createWritable: async () => ({
                write: async (stueck) => { teile.push(stueck); },
                close: async () => { geschrieben = teile.join(''); },
            }),
        };
        window.showOpenFilePicker = async () => [griff];

        // Die Reiter der vorigen Datei muessen weg sein, sonst gaelte eine
        // gleich grosse Reiterzahl schon vor dem Laden als erreicht.
        const alt = reiter();
        const soll = erwarteteReiter(datei);
        document.querySelector('#btnOpen').click();
        await warteBis(() => alt.every((t) => !t.isConnected) && reiter().length === soll,
            `${name}: ${soll} Reiter nach dem Oeffnen`);

        // Den Reiter merken, den die Seite nach dem Oeffnen zeigt, und vor dem
        // Speichern dorthin zurueck: activeVersionId im Gespeicherten soll sagen,
        // was die Datei (bzw. die Migration) waehlt, nicht welcher Reiter hier
        // zuletzt angeklickt wurde.
        const aktiv = reiter().findIndex((t) => t.getAttribute('aria-selected') === 'true');

        const versionen = [];
        for (let i = 0; i < soll; i++) {
            const tab = reiter()[i];      // jeder Wechsel baut die Reiter neu
            tab.click();
            // Der Name ohne die Zahl der Anpassungen: die Marke am Reiter ist
            // ein Kind-Element und gehoert nicht zum Namen der Version.
            const marke = tab.querySelector('.version-tab-anzahl');
            const nameOhneMarke = [...tab.childNodes]
                .filter((n) => n !== marke).map((n) => n.textContent).join('');
            versionen.push({ name: nameOhneMarke, ...summen() });
        }
        reiter()[aktiv].click();

        // Speichern ueber Strg+S, nicht ueber #btnSave: nach dem Oeffnen ist
        // nichts geaendert, und die Seite sperrt den Knopf dann («Gespeichert»).
        // Ein Klick auf einen gesperrten Knopf loest nichts aus -- auch bei
        // einem Menschen nicht, der dafuer ebenfalls Strg+S nimmt.
        document.dispatchEvent(new KeyboardEvent('keydown',
            { key: 's', ctrlKey: true, bubbles: true, cancelable: true }));
        await warteBis(() => geschrieben !== null, `${name}: Speichern`);

        return { versionen, gespeichert: normalisiere(JSON.parse(geschrieben)) };
    }

    const original = window.showOpenFilePicker;
    const ergebnis = {};
    try {
        for (const name of VERSIONEN) ergebnis[name] = await pruefe(name);
    } finally {
        window.showOpenFilePicker = original;
    }
    return ergebnis;
})()
