/**
 * Nimmt Skill-Vorschläge vom Formular entgegen und legt daraus ein Issue an.
 *
 * Bewusst NICHT gespeichert oder protokolliert: IP-Adresse und Browserkennung.
 * Die IP wird ausschliesslich als Hashwert für die Ratenbegrenzung verwendet
 * und verfällt nach einer Stunde.
 */

import { pruefeVorschlag, pruefeAenderung, STUFEN } from "./validate.js";

const HERKUNFT = "https://stayingclean.github.io";
const MAX_PRO_STUNDE = 5;
// Benannte Turnstile-Aktion: muss mit data-action auf der Formularseite
// übereinstimmen, sonst liesse sich ein anderswo erzeugtes Token hier
// wiederverwenden.
const AKTION = "skill-vorschlag";
const ERLAUBTE_HOSTS = new Set(["stayingclean.github.io"]);

function antwort(rumpf, status = 200) {
  return new Response(JSON.stringify(rumpf), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": HERKUNFT,
      "access-control-allow-headers": "content-type",
      "access-control-allow-methods": "POST, OPTIONS",
    },
  });
}

async function hashe(text) {
  const roh = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text)
  );
  return [...new Uint8Array(roh)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function turnstileGeprueft(token, secret, ip) {
  if (!token) return false;
  const formular = new FormData();
  formular.append("secret", secret);
  formular.append("response", token);
  if (ip) formular.append("remoteip", ip);
  try {
    const res = await fetch(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      { method: "POST", body: formular, signal: AbortSignal.timeout(10000) }
    );
    if (!res.ok) return false;
    const ergebnis = await res.json();
    // Geschlossen scheitern: nur eine in jeder Hinsicht gueltige Antwort zaehlt.
    return (
      ergebnis.success === true &&
      ergebnis.action === AKTION &&
      ERLAUBTE_HOSTS.has(ergebnis.hostname)
    );
  } catch {
    return false;
  }
}

/**
 * Maskiert einen Wert fuer eine Markdown-Tabellenzelle.
 *
 * Ein `|` oder ein Zeilenumbruch im Freitext wuerde die Tabelle zerreissen –
 * die Betreuung saehe dann etwas anderes als das, was der JSON-Block traegt und
 * was spaeter uebernommen wird. Die Tabelle ist die einzige Ansicht, die sie zu
 * Gesicht bekommt; sie muss zum Block passen.
 */
export function zelle(wert) {
  return String(wert).replace(/\|/g, "\\|").replace(/\r?\n/g, "<br>");
}

/**
 * Bezugsquellen fuer eine Tabellenzelle. Undefiniert kommt vor: ein
 * zwischengespeicherter Datenstand von vor dieser Neuerung kennt das Feld nicht.
 *
 * Jeder Link steht in Inline-Code (Backticks): die Bezugsquelle ist die
 * einzige Spalte, die Markdown-Metazeichen wie `[`, `]`, `(` oder `)` tragen
 * kann (jedes andere Feld sperrt bereits "http"), und Inline-Code verhindert,
 * dass Markdown sie als Link oder Formatierung interpretiert. pruefeLinks
 * weist einen Backtick im Link selbst bereits zurueck, sonst liesse sich
 * damit aus dem Inline-Code ausbrechen.
 */
export function quellen(liste) {
  return liste && liste.length
    ? liste.map((url) => "`" + zelle(url) + "`").join("<br>")
    : "—";
}

/**
 * Ruft eine Bezugsquelle einmal ab und fasst das Ergebnis in einer Zeile.
 *
 * Lehnt NIE ab: ein Shop, der Cloudflare-Adressen aussperrt, darf keine
 * ehrliche Einreichung blockieren – der Link funktioniert im Browser tadellos,
 * und die einreichende Person haette keine Chance zu verstehen, was von ihr
 * verlangt wird. Die Zeile ist Entscheidungshilfe fuer die Freigabe, nicht mehr.
 *
 * Darum gilt nur 404/410 als Befund; 403, 429 und 5xx heissen "keine Aussage".
 *
 * Der Abruf ist ungefaehrlich, weil pruefeLinks vorher nur https ohne Port und
 * ohne IP-Adresse durchgelassen hat – auf interne Adressen laesst sich der
 * Worker damit nicht richten. Das gilt aber nur fuer den ERSTEN Hop: folgt
 * ein Shop mit "redirect: follow" auf eine interne oder sonst gesperrte
 * Adresse weiter, prueft niemand mehr nach. Und die Zeile ist mit der
 * urspruenglich eingereichten Adresse beschriftet, obwohl Status und "ok" vom
 * LETZTEN Hop stammen – nach einer Weiterleitung passen Beschriftung und
 * Befund nicht mehr zwingend zur selben URL. Bewusst trotzdem "follow" statt
 * "manual": mit "manual" wuerde jede gewoehnliche Shop-Kanonisierung (z. B.
 * ohne www. auf mit www.) als "keine Aussage" erscheinen, und die Zeile waere
 * fuer die allermeisten Shops wertlos.
 */
export async function linkBefund(url) {
  try {
    const res = await fetch(url, {
      method: "GET",
      redirect: "follow",
      headers: { "user-agent": "toolbox-linkpruefung" },
      signal: AbortSignal.timeout(5000),
    });
    if (res.status === 404 || res.status === 410) {
      return `⚠ ${url} — ${res.status}, Link zeigt ins Leere`;
    }
    if (res.ok) {
      return `✓ ${url} — ${res.status} OK`;
    }
    return `· ${url} — ${res.status}, keine Aussage`;
  } catch {
    return `· ${url} — nicht erreichbar, keine Aussage`;
  }
}

/**
 * Haengt die Befunde an den Rumpf – hinter den Kommentarblock, damit dieser
 * der einzige bleibt (parse_body in vorschlaege_holen.py verwirft ein Issue
 * mit mehr als einem Block).
 */
export function mitBefunden(rumpf, befunde) {
  if (!befunde.length) {
    return rumpf;
  }
  return (
    rumpf +
    "\n**Erreichbarkeit beim Einreichen**\n\n```\n" +
    befunde.join("\n") +
    "\n```\n"
  );
}

export function issueRumpf(w) {
  const zeilen = [
    "| Feld | Wert |",
    "| --- | --- |",
    `| Stufe | ${zelle(w.stufe)} |`,
    `| Kategorie | ${zelle(w.kategorie)} |`,
    `| Emoji | ${zelle(w.emoji)} |`,
    `| Titel | ${zelle(w.titel)} |`,
    `| Beschreibung | ${zelle(w.beschreibung)} |`,
    `| Tipp | ${w.tipp ? zelle(w.tipp) : "—"} |`,
    `| Name | ${w.von ? zelle(w.von) : "— (anonym)"} |`,
    `| Bezugsquellen | ${quellen(w.links)} |`,
  ];
  // Der JSON-Block bleibt unveraendert – er traegt die Wahrheit.
  return (
    zeilen.join("\n") +
    "\n\n<!-- vorschlag\n" +
    JSON.stringify(w) +
    "\n-->\n"
  );
}

/**
 * Rumpf fuer eine Aenderung: links der bisherige Stand, rechts der
 * vorgeschlagene. Die betreuende Person soll auf einen Blick sehen, was sich
 * aendert, ohne die Skillsliste daneben aufschlagen zu muessen.
 */
export function issueRumpfAenderung(w, alt) {
  const zeilen = [
    "| Feld | Bisher | Neu |",
    "| --- | --- | --- |",
    `| Emoji | ${zelle(alt.e)} | ${zelle(w.emoji)} |`,
    `| Titel | ${zelle(alt.t)} | ${zelle(w.titel)} |`,
    `| Beschreibung | ${zelle(alt.b)} | ${zelle(w.beschreibung)} |`,
    `| Tipp | ${alt.tip ? zelle(alt.tip) : "—"} | ${w.tipp ? zelle(w.tipp) : "—"} |`,
    `| Bezugsquellen | ${quellen(alt.links)} | ${quellen(w.links)} |`,
  ];
  const kopf =
    `**Stufe:** ${zelle(w.stufe)} · **Kategorie:** ${zelle(w.kategorie)}` +
    (w.erg ? ` · **Ergänzt von:** ${zelle(w.erg)}` : " · **Ergänzt von:** — (anonym)");
  return (
    kopf +
    "\n\n" +
    zeilen.join("\n") +
    "\n\n<!-- vorschlag\n" +
    JSON.stringify(w) +
    "\n-->\n"
  );
}

/**
 * Sucht den bisherigen Stand des Skills im Datenbestand.
 * pruefeAenderung hat bereits sichergestellt, dass es ihn gibt.
 */
function altenSkillFinden(daten, wert) {
  const kat = daten[STUFEN[wert.stufe]].kategorien.find(
    (k) => k.label === wert.kategorie
  );
  return kat.skills.find((s) => s.t === wert.original);
}

export default {
  async fetch(anfrage, umgebung) {
    if (anfrage.method === "OPTIONS") {
      // 204 darf keinen Rumpf haben – sonst wirft die Workers-Laufzeit.
      return new Response(null, {
        status: 204,
        headers: {
          "access-control-allow-origin": HERKUNFT,
          "access-control-allow-headers": "content-type",
          "access-control-allow-methods": "POST, OPTIONS",
          "access-control-max-age": "86400",
        },
      });
    }
    if (anfrage.method !== "POST") {
      return antwort({ fehler: "Nur POST." }, 405);
    }

    // Sichtbar scheitern statt still falsch laufen: fehlt RATE_SALT, liefe der
    // Salt als "undefined" mit und die Ratenbegrenzung waere vorhersagbar.
    // Ein vertippter Secret-Name ist genau so schon einmal passiert.
    for (const name of ["RATE_SALT", "GITHUB_TOKEN", "TURNSTILE_SECRET"]) {
      if (!umgebung[name]) {
        return antwort({ fehler: "Der Dienst ist nicht vollstaendig eingerichtet." }, 500);
      }
    }

    const ip = anfrage.headers.get("CF-Connecting-IP") || "";

    // Ratenbegrenzung: Hashwert der IP, Ablauf nach einer Stunde.
    const schluessel = "rate:" + (await hashe(ip + umgebung.RATE_SALT));
    const bisher = Number((await umgebung.RATE.get(schluessel)) || 0);
    if (bisher >= MAX_PRO_STUNDE) {
      return antwort(
        { fehler: "Zu viele Einreichungen. Bitte in einer Stunde erneut." },
        429
      );
    }

    let eingabe;
    try {
      eingabe = await anfrage.json();
    } catch {
      return antwort({ fehler: "Ungültige Anfrage." }, 400);
    }

    if (
      !(await turnstileGeprueft(eingabe.turnstile, umgebung.TURNSTILE_SECRET, ip))
    ) {
      return antwort({ fehler: "Sicherheitsprüfung fehlgeschlagen." }, 400);
    }

    const datenRes = await fetch(umgebung.DATEN_URL, {
      cf: { cacheTtl: 300, cacheEverything: true },
    });
    if (!datenRes.ok) {
      return antwort({ fehler: "Datenstand nicht erreichbar." }, 503);
    }
    let daten;
    try {
      daten = await datenRes.json();
    } catch {
      return antwort({ fehler: "Datenstand nicht erreichbar." }, 503);
    }

    const istAenderung = eingabe && eingabe.art === "aenderung";
    const geprueft = istAenderung
      ? pruefeAenderung(eingabe, daten)
      : pruefeVorschlag(eingabe, daten);
    if (!geprueft.ok) {
      return antwort({ fehler: geprueft.fehler }, 400);
    }

    const quellenListe = geprueft.wert.links || [];
    const befunde = quellenListe.length
      ? await Promise.all(quellenListe.map(linkBefund))
      : [];

    const issueRes = await fetch(
      `https://api.github.com/repos/${umgebung.REPO}/issues`,
      {
        method: "POST",
        headers: {
          authorization: `Bearer ${umgebung.GITHUB_TOKEN}`,
          accept: "application/vnd.github+json",
          "content-type": "application/json",
          "user-agent": "toolbox-skill-vorschlag",
        },
        body: JSON.stringify({
          title: istAenderung
            ? `[Änderung] ${geprueft.wert.original}`
            : geprueft.wert.titel,
          body: mitBefunden(
            istAenderung
              ? issueRumpfAenderung(geprueft.wert, altenSkillFinden(daten, geprueft.wert))
              : issueRumpf(geprueft.wert),
            befunde
          ),
        }),
      }
    );
    if (!issueRes.ok) {
      return antwort({ fehler: "Konnte den Vorschlag nicht ablegen." }, 502);
    }
    let issue;
    try {
      issue = await issueRes.json();
    } catch {
      return antwort({ fehler: "Konnte den Vorschlag nicht ablegen." }, 502);
    }

    await umgebung.RATE.put(schluessel, String(bisher + 1), {
      expirationTtl: 3600,
    });

    return antwort({ url: issue.html_url });
  },
};
