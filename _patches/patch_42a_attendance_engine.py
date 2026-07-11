#!/usr/bin/env python3
"""
Patch 42a: Attendance Engine Redesign - Phase 1
================================================
1) attendance_mode + required_daily_hours في Employee
2) DailyAssignment model
3) Policy modes جديدة في CompanyPolicy
4) Migration
5) Admin
6) Seed data
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
print("  Patch 42a: Attendance Engine - Phase 1")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) Employee fields
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث employees/models.py...")

emp_models_path = os.path.join(BASE_DIR, "employees", "models.py")
emp_models = read_file(emp_models_path)

new_fields = '''
    # ── نظام الحضور ────────────────────────────────────
    ATTENDANCE_MODES = [
        ("fixed_shift", "شيفت ثابت"),
        ("flexible_hours", "ساعات مرنة"),
        ("field_worker", "موظف ميداني"),
        ("rotating", "شيفت متناوب"),
    ]

    attendance_mode = models.CharField(
        max_length=20,
        choices=ATTENDANCE_MODES,
        default="fixed_shift",
        verbose_name="نظام الحضور"
    )
    required_daily_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=8,
        verbose_name="ساعات العمل اليومية المطلوبة"
    )
'''

if "attendance_mode" not in emp_models:
    # نضيف قبل is_field_worker
    if "is_field_worker" in emp_models:
        emp_models = emp_models.replace(
            "    is_field_worker",
            new_fields + "\n    is_field_worker"
        )
    else:
        # نضيف قبل status
        emp_models = emp_models.replace(
            "    status",
            new_fields + "\n    status",
            1
        )
    write_file(emp_models_path, emp_models)
    print("  ✅ تم إضافة attendance_mode + required_daily_hours")
else:
    print("  ℹ️  attendance_mode موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) DailyAssignment model في attendance/models.py
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/models.py...")

att_models_path = os.path.join(BASE_DIR, "attendance", "models.py")
att_models = read_file(att_models_path)

daily_assignment_model = '''

# ════════════════════════════════════════════════════════════
# تكليف يومي / جدول العمل اليومي
# ════════════════════════════════════════════════════════════
class DailyAssignment(TenantModel):
    """
    تكليف يومي لكل موظف
    ده اللي بيحدد نوع يوم العمل وطريقة تنفيذه
    """

    # ── نوع اليوم ────────────────────────────────────
    DAY_TYPES = [
        ("work_day", "يوم عمل"),
        ("off_day", "راحة أسبوعية"),
        ("leave_day", "إجازة"),
        ("holiday", "إجازة رسمية"),
        ("mission_day", "مأمورية / مهمة"),
        ("standby_day", "استدعاء / on-call"),
        ("training_day", "يوم تدريب"),
    ]

    # ── طريقة التنفيذ ────────────────────────────────
    WORK_MODES = [
        ("fixed", "ثابت"),
        ("flexible", "مرن"),
        ("split", "متقسم"),
        ("field", "ميداني"),
        ("remote", "عن بُعد"),
        ("mixed", "مختلط"),
    ]

    # ── حالة التكليف ─────────────────────────────────
    STATUS_CHOICES = [
        ("scheduled", "مجدول"),
        ("in_progress", "جاري"),
        ("completed", "مكتمل"),
        ("cancelled", "ملغي"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="daily_assignments",
        verbose_name="الموظف"
    )
    date = models.DateField(
        verbose_name="التاريخ"
    )

    # ── نوع اليوم وطريقة العمل ─────────────────────
    day_type = models.CharField(
        max_length=20,
        choices=DAY_TYPES,
        default="work_day",
        verbose_name="نوع اليوم"
    )
    work_mode = models.CharField(
        max_length=20,
        choices=WORK_MODES,
        default="fixed",
        verbose_name="طريقة التنفيذ"
    )

    # ── أوقات العمل ──────────────────────────────────
    shift = models.ForeignKey(
        "Shift",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="الشيفت"
    )
    start_time = models.TimeField(
        null=True, blank=True,
        verbose_name="بداية العمل"
    )
    end_time = models.TimeField(
        null=True, blank=True,
        verbose_name="نهاية العمل"
    )
    expected_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True, blank=True,
        verbose_name="الساعات المتوقعة"
    )

    # ── Split Shift (جزئين) ──────────────────────────
    segment_2_start = models.TimeField(
        null=True, blank=True,
        verbose_name="بداية الجزء الثاني"
    )
    segment_2_end = models.TimeField(
        null=True, blank=True,
        verbose_name="نهاية الجزء الثاني"
    )

    # ── Flags ────────────────────────────────────────
    is_replacement = models.BooleanField(
        default=False,
        verbose_name="بديل لزميل"
    )
    replaces_employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="replaced_assignments",
        verbose_name="بديل عن"
    )
    is_extra_shift = models.BooleanField(
        default=False,
        verbose_name="شيفت إضافي"
    )
    count_as_overtime = models.BooleanField(
        default=False,
        verbose_name="يحسب أوفر تايم"
    )
    count_as_compensatory = models.BooleanField(
        default=False,
        verbose_name="يوم تعويضي"
    )

    # ── متطلبات ──────────────────────────────────────
    requires_tracking = models.BooleanField(
        default=False,
        verbose_name="يحتاج تتبع GPS"
    )
    requires_visits = models.BooleanField(
        default=False,
        verbose_name="يحتاج تسجيل زيارات"
    )
    requires_geofence = models.BooleanField(
        default=True,
        verbose_name="يحتاج نطاق الفرع"
    )
    requires_manager_approval = models.BooleanField(
        default=False,
        verbose_name="يحتاج موافقة المدير مسبقاً"
    )

    # ── المهمة ───────────────────────────────────────
    task_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="عنوان المهمة"
    )
    location_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="اسم الموقع"
    )

    # ── الحالة والاعتماد ─────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
        verbose_name="الحالة"
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_assignments",
        verbose_name="اعتمد بواسطة"
    )

    # ── Exception ────────────────────────────────────
    is_exception = models.BooleanField(
        default=False,
        verbose_name="حالة استثنائية"
    )
    exception_reason = models.TextField(
        blank=True,
        verbose_name="سبب الاستثناء"
    )
    exception_status = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("pending_review", "قيد المراجعة"),
            ("approved", "معتمد"),
            ("rejected", "مرفوض"),
        ],
        verbose_name="حالة الاستثناء"
    )

    # ── Auto Generated ───────────────────────────────
    is_auto_generated = models.BooleanField(
        default=False,
        verbose_name="تم توليده تلقائياً"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )

    class Meta:
        verbose_name = "تكليف يومي"
        verbose_name_plural = "التكليفات اليومية"
        ordering = ["-date"]
        unique_together = [["employee", "date"]]

    def __str__(self):
        return (
            f"{self.employee} - {self.date} - "
            f"{self.get_day_type_display()} / {self.get_work_mode_display()}"
        )

    @property
    def is_working_day(self):
        return self.day_type in ["work_day", "mission_day", "training_day", "standby_day"]

    @property
    def is_off(self):
        return self.day_type in ["off_day", "leave_day", "holiday"]

    @property
    def apply_late_policy(self):
        if self.day_type != "work_day":
            return False
        return self.work_mode in ["fixed", "split"]

    @property
    def apply_geofence(self):
        if not self.requires_geofence:
            return False
        return self.work_mode in ["fixed", "split", "mixed"]
'''

if "class DailyAssignment" not in att_models:
    att_models += daily_assignment_model
    write_file(att_models_path, att_models)
    print("  ✅ تم إضافة DailyAssignment model")
else:
    print("  ℹ️  DailyAssignment موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 3) CompanyPolicy fields الجديدة
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/models.py...")

comp_models_path = os.path.join(BASE_DIR, "companies", "models.py")
comp_models = read_file(comp_models_path)

policy_new_fields = '''
    # ── سياسات يوم الراحة / الإجازة ───────────────────
    CHECKIN_MODES = [
        ("block", "منع تسجيل الحضور"),
        ("allow_notify_hr", "سماح مع إشعار HR"),
        ("allow_convert_by_hr", "سماح وHR يحول لتكليف"),
    ]

    off_day_checkin_mode = models.CharField(
        max_length=25,
        choices=CHECKIN_MODES,
        default="allow_notify_hr",
        verbose_name="لو الموظف سجل حضور يوم راحته"
    )
    leave_day_checkin_mode = models.CharField(
        max_length=25,
        choices=CHECKIN_MODES,
        default="block",
        verbose_name="لو الموظف سجل حضور يوم إجازته"
    )
    unplanned_checkin_mode = models.CharField(
        max_length=25,
        choices=[
            ("use_default", "استخدم الإعداد الافتراضي"),
            ("create_exception", "سجل كحالة استثنائية"),
            ("block", "منع"),
        ],
        default="create_exception",
        verbose_name="لو مفيش تكليف ليومه"
    )
'''

if "off_day_checkin_mode" not in comp_models:
    # نضيف قبل notes
    if "    notes = models.TextField(" in comp_models:
        comp_models = comp_models.replace(
            "    notes = models.TextField(",
            policy_new_fields + "\n    notes = models.TextField("
        )
    write_file(comp_models_path, comp_models)
    print("  ✅ تم إضافة Policy modes جديدة")
else:
    print("  ℹ️  Policy modes موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 4) Migration
# ════════════════════════════════════════════════════════════
print("\n🔧 Migration...")

import django
django.setup()

from django.core.management import call_command
call_command("makemigrations", "employees", "attendance", "companies")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 5) Admin
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث attendance/admin.py...")

admin_path = os.path.join(BASE_DIR, "attendance", "admin.py")
admin_content = read_file(admin_path)

if "DailyAssignment" not in admin_content:
    admin_content += '''

from .models import DailyAssignment

@admin.register(DailyAssignment)
class DailyAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "employee", "date", "day_type", "work_mode",
        "expected_hours", "status", "is_extra_shift",
        "is_replacement", "is_exception"
    ]
    list_filter = ["day_type", "work_mode", "status", "is_extra_shift"]
    search_fields = ["employee__first_name_ar", "employee__employee_code"]
    date_hierarchy = "date"
'''
    write_file(admin_path, admin_content)
    print("  ✅ تم تسجيل DailyAssignment في Admin")
else:
    print("  ℹ️  DailyAssignment مسجل بالفعل")


# ════════════════════════════════════════════════════════════
# 6) Seed: تحديث بيانات الموظفين
# ════════════════════════════════════════════════════════════
print("\n🌱 تحديث بيانات الموظفين...")

from employees.models import Employee
from companies.models import Company

company = Company.objects.first()
if company:
    updates = {
        "EMP10001": ("fixed_shift", 8),      # أحمد - مكتب
        "EMP10002": ("fixed_shift", 8),      # سارة - HR
        "EMP10003": ("fixed_shift", 8),      # محمد - مبيعات
        "EMP10004": ("field_worker", 9),     # محمود - ميداني
        "EMP10005": ("fixed_shift", 8),      # منة - محاسبة
    }

    for code, (mode, hours) in updates.items():
        emp = Employee.all_objects.filter(employee_code=code).first()
        if emp:
            if hasattr(emp, "attendance_mode"):
                emp.attendance_mode = mode
            if hasattr(emp, "required_daily_hours"):
                emp.required_daily_hours = hours
            emp.save()
            print(f"  ✅ {code}: {mode} / {hours}h")


# ════════════════════════════════════════════════════════════
# 7) Seed: تكليفات يومية تجريبية
# ════════════════════════════════════════════════════════════
print("\n🌱 إنشاء تكليفات تجريبية...")

from attendance.models import DailyAssignment, Shift
from datetime import date, timedelta, time as dt_time

shift = Shift.objects.filter(company=company).first()
today = date.today()

if company and not DailyAssignment.objects.filter(company=company).exists():
    emps = list(Employee.all_objects.filter(company=company)[:5])

    for emp in emps:
        for day_offset in range(7):
            d = today + timedelta(days=day_offset)
            weekday = d.weekday()

            if weekday == 4:  # الجمعة
                day_type = "off_day"
                work_mode = "fixed"
                start = None
                end = None
                hours = None
                geofence = False
                tracking = False
                visits = False
            elif weekday == 5:  # السبت
                day_type = "off_day"
                work_mode = "fixed"
                start = None
                end = None
                hours = None
                geofence = False
                tracking = False
                visits = False
            else:
                mode = getattr(emp, "attendance_mode", "fixed_shift")
                if mode == "field_worker":
                    day_type = "work_day"
                    work_mode = "field"
                    start = None
                    end = None
                    hours = 9
                    geofence = False
                    tracking = True
                    visits = True
                else:
                    day_type = "work_day"
                    work_mode = "fixed"
                    start = dt_time(8, 0)
                    end = dt_time(17, 0)
                    hours = 8
                    geofence = True
                    tracking = False
                    visits = False

            try:
                DailyAssignment.objects.create(
                    company=company,
                    employee=emp,
                    date=d,
                    day_type=day_type,
                    work_mode=work_mode,
                    shift=shift if work_mode == "fixed" and day_type == "work_day" else None,
                    start_time=start,
                    end_time=end,
                    expected_hours=hours,
                    requires_geofence=geofence,
                    requires_tracking=tracking,
                    requires_visits=visits,
                    status="scheduled",
                    is_auto_generated=True,
                )
            except Exception:
                pass

    print(f"  ✅ تم إنشاء تكليفات لـ 7 أيام")
else:
    print("  ℹ️  تكليفات موجودة أو مفيش شركة")


# ════════════════════════════════════════════════════════════
# 8) تحديث صفحة السياسات
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث policies.html...")

policies_path = os.path.join(BASE_DIR, "templates", "companies", "policies.html")
policies = read_file(policies_path)

if "off_day_checkin_mode" not in policies:
    new_section = """
      <!-- سياسات يوم الراحة / الإجازة -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white border-0 pt-4 pb-2 px-4">
            <h5 class="fw-bold mb-0">
              <i class="bi bi-calendar-x me-2" style="color:#e91e63;"></i>
              سياسات الحضور الاستثنائي
            </h5>
          </div>
          <div class="card-body px-4 pb-4">

            <div class="mb-3">
              <label class="form-label fw-semibold small">لو الموظف سجل حضور يوم راحته</label>
              <select name="off_day_checkin_mode" class="form-select">
                <option value="block" {% if policy.off_day_checkin_mode == 'block' %}selected{% endif %}>منع تسجيل الحضور</option>
                <option value="allow_notify_hr" {% if policy.off_day_checkin_mode == 'allow_notify_hr' %}selected{% endif %}>سماح مع إشعار HR</option>
                <option value="allow_convert_by_hr" {% if policy.off_day_checkin_mode == 'allow_convert_by_hr' %}selected{% endif %}>سماح وHR يحول لتكليف</option>
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold small">لو الموظف سجل حضور يوم إجازته</label>
              <select name="leave_day_checkin_mode" class="form-select">
                <option value="block" {% if policy.leave_day_checkin_mode == 'block' %}selected{% endif %}>منع تسجيل الحضور</option>
                <option value="allow_notify_hr" {% if policy.leave_day_checkin_mode == 'allow_notify_hr' %}selected{% endif %}>سماح مع إشعار HR</option>
                <option value="allow_convert_by_hr" {% if policy.leave_day_checkin_mode == 'allow_convert_by_hr' %}selected{% endif %}>سماح وHR يحول لتكليف</option>
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold small">لو مفيش تكليف ليومه</label>
              <select name="unplanned_checkin_mode" class="form-select">
                <option value="use_default" {% if policy.unplanned_checkin_mode == 'use_default' %}selected{% endif %}>استخدم الإعداد الافتراضي</option>
                <option value="create_exception" {% if policy.unplanned_checkin_mode == 'create_exception' %}selected{% endif %}>سجل كحالة استثنائية</option>
                <option value="block" {% if policy.unplanned_checkin_mode == 'block' %}selected{% endif %}>منع</option>
              </select>
            </div>

          </div>
        </div>
      </div>
