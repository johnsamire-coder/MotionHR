# أوامر السيرفر Ubuntu — MotionHR

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
\q

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
