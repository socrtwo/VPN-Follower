// Minimal offline-shell cache for the VPN-Follower PWA.
// The app shell is cached so it launches offline; /api/* is always network
// (lookups inherently require connectivity) and is never cached.
const CACHE = "vpnfollower-shell-v1";
const SHELL = [
  ".",
  "index.html",
  "styles.css",
  "app.js",
  "manifest.webmanifest",
  "icons/icon-192.png",
  "icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.includes("/api/")) return; // never cache live lookups
  event.respondWith(
    caches.match(event.request).then((hit) => hit || fetch(event.request))
  );
});
