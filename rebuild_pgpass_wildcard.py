import os
import stat
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from django.conf import settings

db = settings.DATABASES['default']

host = db.get('HOST') or 'localhost'
port = str(db.get('PORT') or '5432')
user = db.get('USER') or ''
password = db.get('PASSWORD') or ''

if not all([host, port, user, password]):
    raise SystemExit("MISSING_DB_FIELDS")

lines = [
    f"{host}:{port}:*:{user}:{password}",
]

# نزود 127.0.0.1 لو الهوست localhost
if host == 'localhost':
    lines.append(f"127.0.0.1:{port}:*:{user}:{password}")

path = "/root/.pgpass"
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 600

print("PGPASS_REBUILT_OK")
print(f"PATH={path}")
print(f"HOSTS_WRITTEN={[line.split(':')[0] for line in lines]}")
print(f"PORT={port}")
print(f"USER={user}")
print("DATABASE=*")
print("PASSWORD=***HIDDEN***")
