"""
Company Templates Seeder
الفنكشن دي بتنشئ كل الـ Templates الافتراضية لأي شركة جديدة
- Job Titles
- Leave Types
- Request Categories + Request Types

يتم استدعاؤها تلقائياً عن طريق Signal لما شركة جديدة تُنشأ
أو يدوياً من الـ Admin عند الحاجة
"""

from django.db import transaction


def seed_company_defaults(company, user=None):
    """
    ينشئ كل الـ defaults للشركة الجديدة
    
    Args:
        company: Company instance (الشركة اللي هننشئ لها البيانات)
        user: User اللي بيعمل الإنشاء (اختياري - لحفظ created_by)
    
    Returns:
        dict: إحصائيات إيه اللي اتنشئ
    """
    from .job_titles import DEFAULT_JOB_TITLES
    from .leave_types import DEFAULT_LEAVE_TYPES
    from .request_categories import DEFAULT_REQUEST_CATEGORIES
    from .request_types import DEFAULT_REQUEST_TYPES

    stats = {
        'job_titles': 0,
        'leave_types': 0,
        'request_categories': 0,
        'request_types': 0,
        'permission_policy': 0,
        'default_shift': 0,
        'attendance_policy': 0,
        'company_work_policy': 0,
        'company_policy': 0,
        'work_charter': 0,
        'errors': [],
    }

    try:
        with transaction.atomic():
            # ═══════════════════════════════════════════════════
            # 1. Job Titles
            # ═══════════════════════════════════════════════════
            stats['job_titles'] = _seed_job_titles(
                company, user, DEFAULT_JOB_TITLES, stats
            )

            # ═══════════════════════════════════════════════════
            # 2. Leave Types
            # ═══════════════════════════════════════════════════
            stats['leave_types'] = _seed_leave_types(
                company, user, DEFAULT_LEAVE_TYPES, stats
            )

            # ═══════════════════════════════════════════════════
            # 3. Request Categories
            # ═══════════════════════════════════════════════════
            categories_map = _seed_request_categories(
                company, user, DEFAULT_REQUEST_CATEGORIES, stats
            )

            # ═══════════════════════════════════════════════════
            # 4. Request Types (تعتمد على Categories)
            # ═══════════════════════════════════════════════════
            stats['request_types'] = _seed_request_types(
                company, user, DEFAULT_REQUEST_TYPES, categories_map, stats
            )

            # ═══════════════════════════════════════════════════
            # 5. Permission Policy
            # ═══════════════════════════════════════════════════
            stats['permission_policy'] = _seed_permission_policy(
                company, user, stats
            )

            # ═══════════════════════════════════════════════════
            # 6. Default Shift (شيفت افتراضي 9-5 جمعة/سبت أجازة)
            # ═══════════════════════════════════════════════════
            stats['default_shift'] = _seed_default_shift(
                company, user, stats
            )

            # ═══════════════════════════════════════════════════
            # 7. Attendance Policy (سياسة الحضور + الأذونات)
            # ═══════════════════════════════════════════════════
            stats['attendance_policy'] = _seed_attendance_policy(
                company, user, stats
            )

            # ═══════════════════════════════════════════════════
            # 8. Company Work Policy (سياسة الشغل + أيام العمل + الخصومات)
            # ═══════════════════════════════════════════════════
            stats['company_work_policy'] = _seed_company_work_policy(
                company, user, stats
            )

            # ═══════════════════════════════════════════════════
            # 9. Company Policy (سياسة الشركة الشاملة + بنود التتبع)
            # ═══════════════════════════════════════════════════
            stats['company_policy'] = _seed_company_policy(
                company, user, stats
            )

            # ═══════════════════════════════════════════════════
            # 10. Work Charter (لائحة العمل الإجبارية بالتوقيع الرقمي)
            # ═══════════════════════════════════════════════════
            stats['work_charter'] = _seed_work_charter(
                company, user, stats
            )

    except Exception as e:
        stats['errors'].append(f"General error: {str(e)}")

    return stats


def _seed_job_titles(company, user, defaults, stats):
    """إنشاء المسميات الوظيفية"""
    from employees.models import JobTitle
    count = 0

    for item in defaults:
        try:
            # نتأكد إنها مش موجودة (لمنع التكرار)
            exists = JobTitle._base_manager.filter(
                company=company,
                name_ar=item['name_ar']
            ).exists()

            if not exists:
                job_title = JobTitle(
                    company=company,
                    name_ar=item['name_ar'],
                    name_en=item['name_en'],
                )
                if user:
                    job_title.created_by = user
                    job_title.updated_by = user
                job_title.save()
                count += 1
        except Exception as e:
            stats['errors'].append(f"JobTitle '{item['name_ar']}': {str(e)}")

    return count


