#!/usr/bin/env python3
"""
Patch 45a: Workflow Models
===========================
1) ApprovalFlow model
2) ApprovalDelegation model
3) EmployeeRequest approval steps
4) LeaveRequest substitute
5) CompanyPolicy leave_requires_substitute
6) Migration
7) Admin
8) Seed default flows
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()

from django.core.management import call_command


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
print("  Patch 45a: Workflow Models")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) requests_app/models.py → ApprovalFlow + steps
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث requests_app/models.py...")

req_models_path = os.path.join(BASE_DIR, "requests_app", "models.py")
req_models = read_file(req_models_path)

workflow_models = '''

# ════════════════════════════════════════════════════════════
# Workflow الموافقات
# ════════════════════════════════════════════════════════════

APPROVAL_ROLE_CHOICES = [
    ("skip", "تخطي"),
    ("direct_manager", "المدير المباشر"),
    ("hr_manager", "مدير HR"),
    ("company_admin", "صاحب الشركة"),
]


class ApprovalFlow(TenantModel):
    """مسار الموافقة لكل نوع طلب"""

    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.CASCADE,
        related_name="approval_flows",
        verbose_name="نوع الطلب"
    )

    step_1_role = models.CharField(
        max_length=20,
        choices=APPROVAL_ROLE_CHOICES,
        default="direct_manager",
        verbose_name="الخطوة 1"
    )
    step_2_role = models.CharField(
        max_length=20,
        choices=APPROVAL_ROLE_CHOICES,
        default="hr_manager",
        verbose_name="الخطوة 2"
    )
    step_3_role = models.CharField(
        max_length=20,
        choices=APPROVAL_ROLE_CHOICES,
        default="skip",
        verbose_name="الخطوة 3"
    )

    escalation_enabled = models.BooleanField(
        default=True,
        verbose_name="تصعيد تلقائي لو المسؤول غير متاح"
    )
    escalation_to = models.CharField(
        max_length=20,
        choices=[
            ("hr_manager", "مدير HR"),
            ("company_admin", "صاحب الشركة"),
        ],
        default="hr_manager",
        verbose_name="التصعيد يروح لمين"
    )
    notify_employee_on_each_step = models.BooleanField(
        default=True,
        verbose_name="إشعار الموظف في كل خطوة"
    )

    class Meta:
        verbose_name = "مسار موافقة"
        verbose_name_plural = "مسارات الموافقة"
        unique_together = [["company", "request_type"]]

    def __str__(self):
        return f"مسار: {self.request_type.name}"

    def get_active_steps(self):
        steps = []
        if self.step_1_role != "skip":
            steps.append(("step_1", self.step_1_role, self.get_step_1_role_display()))
        if self.step_2_role != "skip":
            steps.append(("step_2", self.step_2_role, self.get_step_2_role_display()))
        if self.step_3_role != "skip":
            steps.append(("step_3", self.step_3_role, self.get_step_3_role_display()))
        return steps


class ApprovalDelegation(TenantModel):
    """تفويض الصلاحيات"""

    SCOPE_CHOICES = [
        ("all_approvals", "كل الموافقات"),
        ("team_only", "فريقه فقط"),
    ]

    delegator = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="delegations_given",
        verbose_name="المُفوِّض"
    )
    delegate = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="delegations_received",
        verbose_name="المُفوَّض إليه"
    )
    delegator_role = models.CharField(
        max_length=20,
        verbose_name="دور المُفوِّض"
    )
    start_date = models.DateField(
        verbose_name="من تاريخ"
    )
    end_date = models.DateField(
        verbose_name="إلى تاريخ"
    )
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default="all_approvals",
        verbose_name="نطاق التفويض"
    )
    reason = models.TextField(
        blank=True,
        verbose_name="السبب"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )

    class Meta:
        verbose_name = "تفويض صلاحيات"
        verbose_name_plural = "تفويضات الصلاحيات"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.delegator} → {self.delegate} ({self.start_date} - {self.end_date})"

    @property
    def is_currently_active(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date
'''

if "class ApprovalFlow" not in req_models:
    req_models += workflow_models
    write_file(req_models_path, req_models)
    print("  ✅ تم إضافة ApprovalFlow + ApprovalDelegation")
else:
    print("  ℹ️  موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) EmployeeRequest — approval steps
# ════════════════════════════════════════════════════════════
print("\n🔧 إضافة approval steps في EmployeeRequest...")

req_models = read_file(req_models_path)

approval_steps_fields = '''
    # ── Workflow Steps ──────────────────────────────────
    current_step = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="الخطوة الحالية"
    )

    step_1_status = models.CharField(
        max_length=20,
        blank=True,
        choices=[("pending","قيد الانتظار"),("approved","موافق"),("rejected","مرفوض"),("skipped","تخطي")],
        default="pending",
        verbose_name="حالة الخطوة 1"
    )
    step_1_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="step1_approvals", verbose_name="الخطوة 1 بواسطة"
    )
    step_1_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الخطوة 1")
    step_1_notes = models.TextField(blank=True, verbose_name="ملاحظات الخطوة 1")

    step_2_status = models.CharField(
        max_length=20, blank=True,
        choices=[("pending","قيد الانتظار"),("approved","موافق"),("rejected","مرفوض"),("skipped","تخطي")],
        default="",
        verbose_name="حالة الخطوة 2"
    )
    step_2_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="step2_approvals", verbose_name="الخطوة 2 بواسطة"
    )
    step_2_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الخطوة 2")
    step_2_notes = models.TextField(blank=True, verbose_name="ملاحظات الخطوة 2")

    step_3_status = models.CharField(
        max_length=20, blank=True,
        choices=[("pending","قيد الانتظار"),("approved","موافق"),("rejected","مرفوض"),("skipped","تخطي")],
        default="",
        verbose_name="حالة الخطوة 3"
    )
    step_3_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="step3_approvals", verbose_name="الخطوة 3 بواسطة"
    )
    step_3_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الخطوة 3")
    step_3_notes = models.TextField(blank=True, verbose_name="ملاحظات الخطوة 3")

    # بديل الموظف في الإجازة
    substitute_employee = models.ForeignKey(
        "employees.Employee", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="substituted_requests",
        verbose_name="البديل"
    )
    substitute_notified = models.BooleanField(
        default=False,
        verbose_name="تم إشعار البديل"
    )
'''

if "current_step" not in req_models:
    target = """    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
