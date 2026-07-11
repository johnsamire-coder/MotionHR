from django.db import models


class Company(models.Model):
    """الشركة الرئيسية"""
    
    name_ar = models.CharField(
        max_length=200,
        verbose_name='اسم الشركة بالعربي'
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='اسم الشركة بالإنجليزي'
    )
    logo = models.ImageField(
        upload_to='companies/logos/',
        blank=True,
        null=True,
        verbose_name='الشعار'
    )
    commercial_register = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='السجل التجاري'
    )
    tax_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='الرقم الضريبي'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='البريد الإلكتروني'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name='الموقع الإلكتروني'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تعديل'
    )
    
    class Meta:
        verbose_name = 'شركة'
        verbose_name_plural = 'الشركات'
        ordering = ['name_ar']
    
    def __str__(self):
        return self.name_ar


class Branch(models.Model):
    """فرع الشركة"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name='الشركة'
    )
    name_ar = models.CharField(
        max_length=200,
        verbose_name='اسم الفرع بالعربي'
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='اسم الفرع بالإنجليزي'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    # الموقع الجغرافي - مهم للتتبع بعدين
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط العرض'
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name='خط الطول'
    )
    # نطاق الحضور بالمتر
    check_in_radius = models.IntegerField(
        default=100,
        verbose_name='نطاق تسجيل الحضور (متر)'
    )
    is_main = models.BooleanField(
        default=False,
        verbose_name='الفرع الرئيسي'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'فرع'
        verbose_name_plural = 'الفروع'
        ordering = ['company', 'name_ar']
    
    def __str__(self):
        return f"{self.company.name_ar} - {self.name_ar}"


class Department(models.Model):
    """الإدارة أو القسم"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name='الشركة'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='sub_departments',
        verbose_name='الإدارة الأم'
    )
    name_ar = models.CharField(
        max_length=200,
        verbose_name='اسم الإدارة بالعربي'
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='اسم الإدارة بالإنجليزي'
    )
    code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='كود الإدارة'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='الوصف'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'إدارة'
        verbose_name_plural = 'الإدارات'
        ordering = ['company', 'name_ar']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name_ar} → {self.name_ar}"
        return self.name_ar

# ════════════════════════════════════════════════════════════
# إعدادات تسجيل الدخول لكل شركة
# ════════════════════════════════════════════════════════════
class CompanyLoginSettings(models.Model):
    """
    إعدادات تسجيل الدخول الخاصة بكل شركة
    تتحكم في طرق الدخول وإعدادات كلمة المرور
    """
    company = models.OneToOneField(
        'Company',
        on_delete=models.CASCADE,
        related_name='login_settings',
        verbose_name='الشركة'
    )

    # ── طرق تسجيل الدخول ──
    login_by_email = models.BooleanField(
        default=True,
        verbose_name='الدخول بالإيميل'
    )
    login_by_employee_code = models.BooleanField(
        default=True,
        verbose_name='الدخول بالرقم الوظيفي'
    )
    login_by_phone = models.BooleanField(
        default=False,
        verbose_name='الدخول بالموبايل'
    )
    login_by_username = models.BooleanField(
        default=True,
        verbose_name='الدخول باسم المستخدم'
    )

    # ── إعدادات كلمة المرور ──
    min_password_length = models.PositiveSmallIntegerField(
        default=8,
        verbose_name='الحد الأدنى لطول كلمة المرور'
    )
    require_uppercase = models.BooleanField(
        default=False,
        verbose_name='إجبار حروف كبيرة'
    )
    require_numbers = models.BooleanField(
        default=False,
        verbose_name='إجبار أرقام'
    )
    require_symbols = models.BooleanField(
        default=False,
        verbose_name='إجبار رموز'
    )
    password_expiry_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='مدة انتهاء كلمة المرور (يوم)',
        help_text='0 = لا تنتهي'
    )

    # ── إعدادات القفل ──
    max_login_attempts = models.PositiveSmallIntegerField(
        default=5,
        verbose_name='أقصى محاولات دخول'
    )
    lockout_duration_minutes = models.PositiveSmallIntegerField(
        default=15,
        verbose_name='مدة القفل (دقيقة)'
    )

    # ── تسجيل الدخول الإجباري ──
    force_change_on_first_login = models.BooleanField(
        default=True,
        verbose_name='إجبار تغيير كلمة المرور عند أول دخول'
    )

    class Meta:
        verbose_name        = 'إعدادات تسجيل الدخول'
        verbose_name_plural = 'إعدادات تسجيل الدخول'

    def __str__(self):
        return f'إعدادات دخول - {self.company.name_ar}'

    @classmethod
    def get_for_company(cls, company):
        """جلب الإعدادات أو إنشاء افتراضية"""
        obj, _ = cls.objects.get_or_create(company=company)
        return obj