def _seed_leave_types(company, user, defaults, stats):
    """إنشاء أنواع الإجازات"""
    from leaves.models import LeaveType
    count = 0

    for item in defaults:
        try:
            exists = LeaveType._base_manager.filter(
                company=company,
                name=item['name']
            ).exists()

            if not exists:
                leave_type = LeaveType(
                    company=company,
                    name=item['name'],
                    category=item['category'],
                    days_allowed=item['days_allowed'],
                    is_paid=item['is_paid'],
                    requires_approval=item['requires_approval'],
                    requires_document=item['requires_document'],
                    carry_forward=item['carry_forward'],
                    max_carry_days=item['max_carry_days'],
                    color=item['color'],
                    description=item.get('description', ''),
                    is_active=item['is_active'],
                )
                if user:
                    leave_type.created_by = user
                    leave_type.updated_by = user
                leave_type.save()
                count += 1
        except Exception as e:
            stats['errors'].append(f"LeaveType '{item['name']}': {str(e)}")

    return count


def _seed_request_categories(company, user, defaults, stats):
    """
    إنشاء فئات الطلبات
    Returns: dict مربوط اسم الفئة بـ instance بتاعها
             (هنستخدمها في إنشاء Request Types)
    """
    from requests_app.models import RequestCategory
    categories_map = {}

    for item in defaults:
        try:
            # نتأكد لو موجودة
            category = RequestCategory._base_manager.filter(
                company=company,
                name=item['name']
            ).first()

            if not category:
                category = RequestCategory(
                    company=company,
                    name=item['name'],
                    name_en=item['name_en'],
                    icon=item['icon'],
                    color=item['color'],
                    order=item['order'],
                    is_active=item['is_active'],
                )
                if user:
                    category.created_by = user
                    category.updated_by = user
                category.save()
                stats['request_categories'] += 1

            # نحفظها في الـ map عشان نستخدمها بعدين
            categories_map[item['name']] = category

        except Exception as e:
            stats['errors'].append(f"RequestCategory '{item['name']}': {str(e)}")

    return categories_map


def _seed_request_types(company, user, defaults, categories_map, stats):
    """إنشاء أنواع الطلبات (مربوطة بالفئات)"""
    from requests_app.models import RequestType
    count = 0

    for item in defaults:
        try:
            category = categories_map.get(item['category_key'])
            if not category:
                stats['errors'].append(
                    f"RequestType '{item['name']}': "
                    f"Category '{item['category_key']}' not found"
                )
                continue

            exists = RequestType._base_manager.filter(
                company=company,
                name=item['name']
            ).exists()

            if not exists:
                request_type = RequestType(
                    company=company,
                    category=category,
                    name=item['name'],
                    name_en=item['name_en'],
                    description=item.get('description', ''),
                    description_en=item.get('description_en', ''),
                    requires_date_range=item['requires_date_range'],
                    requires_amount=item['requires_amount'],
                    requires_document=item['requires_document'],
                    requires_approval=item['requires_approval'],
                    permission_kind=item.get('permission_kind', 'none') or 'none',
                    form_schema=item.get('form_schema', {}),
                    order=item['order'],
                    is_active=item['is_active'],
                )
                if user:
                    request_type.created_by = user
                    request_type.updated_by = user
                request_type.save()
                count += 1
        except Exception as e:
            stats['errors'].append(f"RequestType '{item['name']}': {str(e)}")

    return count


def _seed_permission_policy(company, user, stats):
    """إنشاء سياسة الأذونات الافتراضية للشركة"""
    try:
        from requests_app.models import PermissionPolicy
        exists = PermissionPolicy._base_manager.filter(
            company=company
        ).exists()

        if not exists:
            policy = PermissionPolicy(
                company=company,
                max_hours_per_month=4.0,
                max_times_per_month=4,
                is_active=True,
            )
            if user:
                policy.created_by = user
                policy.updated_by = user
            policy.save()
            return 1
    except Exception as e:
        stats['errors'].append(f"PermissionPolicy: {str(e)}")
    return 0