"""
    if target in req_models:
        req_models = req_models.replace(
            target,
            approval_steps_fields + "\n" + target
        )
        write_file(req_models_path, req_models)
        print("  ✅ تم إضافة approval steps")
    else:
        print("  ⚠️  لم أجد المكان المتوقع — محتاج مراجعة يدوية")
else:
    print("  ℹ️  approval steps موجودة بالفعل")


# ════════════════════════════════════════════════════════════
# 3) CompanyPolicy — leave_requires_substitute
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث CompanyPolicy...")

comp_models_path = os.path.join(BASE_DIR, "companies", "models.py")
comp_models = read_file(comp_models_path)

if "leave_requires_substitute" not in comp_models:
    new_field = '''
    # ── سياسة البديل في الإجازة ───────────────────────
    leave_requires_substitute = models.BooleanField(
        default=False,
        verbose_name="الإجازة تحتاج بديل"
    )
    substitute_same_department_only = models.BooleanField(
        default=False,
        verbose_name="البديل من نفس القسم فقط"
    )
'''
    if "    notes = models.TextField(" in comp_models:
        comp_models = comp_models.replace(
            "    notes = models.TextField(",
            new_field + "\n    notes = models.TextField(",
            1
        )
        write_file(comp_models_path, comp_models)
        print("  ✅ تم إضافة leave_requires_substitute")
else:
    print("  ℹ️  leave_requires_substitute موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 4) Manual Migrations
# ════════════════════════════════════════════════════════════
print("\n🔧 Manual Migrations...")

# requests_app
last, num = get_last_migration("requests_app")
new_num = str(num + 1).zfill(4)
create_file(
    os.path.join(BASE_DIR, "requests_app", "migrations", f"{new_num}_add_workflow_models.py"),
    f'''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("requests_app", "{last}"),
        ("companies", "0001_initial"),
        ("accounts", "0001_initial"),
        ("employees", "0001_initial"),
    ]

    operations = [
        # ApprovalFlow
        migrations.CreateModel(
            name="ApprovalFlow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("step_1_role", models.CharField(max_length=20, default="direct_manager")),
                ("step_2_role", models.CharField(max_length=20, default="hr_manager")),
                ("step_3_role", models.CharField(max_length=20, default="skip")),
                ("escalation_enabled", models.BooleanField(default=True)),
                ("escalation_to", models.CharField(max_length=20, default="hr_manager")),
                ("notify_employee_on_each_step", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="companies.company")),
                ("request_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approval_flows", to="requests_app.requesttype")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="accounts.user")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="accounts.user")),
            ],
            options={{"verbose_name": "مسار موافقة", "verbose_name_plural": "مسارات الموافقة"}},
        ),
        migrations.AlterUniqueTogether(
            name="approvalflow",
            unique_together={{("company", "request_type")}},
        ),

        # ApprovalDelegation
        migrations.CreateModel(
            name="ApprovalDelegation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("delegator_role", models.CharField(max_length=20)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("scope", models.CharField(max_length=20, default="all_approvals")),
                ("reason", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="companies.company")),
                ("delegator", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delegations_given", to="accounts.user")),
                ("delegate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delegations_received", to="accounts.user")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="accounts.user")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="accounts.user")),
            ],
            options={{"verbose_name": "تفويض صلاحيات", "verbose_name_plural": "تفويضات الصلاحيات", "ordering": ["-start_date"]}},
        ),

        # EmployeeRequest approval steps
        migrations.AddField(model_name="employeerequest", name="current_step",
            field=models.PositiveSmallIntegerField(default=1)),
        migrations.AddField(model_name="employeerequest", name="step_1_status",
            field=models.CharField(max_length=20, blank=True, default="pending")),
        migrations.AddField(model_name="employeerequest", name="step_1_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="step1_approvals", to="accounts.user")),
        migrations.AddField(model_name="employeerequest", name="step_1_at",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="employeerequest", name="step_1_notes",
            field=models.TextField(blank=True)),

        migrations.AddField(model_name="employeerequest", name="step_2_status",
            field=models.CharField(max_length=20, blank=True, default="")),
        migrations.AddField(model_name="employeerequest", name="step_2_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="step2_approvals", to="accounts.user")),
        migrations.AddField(model_name="employeerequest", name="step_2_at",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="employeerequest", name="step_2_notes",
            field=models.TextField(blank=True)),

        migrations.AddField(model_name="employeerequest", name="step_3_status",
            field=models.CharField(max_length=20, blank=True, default="")),
        migrations.AddField(model_name="employeerequest", name="step_3_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="step3_approvals", to="accounts.user")),
        migrations.AddField(model_name="employeerequest", name="step_3_at",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="employeerequest", name="step_3_notes",
            field=models.TextField(blank=True)),

        migrations.AddField(model_name="employeerequest", name="substitute_employee",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                     related_name="substituted_requests", to="employees.employee")),
        migrations.AddField(model_name="employeerequest", name="substitute_notified",
            field=models.BooleanField(default=False)),
    ]
'''
)

# companies
last, num = get_last_migration("companies")
new_num = str(num + 1).zfill(4)
create_file(
    os.path.join(BASE_DIR, "companies", "migrations", f"{new_num}_add_leave_substitute_policy.py"),
    f'''from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "{last}"),
    ]

    operations = [
        migrations.AddField(
            model_name="companypolicy",
            name="leave_requires_substitute",
            field=models.BooleanField(default=False, verbose_name="الإجازة تحتاج بديل"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="substitute_same_department_only",
            field=models.BooleanField(default=False, verbose_name="البديل من نفس القسم فقط"),
        ),
    ]
'''
)

# migrate
print("\n🔧 migrate...")
call_command("migrate")
print("  ✅ Migration OK")


# ════════════════════════════════════════════════════════════
# 5) Admin
# ════════════════════════════════════════════════════════════
print("\n🔧 Admin...")

admin_path = os.path.join(BASE_DIR, "requests_app", "admin.py")
admin_content = read_file(admin_path)

if "ApprovalFlow" not in admin_content:
    admin_content += '''

from .models import ApprovalFlow, ApprovalDelegation

@admin.register(ApprovalFlow)
class ApprovalFlowAdmin(admin.ModelAdmin):
    list_display = ["request_type", "step_1_role", "step_2_role", "step_3_role", "escalation_enabled"]

@admin.register(ApprovalDelegation)
class ApprovalDelegationAdmin(admin.ModelAdmin):
    list_display = ["delegator", "delegate", "start_date", "end_date", "is_active", "scope"]
'''
    write_file(admin_path, admin_content)
    print("  ✅ تم تسجيل Workflow models في Admin")
else:
    print("  ℹ️  Admin مسجل بالفعل")


# ════════════════════════════════════════════════════════════
# 6) Seed default approval flows
# ════════════════════════════════════════════════════════════
print("\n🌱 إنشاء مسارات موافقة افتراضية...")

from companies.models import Company
from requests_app.models import RequestType, ApprovalFlow

company = Company.objects.first()

if company and not ApprovalFlow.objects.filter(company=company).exists():
    default_flows = {
        "إجازة سنوية": ("direct_manager", "hr_manager", "skip"),
        "إجازة مرضية": ("direct_manager", "hr_manager", "skip"),
        "إجازة طارئة": ("direct_manager", "hr_manager", "skip"),
        "سلفة مالية": ("hr_manager", "company_admin", "skip"),
        "زيادة راتب": ("direct_manager", "hr_manager", "company_admin"),
        "مكافأة": ("direct_manager", "hr_manager", "skip"),
        "شهادة راتب": ("hr_manager", "skip", "skip"),
        "شهادة لمن يهمه الأمر": ("hr_manager", "skip", "skip"),
        "طلب ترقية": ("direct_manager", "hr_manager", "company_admin"),
        "طلب نقل داخلي": ("direct_manager", "hr_manager", "company_admin"),
        "استقالة": ("direct_manager", "hr_manager", "company_admin"),
        "تدريب أو مؤتمر": ("direct_manager", "hr_manager", "skip"),
        "معدات أو أدوات عمل": ("direct_manager", "hr_manager", "skip"),
        "تعويض نفقات": ("hr_manager", "company_admin", "skip"),
    }

    for type_name, (s1, s2, s3) in default_flows.items():
        rt = RequestType.objects.filter(company=company, name=type_name).first()
        if rt:
            ApprovalFlow.objects.create(
                company=company,
                request_type=rt,
                step_1_role=s1,
                step_2_role=s2,
                step_3_role=s3,
                escalation_enabled=True,
                escalation_to="hr_manager",
                notify_employee_on_each_step=True,
            )

    print(f"  ✅ تم إنشاء مسارات افتراضية")
else:
    print("  ℹ️  مسارات موجودة أو مفيش شركة")


print("\n" + "=" * 60)
print("  ✅ Patch 45a اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ ApprovalFlow model
  2. ✅ ApprovalDelegation model
  3. ✅ EmployeeRequest approval steps (3 خطوات)
  4. ✅ substitute_employee في الطلب
  5. ✅ leave_requires_substitute في CompanyPolicy
  6. ✅ Migrations
  7. ✅ Admin registration
  8. ✅ Seed: مسارات موافقة افتراضية لـ 14 نوع طلب

الجاي:
  Patch 45b → Logic + Escalation
  Patch 45c → UI + Templates
""")