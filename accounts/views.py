from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Count, Q


# ════════════════════════════════════════════════════════════
# Dashboard محدث بأرقام حقيقية
# ════════════════════════════════════════════════════════════
from django.contrib.auth.decorators import login_required
from django.utils import timezone as tz


@login_required
def dashboard(request):
    """لوحة التحكم الرئيسية"""
    from datetime import date

    company = request.user.company
    today   = date.today()
    context = {"page_title": "لوحة التحكم"}

    if not company:
        return render(request, "dashboard/index.html", context)

    try:
        from employees.models import Employee
        total_employees  = Employee.objects.filter(
            company=company, status="active").count()
        new_this_month   = Employee.objects.filter(
            company=company,
            hire_date__year=today.year,
            hire_date__month=today.month,
        ).count()
    except Exception:
        total_employees = new_this_month = 0

    try:
        from attendance.models import Attendance
        today_att    = Attendance.objects.filter(company=company, date=today)
        present_today = today_att.filter(
            status__in=["present", "late"]).count()
        absent_today  = today_att.filter(status="absent").count()
        late_today    = today_att.filter(status="late").count()
    except Exception:
        present_today = absent_today = late_today = 0

    try:
        from leaves.models import LeaveRequest
        pending_leaves = LeaveRequest.objects.filter(
            company=company, status="pending").count()
    except Exception:
        pending_leaves = 0

    try:
        from attendance.models import LocationLog
        from datetime import timedelta
        cutoff = tz.now() - timedelta(minutes=5)
        live_field = LocationLog.objects.filter(
            company=company,
            timestamp__gte=cutoff,
        ).values("employee").distinct().count()
    except Exception:
        live_field = 0

    try:
        from employees.models import Employee as Emp
        recent_employees = Emp.objects.filter(
            company=company
        ).select_related(
            "job_title", "department"
        ).order_by("-hire_date")[:5]
    except Exception:
        recent_employees = []

    try:
        from attendance.models import Attendance as Att
        recent_attendance = Att.objects.filter(
            company=company, date=today
        ).select_related("employee").order_by("-check_in_time")[:8]
    except Exception:
        recent_attendance = []

    context.update({
        "total_employees":  total_employees,
        "new_this_month":   new_this_month,
        "present_today":    present_today,
        "absent_today":     absent_today,
        "late_today":       late_today,
        "pending_leaves":   pending_leaves,
        "live_field":       live_field,
        "recent_employees": recent_employees,
        "recent_attendance":recent_attendance,
        "today":            today,
    })

    return render(request, "dashboard/index.html", context)


# ─────────────────────────────────────────────
# بعد تغيير كلمة المرور - نلغي الإجبار
# ─────────────────────────────────────────────
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy


class CustomPasswordChangeView(PasswordChangeView):
    """
    Override لـ PasswordChangeView
    يعمل must_change_password = False بعد التغيير
    """
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        # إلغاء إجبار التغيير
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=['must_change_password'])
        return response


# ════════════════════════════════════════════════════════════
# Smart Login View
# ════════════════════════════════════════════════════════════
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache


@never_cache
@require_http_methods(["GET", "POST"])
def smart_login_view(request):
    """
    صفحة تسجيل الدخول الذكية
    تدعم: username / email / employee_code / phone
    """
    # لو مسجل دخوله خليه يروح للـ dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    # تحديد placeholder حسب الشركة (مبدئياً عام)
    login_hint = 'اسم المستخدم أو الإيميل أو الرقم الوظيفي'

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember  = request.POST.get('remember_me')

        if not username or not password:
            error = 'يرجى إدخال اسم المستخدم وكلمة المرور'
        else:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if not user.is_active:
                    error = 'حسابك موقوف - تواصل مع المدير'
                else:
                    auth_login(request, user,
                               backend='accounts.login_backend.SmartLoginBackend')

                    # Session expiry
                    if not remember:
                        request.session.set_expiry(0)  # ينتهي مع إغلاق المتصفح
                    else:
                        request.session.set_expiry(60 * 60 * 24 * 30)  # 30 يوم

                    # لو لازم يغير كلمة المرور
                    if getattr(user, 'must_change_password', False):
                        return redirect('password_change')

                    return redirect('dashboard')
            else:
                error = 'اسم المستخدم أو كلمة المرور غير صحيحة'

    context = {
        'login_hint': login_hint,
        'error':      error,
    }
    return render(request, 'accounts/login.html', context)


