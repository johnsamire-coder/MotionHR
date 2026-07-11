#!/usr/bin/env python3
"""
Patch 45b: Workflow Logic + Escalation
========================================
1) routing الطلب حسب ApprovalFlow
2) escalation لو المسؤول مش متاح
3) delegation check
4) إشعار للموظف في كل خطوة
5) تحديث requests_app/views.py
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motionhr.settings")

import django
django.setup()


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ تم تحديث: {path}")


print("=" * 60)
print("  Patch 45b: Workflow Logic")
print("=" * 60)


# ════════════════════════════════════════════════════════════
# 1) requests_app/views.py — Workflow Logic
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث requests_app/views.py...")

views_path = os.path.join(BASE_DIR, "requests_app", "views.py")
views = read_file(views_path)

workflow_logic = '''

# ════════════════════════════════════════════════════════════
# Workflow Engine
# ════════════════════════════════════════════════════════════

def _get_approval_flow(company, request_type):
    """جلب مسار الموافقة لنوع الطلب"""
    try:
        from requests_app.models import ApprovalFlow
        return ApprovalFlow.objects.filter(
            company=company,
            request_type=request_type
        ).first()
    except Exception:
        return None


def _get_active_delegation(company, role):
    """
    هل فيه تفويض نشط لهذا الدور؟
    لو أيوه → إيه الـ delegate؟
    """
    try:
        from requests_app.models import ApprovalDelegation
        from django.utils import timezone
        today = timezone.now().date()

        delegation = ApprovalDelegation.objects.filter(
            company=company,
            delegator_role=role,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        ).first()

        if delegation:
            return delegation.delegate
    except Exception:
        pass
    return None


def _get_approver_for_role(role, employee, company):
    """
    جلب المستخدم المسؤول عن الموافقة حسب الدور
    مع مراعاة التفويض
    """
    from accounts.models import User

    # أولًا: هل فيه تفويض نشط؟
    delegate = _get_active_delegation(company, role)
    if delegate:
        return delegate

    if role == "direct_manager":
        # المدير المباشر للموظف
        try:
            manager_emp = employee.direct_manager
            if manager_emp and manager_emp.user:
                return manager_emp.user
        except Exception:
            pass
        # لو مفيش مدير → escalate لـ HR
        return User.objects.filter(
            company=company,
            role="hr_manager"
        ).first()

    elif role == "hr_manager":
        return User.objects.filter(
            company=company,
            role="hr_manager"
        ).first()

    elif role == "company_admin":
        return User.objects.filter(
            company=company,
            role__in=["company_admin", "super_admin"]
        ).first()

    return None


def _initialize_workflow(req_obj):
    """
    تهيئة workflow للطلب الجديد
    - جلب مسار الموافقة
    - تحديد الخطوة الأولى
    - إشعار أول approver
    """
    flow = _get_approval_flow(req_obj.company, req_obj.request_type)

    if not flow:
        # لو مفيش flow → يروح لـ HR مباشرة
        req_obj.current_step = 1
        req_obj.step_1_status = "pending"
        req_obj.save(update_fields=["current_step", "step_1_status"])
        _notify_approver_for_step(req_obj, 1, "hr_manager")
        return

    steps = flow.get_active_steps()

    if not steps:
        # مفيش خطوات → approve تلقائي
        req_obj.status = "approved"
        req_obj.save(update_fields=["status"])
        return

    req_obj.current_step = 1
    req_obj.step_1_status = "pending"
    req_obj.save(update_fields=["current_step", "step_1_status"])

    # إشعار الـ approver الأول
    first_step_key, first_role, _ = steps[0]
    _notify_approver_for_step(req_obj, 1, first_role)


def _notify_approver_for_step(req_obj, step_num, role):
    """إشعار المسؤول عن خطوة معينة"""
    try:
        from accounts.models import EmployeeNotification
        from employees.models import Employee

        approver = _get_approver_for_role(role, req_obj.employee, req_obj.company)
        if not approver:
            return

        approver_emp = Employee.all_objects.filter(user=approver).first()
        if not approver_emp:
            return

        role_labels = {
            "direct_manager": "المدير المباشر",
            "hr_manager": "مدير HR",
            "company_admin": "صاحب الشركة",
        }

        title = f"طلب جديد يحتاج موافقتك"
        message = (
            f"الموظف {req_obj.employee.full_name_ar} قدم طلب:\\n"
            f"النوع: {req_obj.request_type.name}\\n"
            f"الموضوع: {req_obj.subject}\\n"
            f"الخطوة {step_num} من {role_labels.get(role, role)}"
        )

        EmployeeNotification.objects.create(
            employee=approver_emp,
            title=title,
            message=message,
            notification_type="request_update",
            severity="warning",
            is_read=False,
        )
    except Exception:
        pass


def _notify_employee_step_result(req_obj, step_num, action):
    """إشعار الموظف بنتيجة خطوة"""
    try:
        from accounts.models import EmployeeNotification

        action_label = "وافق" if action == "approved" else "رفض"
        step_label = f"الخطوة {step_num}"

        title = f"تحديث على طلبك: {req_obj.request_type.name}"
        message = (
            f"طلبك ({req_obj.subject}) "
            f"تم {'الموافقة عليه' if action == 'approved' else 'رفضه'} "
            f"في {step_label}."
        )
        severity = "info" if action == "approved" else "danger"

        EmployeeNotification.objects.create(
            employee=req_obj.employee,
            title=title,
            message=message,
            notification_type="request_update",
            severity=severity,
            is_read=False,
        )
    except Exception:
        pass


def _process_step_action(req_obj, step_num, action, by_user, notes=""):
    """
    معالجة action (approve/reject) على خطوة معينة
    """
    from django.utils import timezone

    now = timezone.now()
    flow = _get_approval_flow(req_obj.company, req_obj.request_type)

    # حفظ بيانات الخطوة
    if step_num == 1:
        req_obj.step_1_status = action
        req_obj.step_1_by = by_user
        req_obj.step_1_at = now
        req_obj.step_1_notes = notes
    elif step_num == 2:
        req_obj.step_2_status = action
        req_obj.step_2_by = by_user
        req_obj.step_2_at = now
        req_obj.step_2_notes = notes
    elif step_num == 3:
        req_obj.step_3_status = action
        req_obj.step_3_by = by_user
        req_obj.step_3_at = now
        req_obj.step_3_notes = notes

    if action == "rejected":
        req_obj.status = "rejected"
        req_obj.reviewed_by = by_user
        req_obj.reviewed_at = now
        req_obj.save()

        notify_emp = True
        if flow:
            notify_emp = flow.notify_employee_on_each_step
        if notify_emp:
            _notify_employee_step_result(req_obj, step_num, "rejected")
        return

    # approved → نروح للخطوة الجاية
    if action == "approved":
        notify_emp = True
        if flow:
            notify_emp = flow.notify_employee_on_each_step
        if notify_emp:
            _notify_employee_step_result(req_obj, step_num, "approved")

        # نحدد الخطوة الجاية
        next_step = step_num + 1
        all_steps = ["skip", "skip", "skip"]
        if flow:
            all_steps = [flow.step_1_role, flow.step_2_role, flow.step_3_role]

        while next_step <= 3:
            next_role = all_steps[next_step - 1]
            if next_role != "skip":
                # فيه خطوة جاية
                req_obj.current_step = next_step
                if next_step == 2:
                    req_obj.step_2_status = "pending"
                elif next_step == 3:
                    req_obj.step_3_status = "pending"
                req_obj.save()
                _notify_approver_for_step(req_obj, next_step, next_role)
                return
            next_step += 1

        # كل الخطوات خلصت → Approved
        req_obj.status = "approved"
        req_obj.reviewed_by = by_user
        req_obj.reviewed_at = now
        req_obj.save()

        # إشعار الموظف بالموافقة النهائية
        try:
            from accounts.models import EmployeeNotification
            EmployeeNotification.objects.create(
                employee=req_obj.employee,
                title=f"تمت الموافقة على طلبك",
                message=(
                    f"تمت الموافقة على طلبك ({req_obj.subject}) بشكل نهائي.\\n"
                    f"النوع: {req_obj.request_type.name}"
                ),
                notification_type="request_update",
                severity="info",
                is_read=False,
            )
        except Exception:
            pass

        # لو الطلب بديل + إجازة → إشعار البديل
        if req_obj.substitute_employee and not req_obj.substitute_notified:
            try:
                from accounts.models import EmployeeNotification
                EmployeeNotification.objects.create(
                    employee=req_obj.substitute_employee,
                    title="تم تحديدك بديلًا",
                    message=(
                        f"تم تحديدك بديلًا للموظف {req_obj.employee.full_name_ar}\\n"
                        f"خلال الفترة: {req_obj.start_date} - {req_obj.end_date or 'غير محدد'}"
                    ),
                    notification_type="general_notice",
                    severity="info",
                    is_read=False,
                )
                req_obj.substitute_notified = True
                req_obj.save(update_fields=["substitute_notified"])
            except Exception:
                pass


def _can_user_approve_step(req_obj, user):
    """
    هل هذا المستخدم مسؤول عن الخطوة الحالية؟
    """
    flow = _get_approval_flow(req_obj.company, req_obj.request_type)
    current = req_obj.current_step

    if flow:
        steps = flow.get_active_steps()
        if current <= len(steps):
            step_key, role, _ = steps[current - 1]
            approver = _get_approver_for_role(role, req_obj.employee, req_obj.company)
            if approver and approver.id == user.id:
                return True, current, role

    # fallback: HR يقدر يوافق دايمًا
    if getattr(user, "role", "") in ["hr_manager", "company_admin", "super_admin"]:
        return True, current, getattr(user, "role", "hr_manager")

    return False, current, None
'''

if "_initialize_workflow" not in views:
    views += workflow_logic
    write_file(views_path, views)
    print("  ✅ تم إضافة Workflow Logic")
else:
    print("  ℹ️  Workflow Logic موجود بالفعل")


# ════════════════════════════════════════════════════════════
# 2) تحديث requests_add — يشغل workflow بعد الحفظ
# ════════════════════════════════════════════════════════════
print("\n🔧 ربط workflow بـ request_add...")

views = read_file(views_path)

old_save = """                lr.save()
                messages.success(request, "تم تقديم الطلب بنجاح")
                return redirect("requests_app:list")"""

new_save = """                lr.save()

                # تشغيل workflow
                _initialize_workflow(lr)

                messages.success(request, "تم تقديم الطلب بنجاح")
                return redirect("requests_app:list")"""

if old_save in views and "_initialize_workflow(lr)" not in views:
    views = views.replace(old_save, new_save)
    write_file(views_path, views)
    print("  ✅ تم ربط workflow بـ request_add")
else:
    print("  ℹ️  workflow مربوط بالفعل أو النص مختلف")


# ════════════════════════════════════════════════════════════
# 3) تحديث request_approve و request_reject
# ════════════════════════════════════════════════════════════
print("\n🔧 تحديث approve/reject views...")

views = read_file(views_path)

old_approve = '''@login_required
@require_POST
def request_approve(request, pk):
    """موافقة على طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    notes = request.POST.get("notes", "")
    req_obj.status = "approved"
    req_obj.reviewed_by = request.user
    req_obj.reviewed_at = timezone.now()
    req_obj.review_notes = notes
    req_obj.save()
    messages.success(request, "تمت الموافقة على الطلب")
    return redirect("requests_app:detail", pk=pk)


