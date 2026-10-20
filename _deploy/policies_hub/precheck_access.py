# فحص قبل تصليحات الدخول وإيقاف الشركات — قراءة فقط، مابيغيرش أي حاجة.
#
# التشغيل على السيرفر (سطر واحد):
#   sudo sh -c 'zcat -f /var/log/nginx/*access*.log* > /tmp/ngx_mhr.txt 2>/dev/null; chmod 644 /tmp/ngx_mhr.txt'; cd /var/www/motionhr && curl -fsSL https://raw.githubusercontent.com/johnsamire-coder/motionhr/fix/group1-access/_deploy/policies_hub/precheck_access.py | ./venv/bin/python manage.py shell; rm -f /tmp/ngx_mhr.txt
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone

from companies.models import Company
from employees.models import Employee

User = get_user_model()
now = timezone.now()
since = now - timedelta(days=14)


def title(t):
    print('\n' + '═' * 60 + '\n' + t + '\n' + '═' * 60)


def company_name(cid):
    c = Company._base_manager.filter(id=cid).first()
    return f'{cid}: {c.name_ar}' if c else f'{cid}: (مش موجودة)'


# ── 1) الموقع القديم ──
title('1) استخدام الموقع القديم (صفحات Django) آخر 14 يوم')

OLD_SEGMENTS = {
    'dashboard', 'employees', 'attendance', 'companies', 'leaves', 'requests',
    'reports', 'subscriptions', 'accounts', 'admin', 'announcements', 'search', 'password-change',
}
log_path = '/tmp/ngx_mhr.txt'
if os.path.exists(log_path) and os.path.getsize(log_path):
    line_re = re.compile(r'^(\S+) \S+ \S+ \[(\d{2}/\w{3}/\d{4}):[^\]]+\] "(\w+) (\S+)[^"]*" (\d{3})')
    by_page, by_day, by_ip, by_status = Counter(), Counter(), Counter(), Counter()
    total = 0
    for raw in open(log_path, encoding='utf-8', errors='ignore'):
        m = line_re.match(raw)
        if not m:
            continue
        ip, day, method, path, status = m.groups()
        try:
            d = datetime.strptime(day, '%d/%b/%Y').date()
        except ValueError:
            continue
        if d < since.date():
            continue
        path = path.split('?')[0]
        seg = path.strip('/').split('/')[0] if path.strip('/') else ''
        if seg not in OLD_SEGMENTS or '/api/' in path or path.startswith('/static/') or path.startswith('/media/'):
            continue
        if any(b in raw.lower() for b in ('bot', 'crawl', 'spider')):
            continue
        total += 1
        by_page[re.sub(r'/\d+', '/N', path)] += 1
        by_day[str(d)] += 1
        by_ip[ip] += 1
        by_status[status] += 1
    print(f'عدد الطلبات على صفحات الموقع القديم: {total}')
    if total:
        print('حسب النتيجة (200 = اتفتحت، 302 = اتحول لصفحة الدخول، 403/404 = اترفض):', dict(by_status))
        print('حسب اليوم:', dict(sorted(by_day.items())))
        print(f'عدد الأجهزة (IP) المختلفة: {len(by_ip)}')
        print('أكتر 25 صفحة:')
        for p, n in by_page.most_common(25):
            print(f'   {n:6}  {p}')
else:
    print('مالقيتش سجلات nginx (يمكن الأمر الأول ماتنفذش بـ sudo).')

users_recent = User._base_manager.filter(last_login__gte=since)
print(f'\nمستخدمين دخلوا من صفحة الدخول القديمة آخر 14 يوم: {users_recent.count()}')
for (cid, role), n in sorted(Counter((u.company_id, u.role) for u in users_recent).items(), key=lambda x: str(x)):
    print(f'   شركة {company_name(cid) if cid else "-"} | الدور {role}: {n}')

live_sessions = Session.objects.filter(expire_date__gte=now)
sess_users = Counter()
for s in live_sessions:
    uid = s.get_decoded().get('_auth_user_id')
    if uid:
        u = User._base_manager.filter(pk=uid).first()
        if u:
            sess_users[(u.company_id, u.role)] += 1
