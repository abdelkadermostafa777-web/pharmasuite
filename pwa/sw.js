/* Caches the app the first time it loads, so it opens without internet afterwards. */
const CACHE = "pharmasuite-offline-v1";
const APP_FILES = [
  "./", "./index.html", "./offline.js", "./manifest.webmanifest",
  "./icon-192.png", "./icon-512.png",
  "./data/drugs.json", "./data/formulation.json", "./data/elements.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) =>
      Promise.all(APP_FILES.map((f) => cache.add(f).catch(() => null)))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((hit) => {
      if (hit) return hit;
      return fetch(event.request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy)).catch(() => {});
          return res;
        })
        .catch(() => hit);
    })
  );
});