def smart_logout_view(request):
    """تسجيل الخروج"""
    if request.method == 'POST':
        auth_logout(request)
    return redirect('login')


# ════════════════════════════════════════════════════════════
# إعدادات تسجيل الدخول
# ════════════════════════════════════════════════════════════
from django.contrib.auth.decorators import login_required


@login_required
def login_settings_view(request):
    """صفحة إعدادات تسجيل الدخول"""
    from companies.models import CompanyLoginSettings

    if not request.user.company:
        from django.contrib import messages as msg
        msg.error(request, 'لا يوجد شركة مرتبطة بحسابك')
        return redirect('dashboard')

    settings_obj = CompanyLoginSettings.get_for_company(request.user.company)

    # تحديد الميزات المتاحة حسب الخطة
    has_business     = _has_feature(request.user.company, 'login_by_employee_code')
    has_professional = _has_feature(request.user.company, 'login_by_phone')

    login_methods = [
        ('login_by_username',
         'اسم المستخدم',
         'الدخول باسم المستخدم التقليدي',
         True),
        ('login_by_email',
         'البريد الإلكتروني',
         'الدخول بعنوان البريد الإلكتروني',
         True),
        ('login_by_employee_code',
         'الرقم الوظيفي',
         'الدخول بالرقم الوظيفي (EMP00001)',
         has_business),
        ('login_by_phone',
         'رقم الموبايل',
         'الدخول برقم الهاتف المحمول',
         has_professional),
    ]

    password_rules = [
        ('require_uppercase', 'إجبار حروف كبيرة (A-Z)'),
        ('require_numbers',   'إجبار أرقام (0-9)'),
        ('require_symbols',   'إجبار رموز (@#$%)'),
    ]

    lockout_options = [
        (5,  '5 دقائق'),
        (15, '15 دقيقة'),
        (30, '30 دقيقة'),
        (60, 'ساعة'),
    ]

    if request.method == 'POST':
        # حفظ طرق الدخول
        settings_obj.login_by_username      = 'login_by_username'      in request.POST
        settings_obj.login_by_email         = 'login_by_email'         in request.POST
        settings_obj.login_by_employee_code = 'login_by_employee_code' in request.POST
        settings_obj.login_by_phone         = 'login_by_phone'         in request.POST

        # حفظ إعدادات كلمة المرور
        settings_obj.min_password_length  = int(request.POST.get('min_password_length', 8))
        settings_obj.require_uppercase    = 'require_uppercase'    in request.POST
        settings_obj.require_numbers      = 'require_numbers'      in request.POST
        settings_obj.require_symbols      = 'require_symbols'      in request.POST
        settings_obj.password_expiry_days = int(request.POST.get('password_expiry_days', 0))

        # حفظ إعدادات القفل
        settings_obj.max_login_attempts       = int(request.POST.get('max_login_attempts', 5))
        settings_obj.lockout_duration_minutes = int(request.POST.get('lockout_duration_minutes', 15))
        settings_obj.force_change_on_first_login = 'force_change_on_first_login' in request.POST

        settings_obj.save()

        from django.contrib import messages as msg
        msg.success(request, '✅ تم حفظ الإعدادات بنجاح')
        return redirect('accounts:login_settings')

    context = {
        'settings_obj':    settings_obj,
        'login_methods':   login_methods,
        'password_rules':  password_rules,
        'lockout_options': lockout_options,
        'page_title':      'إعدادات تسجيل الدخول',
    }
    return render(request, 'accounts/login_settings.html', context)


def _has_feature(company, feature_name):
    """تحقق من ميزة في اشتراك الشركة"""
    try:
        from subscriptions.models import Subscription
        sub = Subscription.objects.filter(
            company=company,
            status__in=['active', 'trial']
        ).select_related('plan').first()
        if sub:
            return getattr(sub.plan, feature_name, False)
    except Exception:
        pass
    return False


# ════════════════════════════════════════════════════════════
# PWA Views
# ════════════════════════════════════════════════════════════