# ════════════════════════════════════════════════════════════
# ميثاق العمل
# ════════════════════════════════════════════════════════════
class WorkCharter(models.Model):
    """ميثاق العمل — مستند واحد لكل شركة"""

    company = models.OneToOneField(
        "Company",
        on_delete=models.CASCADE,
        related_name="work_charter",
        verbose_name="الشركة"
    )
    title = models.CharField(
        max_length=200,
        default="ميثاق العمل",
        verbose_name="العنوان"
    )
    introduction = models.TextField(
        blank=True,
        verbose_name="مقدمة",
        help_text="نص تمهيدي يظهر قبل البنود"
    )
    content = models.TextField(
        verbose_name="محتوى الميثاق",
        help_text="البنود الكاملة للميثاق"
    )
    version = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="رقم الإصدار"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="مفعّل"
    )
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name="إجباري للموظفين الجدد"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ميثاق العمل"
        verbose_name_plural = "مواثيق العمل"

    def __str__(self):
        return f"{self.title} - {self.company.name_ar} (v{self.version})"


class CharterAcceptance(models.Model):
    """تسجيل موافقة الموظف على الميثاق"""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="charter_acceptances",
        verbose_name="الموظف"
    )
    charter = models.ForeignKey(
        WorkCharter,
        on_delete=models.CASCADE,
        related_name="acceptances",
        verbose_name="الميثاق"
    )
    accepted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الموافقة"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="عنوان IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="المتصفح"
    )

    class Meta:
        verbose_name = "موافقة على الميثاق"
        verbose_name_plural = "موافقات الميثاق"
        unique_together = [["employee", "charter"]]

    def __str__(self):
        return f"{self.employee} وافق على {self.charter.title}"