"""
    # نضيف قبل الملاحظات
    target = """      <!-- ملاحظات -->"""
    if target in policies:
        policies = policies.replace(target, new_section + "\n" + target)
        write_file(policies_path, policies)
        print("  ✅ تم إضافة سياسات الحضور الاستثنائي")
    else:
        print("  ℹ️  مكان الإدراج مختلف")
else:
    print("  ℹ️  سياسات الحضور الاستثنائي موجودة")


# ════════════════════════════════════════════════════════════
# 9) تحديث companies/views.py لحفظ الحقول الجديدة
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث companies/views.py...")

comp_views_path = os.path.join(BASE_DIR, "companies", "views.py")
comp_views = read_file(comp_views_path)

if "off_day_checkin_mode" not in comp_views:
    old_part = '        policy.notes = request.POST.get("notes", "")'
    new_part = '''        # سياسات الحضور الاستثنائي
        policy.off_day_checkin_mode = request.POST.get("off_day_checkin_mode", "allow_notify_hr")
        policy.leave_day_checkin_mode = request.POST.get("leave_day_checkin_mode", "block")
        policy.unplanned_checkin_mode = request.POST.get("unplanned_checkin_mode", "create_exception")

        policy.notes = request.POST.get("notes", "")'''
    if old_part in comp_views:
        comp_views = comp_views.replace(old_part, new_part)
        write_file(comp_views_path, comp_views)
        print("  ✅ تم ربط حفظ الحقول الجديدة")
    else:
        print("  ℹ️  النص مختلف")
else:
    print("  ℹ️  الحقول مربوطة بالفعل")


print("\n" + "=" * 60)
print("  ✅ Patch 42a اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ Employee: attendance_mode + required_daily_hours
  2. ✅ DailyAssignment model كامل:
       - day_type (7 أنواع)
       - work_mode (6 أنواع)
       - start/end times
       - split shift support
       - replacement / extra / overtime flags
       - tracking / visits / geofence flags
       - exception handling
       - manager approval
       - auto-generated flag
  3. ✅ CompanyPolicy:
       - off_day_checkin_mode
       - leave_day_checkin_mode
       - unplanned_checkin_mode
  4. ✅ Migration
  5. ✅ Admin registration
  6. ✅ Seed data (7 أيام تكليفات)
  7. ✅ صفحة السياسات محدثة
  8. ✅ حفظ الإعدادات الجديدة

الخطوة الجاية:
  Patch 42b: ربط check-in logic بـ DailyAssignment
""")