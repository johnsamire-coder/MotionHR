#!/usr/bin/env python3
"""
Patch 45a-fix2: Add missing workflow fields to EmployeeRequest model
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 45a-fix2: EmployeeRequest workflow fields")
print("=" * 60)

req_models_path = os.path.join(BASE_DIR, "requests_app", "models.py")
content = read_file(req_models_path)

if "current_step" in content and "substitute_employee" in content:
    print("  ℹ️  الحقول موجودة بالفعل")
else:
    fields_block = '''
    # Workflow steps
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

'''

    target = '''    notes = models.TextField(blank=True, verbose_name="ملاحظات")

    class Meta:'''

    if target in content:
        content = content.replace(
            target,
            fields_block + '''    notes = models.TextField(blank=True, verbose_name="ملاحظات")

    class Meta:'''
        )
        write_file(req_models_path, content)
        print("  ✅ تم إضافة حقول الـ workflow الناقصة")
    else:
        print("  ⚠️  لم أجد المكان المتوقع داخل EmployeeRequest")
        print("  افتح requests_app/models.py وابعتلي كلاس EmployeeRequest لو احتجنا تعديل يدوي")

print("\n" + "=" * 60)
print("  ✅ Patch 45a-fix2 اكتمل!")
print("=" * 60)
print("""
الخطوة الجاية:
1) شغّل:
   python manage.py check

2) لو مفيش أخطاء:
   هابعتلك Patch 45b فورًا
""")