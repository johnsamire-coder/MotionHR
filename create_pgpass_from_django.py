import os
import stat
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from django.conf import settings

db = settings.DATABASES['default']

host = db.get('HOST') or 'localhost'
port = str(db.get('PORT') or '5432')
name = db.get('NAME') or ''
user = db.get('USER') or ''
password = db.get('PASSWORD') or ''

if not all([host, port, name, user, password]):
    raise SystemExit("MISSING_DB_FIELDS")

content = f"{host}:{port}:{name}:{user}:{password}\n"

path = "/root/.pgpass"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 600

print("PGPASS_CREATED_OK")
print(f"PATH={path}")
print(f"HOST={host}")
print(f"PORT={port}")
print(f"DB={name}")
print(f"USER={user}")
print("PASSWORD=***HIDDEN***")
