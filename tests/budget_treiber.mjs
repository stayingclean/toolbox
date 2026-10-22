/* Schneidet den Rechenkern aus docs/budgetvorlage.html heraus und fuehrt ihn in
   Node aus. So wird genau der Code geprueft, der spaeter im Browser laeuft --
   keine Kopie, die auseinanderlaufen koennte.

   Aufruf: node budget_treiber.mjs <html> <funktion> <argumenteAlsJson>
   Das Ergebnis erscheint als JSON auf stdout. */

import { readFileSync } from 'node:fs';

const [, , htmlPfad, funktion, argumenteJson] = process.argv;

const ANFANG = '/* == budget-kern:anfang == */';
const ENDE = '/* == budget-kern:ende == */';

const html = readFileSync(htmlPfad, 'utf8');
const ab = html.indexOf(ANFANG);
const bis = html.indexOf(ENDE);
if (ab < 0 || bis < 0) {
  console.error('Die Marker des Rechenkerns stehen nicht in ' + htmlPfad + '.');
  process.exit(2);
}

const kern = new Function(
  html.slice(ab, bis) + '\nreturn { anpassungBetrag, anpassungHatInhalt, unbekannteAnpassungenBehalten, stichtagListe, ersterVorschauStand, werteFuerStand, summen, anpassungsGruppen, anpassungenNachStand, standKennzeichnung };'
)();

if (typeof kern[funktion] !== 'function') {
  console.error('Unbekannte Funktion des Rechenkerns: ' + funktion);
  process.exit(3);
}

const argumente = JSON.parse(argumenteJson || '[]');
const ergebnis = kern[funktion](...argumente);
// undefined (kein Ergebnis) wird zu null, damit stdout immer gueltiges JSON ist.
process.stdout.write(JSON.stringify(ergebnis === undefined ? null : ergebnis));
