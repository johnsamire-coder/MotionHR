#!/usr/bin/env python3
"""
Patch 20: PWA - Progressive Web App
=====================================
- manifest.json (تعريف التطبيق)
- Service Worker (العمل بدون إنترنت)
- App Icons (أيقونات)
- Install Banner (زرار تثبيت)
- Offline Page
- Cache Strategy
"""

import os, sys, base64

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")

def create_binary_file(path, content_bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content_bytes)
    print(f"  ✅ تم إنشاء: {path}")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")

def append_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ تم الإضافة لـ: {path}")

print("=" * 60)
print("  Patch 20: PWA")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1. manifest.json
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء manifest.json...")

create_file(
    os.path.join(BASE_DIR, 'static', 'manifest.json'),
    """{
  "name": "MotionHR - إدارة الموارد البشرية",
  "short_name": "MotionHR",
  "description": "HR in Motion - إدارة بسلاسة",
  "start_url": "/dashboard/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait-primary",
  "background_color": "#0f172a",
  "theme_color": "#06B6D4",
  "lang": "ar",
  "dir": "rtl",
  "categories": ["business", "productivity"],
  "icons": [
    {
      "src": "/static/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/static/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/static/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/static/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/static/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/static/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/static/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/static/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable any"
    }
  ],
  "shortcuts": [
    {
      "name": "تسجيل الحضور",
      "short_name": "حضور",
      "description": "سجّل حضورك الآن",
      "url": "/attendance/check-in/",
      "icons": [{"src": "/static/icons/icon-96x96.png", "sizes": "96x96"}]
    },
    {
      "name": "الموظفون",
      "short_name": "موظفون",
      "description": "قائمة الموظفين",
      "url": "/employees/",
      "icons": [{"src": "/static/icons/icon-96x96.png", "sizes": "96x96"}]
    },
    {
      "name": "الخريطة الحية",
      "short_name": "الخريطة",
      "description": "تتبع الموظفين الميدانيين",
      "url": "/attendance/map/",
      "icons": [{"src": "/static/icons/icon-96x96.png", "sizes": "96x96"}]
    }
  ]
}
"""
)


# ════════════════════════════════════════════════════════════
# 2. إنشاء أيقونات SVG → PNG بسيطة
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء أيقونات التطبيق...")

icons_dir = os.path.join(BASE_DIR, 'static', 'icons')
os.makedirs(icons_dir, exist_ok=True)

# SVG بسيط للأيقونة
def make_svg_icon(size):
    return f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <rect width="{size}" height="{size}" rx="{size//5}"
        fill="#06B6D4"/>
  <text x="50%" y="55%"
        font-family="Arial, sans-serif"
        font-size="{size//2}"
        font-weight="bold"
        fill="white"
        text-anchor="middle"
        dominant-baseline="middle">M</text>
</svg>"""

# نحفظ SVG كـ PNG باستخدام Python فقط (بدون مكتبات خارجية)
# نستخدم SVG مباشرة كـ icon لو مفيش Pillow
# ونعمل PNG بسيط يدوياً

def create_simple_png(size, output_path):
    """
    إنشاء PNG بسيط بدون مكتبات خارجية
    أيقونة زرقاء بحرف M أبيض
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # إنشاء صورة
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # خلفية زرقاء مدورة
        margin = size // 10
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=size // 5,
            fill=(6, 182, 212, 255)
        )
        
        # حرف M أبيض
        font_size = size // 2
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        
        text = "M"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width  = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        img.save(output_path, 'PNG')
        return True
    except ImportError:
        # بدون Pillow - نحفظ SVG بدل PNG
        svg_path = output_path.replace('.png', '.svg')
        with open(svg_path, 'w') as f:
            f.write(make_svg_icon(size))
        # نحفظ ملف PNG فاضي كـ placeholder
        # PNG signature + IHDR chunk بسيط
        _write_minimal_png(output_path, size)
        return False


