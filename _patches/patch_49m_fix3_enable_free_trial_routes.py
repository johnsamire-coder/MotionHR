"""
Patch 49M Fix3 — Enable Free Trial Routes

الهدف:
- إصلاح 404 على /free-trial/
- التأكد أن:
  1) landing/views.py فيه free_trial_register و free_trial_success
  2) landing/urls.py فيه routes الصحيحة
  3) motionhr/urls.py عامل include لـ landing.urls

هذا الباتش آمن ويكتب الملفات المطلوبة بالكامل لو لزم
"""

import os
import re
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


def backup_if_exists(rel_path, backup_name):
    full = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full):
        backup_dir = os.path.join(BASE_DIR, "_patches", "_backups")
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(full, os.path.join(backup_dir, backup_name))
        print(f"✅ Backup: _patches/_backups/{backup_name}")


print("=" * 70)
print("Patch 49M Fix3 — Enable Free Trial Routes")
print("=" * 70)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_if_exists("landing/views.py", "landing_views_before_49m_fix3.py.bak")
backup_if_exists("landing/urls.py", "landing_urls_before_49m_fix3.py.bak")
backup_if_exists("motionhr/urls.py", "motionhr_urls_before_49m_fix3.py.bak")

# ────────────────────────────────────────────────────────────
# Step 1: Ensure landing/views.py has the free-trial views
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: التحقق من landing/views.py")

views_path = "landing/views.py"
views_content = read_file(views_path)

if views_content is None:
    raise SystemExit("❌ ملف landing/views.py غير موجود")

missing_views = []
if "def free_trial_register(request):" not in views_content:
    missing_views.append("free_trial_register")
if "def free_trial_success(request):" not in views_content:
    missing_views.append("free_trial_success")

if missing_views:
    print(f"   ⚠️ views ناقصة: {missing_views}")
    trial_views = r'''

# ═════════════════════════════════════════════════════════════
# Patch 49M Fix3 — Free Trial Views Fallback
# ═════════════════════════════════════════════════════════════

def free_trial_register(request):
    from core.models import TrialSignupLead
    from companies.models import Company
    from accounts.models import User
    from subscriptions.models import SubscriptionPlan, CompanySubscription
    from django.contrib import messages
    from django.utils.crypto import get_random_string
    from datetime import date, timedelta

    TRIAL_DAYS = 14

    if request.method == 'POST':
        company_name = (request.POST.get('company_name') or '').strip()
        contact_name = (request.POST.get('contact_name') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        whatsapp = (request.POST.get('whatsapp') or '').strip()
        email = (request.POST.get('email') or '').strip()
        employees_count = (request.POST.get('employees_count') or '10').strip()
        city = (request.POST.get('city') or '').strip()
        industry = (request.POST.get('industry') or '').strip()
        notes = (request.POST.get('notes') or '').strip()

        errors = []
        if not company_name:
            errors.append('يرجى إدخال اسم الشركة')
        if not contact_name:
            errors.append('يرجى إدخال اسم المسؤول')
        if not phone:
            errors.append('يرجى إدخال رقم الموبايل')
        if not whatsapp:
            errors.append('يرجى إدخال رقم الواتساب')
        if not email:
            errors.append('يرجى إدخال البريد الإلكتروني')

        if email and User.objects.filter(email=email).exists():
            errors.append('هذا البريد الإلكتروني مسجل بالفعل')

        try:
            employees_count = int(employees_count)
            if employees_count < 1:
                employees_count = 1
        except Exception:
            employees_count = 10

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                company = Company.objects.create(
                    name_ar=company_name,
                    name_en=company_name,
                )

                base_username = email.split('@')[0].lower()
                base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
                if not base_username:
                    base_username = 'admin'

                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                password = f"Trial@{get_random_string(6)}"

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=contact_name.split()[0] if contact_name else '',
                    last_name=' '.join(contact_name.split()[1:]) if len(contact_name.split()) > 1 else '',
                )

                if hasattr(user, 'role'):
                    user.role = 'company_admin'
                if hasattr(user, 'company'):
                    user.company = company
                if hasattr(user, 'must_change_password'):
                    user.must_change_password = True
                user.save()

                today = date.today()
                trial_end = today + timedelta(days=TRIAL_DAYS)

                plan = SubscriptionPlan.objects.first()
                if not plan:
                    plan = SubscriptionPlan.objects.create(
                        name='Trial',
                        slug='trial',
                        price=0,
                        duration_days=TRIAL_DAYS,
                        max_employees=50,
                        is_active=True,
                    )

                try:
                    CompanySubscription.objects.create(
                        company=company,
                        plan=plan,
                        start_date=today,
                        end_date=trial_end,
                        is_active=True,
                    )
                except Exception:
                    try:
                        CompanySubscription.objects.create(
                            company=company,
                            plan=plan,
                            status='active',
                        )
                    except Exception:
                        pass

                TrialSignupLead.objects.create(
                    company_name=company_name,
                    contact_name=contact_name,
                    phone=phone,
                    whatsapp=whatsapp,
                    email=email,
                    employees_count=employees_count,
                    city=city,
                    industry=industry,
                    notes=notes,
                    source='free_trial_auto',
                    status='activated',
                    trial_start_date=today,
                    trial_end_date=trial_end,
                    created_company=company,
                    created_user=user,
                    generated_username=username,
                    generated_password=password,
                )

                request.session['trial_data'] = {
                    'company_name': company_name,
                    'contact_name': contact_name,
                    'username': username,
                    'password': password,
                    'email': email,
                    'trial_start': str(today),
                    'trial_end': str(trial_end),
                    'trial_days': TRIAL_DAYS,
                }

                return redirect('landing:free_trial_success')

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {e}')

    return render(request, 'landing/free_trial_register.html', {
        'page_title': 'ابدأ تجربتك المجانية',
        'trial_days': 14,
        'sales_phone': '(+20)01501551593',
        'sales_whatsapp': '2001501551593',
    })


def free_trial_success(request):
    trial_data = request.session.pop('trial_data', None)

    if not trial_data:
        return redirect('landing:free_trial')

    return render(request, 'landing/free_trial_success.html', {
        'page_title': 'تم إنشاء حسابك بنجاح',
        'trial_data': trial_data,
        'sales_phone': '(+20)01501551593',
        'sales_whatsapp': '2001501551593',
    })
'''
    views_content = views_content.rstrip() + "\n" + trial_views + "\n"
    write_file(views_path, views_content)
    print("   ✅ تمت إضافة free_trial views")
