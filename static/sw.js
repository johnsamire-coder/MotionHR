// MotionHR Service Worker
// ========================

const CACHE_NAME = 'motionhr-v1';
const OFFLINE_URL = '/offline/';

// الملفات اللي هنخزنها في الـ Cache
const STATIC_ASSETS = [
  '/',
  '/dashboard/',
  '/offline/',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css',
];

// ── Install ──────────────────────────────────────────────
self.addEventListener('install', event => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching static assets');
        // نحاول نخزن كل ملف بشكل منفرد لتجنب الفشل الكامل
        return Promise.allSettled(
          STATIC_ASSETS.map(url =>
            cache.add(url).catch(err =>
              console.warn('[SW] Failed to cache:', url, err)
            )
          )
        );
      })
      .then(() => self.skipWaiting())
  );
});

// ── Activate ─────────────────────────────────────────────
self.addEventListener('activate', event => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch Strategy ───────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // تجاهل الطلبات غير HTTP
  if (!request.url.startsWith('http')) return;

  // تجاهل Admin + API + Media
  if (
    url.pathname.startsWith('/admin/') ||
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/media/')
  ) return;

  // GPS/Location APIs - دايماً من الشبكة
  if (
    url.pathname.includes('check-in') ||
    url.pathname.includes('check-out') ||
    url.pathname.includes('track') ||
    url.pathname.includes('live')
  ) {
    event.respondWith(
      fetch(request).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // Navigation requests - Network First
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(response => {
          // نخزن نسخة في الـ Cache
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          return response;
        })
        .catch(() =>
          caches.match(request)
            .then(cached => cached || caches.match(OFFLINE_URL))
        )
    );
    return;
  }

  // Static assets - Cache First
  if (
    url.pathname.startsWith('/static/') ||
    url.hostname.includes('cdn.jsdelivr.net') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com')
  ) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          return response;
        });
      })
    );
    return;
  }

  // باقي الطلبات - Network First with Cache Fallback
  event.respondWith(
    fetch(request)
      .catch(() => caches.match(request))
  );
});

// ── Background Sync ──────────────────────────────────────
self.addEventListener('sync', event => {
  if (event.tag === 'sync-attendance') {
    console.log('[SW] Syncing attendance...');
    // هنضيف الـ sync logic لاحقاً
  }
});

// ── Push Notifications ───────────────────────────────────
self.addEventListener('push', event => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body:    data.body || '',
    icon:    '/static/icons/icon-192x192.png',
    badge:   '/static/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    dir:     'rtl',
    lang:    'ar',
    data:    { url: data.url || '/dashboard/' },
    actions: [
      { action: 'open',    title: 'فتح' },
      { action: 'dismiss', title: 'إغلاق' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'MotionHR', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'dismiss') return;

  const url = event.notification.data?.url || '/dashboard/';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(windowClients => {
      for (const client of windowClients) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