def _write_minimal_png(path, size):
    """كتابة PNG بسيط جداً (مربع أزرق)"""
    import struct, zlib
    
    def png_chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    
    # PNG signature
    sig = b'\x89PNG\r\n\x1a\n'
    
    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    ihdr = png_chunk(b'IHDR', ihdr_data)
    
    # IDAT - صورة زرقاء بسيطة
    raw_rows = []
    for y in range(size):
        row = b'\x00'  # filter type
        for x in range(size):
            row += bytes([6, 182, 212])  # RGB أزرق
        raw_rows.append(row)
    
    raw_data = b''.join(raw_rows)
    compressed = zlib.compress(raw_data, 9)
    idat = png_chunk(b'IDAT', compressed)
    
    # IEND
    iend = png_chunk(b'IEND', b'')
    
    with open(path, 'wb') as f:
        f.write(sig + ihdr + idat + iend)


# إنشاء الأيقونات
sizes = [72, 96, 128, 144, 152, 192, 384, 512]
for size in sizes:
    icon_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
    create_simple_png(size, icon_path)
    print(f"  ✅ icon-{size}x{size}.png")

# Apple Touch Icon
create_simple_png(180, os.path.join(icons_dir, 'apple-touch-icon.png'))
print("  ✅ apple-touch-icon.png")

# Favicon
create_simple_png(32, os.path.join(BASE_DIR, 'static', 'favicon.ico'))
print("  ✅ favicon.ico")


# ════════════════════════════════════════════════════════════
# 3. Service Worker
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء Service Worker...")

create_file(
    os.path.join(BASE_DIR, 'static', 'sw.js'),
    r"""// MotionHR Service Worker
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
"""
)


# ════════════════════════════════════════════════════════════
# 4. Offline Page
# ════════════════════════════════════════════════════════════
print("\n📄 إنشاء صفحة Offline...")

