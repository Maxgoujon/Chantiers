/* Chantiers — le technicien doit pouvoir travailler dans un sous-sol.
   Coquille en cache, données en IndexedDB : rien ne dépend du réseau
   avant l'envoi final. */
const CACHE = "chantiers-v8";
const COQUILLE = [
  "/chantier",
  "/static/chantier-manifest.json",
  "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
  "https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap",
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE)
    .then(c => Promise.all(COQUILLE.map(u => c.add(u).catch(() => {}))))
    .then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(k => Promise.all(k.filter(n => n !== CACHE).map(n => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // L'envoi ne doit jamais sortir du cache : il part ou il échoue.
  if (e.request.method !== "GET" || url.pathname.startsWith("/chantier/envoi")) return;

  const estLaPage = e.request.mode === "navigate" || url.pathname === "/chantier";

  if (estLaPage) {
    // Réseau d'abord : sinon une correction déployée n'atteint jamais le
    // téléphone du technicien, qui reste sur une version morte sans le savoir.
    e.respondWith(
      fetch(e.request).then(r => {
        if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put("/chantier", c)); }
        return r;
      }).catch(() => caches.match("/chantier"))
    );
    return;
  }

  // Le reste ne bouge pas : cache d'abord, c'est ce qui fait tenir hors ligne.
  e.respondWith(
    caches.match(e.request).then(rep => rep || fetch(e.request).then(r => {
      if (r.ok && (url.origin === location.origin || url.hostname.includes("cdnjs")
                   || url.hostname.includes("fonts."))) {
        const copie = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, copie));
      }
      return r;
    }))
  );
});
