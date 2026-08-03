import os
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motionhr.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
client = APIClient()

response = client.post(
    '/attendance/api/mobile/login/',
    {'username': 'hr_motionhr', 'password': '12345678'},
    format='json',
    HTTP_HOST='motion.jssolutions-eg.com'
)

print('STATUS =', response.status_code)

try:
    data = response.json()
except Exception:
    print('NON_JSON:', response.content[:500])
    exit()

print('token =', data.get('token', 'MISSING')[:20] if data.get('token') else 'MISSING')
print('access =', data.get('access', 'MISSING')[:30] if data.get('access') else 'MISSING')
print('refresh =', data.get('refresh', 'MISSING')[:30] if data.get('refresh') else 'MISSING')
print('role =', data.get('role'))
print('app_mode =', data.get('app_mode'))
print()

# تحقق إن الـ access يشتغل فعلًا
if data.get('access'):
    client2 = APIClient()
    client2.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
    r2 = client2.get(
        '/attendance/api/mobile/status/',
        HTTP_HOST='motion.jssolutions-eg.com'
    )
    print('Bearer access test → STATUS =', r2.status_code)
else:
    print('access token MISSING — skipping Bearer test')

# تحقق إن الـ refresh يشتغل فعلًا
if data.get('refresh'):
    r3 = client.post(
        '/attendance/api/mobile/jwt/refresh/',
        {'refresh': data['refresh']},
        format='json',
        HTTP_HOST='motion.jssolutions-eg.com'
    )
    print('Refresh test → STATUS =', r3.status_code)
    try:
        r3_data = r3.json()
        print('new_access =', r3_data.get('access', 'MISSING')[:30] if r3_data.get('access') else 'MISSING')
    except Exception:
        print('Refresh response:', r3.content[:200])
else:
    print('refresh token MISSING — skipping refresh test')