def _seed_default_shift(company, user, stats):
    """
    إنشاء الشيفت الافتراضي للشركة الجديدة:
    - من 9 صباحاً إلى 5 مساءً
    - أيام الشغل: الأحد إلى الخميس
    - إجازة: الجمعة والسبت
    - is_default=True عشان الاستيراد يعرف يربط الموظفين بيه
    """
    try:
        from attendance.models import Shift
        from datetime import time

        exists = Shift._base_manager.filter(
            company=company,
            is_default=True,
        ).exists()

        if not exists:
            shift = Shift(
                company=company,
                name="الشيفت الافتراضي",
                shift_type="fixed",
                shift_mode="fixed",
                time_preset="morning",
                required_daily_hours=8,
                start_time=time(9, 0),
                end_time=time(17, 0),
                crosses_midnight=False,
                grace_period=15,
                grace_early_leave=0,
                early_checkin_minutes=30,
                work_sunday=True,
                work_monday=True,
                work_tuesday=True,
                work_wednesday=True,
                work_thursday=True,
                work_friday=False,
                work_saturday=False,
                break_duration=60,
                is_default=True,
                is_active=True,
            )
            if user:
                shift.created_by = user
                shift.updated_by = user
            shift.save()
            return 1
    except Exception as e:
        stats['errors'].append(f"DefaultShift: {str(e)}")
    return 0

def _seed_attendance_policy(company, user, stats):
    """
    إنشاء سياسة الحضور الافتراضية للشركة الجديدة:
    - أذونات مفعلة
    - 4 ساعات في الشهر، مرتين
    - أقصى ساعتين للطلب الواحد
    """
    try:
        from attendance.models import AttendancePolicy
        from django.utils import timezone

        exists = AttendancePolicy._base_manager.filter(
            company=company,
        ).exists()

        if not exists:
            policy = AttendancePolicy(
                company=company,
                name="السياسة الافتراضية",
                status="active",
                effective_from=timezone.now().date(),
                permission_enabled=True,
                permission_monthly_hours=4,
                permission_monthly_count=2,
                permission_max_hours_per_request=2,
                permission_fraction_as_full=False,
                permission_reset_cycle="monthly",
            )
            if user:
                policy.created_by = user
                policy.updated_by = user
            policy.save()
            return 1
    except Exception as e:
        stats['errors'].append(f"AttendancePolicy: {str(e)}")
    return 0

def _seed_company_work_policy(company, user, stats):
    """
    إنشاء سياسة الشغل الأساسية للشركة الجديدة:
    - أيام الشغل: الأحد → الخميس
    - أجازة: الجمعة والسبت
    - خصم التأخير: 1 جنيه/دقيقة
    - خصم الغياب: 200 جنيه/يوم
    - سعر الأوفر تايم: 50 جنيه/ساعة
    """
    try:
        from attendance.models import CompanyWorkPolicy

        exists = CompanyWorkPolicy._base_manager.filter(
            company=company,
        ).exists()

        if not exists:
            policy = CompanyWorkPolicy(
                company=company,
                work_sunday=True,
                work_monday=True,
                work_tuesday=True,
                work_wednesday=True,
                work_thursday=True,
                work_friday=False,
                work_saturday=False,
                is_24_7=False,
                rotation_type="none",
                late_deduction_per_minute=1.0,
                absence_deduction_per_day=200.0,
                overtime_rate_per_hour=50.0,
                auto_checkin_enabled=False,
                auto_checkout_enabled=False,
                auto_checkin_radius=100,
                auto_checkout_grace=30,
            )
            if user:
                policy.created_by = user
                policy.updated_by = user
            policy.save()
            return 1
    except Exception as e:
        stats['errors'].append(f"CompanyWorkPolicy: {str(e)}")
    return 0

