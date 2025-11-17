/*! coi-serviceworker */
// Enables SharedArrayBuffer + COOP/COEP
self.addEventListener("install", e => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", event => {
  const r = event.request;
  if (r.cache === "only-if-cached" && r.mode !== "same-origin") return;

  event.respondWith(
    fetch(r).then(resp => {
      const newHeaders = new Headers(resp.headers);
      newHeaders.set("Cross-Origin-Opener-Policy", "same-origin");
      newHeaders.set("Cross-Origin-Embedder-Policy", "require-corp");
      newHeaders.set("Cross-Origin-Resource-Policy", "cross-origin");

      return new Response(resp.body, {
        status: resp.status,
        statusText: resp.statusText,
        headers: newHeaders
      });
    })
  );
});