def offline_view(request):
    """صفحة عدم الاتصال"""
    return render(request, "offline.html")


def manifest_view(request):
    """manifest.json"""
    import json
    from django.http import JsonResponse
    from django.conf import settings as django_settings
    import os

    manifest_path = os.path.join(django_settings.BASE_DIR, "static", "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    response = JsonResponse(manifest_data)
    response["Content-Type"] = "application/manifest+json"
    return response


def service_worker_view(request):
    """Service Worker JS"""
    from django.http import HttpResponse
    from django.conf import settings as django_settings
    import os

    sw_path = os.path.join(django_settings.BASE_DIR, "static", "sw.js")
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_content = f.read()

    response = HttpResponse(sw_content, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


# ════════════════════════════════════════════════════════════
# Profile Views
# ════════════════════════════════════════════════════════════

@login_required
def profile_view(request):
    """صفحة الملف الشخصي"""
    context = {
        "page_title": "الملف الشخصي",
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_update(request):
    """تحديث بيانات الملف الشخصي"""
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name  = request.POST.get("last_name",  user.last_name)
        user.email      = request.POST.get("email",      user.email)
        user.phone      = request.POST.get("phone",      getattr(user, "phone", ""))

        if "avatar" in request.FILES:
            user.avatar = request.FILES["avatar"]

        user.save()
        from django.contrib import messages as msg
        msg.success(request, "✅ تم تحديث ملفك الشخصي بنجاح")

    return redirect("accounts:profile")


# ════════════════════════════════════════════════════════════
# Global Search
# ════════════════════════════════════════════════════════════

@login_required
def global_search(request):
    """البحث الشامل"""
    from django.db.models import Q

    query     = request.GET.get("q", "").strip()
    employees = []
    total     = 0

    if query and request.user.company:
        try:
            from employees.models import Employee
            employees = Employee.objects.filter(
                company=request.user.company
            ).filter(
                Q(first_name_ar__icontains=query) |
                Q(last_name_ar__icontains=query) |
                Q(first_name_en__icontains=query) |
                Q(last_name_en__icontains=query) |
                Q(employee_code__icontains=query) |
                Q(national_id__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query)
            ).select_related(
                "job_title", "department"
            )[:20]
            total = len(employees)
        except Exception:
            pass

    context = {
        "query":         query,
        "employees":     employees,
        "total_results": total,
        "page_title":    f"بحث: {query}" if query else "البحث",
    }
    return render(request, "search.html", context)


# ════════════════════════════════════════════════════════════
# Notifications
# ════════════════════════════════════════════════════════════

@login_required
def notifications_view(request):
    """مركز الإشعارات"""
    from accounts.models import EmployeeNotification
    from employees.models import Employee

    current_emp = Employee.all_objects.filter(user=request.user).first()

    # إشعارات النظام القديمة
    notifications = _get_notifications(request.user)

    # إشعارات الموظف الجديدة
    db_notifications_qs = EmployeeNotification.objects.none()
    if current_emp:
        db_notifications_qs = EmployeeNotification.objects.filter(
            employee=current_emp
        ).order_by("-created_at")

    # Mark all read
    if request.method == "POST" and request.POST.get("mark_all_read") == "1":
        db_notifications_qs.filter(is_read=False).update(is_read=True)
        messages.success(request, "تم تعليم كل الإشعارات كمقروءة")
        return redirect("accounts:notifications")

    db_notifications = []
    for n in db_notifications_qs[:30]:
        icon_map = {
            "late_warning": "exclamation-triangle",
            "deduction_notice": "receipt-cutoff",
            "general_notice": "info-circle",
            "policy_reminder": "journal-text",
            "charter_reminder": "file-earmark-text",
            "request_update": "inbox",
        }
        type_map = {
            "info": "info",
            "warning": "warning",
            "danger": "danger",
        }
        db_notifications.append({
            "type": type_map.get(n.severity, "info"),
            "icon": icon_map.get(n.notification_type, "info-circle"),
            "title": n.title,
            "message": n.message,
            "time": n.created_at.strftime("%d/%m/%Y %H:%M"),
            "url": "",
            "unread": not n.is_read,
            "is_db": True,
            "id": n.pk,
        })

    merged_notifications = db_notifications + notifications

    context = {
        "page_title": "الإشعارات",
        "notifications": merged_notifications,
        "db_unread_count": db_notifications_qs.filter(is_read=False).count() if current_emp else 0,
    }
    return render(request, "accounts/notifications.html", context)

def _get_notifications(user):
    """جمع الإشعارات من كل الأماكن"""
    notifications = []

    if not user.company:
        return notifications

    try:
        # إجازات معلقة (للمدير)
        from leaves.models import LeaveRequest
        pending = LeaveRequest.objects.filter(
            company=user.company,
            status="pending"
        ).count()
        if pending:
            notifications.append({
                "type":    "warning",
                "icon":    "calendar2-week",
                "title":   f"{pending} طلب إجازة ينتظر موافقتك",
                "time":    "الآن",
                "url":     "/leaves/",
                "unread":  True,
            })

        # اشتراك ينتهي قريباً
        from subscriptions.models import Subscription
        sub = Subscription.objects.filter(
            company=user.company,
            status__in=["active", "trial"]
        ).first()
        if sub and sub.days_remaining <= 14:
            notifications.append({
                "type":    "danger",
                "icon":    "exclamation-triangle",
                "title":   f"اشتراكك ينتهي خلال {sub.days_remaining} يوم",
                "time":    "",
                "url":     "/subscriptions/my-plan/",
                "unread":  True,
            })

    except Exception:
        pass

    return notifications


# ════════════════════════════════════════════════════════════
# Error Handlers
# ════════════════════════════════════════════════════════════

def handler_404(request, exception=None):
    return render(request, "404.html", status=404)

def handler_500(request):
    return render(request, "500.html", status=500)


# ════════════════════════════════════════════════════════════
# Dashboard حسب الدور
# ════════════════════════════════════════════════════════════
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone as dj_timezone


@login_required
def dashboard(request):
    """لوحة تحكم حسب الدور"""
    today = dj_timezone.now().date()
    role = getattr(request.user, "role", "") or ""
    company = getattr(request.user, "company", None)

    context = {
        "page_title": "لوحة التحكم",
        "today": today,
        "dashboard_mode": "guest",
        "role": role,
        "current_employee": getattr(request, "current_employee", None),
    }

    # لو مفيش شركة
    if not company and role != "super_admin":
        return render(request, "dashboard/index.html", context)

    # استيرادات آمنة
    try:
        from employees.models import Employee, Deduction
    except Exception:
        Employee = None
        Deduction = None

    try:
        from attendance.models import Attendance, LocationLog
    except Exception:
        Attendance = None
        LocationLog = None

    try:
        from requests_app.models import EmployeeRequest
    except Exception:
        EmployeeRequest = None

    try:
        from leaves.models import LeaveBalance, LeaveRequest
    except Exception:
        LeaveBalance = None
        LeaveRequest = None

    try:
        from companies.models import WorkCharter, CharterAcceptance
    except Exception:
        WorkCharter = None
        CharterAcceptance = None

    # current employee
    current_employee = getattr(request, "current_employee", None)
    if not current_employee and Employee:
        current_employee = Employee.all_objects.filter(
            user=request.user
        ).select_related("job_title", "department", "branch").first()

    context["current_employee"] = current_employee

    # ═══════════════════════════════════════
    # Employee Dashboard
    # ═══════════════════════════════════════
    if role == "employee":
        context["dashboard_mode"] = "employee"

        today_attendance = None
        if Attendance and current_employee:
            today_attendance = Attendance.objects.filter(
                employee=current_employee,
                date=today
            ).first()

        attendance_text = "لم تسجل حضور اليوم"
        attendance_color = "secondary"
        if today_attendance:
            if getattr(today_attendance, "check_out_time", None):
                attendance_text = "تم تسجيل الحضور والانصراف"
                attendance_color = "success"
            elif getattr(today_attendance, "check_in_time", None):
                attendance_text = "أنت في العمل الآن"
                attendance_color = "warning"

        # رصيد الإجازات
        leave_balances = []
        leave_remaining_total = 0
        if LeaveBalance and current_employee:
            leave_balances = LeaveBalance.objects.filter(
                company=company,
                employee=current_employee,
                year=today.year
            ).select_related("leave_type")
            try:
                leave_remaining_total = sum(
                    max(float(getattr(b, "remaining_days", 0) or 0), 0)
                    for b in leave_balances
                )
            except Exception:
                leave_remaining_total = 0

        # طلباتي
        pending_requests_count = 0
        recent_requests = []
        if EmployeeRequest and current_employee:
            pending_requests_count = EmployeeRequest.objects.filter(
                company=company,
                employee=current_employee,
                status="pending"
            ).count()
            recent_requests = EmployeeRequest.objects.filter(
                company=company,
                employee=current_employee
            ).select_related("request_type").order_by("-created_at")[:5]

        # خصوماتي
        recent_deductions = []
        deductions_month_total = 0
        if Deduction and current_employee:
            current_month_deductions = Deduction.objects.filter(
                company=company,
                employee=current_employee,
                month=today.month,
                year=today.year,
                is_visible_to_employee=True
            )
            recent_deductions = current_month_deductions.order_by("-date")[:5]
            try:
                deductions_month_total = current_month_deductions.aggregate(
                    total=Sum("amount")
                )["total"] or 0
            except Exception:
                deductions_month_total = 0

        # إشعاراتي
        employee_unread_notifications_count = 0
        try:
            from accounts.models import EmployeeNotification
            if current_employee:
                employee_unread_notifications_count = EmployeeNotification.objects.filter(
                    employee=current_employee,
                    is_read=False
                ).count()
        except Exception:
            pass

        # الميثاق
        charter_accepted = True
        if WorkCharter and CharterAcceptance and current_employee:
            charter = WorkCharter.objects.filter(
                company=company,
                is_active=True
            ).first()
            if charter:
                charter_accepted = CharterAcceptance.objects.filter(
                    employee=current_employee,
                    charter=charter
                ).exists()

        context.update({
            "today_attendance": today_attendance,
            "attendance_text": attendance_text,
            "attendance_color": attendance_color,
            "leave_balances": leave_balances,
            "leave_remaining_total": leave_remaining_total,
            "pending_requests_count": pending_requests_count,
            "recent_requests": recent_requests,
            "recent_deductions": recent_deductions,
            "deductions_month_total": deductions_month_total,
            "charter_accepted": charter_accepted,
            "employee_unread_notifications_count": employee_unread_notifications_count,
        })

        return render(request, "dashboard/index.html", context)

    # ═══════════════════════════════════════
    # Manager Dashboard
    # ═══════════════════════════════════════
    if role == "manager":
        context["dashboard_mode"] = "manager"

        team_members = []
        team_count = 0
        team_present_today = 0
        team_pending_requests = 0
        team_pending_leaves = 0
        recent_team_requests = []

        if Employee:
            manager_emp = current_employee or Employee.all_objects.filter(user=request.user).first()
            if manager_emp and hasattr(manager_emp, "pk") and hasattr(manager_emp, "direct_reports"):
                try:
                    team_qs = Employee.all_objects.filter(
                        company=company,
                        direct_manager=manager_emp,
                        status="active"
                    ).select_related("department", "job_title")
                except Exception:
                    team_qs = Employee.all_objects.none()
            else:
                try:
                    team_qs = Employee.all_objects.filter(
                        company=company,
                        direct_manager=manager_emp
                    ).select_related("department", "job_title")
                except Exception:
                    team_qs = Employee.all_objects.none()

            team_members = list(team_qs[:8])
            team_count = team_qs.count()
            team_ids = list(team_qs.values_list("id", flat=True))

            if Attendance and team_ids:
                team_present_today = Attendance.objects.filter(
                    company=company,
                    employee_id__in=team_ids,
                    date=today,
                    status__in=["present", "late"]
                ).count()

            if EmployeeRequest and team_ids:
                team_pending_requests = EmployeeRequest.objects.filter(
                    company=company,
                    employee_id__in=team_ids,
                    status="pending"
                ).count()

                recent_team_requests = EmployeeRequest.objects.filter(
                    company=company,
                    employee_id__in=team_ids
                ).select_related("employee", "request_type").order_by("-created_at")[:5]

            if LeaveRequest and team_ids:
                team_pending_leaves = LeaveRequest.objects.filter(
                    company=company,
                    employee_id__in=team_ids,
                    status="pending"
                ).count()

        context.update({
            "team_members": team_members,
            "team_count": team_count,
            "team_present_today": team_present_today,
            "team_pending_requests": team_pending_requests,
            "team_pending_leaves": team_pending_leaves,
            "recent_team_requests": recent_team_requests,
        })

        return render(request, "dashboard/index.html", context)

    # ═══════════════════════════════════════
    # HR / Company Admin / Super Admin Dashboard
    # ═══════════════════════════════════════
    context["dashboard_mode"] = "admin"

    total_employees = 0
    present_today = 0
    absent_today = 0
    late_today = 0
    live_field = 0
    pending_requests = 0
    pending_leaves = 0
    recent_employees = []
    recent_attendance = []
    recent_requests = []
    charter_accepted_count = 0
    charter_not_accepted_count = 0
    charter_not_accepted_employees = []

    if Employee:
        try:
            total_employees = Employee.all_objects.filter(
                company=company,
                status="active"
            ).count()
            recent_employees = Employee.all_objects.filter(
                company=company
            ).select_related("job_title", "department").order_by("-hire_date")[:6]
        except Exception:
            pass

    if Attendance:
        try:
            present_today = Attendance.objects.filter(
                company=company,
                date=today,
                status__in=["present", "late"]
            ).count()

            absent_today = Attendance.objects.filter(
                company=company,
                date=today,
                status="absent"
            ).count()

            late_today = Attendance.objects.filter(
                company=company,
                date=today,
                status="late"
            ).count()

            recent_attendance = Attendance.objects.filter(
                company=company,
                date=today
            ).select_related("employee").order_by("-id")[:8]
        except Exception:
            pass

    if LocationLog:
        try:
            cutoff = dj_timezone.now() - __import__("datetime").timedelta(minutes=10)
            live_field = LocationLog.objects.filter(
                company=company,
                timestamp__gte=cutoff
            ).values("employee").distinct().count()
        except Exception:
            pass

    if EmployeeRequest:
        try:
            pending_requests = EmployeeRequest.objects.filter(
                company=company,
                status="pending"
            ).count()

            recent_requests = EmployeeRequest.objects.filter(
                company=company
            ).select_related("employee", "request_type").order_by("-created_at")[:6]
        except Exception:
            pass

    if LeaveRequest:
        try:
            pending_leaves = LeaveRequest.objects.filter(
                company=company,
                status="pending"
            ).count()
        except Exception:
            pass

    # الميثاق - مهم لـ HR / الإدارة
    if WorkCharter and CharterAcceptance and Employee:
        try:
            charter = WorkCharter.objects.filter(
                company=company,
                is_active=True
            ).first()

            if charter:
                charter_accepted_count = CharterAcceptance.objects.filter(
                    charter=charter
                ).count()

                active_employees_qs = Employee.all_objects.filter(
                    company=company,
                    status="active"
                )
                active_count = active_employees_qs.count()
                charter_not_accepted_count = max(active_count - charter_accepted_count, 0)

                accepted_ids = CharterAcceptance.objects.filter(
                    charter=charter
                ).values_list("employee_id", flat=True)

                charter_not_accepted_employees = active_employees_qs.exclude(
                    id__in=accepted_ids
                )[:5]
        except Exception:
            pass

    context.update({
        "total_employees": total_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "late_today": late_today,
        "live_field": live_field,
        "pending_requests": pending_requests,
        "pending_leaves": pending_leaves,
        "recent_employees": recent_employees,
        "recent_attendance": recent_attendance,
        "recent_requests": recent_requests,
        "charter_accepted_count": charter_accepted_count,
        "charter_not_accepted_count": charter_not_accepted_count,
        "charter_not_accepted_employees": charter_not_accepted_employees,
    })

    return render(request, "dashboard/index.html", context)


# ════════════════════════════════════════════════════════════
# HR Manual Employee Notifications
# ════════════════════════════════════════════════════════════

@login_required
def send_employee_notification_view(request):
    """
    HR / الإدارة يبعث إشعار لموظف أو قسم أو الكل
    """
    role = getattr(request.user, "role", "")
    if role not in ["super_admin", "company_admin", "hr_manager"]:
        messages.error(request, "ليس لديك صلاحية إرسال إشعارات")
        return redirect("dashboard")

    from employees.models import Employee
    from companies.models import Department
    from accounts.models import EmployeeNotification

    company = request.user.company
    employees = Employee.all_objects.filter(
        company=company,
        status="active"
    ).select_related("department").order_by("first_name_ar")

    departments = Department.objects.filter(
        company=company,
        is_active=True
    ).order_by("name_ar")

    if request.method == "POST":
        audience_type = request.POST.get("audience_type", "single")
        employee_id = request.POST.get("employee")
        department_id = request.POST.get("department")
        title = request.POST.get("title", "").strip()
        message = request.POST.get("message", "").strip()
        severity = request.POST.get("severity", "info")

        if not title or not message:
            messages.error(request, "العنوان والرسالة مطلوبان")
            return redirect("accounts:send_employee_notification")

        target_employees = Employee.all_objects.none()

        if audience_type == "single" and employee_id:
            target_employees = Employee.all_objects.filter(
                company=company,
                pk=employee_id
            )

        elif audience_type == "department" and department_id:
            target_employees = Employee.all_objects.filter(
                company=company,
                department_id=department_id,
                status="active"
            )

        elif audience_type == "all":
            target_employees = Employee.all_objects.filter(
                company=company,
                status="active"
            )

        count = 0
        for emp in target_employees:
            EmployeeNotification.objects.create(
                employee=emp,
                title=title,
                message=message,
                notification_type="general_notice",
                severity=severity,
                is_read=False,
                sent_by=request.user,
            )
            count += 1

        messages.success(request, f"تم إرسال الإشعار إلى {count} موظف")
        return redirect("accounts:notifications")

    context = {
        "employees": employees,
        "departments": departments,
        "page_title": "إرسال إشعار",
    }
    return render(request, "accounts/send_notification.html", context)


# ════════════════════════════════════════════════════════════
# Push Subscription API
# ════════════════════════════════════════════════════════════

from django.views.decorators.http import require_POST as require_post_method
from django.http import JsonResponse
import json as json_lib


@login_required
@require_post_method
def push_subscribe(request):
    """اشتراك في Push Notifications"""
    try:
        from accounts.models import PushSubscription
        body = json_lib.loads(request.body)
        endpoint = body.get("endpoint", "")
        keys = body.get("keys", {})
        p256dh = keys.get("p256dh", "")
        auth = keys.get("auth", "")

        if not endpoint or not p256dh or not auth:
            return JsonResponse({"ok": False, "message": "بيانات ناقصة"})

        sub, created = PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=endpoint,
            defaults={
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
                "is_active": True,
            }
        )
        return JsonResponse({"ok": True, "created": created})
    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)})