create_file(
    os.path.join(BASE_DIR, 'templates', 'offline.html'),
    r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>غير متصل - MotionHR</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap"
        rel="stylesheet">
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: 'Cairo', sans-serif;
      background: linear-gradient(135deg, #0f172a, #1e3a5f);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      text-align: center;
      padding: 20px;
    }
    .container { max-width: 400px; }
    .icon { font-size: 5rem; margin-bottom: 24px; }
    h1 { font-size: 1.8rem; font-weight: 900; margin-bottom: 12px; }
    p { color: rgba(255,255,255,0.7); margin-bottom: 32px; line-height: 1.6; }
    .btn {
      display: inline-block;
      padding: 12px 32px;
      background: #06B6D4;
      color: white;
      border: none;
      border-radius: 12px;
      font-family: 'Cairo', sans-serif;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.9; }
    .status {
      margin-top: 24px;
      padding: 12px 20px;
      background: rgba(255,255,255,0.1);
      border-radius: 8px;
      font-size: 0.85rem;
      color: rgba(255,255,255,0.6);
    }
    .dot {
      display: inline-block;
      width: 8px; height: 8px;
      border-radius: 50%;
      background: #ef4444;
      margin-left: 8px;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="icon">📡</div>
    <h1>أنت غير متصل بالإنترنت</h1>
    <p>
      تحقق من اتصالك بالإنترنت وحاول مرة أخرى.
      <br>
      بعض الصفحات متاحة بدون إنترنت.
    </p>
    <button class="btn" onclick="window.location.reload()">
      🔄 إعادة المحاولة
    </button>
    <a class="btn" href="/dashboard/" style="margin-right:12px; background:rgba(255,255,255,0.15);">
      🏠 الرئيسية
    </a>
    <div class="status">
      <span class="dot"></span>
      لا يوجد اتصال بالإنترنت
    </div>
  </div>

  <script>
    // لما يرجع الإنترنت - رجّعه للصفحة اللي كان فيها
    window.addEventListener('online', () => {
      window.location.reload();
    });

    // اختبار الاتصال كل 5 ثواني
    setInterval(() => {
      fetch('/dashboard/', { method: 'HEAD', cache: 'no-store' })
        .then(() => window.location.reload())
        .catch(() => {});
    }, 5000);
  </script>
</body>
</html>
"""
)


# ════════════════════════════════════════════════════════════
# 5. PWA View + URL
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة PWA Views...")

# View للـ offline page و manifest و sw
pwa_views = '''

# ════════════════════════════════════════════════════════════
# PWA Views
# ════════════════════════════════════════════════════════════

def offline_view(request):
    """صفحة عدم الاتصال"""
    return render(request, "offline.html")


def manifest_view(request):
    """manifest.json"""
    import json
    from django.http import JsonResponse
    from django.conf import settings as django_settings
    import os

    manifest_path = os.path.join(django_settings.BASE_DIR, "static", "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    response = JsonResponse(manifest_data)
    response["Content-Type"] = "application/manifest+json"
    return response


def service_worker_view(request):
    """Service Worker JS"""
    from django.http import HttpResponse
    from django.conf import settings as django_settings
    import os

    sw_path = os.path.join(django_settings.BASE_DIR, "static", "sw.js")
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_content = f.read()

    response = HttpResponse(sw_content, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response
'''

accounts_views_path = os.path.join(BASE_DIR, 'accounts', 'views.py')
accounts_views = read_file(accounts_views_path)

if 'offline_view' not in accounts_views:
    append_file(accounts_views_path, pwa_views)
else:
    print("  ℹ️  PWA views موجودة")


# ════════════════════════════════════════════════════════════
# 6. إضافة PWA URLs في motionhr/urls.py
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة PWA URLs...")

main_urls_path = os.path.join(BASE_DIR, 'motionhr', 'urls.py')
main_urls_content = read_file(main_urls_path)

if 'offline_view' not in main_urls_content:
    # إضافة imports
    old_import = "from accounts.views import ("
    new_import  = """from accounts.views import ("""
    
    # نضيف offline_view, manifest_view, service_worker_view للـ import
    main_urls_content = main_urls_content.replace(
        "from accounts.views import (\n    CustomPasswordChangeView,\n    smart_login_view,\n    smart_logout_view,\n    dashboard,\n)",
        "from accounts.views import (\n    CustomPasswordChangeView,\n    smart_login_view,\n    smart_logout_view,\n    dashboard,\n    offline_view,\n    manifest_view,\n    service_worker_view,\n)"
    )
    
    # إضافة URLs
    main_urls_content = main_urls_content.replace(
        "    path('', home_redirect, name='home'),",
        """    path('', home_redirect, name='home'),

    # ── PWA ───────────────────────────────────────────────
    path('offline/',     offline_view,        name='offline'),
    path('manifest.json', manifest_view,      name='manifest'),
    path('sw.js',        service_worker_view, name='service_worker'),
"""
    )
    write_file(main_urls_path, main_urls_content)
else:
    print("  ℹ️  PWA URLs موجودة")


# ════════════════════════════════════════════════════════════
# 7. تحديث base.html - إضافة PWA meta tags + SW registration
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث base/base.html...")

base_html_path = os.path.join(BASE_DIR, 'templates', 'base', 'base.html')

if os.path.exists(base_html_path):
    base_content = read_file(base_html_path)

    pwa_meta = """
  <!-- PWA Meta Tags -->
  <meta name="theme-color" content="#06B6D4">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="MotionHR">
  <link rel="manifest" href="/manifest.json">
  <link rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/static/icons/icon-96x96.png">"""

    pwa_sw_script = """
  <!-- PWA Service Worker -->
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
          .then(reg => console.log('[PWA] SW registered:', reg.scope))
          .catch(err => console.warn('[PWA] SW failed:', err));
      });
    }
  </script>"""

    if 'manifest' not in base_content:
        # إضافة قبل </head>
        base_content = base_content.replace('</head>', pwa_meta + '\n</head>')
        print("  ✅ تم إضافة PWA meta tags")

    if 'serviceWorker' not in base_content:
        # إضافة قبل </body>
        base_content = base_content.replace('</body>', pwa_sw_script + '\n</body>')
        print("  ✅ تم إضافة Service Worker registration")

    write_file(base_html_path, base_content)
else:
    print("  ⚠️  base.html مش موجود")


# ════════════════════════════════════════════════════════════
# 8. تحديث dashboard_base.html - إضافة Install Banner
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة Install Banner في dashboard_base.html...")

dashboard_base_path = os.path.join(BASE_DIR, 'templates', 'base', 'dashboard_base.html')
dashboard_base = read_file(dashboard_base_path)

install_banner = r"""
  <!-- PWA Install Banner -->
  <div id="installBanner"
       class="d-none"
       style="position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
              z-index:9999; min-width:300px; max-width:400px;">
    <div class="card border-0 shadow-lg"
         style="border-radius:16px; overflow:hidden;">
      <div class="card-body p-3 d-flex align-items-center gap-3"
           style="background: linear-gradient(135deg, #0f172a, #1e3a5f);">
        <img src="/static/icons/icon-72x72.png"
             width="48" height="48"
             class="rounded-3" alt="MotionHR">
        <div class="flex-grow-1">
          <div class="fw-bold text-white small">MotionHR</div>
          <div class="text-white-50 small">ثبّت التطبيق على جهازك</div>
        </div>
        <div class="d-flex gap-2">
          <button id="installBtn"
                  class="btn btn-sm text-white fw-bold"
                  style="background:#06B6D4; border-radius:8px; font-size:0.8rem;">
            تثبيت
          </button>
          <button id="dismissBtn"
                  class="btn btn-sm"
                  style="background:rgba(255,255,255,0.1); color:white;
                         border-radius:8px; font-size:0.8rem;">
            ✕
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- PWA Install Script -->
  <script>
    let deferredPrompt = null;
    const banner  = document.getElementById('installBanner');
    const installBtn = document.getElementById('installBtn');
    const dismissBtn = document.getElementById('dismissBtn');

    // استقبال حدث التثبيت
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;

      // اعرض الـ Banner لو مش متثبت
      if (!localStorage.getItem('pwa-dismissed')) {
        setTimeout(() => banner.classList.remove('d-none'), 3000);
      }
    });

    // زرار التثبيت
    installBtn?.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log('[PWA] Install outcome:', outcome);
      deferredPrompt = null;
      banner.classList.add('d-none');
    });

    // زرار الإغلاق
    dismissBtn?.addEventListener('click', () => {
      banner.classList.add('d-none');
      localStorage.setItem('pwa-dismissed', '1');
    });

    // لو اتثبت - اخفي الـ Banner
    window.addEventListener('appinstalled', () => {
      banner.classList.add('d-none');
      console.log('[PWA] App installed!');
    });
  </script>"""

if 'installBanner' not in dashboard_base:
    dashboard_base = dashboard_base.replace('</body>', install_banner + '\n</body>')
    write_file(dashboard_base_path, dashboard_base)
    print("  ✅ تم إضافة Install Banner")
else:
    print("  ℹ️  Install Banner موجود")


# ════════════════════════════════════════════════════════════
# 9. إنشاء static/css/pwa.css
# ════════════════════════════════════════════════════════════
print("\n🔧 إنشاء static/css/pwa.css...")

create_file(
    os.path.join(BASE_DIR, 'static', 'css', 'pwa.css'),
    """/* PWA Styles */

/* منع التحديد على الموبايل للعناصر التفاعلية */
.nav-link, .btn, .card {
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

/* تحسين الـ touch */
button, a, .btn {
  touch-action: manipulation;
}

/* Safe Area لـ iPhone X+ */
body {
  padding-bottom: env(safe-area-inset-bottom);
}

.sidebar {
  padding-bottom: calc(env(safe-area-inset-bottom) + 20px);
}

/* Splash Screen */
@media (display-mode: standalone) {
  body::before {
    content: '';
    display: none;
  }

  /* إخفاء بعض العناصر في وضع التطبيق */
  .hide-in-app {
    display: none !important;
  }
}

/* تحسين الـ Scrolling على الموبايل */
.table-responsive,
.sidebar,
.content-area {
  -webkit-overflow-scrolling: touch;
}

/* Loading Indicator */
.pwa-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #06B6D4, #0891B2, #06B6D4);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  z-index: 10000;
}

@keyframes loading {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Online/Offline Indicator */
.connection-status {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  z-index: 9998;
  transition: all 0.3s;
}

.connection-status.online {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #4caf50;
}

.connection-status.offline {
  background: #fde8e8;
  color: #c62828;
  border: 1px solid #ef5350;
}
"""
)


# ════════════════════════════════════════════════════════════
# 10. إضافة Connection Status Script
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة Connection Status في dashboard_base.html...")

dashboard_base = read_file(dashboard_base_path)

connection_script = r"""
  <!-- Connection Status -->
  <div id="connectionStatus" class="connection-status d-none"></div>
  <script>
    const statusEl = document.getElementById('connectionStatus');

    function updateStatus() {
      if (navigator.onLine) {
        statusEl.className = 'connection-status online';
        statusEl.textContent = '✅ متصل';
        setTimeout(() => statusEl.classList.add('d-none'), 2000);
      } else {
        statusEl.className = 'connection-status offline';
        statusEl.textContent = '❌ غير متصل';
        statusEl.classList.remove('d-none');
      }
    }

    window.addEventListener('online',  updateStatus);
    window.addEventListener('offline', updateStatus);
  </script>"""

if 'connectionStatus' not in dashboard_base:
    dashboard_base = dashboard_base.replace('</body>', connection_script + '\n</body>')
    write_file(dashboard_base_path, dashboard_base)
    print("  ✅ تم إضافة Connection Status")
else:
    print("  ℹ️  Connection Status موجود")


# ════════════════════════════════════════════════════════════
# 11. إضافة pwa.css في dashboard_base.html
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة pwa.css في dashboard_base.html...")

dashboard_base = read_file(dashboard_base_path)

if 'pwa.css' not in dashboard_base:
    dashboard_base = dashboard_base.replace(
        '</head>',
        '  <link rel="stylesheet" href="/static/css/pwa.css">\n</head>'
    )
    write_file(dashboard_base_path, dashboard_base)
    print("  ✅ تم إضافة pwa.css")
else:
    print("  ℹ️  pwa.css موجود")


# ════════════════════════════════════════════════════════════
# النهاية
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Patch 20 اكتمل بنجاح!")
print("=" * 60)
print("""
📋 اللي اتعمل:
  1.  ✅ manifest.json - تعريف التطبيق
  2.  ✅ أيقونات بكل المقاسات (8 أيقونات)
  3.  ✅ sw.js - Service Worker كامل
  4.  ✅ offline.html - صفحة عدم الاتصال
  5.  ✅ PWA Views (offline, manifest, sw)
  6.  ✅ PWA URLs
  7.  ✅ Meta Tags في base.html
  8.  ✅ SW Registration
  9.  ✅ Install Banner
  10. ✅ pwa.css
  11. ✅ Connection Status Indicator

🔗 URLs الجديدة:
  /manifest.json  ← تعريف التطبيق
  /sw.js          ← Service Worker
  /offline/       ← صفحة عدم الاتصال

📱 لتجربة PWA:
  1. شغّل السيرفر
  2. افتح Chrome على الموبايل
  3. روح على http://192.168.1.45:8000
  4. هيظهر Banner "تثبيت التطبيق"
  5. اضغط تثبيت

🚀 الخطوة الجاية: Patch 21 - Landing Page
""")