# ════════════════════════════════════════════════════════════
# سياسات الشركة / HR Controls
# ════════════════════════════════════════════════════════════
class CompanyPolicy(models.Model):
    """
    السياسات العامة للشركة:
    - التأخير
    - الأذونات
    - الأوفر تايم
    - النطاق / المسافة
    - صلاحيات HR
    """

    company = models.OneToOneField(
        "Company",
        on_delete=models.CASCADE,
        related_name="policy",
        verbose_name="الشركة"
    )

    # ── سياسة التأخير ─────────────────────────────────
    grace_period_minutes = models.PositiveSmallIntegerField(
        default=15,
        verbose_name="سماحية التأخير بالدقائق"
    )
    reset_late_counter_monthly = models.BooleanField(
        default=True,
        verbose_name="تصفير عداد التأخير شهريًا"
    )

    late_first_warning_after_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="أول إنذار بعد عدد مرات"
    )
    late_second_warning_after_count = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="ثاني إنذار بعد عدد مرات"
    )
    late_quarter_day_deduction_after_count = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="خصم ربع يوم بعد عدد مرات"
    )
    late_half_day_deduction_after_count = models.PositiveSmallIntegerField(
        default=4,
        verbose_name="خصم نصف يوم بعد عدد مرات"
    )
    late_full_day_deduction_after_count = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="خصم يوم كامل بعد عدد مرات"
    )

    # ── سياسة الأذونات ─────────────────────────────────
    permission_enabled = models.BooleanField(
        default=True,
        verbose_name="الأذونات مفعلة"
    )
    permission_monthly_limit = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="عدد الأذونات المسموح بها شهريًا"
    )
    permission_max_hours_per_request = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=2,
        verbose_name="أقصى عدد ساعات للإذن الواحد"
    )
    permission_requires_approval = models.BooleanField(
        default=True,
        verbose_name="الأذونات تحتاج موافقة"
    )

    # ── سياسة الأوفر تايم ─────────────────────────────
    overtime_enabled = models.BooleanField(
        default=True,
        verbose_name="الأوفر تايم مفعل"
    )
    overtime_start_after_minutes = models.PositiveSmallIntegerField(
        default=30,
        verbose_name="يبدأ الأوفر تايم بعد عدد دقائق"
    )
    overtime_requires_approval = models.BooleanField(
        default=True,
        verbose_name="الأوفر تايم يحتاج موافقة"
    )
    overtime_requires_reason = models.BooleanField(
        default=True,
        verbose_name="الموظف لازم يكتب سبب الأوفر تايم"
    )
    overtime_daily_max_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=4,
        verbose_name="أقصى أوفر تايم يومي"
    )
    overtime_monthly_max_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=40,
        verbose_name="أقصى أوفر تايم شهري"
    )

    # ── سياسة الحضور بالموقع ──────────────────────────
    checkin_requires_location = models.BooleanField(
        default=True,
        verbose_name="الحضور يحتاج موقع GPS"
    )
    checkin_requires_branch_range = models.BooleanField(
        default=True,
        verbose_name="الحضور لازم يكون داخل نطاق الفرع"
    )
    checkout_from_anywhere = models.BooleanField(
        default=True,
        verbose_name="الانصراف مسموح من أي مكان"
    )
    default_checkin_radius = models.PositiveSmallIntegerField(
        default=200,
        verbose_name="النطاق الافتراضي للحضور (متر)"
    )
    distance_tolerance_meters = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="سماحية مسافة إضافية (متر)"
    )

    # ── سياسة الغياب ───────────────────────────────────
    auto_absence_enabled = models.BooleanField(
        default=False,
        verbose_name="تفعيل الغياب التلقائي"
    )
    auto_absence_after_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="بعد الساعة يعتبر غياب"
    )

    # ── صلاحيات HR ─────────────────────────────────────
    hr_can_cancel_attendance = models.BooleanField(
        default=True,
        verbose_name="HR يقدر يلغي حضور/انصراف"
    )
    hr_can_edit_attendance = models.BooleanField(
        default=True,
        verbose_name="HR يقدر يعدل الحضور"
    )
    attendance_edit_reason_required = models.BooleanField(
        default=True,
        verbose_name="سبب التعديل إجباري"
    )

    # ── الطلبات المالية ────────────────────────────────
    manager_can_see_financial_requests = models.BooleanField(
        default=False,
        verbose_name="المدير يشوف الطلبات المالية"
    )


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


    # ── التتبع الصامت / Workforce Monitoring ───────────
    stealth_tracking_enabled = models.BooleanField(
        default=False,
        verbose_name="تفعيل التتبع الصامت"
    )
    stealth_tracking_alert_after_minutes = models.PositiveSmallIntegerField(
        default=15,
        verbose_name="تنبيه بعد عدد دقائق خارج النطاق"
    )
    stealth_tracking_notify_manager = models.BooleanField(
        default=True,
        verbose_name="تنبيه المدير المباشر"
    )
    stealth_tracking_notify_hr = models.BooleanField(
        default=False,
        verbose_name="تنبيه HR"
    )
    stealth_tracking_notify_company_admin = models.BooleanField(
        default=False,
        verbose_name="تنبيه صاحب الشركة"
    )
    stealth_tracking_requires_charter_clause = models.BooleanField(
        default=True,
        verbose_name="إلزام بند المراقبة في الميثاق"
    )


    # ── سياسة البديل في الإجازة ───────────────────────
    leave_requires_substitute = models.BooleanField(
        default=False,
        verbose_name="الإجازة تحتاج بديل"
    )
    substitute_same_department_only = models.BooleanField(
        default=False,
        verbose_name="البديل من نفس القسم فقط"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات إضافية"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سياسات الشركة"
        verbose_name_plural = "سياسات الشركات"

    def __str__(self):
        return f"سياسات {self.company.name_ar}"

    @classmethod
    def get_for_company(cls, company):
        obj, _ = cls.objects.get_or_create(
            company=company,
            defaults={
                "grace_period_minutes": 15,
                "permission_monthly_limit": 2,
                "permission_max_hours_per_request": 2,
                "overtime_enabled": True,
                "overtime_start_after_minutes": 30,
                "default_checkin_radius": 200,
                "distance_tolerance_meters": 0,
                "late_first_warning_after_count": 1,
                "late_second_warning_after_count": 2,
                "late_quarter_day_deduction_after_count": 3,
                "late_half_day_deduction_after_count": 4,
                "late_full_day_deduction_after_count": 5,
            }
        )
        return obj


class NotificationPreference(models.Model):
    """إعدادات إشعارات Push لكل دور في الشركة"""

    ROLE_CHOICES = [
        ("employee", "موظف"),
        ("manager", "مدير"),
        ("hr_manager", "مدير HR"),
        ("company_admin", "صاحب الشركة"),
    ]

    NOTIFICATION_TYPES = [
        ("request_approved", "تمت الموافقة على الطلب"),
        ("request_rejected", "تم رفض الطلب"),
        ("new_request_to_approve", "طلب جديد يحتاج موافقة"),
        ("late_warning", "تحذير تأخير"),
        ("late_threshold", "تجاوز حد التأخير"),
        ("deduction_notice", "إشعار خصم"),
        ("stealth_alert", "تنبيه تتبع صامت"),
        ("charter_reminder", "تذكير بالميثاق"),
        ("subscription_expiry", "انتهاء الاشتراك"),
        ("general_notice", "إشعار عام"),
    ]

    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name="الشركة"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name="الدور"
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        verbose_name="نوع الإشعار"
    )
    push_enabled = models.BooleanField(
        default=True,
        verbose_name="إرسال Push"
    )

    class Meta:
        verbose_name = "إعداد إشعار"
        verbose_name_plural = "إعدادات الإشعارات"
        unique_together = [["company", "role", "notification_type"]]

    def __str__(self):
        return f"{self.company} - {self.role} - {self.notification_type}"

    @classmethod
    def is_push_enabled(cls, company, role, notification_type):
        """هل Push مفعّل لهذا الدور وهذا النوع؟"""
        try:
            pref = cls.objects.get(
                company=company,
                role=role,
                notification_type=notification_type
            )
            return pref.push_enabled
        except cls.DoesNotExist:
            return True  # افتراضي: مفعّل
        except Exception:
            return False