@login_required
@require_post_method
def push_unsubscribe(request):
    """إلغاء اشتراك Push"""
    try:
        from accounts.models import PushSubscription
        body = json_lib.loads(request.body)
        endpoint = body.get("endpoint", "")

        PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint,
        ).update(is_active=False)

        return JsonResponse({"ok": True})
    except Exception:
        return JsonResponse({"ok": False})


# ════════════════════════════════════════════════════════════
# Push Trigger — بيتشغل لما EmployeeNotification يتنشأ
# ════════════════════════════════════════════════════════════
def trigger_push_for_employee_notification(notification_obj):
    """
    بعد ما EmployeeNotification يتنشأ → ابعت Push
    """
    try:
        from core.push_helper import send_push_to_user
        from employees.models import Employee

        employee = notification_obj.employee
        if not employee.user:
            return

        type_map = {
            "late_warning": "late_warning",
            "deduction_notice": "deduction_notice",
            "request_update": "request_approved",
            "general_notice": "general_notice",
            "policy_reminder": "general_notice",
            "charter_reminder": "charter_reminder",
        }

        notif_type = type_map.get(
            notification_obj.notification_type,
            "general_notice"
        )

        send_push_to_user(
            user=employee.user,
            title=notification_obj.title,
            body=notification_obj.message[:100] if notification_obj.message else "",
            url="/accounts/notifications/",
            notification_type=notif_type,
        )
    except Exception:
        pass
