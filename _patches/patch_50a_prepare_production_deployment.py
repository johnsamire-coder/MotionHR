"""
Patch 50a — Prepare MotionHR for Production Deployment

الهدف:
1) تجهيز settings.py للإنتاج بدون كسر التطوير
2) إنشاء ملفات deployment جاهزة:
   - .env.example
   - gunicorn.service
   - nginx.conf
   - deploy_checklist.md
   - ubuntu_server_commands.md
3) إضافة إعدادات PostgreSQL + ALLOWED_HOSTS + SSL + STATIC_ROOT
4) كل ده بدون ما نحتاج تعديل يدوي في الكود لاحقًا

هذا الباتش لا يغير قاعدة البيانات
ولا يشغل أي migrate
فقط يجهز المشروع للرفع
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_file(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    full = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ كُتب: {path}")

def backup(rel_path, backup_name):
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(full, os.path.join(backup_dir, backup_name))
        print(f"✅ Backup: _patches/_backups/{backup_name}")

print("=" * 70)
print("Patch 50a — Prepare MotionHR for Production Deployment")
print("=" * 70)

# Backups
backup("motionhr/settings.py", "motionhr_settings_before_50a.py.bak")
backup("motionhr/urls.py", "motionhr_urls_before_50a.py.bak")

# ────────────────────────────────────────────────────────────
# Step 1: Append production block to settings.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: تجهيز settings.py للإنتاج")

settings_path = "motionhr/settings.py"
settings_content = read_file(settings_path)
if settings_content is None:
    raise SystemExit("❌ ملف motionhr/settings.py غير موجود")

prod_block = r'''

# ═════════════════════════════════════════════════════════════
# Patch 50a — Production Deployment Overrides
# ═════════════════════════════════════════════════════════════
import os

# ── Environment helpers ─────────────────────────────────────
def _env_bool(name, default=False):
    value = os.getenv(name, str(default))
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

def _env_list(name, default=''):
    value = os.getenv(name, default)
    return [item.strip() for item in str(value).split(',') if item.strip()]

# ── Core ────────────────────────────────────────────────────
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', SECRET_KEY)
DEBUG = _env_bool('DJANGO_DEBUG', DEBUG)

try:
    _default_hosts = ",".join(ALLOWED_HOSTS) if isinstance(ALLOWED_HOSTS, (list, tuple)) else str(ALLOWED_HOSTS)
except Exception:
    _default_hosts = ''
ALLOWED_HOSTS = _env_list('DJANGO_ALLOWED_HOSTS', _default_hosts or '127.0.0.1,localhost')

# CSRF trusted origins
_default_csrf = os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '')
if _default_csrf:
    CSRF_TRUSTED_ORIGINS = _env_list('DJANGO_CSRF_TRUSTED_ORIGINS', _default_csrf)
else:
    try:
        if not DEBUG:
            CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host not in ['127.0.0.1', 'localhost']]
    except Exception:
        pass

# ── Database: PostgreSQL if env exists ──────────────────────
if os.getenv('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', ''),
            'USER': os.getenv('POSTGRES_USER', ''),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }

# ── Static / Media ──────────────────────────────────────────
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Security for production behind Nginx ────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = _env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# ── Default admin contacts ──────────────────────────────────
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'info@jssolutions.com')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
'''

if "Patch 50a — Production Deployment Overrides" not in settings_content:
    settings_content = settings_content.rstrip() + "\n" + prod_block + "\n"
    write_file(settings_path, settings_content)
else:
    print("ℹ️ production block موجود بالفعل")

# ────────────────────────────────────────────────────────────
# Step 2: Create deployment files
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إنشاء ملفات deployment")

env_example = """# MotionHR Production Environment
DJANGO_SECRET_KEY=CHANGE_ME_TO_A_LONG_RANDOM_SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=app.motionhr-eg.com,motionhr-eg.com,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://app.motionhr-eg.com,https://motionhr-eg.com
DJANGO_SECURE_SSL_REDIRECT=True

POSTGRES_DB=motionhr_db
POSTGRES_USER=motionhr_user
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

DEFAULT_FROM_EMAIL=info@jssolutions.com
SERVER_EMAIL=info@jssolutions.com
"""
write_file("_deploy/.env.example", env_example)

gunicorn_service = """[Unit]
Description=MotionHR Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/motionhr/app
EnvironmentFile=/opt/motionhr/app/_deploy/.env
ExecStart=/opt/motionhr/app/.venv/bin/gunicorn motionhr.wsgi:application --bind 127.0.0.1:8001 --workers 3 --timeout 120

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
write_file("_deploy/gunicorn_motionhr.service", gunicorn_service)

nginx_conf = """server {
    listen 80;
    server_name app.motionhr-eg.com motionhr-eg.com;

    client_max_body_size 30M;

    location /static/ {
        alias /opt/motionhr/app/staticfiles/;
    }

    location /media/ {
        alias /opt/motionhr/app/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
}
"""
write_file("_deploy/nginx_motionhr.conf", nginx_conf)

