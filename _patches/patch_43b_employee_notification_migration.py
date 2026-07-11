#!/usr/bin/env python3
"""
Patch 43b: Manual Migration for EmployeeNotification
====================================================
- إنشاء migration يدوي لـ EmployeeNotification
- تشغيل migrate
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.core.management import call_command


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 43b: EmployeeNotification Migration")
print("=" * 60)

migrations_dir = os.path.join(BASE_DIR, "accounts", "migrations")
existing = sorted([
    f for f in os.listdir(migrations_dir)
    if f.endswith(".py") and f != "__init__.py"
])

if existing:
    last = existing[-1].replace(".py", "")
    last_num = int(last.split("_")[0])
else:
    last = "0001_initial"
    last_num = 1

new_num = str(last_num + 1).zfill(4)
migration_name = f"{new_num}_add_employee_notification"
migration_path = os.path.join(migrations_dir, f"{migration_name}.py")

migration_content = f'''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "{last}"),
        ("attendance", "0003_latenotification_disciplinaryaction_lateincident"),
        ("employees", "0004_employee_attendance_mode_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmployeeNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="العنوان")),
                ("message", models.TextField(verbose_name="الرسالة")),
                ("notification_type", models.CharField(
                    max_length=20,
                    default="general_notice",
                    verbose_name="نوع الإشعار",
                    choices=[
                        ("late_warning", "تحذير تأخير"),
                        ("deduction_notice", "إشعار خصم"),
                        ("general_notice", "إشعار عام"),
                        ("policy_reminder", "تذكير بسياسة"),
                        ("charter_reminder", "تذكير بالميثاق"),
                        ("request_update", "تحديث طلب"),
                    ],
                )),
                ("severity", models.CharField(
                    max_length=10,
                    default="info",
                    verbose_name="الأهمية",
                    choices=[
                        ("info", "معلومة"),
                        ("warning", "تحذير"),
                        ("danger", "هام"),
                    ],
                )),
                ("is_read", models.BooleanField(default=False, verbose_name="تمت القراءة")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notifications",
                    to="employees.employee",
                    verbose_name="الموظف"
                )),
                ("related_action", models.ForeignKey(
                    null=True,
                    blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="employee_notifications",
                    to="attendance.disciplinaryaction",
                    verbose_name="الإجراء المرتبط"
                )),
                ("sent_by", models.ForeignKey(
                    null=True,
                    blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="sent_employee_notifications",
                    to="accounts.user",
                    verbose_name="مرسل بواسطة"
                )),
            ],
            options={{
                "verbose_name": "إشعار موظف",
                "verbose_name_plural": "إشعارات الموظفين",
                "ordering": ["-created_at"],
            }},
        ),
    ]
'''
create_file(migration_path, migration_content)

print("\n🔧 تشغيل migrate...")
call_command("migrate")
print("  ✅ Migration applied")

print("\n" + "=" * 60)
print("  ✅ Patch 43b اكتمل!")
print("=" * 60)
print("""
اللي اتصلح:
  ✅ migration يدوي لـ EmployeeNotification
  ✅ الجدول اتعمل في قاعدة البيانات

جرب دلوقتي:
  1) hr_manager ياخد إجراء على Late Notification
  2) emp10003 يفتح /accounts/notifications/
""")