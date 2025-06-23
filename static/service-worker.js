const CACHE_NAME = 'fallahi-smartirrig-v1';
const urlsToCache = [
  '/',
  '/dashboard',
  '/login',
  '/register',
  '/profile',
  '/notifications',
  '/guide',
  '/static/css/style.css',
  '/static/img/image.png',
  '/static/js/main.js',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
}); 