print(f'جلسات شغالة على الموقع القديم دلوقتي: {sum(sess_users.values())}')
for (cid, role), n in sorted(sess_users.items(), key=lambda x: str(x)):
    print(f'   شركة {company_name(cid) if cid else "-"} | الدور {role}: {n}')

# ── 2) قبل تشغيل الإيقاف ──
title('2) حالة الشركات والحسابات (قبل تشغيل الإيقاف)')

inactive_companies = Company._base_manager.filter(is_active=False)
print(f'شركات متعلّم عليها "مش نشطة" دلوقتي: {inactive_companies.count()}  ← دي هتتقفل أول ما الإيقاف يشتغل، لازم نراجعها قبل الرفع')
for c in inactive_companies:
    print(f'   {c.id}: {c.name_ar} — موظفين نشطين: {Employee._base_manager.filter(company=c, status="active").count()}')

try:
    from subscriptions.models import CompanySubscription
    print('\nحالة الاشتراكات:', dict(Counter(CompanySubscription._base_manager.values_list('status', flat=True))))
    expired = CompanySubscription._base_manager.filter(end_date__lt=now.date())
    print(f'اشتراكات تاريخ انتهائها فات: {expired.count()}')
    for s in expired.select_related('company'):
        print(f'   {s.company_id}: {s.company.name_ar} — انتهى {s.end_date} — الحالة {s.status}')
except Exception as e:
    print('مقدرتش أقرا الاشتراكات:', e)

gpr = Company._base_manager.filter(id=61).first()
if gpr:
    print(f'\nشركة رقم 61: {gpr.name_ar} / {gpr.name_en} — نشطة: {gpr.is_active}')
    print(f'   موظفين نشطين: {Employee._base_manager.filter(company=gpr, status="active").count()}'
          f' — حسابات مستخدمين: {User._base_manager.filter(company=gpr).count()}')
else:
    print('\nمفيش شركة رقم 61')

inactive_but_working = Employee._base_manager.filter(status='active', user__is_active=False)
print(f'\nموظفين حالتهم "نشط" بس حسابهم موقوف: {inactive_but_working.count()}  ← دول مش هيقدروا يدخلوا بعد التصليح')
for cid, n in Counter(inactive_but_working.values_list('company_id', flat=True)).items():
    print(f'   شركة {company_name(cid)}: {n}')
print(f'حسابات موقوفة لموظفين انتهت خدمتهم/موقوفين: '
      f'{Employee._base_manager.exclude(status="active").filter(user__is_active=False).count()}')
print(f'حسابات لسه ماتفعلتش (لازم تغير كلمة السر): {User._base_manager.filter(must_change_password=True, is_active=True).count()}')
print(f'حسابات السوبر أدمن: {User._base_manager.filter(role="super_admin").count()}')

# ── 3) قبل قلب المستودعات خاصة ──
title('3) حاجات على السيرفر بتسحب من GitHub')
for d in ('/var/www/motionhr', '/var/www/motionhr_web'):
    try:
        r = subprocess.run(['git', '-C', d, 'remote', '-v'], capture_output=True, text=True)
        out = re.sub(r'://[^@/\s]+@', '://***@', r.stdout.strip())  # ماتطبعش أي مفتاح
    except OSError:
        out = ''
    print(f'{d}: {out or "مش git (ماحدش بيعمل git pull هنا)"}')
try:
    r = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    hits = [l for l in r.stdout.splitlines() if 'github' in l.lower()]
except OSError:
    hits = []
for f in ('/etc/crontab',) + tuple(os.path.join('/etc/cron.d', x) for x in (os.listdir('/etc/cron.d') if os.path.isdir('/etc/cron.d') else [])):
    try:
        hits += [f'{f}: {l}' for l in open(f, errors='ignore') if 'github' in l.lower()]
    except OSError:
        pass
print('مهام مجدولة بتكلم GitHub:', hits or 'مفيش')
print('\nخلص الفحص — ماتغيرش أي حاجة.')
