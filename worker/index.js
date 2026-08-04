/**
 * Nimmt Skill-Vorschläge vom Formular entgegen und legt daraus ein Issue an.
 *
 * Bewusst NICHT gespeichert oder protokolliert: IP-Adresse und Browserkennung.
 * Die IP wird ausschliesslich als Hashwert für die Ratenbegrenzung verwendet
 * und verfällt nach einer Stunde.
 */

import { pruefeVorschlag, pruefeAenderung } from "./validate.js";

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
  const STUFEN = { Hoch: "hoch", Mittel: "mittel", Tief: "tief" };
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
          body: istAenderung
            ? issueRumpfAenderung(geprueft.wert, altenSkillFinden(daten, geprueft.wert))
            : issueRumpf(geprueft.wert),
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
