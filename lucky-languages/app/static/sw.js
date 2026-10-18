const CACHE = "linguabloom-academy-shell-v2";
const SHELL = ["/", "/static/manifest.webmanifest", "/static/icon.svg"];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname === "/api/courses" || /^\/api\/courses\/\d+$/.test(url.pathname)) {
    event.respondWith(fetch(req).then(res => {
      if (res.ok) caches.open(CACHE).then(cache => cache.put(req, res.clone()));
      return res;
    }).catch(async () => (await caches.match(req)) || new Response(JSON.stringify({detail:"Contenu non disponible hors ligne"}), {status:503,headers:{"Content-Type":"application/json"}})));
    return;
  }
  if (req.mode === "navigate" || SHELL.includes(url.pathname)) {
    event.respondWith(fetch(req).catch(async () => (await caches.match(req)) || (await caches.match("/"))));
  }
});