deploy_checklist = """# MotionHR — Production Deployment Checklist

## ما الذي ستشتريه؟
1. دومين
2. VPS Ubuntu 22.04

## أقل مواصفات مناسبة:
- 2 vCPU
- 2 GB RAM
- 50 GB SSD
- Ubuntu 22.04

## البيانات التي أحتاجها منك بعد الشراء:
1. IP السيرفر
2. اسم الدومين
3. اسم المستخدم للدخول (غالبًا root)
4. كلمة المرور أو SSH access

## التسلسل:
1. شراء الدومين
2. شراء VPS
3. ربط الدومين بالـ IP
4. رفع المشروع
5. إعداد PostgreSQL
6. إعداد Gunicorn
7. إعداد Nginx
8. تفعيل SSL
9. اختبار:
   - /
   - /pricing/
   - /free-trial/
   - /accounts/login/
"""
write_file("_deploy/deploy_checklist.md", deploy_checklist)

ubuntu_commands = """# أوامر السيرفر Ubuntu — MotionHR

## 1) تحديث السيرفر
sudo apt update && sudo apt upgrade -y

## 2) تثبيت الأدوات الأساسية
sudo apt install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib git

## 3) إنشاء مجلد المشروع
sudo mkdir -p /opt/motionhr
sudo chown -R $USER:$USER /opt/motionhr

## 4) ارفع ملفات المشروع إلى:
# /opt/motionhr/app

## 5) ادخل المجلد
cd /opt/motionhr/app

## 6) إنشاء venv
python3 -m venv .venv
source .venv/bin/activate

## 7) تثبيت الباكدجات
pip install --upgrade pip
pip install Django gunicorn psycopg[binary] reportlab arabic-reshaper python-bidi openpyxl xhtml2pdf pillow

## 8) PostgreSQL
sudo -u postgres psql

# داخل psql:
CREATE DATABASE motionhr_db;
CREATE USER motionhr_user WITH PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
ALTER ROLE motionhr_user SET client_encoding TO 'utf8';
ALTER ROLE motionhr_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE motionhr_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE motionhr_db TO motionhr_user;
\\q

## 9) إنشاء ملف .env من المثال
cp _deploy/.env.example _deploy/.env
# ثم عدّل القيم داخل الملف

## 10) المايجريشن والستاتيك
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check

## 11) Gunicorn service
sudo cp _deploy/gunicorn_motionhr.service /etc/systemd/system/motionhr.service
sudo systemctl daemon-reload
sudo systemctl enable motionhr
sudo systemctl start motionhr
sudo systemctl status motionhr

## 12) Nginx
sudo cp _deploy/nginx_motionhr.conf /etc/nginx/sites-available/motionhr
sudo ln -s /etc/nginx/sites-available/motionhr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

## 13) SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d app.motionhr-eg.com -d motionhr-eg.com

## 14) اختبر
https://app.motionhr-eg.com/
https://app.motionhr-eg.com/pricing/
https://app.motionhr-eg.com/free-trial/
https://app.motionhr-eg.com/accounts/login/
"""
write_file("_deploy/ubuntu_server_commands.md", ubuntu_commands)

# ────────────────────────────────────────────────────────────
# Step 3: Create production budget sheet
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: إنشاء ورقة ميزانية بسيطة")

budget_md = """# MotionHR — أبسط Setup احترافي

## 1) Domain
- السعر السنوي المتوقع: 400 إلى 900 جنيه

## 2) VPS
- المواصفات:
  - 2 vCPU
  - 2 GB RAM
  - 50 GB SSD
  - Ubuntu 22.04
- السعر الشهري المتوقع:
  - 300 إلى 600 جنيه

## 3) SSL
- مجاني (Let's Encrypt)

## 4) PostgreSQL
- مجاني داخل السيرفر

## 5) Backup
- يمكن البدء بدون تكلفة إضافية أو 50-100 جنيه تقريبًا شهريًا لاحقًا

## التكلفة المتوقعة:
### أول شهر:
- Domain: 500–900
- VPS: 300–600
- الإجمالي: تقريبًا 800–1500 جنيه

### بعد ذلك شهريًا:
- VPS فقط غالبًا: 300–600 جنيه
"""
write_file("_deploy/budget_estimate.md", budget_md)

print("\n" + "=" * 70)
print("✅ Patch 50a اكتمل")
print("=" * 70)
print("""
اللي اتعمل:
  ✅ تجهيز settings.py للإنتاج
  ✅ إنشاء ملفات deployment جاهزة في مجلد _deploy/
     - .env.example
     - gunicorn_motionhr.service
     - nginx_motionhr.conf
     - deploy_checklist.md
     - ubuntu_server_commands.md
     - budget_estimate.md

الخطوة التالية:
  1) اشترِ دومين
  2) اشترِ VPS
  3) ابعتلي:
     - IP السيرفر
     - اسم الدومين
     - نوع الشركة اللي اخترتها
وأنا هكملك "خطوة بخطوة" بالضبط
""")