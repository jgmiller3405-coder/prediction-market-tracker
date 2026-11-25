/* Service worker: the app shell is cached on install; data files are network-first with a saved copy as fallback. */
const VERSION = "v3";
const SHELL = `odds-shell-${VERSION}`;
const DATA = `odds-data-${VERSION}`;
const SHELL_FILES = [
  "./", "index.html", "browse.html", "trends.html", "app.css", "app.js", "lib.js",
  "vendor/chart.umd.js", "manifest.webmanifest", "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL).then((c) => Promise.all(SHELL_FILES.map((f) => c.add(new Request(f, { cache: "reload" }))))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => ![SHELL, DATA].includes(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;

  if (url.pathname.includes("/data/")) {
    // online: take the network answer and keep a copy; offline: the last copy
    event.respondWith(
      fetch(req, { cache: "no-cache" }).then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(DATA).then((c) => c.put(req, copy)); }
        return res;
      }).catch(() => caches.match(req, { ignoreSearch: true }))
    );
    return;
  }

  // pages and assets: network first so a new deploy shows up, saved copy when offline
  event.respondWith(
    fetch(req, { cache: "no-cache" }).then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(SHELL).then((c) => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then((hit) => hit || caches.match("index.html")))
  );
});