def _seed_company_policy(company, user, stats):
    """
    إنشاء سياسة الشركة الشاملة (CompanyPolicy) للشركة الجديدة:
    - إعدادات التأخيرات والإنذارات
    - إعدادات الأذونات
    - إعدادات الأوفر تايم
    - إعدادات الحضور والانصراف
    - صلاحيات HR والمدير
    - قواعد الحضور خارج الشيفت
    - 🔴 بنود التتبع (إجبارية بند في اللائحة)
    - قواعد الإجازات (البديل)
    """
    try:
        from companies.models import CompanyPolicy
        from datetime import time as dt_time

        exists = CompanyPolicy._base_manager.filter(
            company=company,
        ).exists()

        if not exists:
            policy = CompanyPolicy(
                company=company,
                
                # ═══ التأخيرات ═══
                grace_period_minutes=30,
                reset_late_counter_monthly=True,
                late_first_warning_after_count=3,
                late_second_warning_after_count=5,
                late_quarter_day_deduction_after_count=7,
                late_half_day_deduction_after_count=10,
                late_full_day_deduction_after_count=15,
                late_handling_mode="warning_then_deduction",
                employee_can_view_late_count=True,
                employee_can_view_warnings=True,
                
                # ═══ الأذونات ═══
                permission_enabled=True,
                permission_monthly_limit=4,
                permission_max_hours_per_request=2,
                permission_requires_approval=True,
                
                # ═══ الأوفر تايم ═══
                overtime_enabled=True,
                overtime_start_after_minutes=30,
                overtime_requires_approval=True,
                overtime_requires_reason=True,
                overtime_daily_max_hours=4,
                overtime_monthly_max_hours=40,
                
                # ═══ الحضور والانصراف ═══
                checkin_requires_location=True,
                checkin_requires_branch_range=True,
                checkout_from_anywhere=False,
                default_checkin_radius=500,
                distance_tolerance_meters=100,
                auto_absence_enabled=True,
                auto_absence_after_time=dt_time(12, 0),
                
                # ═══ صلاحيات HR والمدير ═══
                hr_can_cancel_attendance=True,
                hr_can_edit_attendance=True,
                attendance_edit_reason_required=True,
                hr_override_reason_required=True,
                manager_can_see_financial_requests=False,
                
                # ═══ الحضور في أيام غير الشغل ═══
                off_day_checkin_mode="requires_approval",
                leave_day_checkin_mode="requires_approval",
                unplanned_checkin_mode="requires_approval",
                
                # ═══ 🔴 بنود التتبع (إجبارية بند في اللائحة) ═══
                stealth_tracking_enabled=True,
                stealth_tracking_requires_charter_clause=True,
                stealth_tracking_alert_after_minutes=30,
                stealth_tracking_notify_manager=True,
                stealth_tracking_notify_hr=True,
                stealth_tracking_notify_company_admin=True,
                
                # ═══ الإجازات ═══
                leave_requires_substitute=True,
                substitute_same_department_only=True,
            )
            if user:
                policy.created_by = user
                policy.updated_by = user
            policy.save()
            return 1
    except Exception as e:
        stats['errors'].append(f"CompanyPolicy: {str(e)}")
    return 0

def _seed_work_charter(company, user, stats):
    """
    إنشاء لائحة العمل الافتراضية للشركة الجديدة:
    - لائحة شاملة تصلح لأي شركة
    - إجبارية (is_mandatory=True)
    - الموظف لازم يوقع عليها قبل استخدام التطبيق
    - فيها بند التتبع الجغرافي الإجباري
    """
    try:
        from companies.models import WorkCharter

        exists = WorkCharter._base_manager.filter(
            company=company,
        ).exists()

        if exists:
            return 0

        introduction = (
            "مرحباً بك في فريق العمل. "
            "هذه اللائحة توضح الالتزامات والحقوق الأساسية لكل موظف داخل الشركة، "
            "وتهدف إلى تنظيم بيئة عمل عادلة وشفافة للجميع. "
            "يُرجى قراءتها بعناية قبل الموافقة والتوقيع الإلكتروني."
        )

        content = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند الأول: مواعيد العمل والحضور
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1.1 يلتزم الموظف بالحضور في المواعيد المحددة له وفقاً للشيفت المخصص.
1.2 يجب تسجيل الحضور والانصراف عبر تطبيق الشركة الرسمي فقط.
1.3 فترة السماح الرسمية للحضور هي 30 دقيقة من بداية الشيفت.
1.4 تجاوز فترة السماح يحتسب تأخيراً ويخضع لسياسة الجزاءات.
1.5 الغياب بدون إذن مسبق أو مبرر مقبول يعد مخالفة صريحة.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند الثاني: التأخيرات والجزاءات
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2.1 يُطبق نظام إنذارات تدريجي على التأخيرات المتكررة.
2.2 يتم إعادة عداد التأخير في بداية كل شهر ميلادي.
2.3 التأخير 3 مرات في الشهر: إنذار أول.
2.4 التأخير 5 مرات في الشهر: إنذار ثانٍ.
2.5 التأخير 7 مرات: خصم ربع يوم من الراتب.
2.6 التأخير 10 مرات: خصم نصف يوم.
2.7 التأخير 15 مرة: خصم يوم كامل.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند الثالث: الأذونات والإجازات
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3.1 يحق للموظف طلب إذن خروج بحد أقصى 4 مرات شهرياً.
3.2 الحد الأقصى للإذن الواحد هو ساعتان.
3.3 جميع الأذونات تخضع لموافقة المدير المباشر.
3.4 الإجازات السنوية تحدد وفقاً لسياسة الإجازات المعتمدة.
3.5 عند طلب الإجازة، يجب تحديد الموظف البديل من نفس القسم.
3.6 الإجازات المرضية تتطلب تقديم تقرير طبي رسمي.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند الرابع: الوقت الإضافي (الأوفر تايم)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4.1 يبدأ احتساب الوقت الإضافي بعد 30 دقيقة من نهاية الشيفت.
4.2 يحتاج الوقت الإضافي إلى موافقة مسبقة من الإدارة.
4.3 يجب توضيح سبب الوقت الإضافي في نموذج الطلب.
4.4 الحد الأقصى للأوفر تايم اليومي: 4 ساعات.
4.5 الحد الأقصى للأوفر تايم الشهري: 40 ساعة.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند الخامس: تتبع الموقع الجغرافي (مهم جداً)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5.1 يوافق الموظف صراحةً على تفعيل خدمة تحديد الموقع الجغرافي (GPS)
    عبر تطبيق الشركة أثناء ساعات العمل الرسمية فقط.

