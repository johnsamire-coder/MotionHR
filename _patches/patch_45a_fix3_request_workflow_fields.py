#!/usr/bin/env python3
"""
Patch 45a-fix3: Add workflow fields to EmployeeRequest model
============================================================
- يضيف حقول الـ workflow الناقصة داخل EmployeeRequest
- يطابق models.py مع الـ migrations اللي اتطبقت
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 45a-fix3: EmployeeRequest workflow fields")
print("=" * 60)

req_models_path = os.path.join(BASE_DIR, "requests_app", "models.py")
content = read_file(req_models_path)

if "current_step = models.PositiveSmallIntegerField" in content and "substitute_employee = models.ForeignKey" in content:
    print("  ℹ️  حقول الـ workflow موجودة بالفعل")
else:
    fields_block = '''
    # ── Workflow Steps ──────────────────────────────────
    current_step = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="الخطوة الحالية"
    )

    step_1_status = models.CharField(
        max_length=20,
        blank=True,
        default="pending",
        choices=[
            ("pending", "قيد الانتظار"),
            ("approved", "موافق"),
            ("rejected", "مرفوض"),
            ("skipped", "تخطي"),
        ],
        verbose_name="حالة الخطوة 1"
    )
    step_1_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="step1_approvals",
        verbose_name="الخطوة 1 بواسطة"
    )
    step_1_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="وقت الخطوة 1"
    )
    step_1_notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات الخطوة 1"
    )

    step_2_status = models.CharField(
        max_length=20,
        blank=True,
        default="",
        choices=[
            ("pending", "قيد الانتظار"),
            ("approved", "موافق"),
            ("rejected", "مرفوض"),
            ("skipped", "تخطي"),
        ],
        verbose_name="حالة الخطوة 2"
    )
    step_2_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="step2_approvals",
        verbose_name="الخطوة 2 بواسطة"
    )
    step_2_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="وقت الخطوة 2"
    )
    step_2_notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات الخطوة 2"
    )

    step_3_status = models.CharField(
        max_length=20,
        blank=True,
        default="",
        choices=[
            ("pending", "قيد الانتظار"),
            ("approved", "موافق"),
            ("rejected", "مرفوض"),
            ("skipped", "تخطي"),
        ],
        verbose_name="حالة الخطوة 3"
    )
    step_3_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="step3_approvals",
        verbose_name="الخطوة 3 بواسطة"
    )
    step_3_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="وقت الخطوة 3"
    )
    step_3_notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات الخطوة 3"
    )

    # ── Substitute ───────────────────────────────────────
    substitute_employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="substituted_requests",
        verbose_name="البديل"
    )
    substitute_notified = models.BooleanField(
        default=False,
        verbose_name="تم إشعار البديل"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )
'''

    # نحاول نستبدل آخر جزء موجود بعد review_notes
    pattern = re.compile(
        r'''(\s*review_notes = models\.TextField\(\s*
        blank=True,\s*verbose_name="ملاحظات المراجع"\s*
        \)\s*)''',
        re.VERBOSE
    )

    if pattern.search(content):
        content = pattern.sub(r'\1\n' + fields_block + '\n', content, count=1)
        write_file(req_models_path, content)
        print("  ✅ تم إضافة حقول الـ workflow بعد review_notes")
    else:
        print("  ⚠️  لم أجد review_notes بالشكل المتوقع")
        print("  افتح requests_app/models.py وتأكد يدويًا")

print("\n" + "=" * 60)
print("  ✅ Patch 45a-fix3 اكتمل!")
print("=" * 60)
print("""
الخطوة الجاية:
1) شغّل:
   python manage.py check

2) لو كل شيء تمام:
   ابعتلي النتيجة
   وأنا أبعتلك Patch 45b فورًا
""")