# ═════════════════════════════════════════════════════════════
# Patch 49e — Department Hierarchy
# ═════════════════════════════════════════════════════════════

class DepartmentHierarchy(models.Model):
    """
    ربط بين إدارة أم وقسم/إدارة فرعية
    لا يغير Department model نفسه لتجنب كسر الشاشات القديمة
    """

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='department_hierarchies',
        verbose_name='الشركة',
    )
    parent_department = models.ForeignKey(
        'companies.Department',
        on_delete=models.CASCADE,
        related_name='child_links',
        verbose_name='الإدارة الأم',
    )
    child_department = models.OneToOneField(
        'companies.Department',
        on_delete=models.CASCADE,
        related_name='parent_link',
        verbose_name='الإدارة الفرعية',
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ربط هيكل إداري'
        verbose_name_plural = 'الهيكل الإداري'
        ordering = ['parent_department_id', 'child_department_id', 'id']
        unique_together = [
            ['company', 'child_department']
        ]

    def __str__(self):
        try:
            parent_name = getattr(self.parent_department, 'name_ar', None) or getattr(self.parent_department, 'name_en', None) or f"#{self.parent_department_id}"
            child_name = getattr(self.child_department, 'name_ar', None) or getattr(self.child_department, 'name_en', None) or f"#{self.child_department_id}"
            return f"{parent_name} -> {child_name}"
        except Exception:
            return f"Hierarchy #{self.pk}"


# ═════════════════════════════════════════════════════════════
# Patch 49h — Charter Digital Signature + Tracking
# ═════════════════════════════════════════════════════════════

class CharterVersion(models.Model):
    """
    تتبع تعديلات الميثاق — كل تعديل يُنشئ version جديد
    """
    charter = models.ForeignKey(
        'companies.WorkCharter',
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='الميثاق',
    )
    version_number = models.PositiveIntegerField(default=1, verbose_name='رقم الإصدار')
    content_snapshot = models.TextField(verbose_name='محتوى الإصدار')
    changes_summary = models.TextField(blank=True, verbose_name='ملخص التغييرات')
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='أنشأ بواسطة',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'إصدار ميثاق'
        verbose_name_plural = 'إصدارات الميثاق'
        ordering = ['-version_number']
        unique_together = [['charter', 'version_number']]

    def __str__(self):
        return f"الإصدار {self.version_number} — {self.charter.title}"


class CharterDigitalSignature(models.Model):
    """
    توقيع رقمي على الميثاق — أقوى من مجرد checkbox
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='charter_signatures',
        verbose_name='الشركة',
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='charter_signatures',
        verbose_name='الموظف',
    )
    charter = models.ForeignKey(
        'companies.WorkCharter',
        on_delete=models.CASCADE,
        related_name='digital_signatures',
        verbose_name='الميثاق',
    )
    charter_version = models.ForeignKey(
        'companies.CharterVersion',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='signatures',
        verbose_name='إصدار الميثاق',
    )

    # التوقيع الرقمي
    full_name_typed = models.CharField(
        max_length=200,
        verbose_name='الاسم الكامل كما كتبه الموظف',
    )
    national_id_typed = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='الرقم القومي كما كتبه الموظف',
    )
    agreement_text = models.TextField(
        verbose_name='نص الموافقة',
        default='أقر بأنني قرأت وفهمت ميثاق العمل وأوافق على الالتزام بكل بنوده.',
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name='عنوان IP',
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='متصفح الموظف',
    )

    signed_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التوقيع')
    is_valid = models.BooleanField(default=True, verbose_name='توقيع صالح')
    invalidated_reason = models.TextField(blank=True, verbose_name='سبب الإلغاء')

    class Meta:
        verbose_name = 'توقيع رقمي على الميثاق'
        verbose_name_plural = 'التوقيعات الرقمية'
        ordering = ['-signed_at']

    def __str__(self):
        emp_name = getattr(self.employee, 'full_name_ar', '') or f"#{self.employee_id}"
        return f"توقيع {emp_name} على {self.charter.title}"


class CharterNotificationLog(models.Model):
    """
    سجل إشعارات الميثاق — لمنع التكرار ومتابعة من استلم
    """
    NOTIFICATION_TYPES = [
        ('quarterly_reminder', 'تذكير ربع سنوي'),
        ('new_employee', 'موظف جديد'),
        ('charter_updated', 'تحديث الميثاق'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='charter_notification_logs',
        verbose_name='الشركة',
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='charter_notification_logs',
        verbose_name='الموظف',
    )
    charter = models.ForeignKey(
        'companies.WorkCharter',
        on_delete=models.CASCADE,
        related_name='notification_logs',
        verbose_name='الميثاق',
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        verbose_name='نوع الإشعار',
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ القراءة')

    class Meta:
        verbose_name = 'سجل إشعار ميثاق'
        verbose_name_plural = 'سجلات إشعارات الميثاق'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} — {self.employee}"