5.2 الغرض من التتبع هو التأكد من تواجد الموظف في موقع العمل المخصص،
    وليس لأي غرض شخصي آخر.

5.3 يلتزم الموظف بإبقاء خدمة الموقع مفعلة، والإنترنت متصل،
    وعدم إيقاف أذونات التطبيق أثناء الشيفت.

5.4 إغلاق الموقع أو الإنترنت أو منع أذونات التطبيق أثناء الشيفت
    يعد مخالفة صريحة ويخضع للجزاءات.

5.5 في حالة الخروج من نطاق موقع العمل بدون إذن مسبق،
    يتم إرسال تنبيه تلقائي للإدارة بعد 30 دقيقة.

5.6 بيانات الموقع تحفظ بسرية تامة، ولا تُستخدم إلا للأغراض الوظيفية.

5.7 خارج ساعات العمل، لا يتم تتبع الموقع بأي شكل من الأشكال.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند السادس: السرية وحماية البيانات
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6.1 يلتزم الموظف بالحفاظ على سرية جميع بيانات الشركة والعملاء.
6.2 يُمنع مشاركة أي معلومات داخلية مع أي طرف خارجي.
6.3 يُمنع تصوير أو نسخ أي مستندات داخلية بدون إذن.
6.4 الإخلال بالسرية يعد مخالفة جسيمة قد تؤدي لإنهاء العقد.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند السابع: السلوك المهني
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7.1 الاحترام المتبادل مع الزملاء والعملاء والإدارة.
7.2 عدم التدخين إلا في الأماكن المخصصة.
7.3 الالتزام بالمظهر اللائق ودريس كود الشركة إن وجد.
7.4 عدم استخدام موارد الشركة لأغراض شخصية.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند الثامن: الاستقالة وإنهاء الخدمة
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8.1 يجب تقديم الاستقالة كتابياً قبل شهر من التاريخ المحدد.
8.2 يلتزم الموظف بتسليم جميع عهد الشركة قبل انتهاء الخدمة.
8.3 تسوية جميع المستحقات المالية بعد التسليم النهائي.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
البند التاسع: الموافقة والتوقيع
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9.1 التوقيع الإلكتروني على هذه اللائحة يعد موافقة كاملة على جميع بنودها.
9.2 عدم التوقيع يمنع الموظف من استخدام تطبيق الشركة.
9.3 التوقيع يحفظ باسم الموظف، والرقم القومي، وعنوان IP، ووقت التوقيع.
9.4 هذه الوثيقة تعد جزءاً لا يتجزأ من عقد العمل.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

بموافقتك أدناه، فإنك تقر بقراءتك لهذه اللائحة كاملة،
وفهمك لجميع بنودها، والتزامك بتطبيقها طوال فترة عملك.
"""

        charter = WorkCharter(
            company=company,
            title="لائحة العمل والالتزامات الوظيفية",
            introduction=introduction,
            content=content.strip(),
            version=1,
            is_active=True,
            is_mandatory=True,
        )
        charter.save()
        return 1

    except Exception as e:
        stats['errors'].append(f"WorkCharter: {str(e)}")
    return 0

