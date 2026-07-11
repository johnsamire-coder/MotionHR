#!/usr/bin/env python3
"""
Patch 41a: Late Engine Models
==============================
1) LateIncident model
2) LateNotification model
3) DisciplinaryAction model
4) CompanyPolicy fields update
5) Migration
6) Admin
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم إنشاء: {path}")


print("=" * 60)
print("  Patch 41a: Late Engine Models")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) إضافة Models في attendance/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/models.py...")

models_path = os.path.join(BASE_DIR, "attendance", "models.py")
models_content = read_file(models_path)

late_models = '''

# ════════════════════════════════════════════════════════════
# نظام التأخيرات والإجراءات التأديبية
# ════════════════════════════════════════════════════════════

class LateIncident(TenantModel):
    """حادثة تأخير"""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="late_incidents",
        verbose_name="الموظف"
    )
    attendance = models.ForeignKey(
        "Attendance",
        on_delete=models.CASCADE,
        related_name="late_incidents",
        verbose_name="سجل الحضور",
        null=True,
        blank=True
    )
    date = models.DateField(verbose_name="التاريخ")
    late_minutes = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="دقائق التأخير"
    )
    shift_start_time = models.TimeField(
        null=True, blank=True,
        verbose_name="بداية الشيفت"
    )
    actual_checkin_time = models.TimeField(
        null=True, blank=True,
        verbose_name="وقت الحضور الفعلي"
    )
    grace_period_used = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="السماحية المستخدمة"
    )
    month = models.PositiveSmallIntegerField(verbose_name="الشهر")
    year = models.PositiveSmallIntegerField(verbose_name="السنة")
    incident_number_in_month = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="رقم الحادثة في الشهر"
    )
    is_excused = models.BooleanField(
        default=False,
        verbose_name="معذور"
    )
    excuse_reason = models.TextField(
        blank=True,
        verbose_name="سبب العذر"
    )

    class Meta:
        verbose_name = "حادثة تأخير"
        verbose_name_plural = "حوادث التأخير"
        ordering = ["-date"]
        unique_together = [["employee", "date"]]

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.late_minutes} دقيقة"


class LateNotification(TenantModel):
    """إشعار تأخير لـ HR"""

    NOTIFICATION_TYPES = [
        ("single_late", "تأخير عادي"),
        ("threshold_reached", "وصل الحد"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="late_notifications",
        verbose_name="الموظف"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default="single_late",
        verbose_name="نوع الإشعار"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="العنوان"
    )
    message = models.TextField(
        verbose_name="الرسالة"
    )
    details = models.TextField(
        blank=True,
        verbose_name="التفاصيل"
    )
    suggested_action = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="الإجراء المقترح"
    )
    incident_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="عدد مرات التأخير"
    )
    month = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="الشهر"
    )
    year = models.PositiveSmallIntegerField(
        default=2025,
        verbose_name="السنة"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="تم القراءة"
    )
    is_acted_upon = models.BooleanField(
        default=False,
        verbose_name="تم اتخاذ إجراء"
    )
    action_taken = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="الإجراء المتخذ"
    )
    action_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="late_actions_taken",
        verbose_name="تم بواسطة"
    )
    action_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="وقت الإجراء"
    )
    action_notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات الإجراء"
    )

    class Meta:
        verbose_name = "إشعار تأخير"
        verbose_name_plural = "إشعارات التأخير"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.title}"


class DisciplinaryAction(TenantModel):
    """إجراء تأديبي"""

    ACTION_TYPES = [
        ("verbal_warning", "إنذار شفهي"),
        ("written_warning", "إنذار كتابي"),
        ("quarter_day_deduction", "خصم ربع يوم"),
        ("half_day_deduction", "خصم نصف يوم"),
        ("full_day_deduction", "خصم يوم كامل"),
        ("suspension", "إيقاف عن العمل"),
        ("termination_warning", "إنذار فصل"),
        ("dismissed", "تم الإعفاء / التجاهل"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="disciplinary_actions",
        verbose_name="الموظف"
    )
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPES,
        verbose_name="نوع الإجراء"
    )
    reason = models.TextField(
        verbose_name="السبب"
    )
    related_notification = models.ForeignKey(
        LateNotification,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="disciplinary_actions",
        verbose_name="الإشعار المرتبط"
    )
    auto_generated = models.BooleanField(
        default=False,
        verbose_name="تم تلقائيًا"
    )
    deduction_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        verbose_name="مبلغ الخصم"
    )
    deduction_created = models.BooleanField(
        default=False,
        verbose_name="تم إنشاء خصم فعلي"
    )
    performed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="disciplinary_actions_performed",
        verbose_name="تم بواسطة"
    )
    performed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإجراء"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )

    class Meta:
        verbose_name = "إجراء تأديبي"
        verbose_name_plural = "الإجراءات التأديبية"
        ordering = ["-performed_at"]

    def __str__(self):
        return f"{self.employee} - {self.get_action_type_display()}"
'''

if "class LateIncident" not in models_content:
    models_content += late_models
    write_file(models_path, models_content)
    print("  ✅ تم إضافة Late Engine Models")
else:
    print("  ℹ️  Late Engine Models موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 2) تحديث CompanyPolicy
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث CompanyPolicy...")

comp_models_path = os.path.join(BASE_DIR, "companies", "models.py")
comp_models = read_file(comp_models_path)

new_policy_fields = '''
    # ── وضع التعامل مع التأخير ─────────────────────────
    LATE_HANDLING_MODES = [
        ("monitor_only", "مراقبة فقط"),
        ("recommendation_only", "توصية + قرار HR"),
        ("auto_warn_manual_deduct", "إنذارات تلقائية + خصومات بموافقة"),
        ("fully_automatic", "تلقائي كامل"),
    ]

    late_handling_mode = models.CharField(
        max_length=30,
        choices=LATE_HANDLING_MODES,
        default="recommendation_only",
        verbose_name="طريقة التعامل مع التأخير"
    )

    # ── شفافية الموظف ─────────────────────────────────
    employee_can_view_late_count = models.BooleanField(
        default=True,
        verbose_name="الموظف يشوف عدد تأخيراته"
    )
    employee_can_view_warnings = models.BooleanField(
        default=True,
        verbose_name="الموظف يشوف إنذاراته"
    )

    # ── تجاهل HR ──────────────────────────────────────
    hr_override_reason_required = models.BooleanField(
        default=True,
        verbose_name="سبب إجباري لو HR تجاهل الإجراء"
    )
'''

if "late_handling_mode" not in comp_models:
    # نضيف قبل notes field
    if "notes = models.TextField" in comp_models:
        comp_models = comp_models.replace(
            "    notes = models.TextField(",
            new_policy_fields + "\n    notes = models.TextField("
        )
    else:
        # نضيف قبل class Meta أو في آخر CompanyPolicy
        comp_models = comp_models.replace(
            "    created_at = models.DateTimeField(auto_now_add=True)",
            new_policy_fields + "\n    created_at = models.DateTimeField(auto_now_add=True)"
        )
    write_file(comp_models_path, comp_models)
    print("  ✅ تم إضافة حقول Late Engine في CompanyPolicy")
else:
    print("  ℹ️  حقول Late Engine موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 3) Admin Registration
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/admin.py...")

admin_path = os.path.join(BASE_DIR, "attendance", "admin.py")
admin_content = read_file(admin_path)

if "LateIncident" not in admin_content:
    admin_content += '''

from .models import LateIncident, LateNotification, DisciplinaryAction

@admin.register(LateIncident)
class LateIncidentAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "late_minutes", "incident_number_in_month", "is_excused"]
    list_filter = ["month", "year", "is_excused"]

@admin.register(LateNotification)
class LateNotificationAdmin(admin.ModelAdmin):
    list_display = ["employee", "notification_type", "title", "is_read", "is_acted_upon", "created_at"]
    list_filter = ["notification_type", "is_read", "is_acted_upon"]

@admin.register(DisciplinaryAction)
class DisciplinaryActionAdmin(admin.ModelAdmin):
    list_display = ["employee", "action_type", "reason", "auto_generated", "performed_at"]
    list_filter = ["action_type", "auto_generated"]
'''
    write_file(admin_path, admin_content)
    print("  ✅ تم تسجيل Models في Admin")
else:
    print("  ℹ️  Admin مسجل بالفعل")


# ════════════════════════════════════════════════════════════
# 4) Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

import django
django.setup()

from django.core.management import call_command

call_command("makemigrations", "attendance", "companies")
call_command("migrate")
print("  ✅ Migration OK")


print("\n" + "=" * 60)
print("  ✅ Patch 41a اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ LateIncident model
  2. ✅ LateNotification model
  3. ✅ DisciplinaryAction model
  4. ✅ CompanyPolicy fields:
       - late_handling_mode
       - employee_can_view_late_count
       - employee_can_view_warnings
       - hr_override_reason_required
  5. ✅ Admin registration
  6. ✅ Migration

الجاي:
  Patch 41b: Late Engine Logic
  Patch 41c: HR Action Pages + Templates
""")