/* Schneidet den PDF-Kern aus docs/plakat.html heraus und fuehrt ihn in Node
   aus. So wird genau der Code geprueft, der spaeter im Browser laeuft -- keine
   Kopie, die auseinanderlaufen koennte.

   Aufruf: node plakat_pdf_treiber.mjs <html> <png> <breiteMm> <hoeheMm> <ziel> */

import { readFileSync, writeFileSync } from 'node:fs';

const [, , htmlPfad, pngPfad, breiteMm, hoeheMm, zielPfad] = process.argv;

const ANFANG = '/* == pdf-kern:anfang == */';
const ENDE = '/* == pdf-kern:ende == */';

const html = readFileSync(htmlPfad, 'utf8');
const ab = html.indexOf(ANFANG);
const bis = html.indexOf(ENDE);
if (ab < 0 || bis < 0) {
  console.error('Die Marker des PDF-Kerns stehen nicht in ' + htmlPfad + '.');
  process.exit(2);
}

const kern = new Function(
  html.slice(ab, bis) + '\nreturn { pngLesen, pdfAusPng, pdfAusJpeg };'
)();

const png = new Uint8Array(readFileSync(pngPfad));
const pdf = kern.pdfAusPng(png, Number(breiteMm), Number(hoeheMm));
writeFileSync(zielPfad, Buffer.from(pdf));
