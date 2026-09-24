/* Navigation, Pager und die beiden Knopf-Verhalten aller Anleitungsseiten.
   Herausgeloest aus den 13 damals identischen <script>-Bloecken.

   SEITEN ist die einzige Stelle, an der die Reihenfolge der Anleitung steht.
   Daraus entstehen die Seitenleiste und das Zurueck/Weiter am Seitenende. Eine Seite, die hier fehlt, taucht nirgends auf; eine, die hier
   steht, aber nicht existiert, ist ein toter Link. Beides faellt sonst
   niemandem auf, darum: beim Hinzufuegen oder Loeschen einer Seite NUR diese
   Liste anfassen.

   Achtung, zwei Repos: Die Seiten der Gruppe "Arbeitsweise" kommen beim
   Deployment aus stayingclean/ki-tasks (siehe .github/workflows/deploy.yml).
   Sie duerfen erst hier eingetragen werden, wenn sie dort auch liegen.

   Ein Eintrag kann neben `titel` ein `kurz` tragen: Das steht dann in der
   Seitenleiste, der lange Titel im Zurueck/Weiter. Die Leiste ist schmal,
   und ein Titel ueber zwei Zeilen macht sie unruhig. Nummern gibt es dort
   bewusst keine mehr: Die Aufgaben arbeitet niemand der Reihe nach ab, und
   jede neue Aufgabe haette alle Nummern dahinter verschoben.

   Diese Datei ist UTF-8. GitHub Pages liefert .js mit charset=utf-8 aus, und
   lokal per file:// erbt ein externes Skript die Kodierung der Seite, die
   ebenfalls UTF-8 deklariert. Darum stehen Umlaute hier unverschluesselt. */

var SEITEN = [
  { gruppe: 'Einstieg', seiten: [
    { href: 'index.html',           titel: 'Start' },
    { href: 'voraussetzungen.html', titel: 'Voraussetzungen' },
    { href: 'abos.html',            titel: 'Abos & Kosten' },
    { href: 'datenschutz.html',     titel: 'Datenschutz' }
  ]},

  /* Diese beiden Seiten liegen NICHT in diesem Repo. Sie kommen aus
     stayingclean/ki-tasks unter anleitung/ und werden beim Deployment
     darueberkopiert. Lokal fehlen sie darum — das ist kein Fehler. */
  { gruppe: 'Arbeitsweise', seiten: [
    { href: 'der-ordner.html',  titel: 'Der Ordner' },
    { href: 'platzhalter.html', titel: 'Platzhalter einsetzen' }
  ]},

  /* Ebenfalls aus stayingclean/ki-tasks: eine Seite je Aufgabe, dazu die
     Uebersicht. `kurz` kommt aus `navtitel:` in der INFO.md. Sie gehoeren zu den Aufgabenordnern und aendern sich mit
     ihnen, darum liegen sie drueben und fehlen hier lokal.

     Zwischen den beiden Markern NICHT von Hand pflegen: Der Deploy ersetzt
     den Block mit tools/anleitung_aufgaben.py aus aufgaben/<name>/INFO.md
     und anleitung/<name>.html drueben. Was hier steht, ist nur der Stand
     fuer die lokale Ansicht. */
  { gruppe: 'Aufgaben', seiten: [
    { href: 'aufgaben.html', titel: 'Übersicht' },
    /* AUFGABEN-ANFANG */
    { href: 'wohnung.html',                 titel: 'Wohnung suchen', kurz: 'Wohnung' },
    { href: 'stelle.html',                  titel: 'Stelle suchen', kurz: 'Stelle' },
    { href: 'praemienverbilligung.html',    titel: 'Prämienverbilligung beantragen', kurz: 'Prämienverbilligung' },
    { href: 'krankenkasse.html',            titel: 'Krankenkasse wählen', kurz: 'Krankenkasse' },
    { href: 'gesuch-krankheitskosten.html', titel: 'Gesuche für Krankheitskosten', kurz: 'Krankheitskosten' }
    /* AUFGABEN-ENDE */
  ]},

  { gruppe: 'Weiterführend', seiten: [
    { href: 'prompts.html',      titel: 'Weitere Prompts' },
    { href: 'alternativen.html', titel: 'ChatGPT & Grok' }
  ]}
];

(function () {
  var flach = [];
  SEITEN.forEach(function (g) {
    g.seiten.forEach(function (s) { flach.push(s); });
  });

  var datei = location.pathname.split('/').pop() || 'index.html';
  var hier = -1;
  flach.forEach(function (s, i) { if (s.href === datei) { hier = i; } });

  function schuetze(t) {
    return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /* Seitenleiste */
  var nav = document.querySelector('.nav');
  if (nav) {
    var teile = [];
    SEITEN.forEach(function (g) {
      teile.push('<h2>' + schuetze(g.gruppe) + '</h2>');
      g.seiten.forEach(function (s) {
        var aktiv = (s.href === datei);
        teile.push(
          '<a href="' + s.href + '"' +
          (aktiv ? ' class="active" aria-current="page"' : '') +
          (s.kurz ? ' title="' + schuetze(s.titel).replace(/"/g, '&quot;') + '"' : '') + '>' +
          schuetze(s.kurz || s.titel) + '</a>'
        );
      });
    });
    nav.innerHTML = teile.join('\n');
  }

  /* Zurueck / Weiter */
  var pager = document.querySelector('.pager');
  if (pager && hier !== -1) {
    var vor = flach[hier - 1];
    var weiter = flach[hier + 1];
    pager.innerHTML =
      (vor
        ? '<a class="prev" href="' + vor.href + '"><small>Zurück</small>← ' +
          schuetze(vor.titel) + '</a>'
        : '<span></span>') +
      (weiter
        ? '<a class="next" href="' + weiter.href + '"><small>Weiter</small>' +
          schuetze(weiter.titel) + ' →</a>'
        : '<span></span>');
  }

  /* Menue auf dem Handy */
  var knopf = document.querySelector('.menu-toggle');
  if (knopf && nav) {
    knopf.addEventListener('click', function () {
      nav.classList.toggle('open');
      knopf.setAttribute('aria-expanded', nav.classList.contains('open'));
    });
  }

  /* Kopierknoepfe an den Prompt-Kaesten */
  document.querySelectorAll('.copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var pre = b.closest('.prompt').querySelector('pre');
      var txt = pre.innerText;
      function fertig() {
        var o = b.textContent;
        b.textContent = 'Kopiert ✓';
        setTimeout(function () { b.textContent = o; }, 1600);
      }
      function ersatz() {
        var ta = document.createElement('textarea');
        ta.value = txt;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(ta);
        fertig();
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(fertig, ersatz);
      } else { ersatz(); }
    });
  });
})();
