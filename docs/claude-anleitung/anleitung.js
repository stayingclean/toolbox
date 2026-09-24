/* Navigation, Pager und die beiden Knopf-Verhalten aller Anleitungsseiten.
   Herausgeloest aus den 13 damals identischen <script>-Bloecken.

   SEITEN ist die einzige Stelle, an der die Reihenfolge der Anleitung steht.
   Daraus entstehen die Seitenleiste, die Nummern und das Zurueck/Weiter am
   Seitenende. Eine Seite, die hier fehlt, taucht nirgends auf; eine, die hier
   steht, aber nicht existiert, ist ein toter Link. Beides faellt sonst
   niemandem auf, darum: beim Hinzufuegen oder Loeschen einer Seite NUR diese
   Liste anfassen.

   Achtung, zwei Repos: Die Seiten der Gruppe "Arbeitsweise" kommen beim
   Deployment aus stayingclean/ki-tasks (siehe .github/workflows/deploy.yml).
   Sie duerfen erst hier eingetragen werden, wenn sie dort auch liegen.

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
     Uebersicht. Sie gehoeren zu den Aufgabenordnern und aendern sich mit
     ihnen, darum liegen sie drueben und fehlen hier lokal. */
  { gruppe: 'Aufgaben', seiten: [
    { href: 'aufgaben.html',                titel: 'Übersicht' },
    { href: 'wohnung.html',                 titel: 'Wohnung suchen' },
    { href: 'stelle.html',                  titel: 'Stelle suchen' },
    { href: 'gesuch-krankheitskosten.html', titel: 'Gesuche für Krankheitskosten' }
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
    var n = 0;
    SEITEN.forEach(function (g) {
      teile.push('<h2>' + schuetze(g.gruppe) + '</h2>');
      g.seiten.forEach(function (s) {
        n += 1;
        var aktiv = (s.href === datei);
        teile.push(
          '<a href="' + s.href + '"' +
          (aktiv ? ' class="active" aria-current="page"' : '') + '>' +
          '<span class="n">' + n + '</span>' + schuetze(s.titel) + '</a>'
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

  /* Aufgabenkatalog.

     Die Kurzbeschriebe stehen in ki-tasks/aufgaben/<name>/INFO.md und werden
     dort nach aufgaben.json veroeffentlicht. Sie werden hier NICHT noch einmal
     hingeschrieben: eine zweite Kopie veraltet, sobald jemand drueben etwas
     aendert. Kommt eine Aufgabe dazu, erscheint sie hier von selbst.

     Schlaegt der Abruf fehl (kein Netz, oder die Seite wurde als Datei
     geoeffnet, wo der Browser den Abruf sperrt), bleibt der Kasten leer. Der
     Link auf den Katalog steht als Satz daneben und traegt den Fall. */
  var katalog = document.getElementById('aufgaben');
  if (katalog && katalog.dataset.quelle && window.fetch) {
    fetch(katalog.dataset.quelle)
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (aufgaben) {
        if (!Array.isArray(aufgaben) || !aufgaben.length) { return; }
        katalog.innerHTML = aufgaben.map(function (a) {
          return '<a class="card" href="https://stayingclean.github.io/ki-tasks/' +
            encodeURIComponent(a.name) + '.zip">' +
            '<span class="name">' + schuetze(a.titel) + '</span>' +
            '<span class="meta">' + schuetze(a.kurz) + '</span></a>';
        }).join('');
      })
      .catch(function () { /* Katalogseite nebenan traegt den Fall */ });
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
