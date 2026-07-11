#!/usr/bin/env python3
"""
Patch 44a-fix: Manual Migrations
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


def get_last_migration(app_dir):
    migrations_dir = os.path.join(BASE_DIR, app_dir, "migrations")
    existing = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith(".py") and f != "__init__.py"
    ])
    if existing:
        last = existing[-1].replace(".py", "")
        last_num = int(last.split("_")[0])
        return last, last_num
    return "0001_initial", 1


print("=" * 60)
print("  Patch 44a-fix: Manual Migrations")
print("=" * 60)

# ════════════════════════════════════════════
# 1) employees migration
# ════════════════════════════════════════════
print("\n🔧 employees migration...")

last, num = get_last_migration("employees")
new_num = str(num + 1).zfill(4)
migration_name = f"{new_num}_add_stealth_tracking_to_employee"
migration_path = os.path.join(
    BASE_DIR, "employees", "migrations", f"{migration_name}.py"
)

create_file(migration_path, f'''from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "{last}"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="stealth_tracking_enabled",
            field=models.BooleanField(default=False, verbose_name="التتبع الصامت مفعل"),
        ),
    ]
''')

# ════════════════════════════════════════════
# 2) companies migration
# ════════════════════════════════════════════
print("\n🔧 companies migration...")

last, num = get_last_migration("companies")
new_num = str(num + 1).zfill(4)
migration_name = f"{new_num}_add_stealth_tracking_to_policy"
migration_path = os.path.join(
    BASE_DIR, "companies", "migrations", f"{migration_name}.py"
)

create_file(migration_path, f'''from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "{last}"),
    ]

    operations = [
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_enabled",
            field=models.BooleanField(default=False, verbose_name="تفعيل التتبع الصامت"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_alert_after_minutes",
            field=models.PositiveSmallIntegerField(default=15, verbose_name="تنبيه بعد عدد دقائق"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_notify_manager",
            field=models.BooleanField(default=True, verbose_name="تنبيه المدير المباشر"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_notify_hr",
            field=models.BooleanField(default=False, verbose_name="تنبيه HR"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_notify_company_admin",
            field=models.BooleanField(default=False, verbose_name="تنبيه صاحب الشركة"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_requires_charter_clause",
            field=models.BooleanField(default=True, verbose_name="إلزام بند المراقبة في الميثاق"),
        ),
    ]
''')

# ════════════════════════════════════════════
# 3) attendance migration (TrackingAlert)
# ════════════════════════════════════════════
print("\n🔧 attendance migration...")

last, num = get_last_migration("attendance")
new_num = str(num + 1).zfill(4)
migration_name = f"{new_num}_add_tracking_alert"
migration_path = os.path.join(
    BASE_DIR, "attendance", "migrations", f"{migration_name}.py"
)

create_file(migration_path, f'''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "{last}"),
        ("companies", "0001_initial"),
        ("employees", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackingAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField(verbose_name="التاريخ")),
                ("started_at", models.DateTimeField(verbose_name="وقت بداية الخروج")),
                ("last_seen_at", models.DateTimeField(blank=True, null=True, verbose_name="آخر وقت رصد")),
                ("minutes_outside", models.PositiveSmallIntegerField(default=0, verbose_name="دقائق خارج النطاق")),
                ("last_latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("last_longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("last_address", models.TextField(blank=True)),
                ("status", models.CharField(
                    choices=[("open","مفتوح"),("resolved","تمت المعالجة"),("ignored","تم التجاهل")],
                    default="open", max_length=20, verbose_name="الحالة"
                )),
                ("notified_manager", models.BooleanField(default=False)),
                ("notified_hr", models.BooleanField(default=False)),
                ("notified_company_admin", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="companies.company"
                )),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="tracking_alerts",
                    to="employees.employee",
                    verbose_name="الموظف"
                )),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user"
                )),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user"
                )),
                ("resolved_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="resolved_tracking_alerts",
                    to="accounts.user"
                )),
            ],
            options={{
                "verbose_name": "تنبيه تتبع",
                "verbose_name_plural": "تنبيهات التتبع",
                "ordering": ["-started_at"],
            }},
        ),
    ]
''')

# ════════════════════════════════════════════
# 4) migrate
# ════════════════════════════════════════════
print("\n🔧 تشغيل migrate...")
from django.core.management import call_command
call_command("migrate")
print("  ✅ Migration OK")

print("\n" + "=" * 60)
print("  ✅ Patch 44a-fix اكتمل!")
print("=" * 60)
print("""
تم إنشاء وتشغيل:
  ✅ employees → stealth_tracking_enabled
  ✅ companies → stealth tracking policy fields
  ✅ attendance → TrackingAlert

دلوقتي ابعت Patch 44b (المنطق الفعلي)
""")