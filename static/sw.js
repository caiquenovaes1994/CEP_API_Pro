const CACHE_NAME = 'cep-api-pro-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/index.html',
  '/static/logo.png',
  '/static/manifest.json'
];

// Instalação do Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(ASSETS_TO_CACHE);
      })
  );
});

// Interceptando requisições
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Retorna do cache se encontrar, senão vai para a rede
        return response || fetch(event.request);
      })
  );
});
