const CACHE_NAME = 'portal-pesquisador-cache-v2';
const ASSETS = [
  './index.html',
  './manifest.json',
  './logo.png'
];

// Instalação rápida: pré-cache apenas dos arquivos de interface essenciais
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Limpeza de caches antigos
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Intercepção de requisições: Cache Dinâmico para o banco de dados dados.csv
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(e.request).then((networkResponse) => {
        // Se for o banco de dados dados.csv, salva em cache dinamicamente após o primeiro download com sucesso
        if (networkResponse && networkResponse.status === 200 && e.request.url.includes('dados.csv')) {
          const cacheCopy = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(e.request, cacheCopy);
          });
        }
        return networkResponse;
      });
    })
  );
});
