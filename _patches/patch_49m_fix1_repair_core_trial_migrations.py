"""
Patch 49M Fix1 — Repair Core Trial Migrations

الهدف:
- إصلاح خطأ:
  NodeNotFoundError: core.0002_enhanced_trial_signup depends on nonexistent core.0001_initial
- إنشاء core/migrations/__init__.py
- إنشاء core/migrations/0001_initial.py بالنسخة النهائية من TrialSignupLead
- تحويل 0002_enhanced_trial_signup إلى no-op migration آمنة

مهم:
- لا يحتاج حذف أي ملفات يدويًا
- آمن حتى لو لم يتم تطبيق migrations السابقة
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
print("Patch 49M Fix1 — Repair Core Trial Migrations")
print("=" * 70)

# ────────────────────────────────────────────────────────────
# Backups
# ────────────────────────────────────────────────────────────
backup_if_exists("core/migrations/0001_initial.py", "core_migrations_0001_initial_before_49m_fix1.py.bak")
backup_if_exists("core/migrations/0002_enhanced_trial_signup.py", "core_migrations_0002_before_49m_fix1.py.bak")

# ────────────────────────────────────────────────────────────
# Step 1: Ensure package init
# ────────────────────────────────────────────────────────────
print("\n📌 Step 1: إنشاء core/migrations/__init__.py")
write_file("core/migrations/__init__.py", "")

# ────────────────────────────────────────────────────────────
# Step 2: Create proper 0001_initial.py
# ────────────────────────────────────────────────────────────
print("\n📌 Step 2: إنشاء core/migrations/0001_initial.py")

migration_0001 = '''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0015_charter_digital_signature'),
        ('accounts', '0006_alter_pushsubscription_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrialSignupLead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=200, verbose_name='اسم الشركة')),
                ('contact_name', models.CharField(max_length=200, verbose_name='اسم المسؤول')),
                ('phone', models.CharField(max_length=30, verbose_name='رقم الموبايل')),
                ('whatsapp', models.CharField(max_length=30, verbose_name='رقم الواتساب')),
                ('email', models.EmailField(max_length=254, verbose_name='البريد الإلكتروني')),
                ('employees_count', models.PositiveIntegerField(default=1, verbose_name='عدد الموظفين المتوقع')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='المدينة')),
                ('industry', models.CharField(blank=True, max_length=150, verbose_name='نوع النشاط')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات العميل')),
                ('source', models.CharField(blank=True, default='free_trial', max_length=100, verbose_name='مصدر التسجيل')),
                ('status', models.CharField(choices=[
                    ('new', 'جديد'),
                    ('activated', 'تم التفعيل'),
                    ('contacted', 'تم التواصل'),
                    ('converted', 'تم التحويل لعميل'),
                    ('expired', 'انتهت التجربة'),
                    ('rejected', 'مرفوض')
                ], default='new', max_length=20, verbose_name='حالة الطلب')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التسجيل')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trial_start_date', models.DateField(blank=True, null=True, verbose_name='بداية التجربة')),
                ('trial_end_date', models.DateField(blank=True, null=True, verbose_name='نهاية التجربة')),
                ('generated_username', models.CharField(blank=True, max_length=100, verbose_name='اسم المستخدم المولّد')),
                ('generated_password', models.CharField(blank=True, max_length=100, verbose_name='كلمة المرور المولّدة')),
                ('sales_notes', models.TextField(blank=True, verbose_name='ملاحظات فريق المبيعات')),
                ('created_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_leads', to='companies.company', verbose_name='الشركة المنشأة')),
                ('created_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_leads', to='accounts.user', verbose_name='الحساب المنشأ')),
            ],
            options={
                'verbose_name': 'طلب تجربة مجانية',
                'verbose_name_plural': 'طلبات التجربة المجانية',
                'ordering': ['-created_at'],
            },
        ),
    ]
}
'''
# إصلاح قوس class migration النهائي
migration_0001 = migration_0001.replace("\n}\n'''", "\n]\n")
write_file("core/migrations/0001_initial.py", migration_0001)

# ────────────────────────────────────────────────────────────
# Step 3: Rewrite 0002 as safe no-op
# ────────────────────────────────────────────────────────────
print("\n📌 Step 3: تحويل 0002_enhanced_trial_signup.py إلى no-op migration")

migration_0002 = '''from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # No-op migration
        # Patch 49M Fix1:
        # هذه المايجريشن أصبحت فارغة لأن 0001_initial تحتوي بالفعل
        # على النسخة النهائية من TrialSignupLead
    ]
'''
write_file("core/migrations/0002_enhanced_trial_signup.py", migration_0002)

# ────────────────────────────────────────────────────────────
# Step 4: Final message
# ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("✅ Patch 49M Fix1 اكتمل")
print("=" * 70)
print("""
اللي اتعمل:
  ✅ إنشاء core/migrations/__init__.py
  ✅ إنشاء core/migrations/0001_initial.py بالنسخة النهائية من TrialSignupLead
  ✅ تحويل core/migrations/0002_enhanced_trial_signup.py إلى no-op آمنة
  ✅ إصلاح dependency chain الخاصة بـ core migrations

شغّل بالترتيب:
  python manage.py migrate
  python manage.py check
  python manage.py runserver 0.0.0.0:8000

ولو migrate اشتغلت:
  اختبر /free-trial/
""")