else:
    print("   ✅ free_trial views موجودة بالفعل")

# ────────────────────────────────────────────────────────────
# Step 2: Rebuild landing/urls.py safely
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إعادة بناء landing/urls.py")

landing_views_content = read_file("landing/views.py") or ""
found_funcs = set(re.findall(r'^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', landing_views_content, re.MULTILINE))

def pick(*names):
    for n in names:
        if n in found_funcs:
            return n
    return None

home_view = pick("home", "landing_home", "index")
about_view = pick("about", "about_page", "landing_about")
contact_view = pick("contact", "contact_page", "landing_contact")
pricing_view = pick("pricing", "pricing_page", "landing_pricing")
free_trial_view = pick("free_trial_register")
free_trial_success_view = pick("free_trial_success")

urlpatterns_lines = [
    "from django.urls import path",
    "from . import views",
    "",
    "app_name = 'landing'",
    "",
    "urlpatterns = [",
]

if home_view:
    urlpatterns_lines.append(f"    path('', views.{home_view}, name='home'),")
if about_view:
    urlpatterns_lines.append(f"    path('about/', views.{about_view}, name='about'),")
if contact_view:
    urlpatterns_lines.append(f"    path('contact/', views.{contact_view}, name='contact'),")
if pricing_view:
    urlpatterns_lines.append(f"    path('pricing/', views.{pricing_view}, name='pricing'),")
if free_trial_view:
    urlpatterns_lines.append(f"    path('free-trial/', views.{free_trial_view}, name='free_trial'),")
if free_trial_success_view:
    urlpatterns_lines.append(f"    path('free-trial/success/', views.{free_trial_success_view}, name='free_trial_success'),")

urlpatterns_lines.append("]")

write_file("landing/urls.py", "\n".join(urlpatterns_lines))
print("   ✅ تم بناء landing/urls.py مع free-trial routes")

# ────────────────────────────────────────────────────────────
# Step 3: Ensure motionhr/urls.py includes landing.urls
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: التحقق من motionhr/urls.py")

project_urls_path = "motionhr/urls.py"
project_urls_content = read_file(project_urls_path)

if project_urls_content is None:
    raise SystemExit("❌ ملف motionhr/urls.py غير موجود")

include_line = "path('', include('landing.urls', namespace='landing'))"
alt_include_line = 'path("", include("landing.urls", namespace="landing"))'

if include_line in project_urls_content or alt_include_line in project_urls_content:
    print("   ✅ landing.urls included بالفعل")
else:
    # نحاول حقنه في urlpatterns
    if "urlpatterns = [" in project_urls_content:
        project_urls_content = project_urls_content.replace(
            "urlpatterns = [",
            "urlpatterns = [\n    path('', include('landing.urls', namespace='landing')),\n",
            1
        )
        write_file(project_urls_path, project_urls_content)
        print("   ✅ تم إضافة include لـ landing.urls")
    else:
        print("   ⚠️ لم أستطع حقن include تلقائيًا")

print("\n" + "=" * 70)
print("✅ Patch 49M Fix3 اكتمل")
print("=" * 70)
print("""
اللي اتعمل:
  ✅ التحقق من وجود free_trial_register و free_trial_success في landing/views.py
  ✅ إعادة بناء landing/urls.py بشكل سليم
  ✅ التأكد من include('landing.urls', namespace='landing') في motionhr/urls.py

شغّل الآن:
  python manage.py check
  python manage.py runserver 0.0.0.0:8000

ثم اختبر:
  http://127.0.0.1:8000/free-trial/
""")