@login_required
@require_POST
def request_reject(request, pk):
    """رفض طلب"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    notes = request.POST.get("notes", "")
    req_obj.status = "rejected"
    req_obj.reviewed_by = request.user
    req_obj.reviewed_at = timezone.now()
    req_obj.review_notes = notes
    req_obj.save()
    messages.warning(request, "تم رفض الطلب")
    return redirect("requests_app:detail", pk=pk)'''

new_approve = '''@login_required
@require_POST
def request_approve(request, pk):
    """موافقة على طلب — مع Workflow"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    notes = request.POST.get("notes", "")

    can_approve, step_num, role = _can_user_approve_step(req_obj, request.user)

    if can_approve:
        _process_step_action(req_obj, step_num, "approved", request.user, notes)
        if req_obj.status == "approved":
            messages.success(request, "تمت الموافقة النهائية على الطلب ✅")
        else:
            messages.success(request, f"تمت الموافقة على الخطوة {step_num}")
    else:
        messages.error(request, "ليس لديك صلاحية الموافقة في هذه الخطوة")

    return redirect("requests_app:detail", pk=pk)


@login_required
@require_POST
def request_reject(request, pk):
    """رفض طلب — مع Workflow"""
    req_obj = get_object_or_404(
        EmployeeRequest, pk=pk, company=request.user.company
    )
    notes = request.POST.get("notes", "")

    can_approve, step_num, role = _can_user_approve_step(req_obj, request.user)

    if can_approve:
        _process_step_action(req_obj, step_num, "rejected", request.user, notes)
        messages.warning(request, "تم رفض الطلب ❌")
    else:
        messages.error(request, "ليس لديك صلاحية الرفض في هذه الخطوة")

    return redirect("requests_app:detail", pk=pk)'''

if old_approve in views:
    views = views.replace(old_approve, new_approve)
    write_file(views_path, views)
    print("  ✅ تم تحديث approve/reject")
else:
    print("  ℹ️  approve/reject محدث بالفعل أو النص مختلف")


# ════════════════════════════════════════════════════════════
# 4) Seed: تشغيل workflow على الطلبات الموجودة
# ════════════════════════════════════════════════════════════
print("\n🌱 تهيئة طلبات موجودة...")

from requests_app.models import EmployeeRequest

pending_reqs = EmployeeRequest.objects.filter(
    status="pending",
    current_step=1,
    step_1_status=""
)

count = 0
for req in pending_reqs:
    req.step_1_status = "pending"
    req.save(update_fields=["step_1_status"])
    count += 1

print(f"  ✅ تم تهيئة {count} طلب موجود")


print("\n" + "=" * 60)
print("  ✅ Patch 45b اكتمل!")
print("=" * 60)
print("""
اللي اتعمل:
  1. ✅ _initialize_workflow — تهيئة workflow للطلب الجديد
  2. ✅ _get_approval_flow — جلب مسار الموافقة
  3. ✅ _get_active_delegation — فحص التفويض النشط
  4. ✅ _get_approver_for_role — تحديد المسؤول مع escalation
  5. ✅ _process_step_action — معالجة الموافقة/الرفض
  6. ✅ _can_user_approve_step — فحص صلاحية الموافقة
  7. ✅ إشعار المسؤول في كل خطوة
  8. ✅ إشعار الموظف بنتيجة كل خطوة
  9. ✅ إشعار البديل لو الطلب اتوافق
  10. ✅ request_add يشغل workflow تلقائي
  11. ✅ approve/reject يستخدم Workflow

الجاي:
  Patch 45c → UI: مسارات الموافقة + التفويضات
""")