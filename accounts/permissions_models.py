from django.db import models


# ═══════════════════════════════════════
# قايمة كل الصلاحيات الممكنة في النظام
# ═══════════════════════════════════════
PERMISSION_CHOICES = [
    # ── الموظفين ──
    ('employees.view',     'عرض الموظفين'),
    ('employees.add',      'إضافة موظف'),
    ('employees.edit',     'تعديل موظف'),
    ('employees.delete',   'حذف موظف'),
    ('employees.transfer', 'نقل موظف'),
    # ── الحضور ──
    ('attendance.view',    'عرض الحضور'),
    ('attendance.edit',    'تعديل الحضور'),
    # ── الإجازات ──
    ('leaves.view',        'عرض الإجازات'),
    ('leaves.approve',     'اعتماد الإجازات'),
    # ── الطلبات ──
    ('requests.view',      'عرض الطلبات'),
    ('requests.approve',   'اعتماد الطلبات'),
    # ── المرتبات ──
    ('payroll.view',       'عرض المرتبات'),
    ('payroll.edit',       'تعديل المرتبات'),
    # ── التقارير ──
    ('reports.view',       'عرض التقارير'),
    ('reports.export',     'تصدير التقارير'),
    # ── المهام ──
    ('missions.view',      'عرض المهام'),
    ('missions.manage',    'إدارة المهام'),
    # ── إعدادات الشركة ──
    ('company.view',       'عرض إعدادات الشركة'),
    ('company.edit',       'تعديل إعدادات الشركة'),
    # ── الأقسام ──
    ('departments.view',             'عرض الأقسام'),
    ('departments.add',              'إضافة قسم'),
    ('departments.edit',             'تعديل قسم'),
    ('departments.delete',           'حذف قسم'),
    ('departments.transfer_employees', 'نقل موظفين بين الأقسام'),
    # ── إنهاء الخدمة ──
    ('offboarding.execute',          'إنهاء خدمة موظف أو مدير'),
    # ── الشيفتات ──
    ('shifts.view',                  'عرض الشيفتات'),
    ('shifts.manage',                'إدارة الشيفتات'),
    # ── السياسات ──
    ('policies.view',                'عرض السياسات'),
    ('policies.manage',              'إدارة السياسات'),
    # ── الإجازات الرسمية ──
    ('holidays.view',                'عرض الإجازات الرسمية'),
    ('holidays.manage',              'إدارة الإجازات الرسمية'),
    # ── التتبع ──
    ('tracking.view',                'عرض التتبع والمواقع'),
    ('tracking.manage',              'إدارة التتبع'),
    # ── صلاحيات الموظف نفسه ──
    ('payroll.view_own',             'عرض مرتبي فقط'),
    ('attendance.checkin',           'تسجيل الحضور والانصراف'),
    ('leaves.request',               'تقديم طلب إجازة'),
    ('requests.submit',              'تقديم طلبات'),
    ('profile.view',                 'عرض الملف الشخصي'),
    ('profile.edit_basic',           'تعديل البيانات الأساسية'),
    ('missions.view_own',            'عرض مهامي فقط'),
    # ── إدارة الأدوار ──
    ('roles.manage',                 'إدارة الأدوار والصلاحيات'),
]

# مستويات الوصول
SCOPE_CHOICES = [
    ('self',    'نفسه فقط'),
    ('team',    'فريقه فقط'),
    ('dept',    'قسمه فقط'),
    ('company', 'كل الشركة'),
]


class CustomRole(models.Model):
    """دور مخصص ينشئه مدير الشركة"""
    company   = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='custom_roles')
    name      = models.CharField(max_length=100, verbose_name='اسم الدور')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'name')
        verbose_name = 'دور مخصص'
        verbose_name_plural = 'الأدوار المخصصة'

    def __str__(self):
        return f"{self.company} | {self.name}"


class RolePermission(models.Model):
    """صلاحيات الدور"""
    role       = models.ForeignKey(CustomRole, on_delete=models.CASCADE, related_name='permissions')
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    scope      = models.CharField(max_length=10, choices=SCOPE_CHOICES, default='company')

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = 'صلاحية دور'
        verbose_name_plural = 'صلاحيات الأدوار'

    def __str__(self):
        return f"{self.role.name} | {self.permission} | {self.scope}"


class UserRole(models.Model):
    """تعيين دور لمستخدم"""
    user    = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='custom_roles')
    role    = models.ForeignKey(CustomRole, on_delete=models.CASCADE, related_name='users')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'role')
        verbose_name = 'دور المستخدم'
        verbose_name_plural = 'أدوار المستخدمين'

    def __str__(self):
        return f"{self.user} | {self.role.name}"


class UserPermissionOverride(models.Model):
    """استثناء لشخص معين - زيادة أو منع صلاحية معينة"""
    user       = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='permission_overrides')
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    scope      = models.CharField(max_length=10, choices=SCOPE_CHOICES, default='company')
    is_granted = models.BooleanField(default=True, verbose_name='ممنوحة أم ممنوعة')

    class Meta:
        unique_together = ('user', 'permission')
        verbose_name = 'استثناء صلاحية'
        verbose_name_plural = 'استثناءات الصلاحيات'

    def __str__(self):
        status = '✅' if self.is_granted else '❌'
        return f"{status} {self.user} | {self.permission}"


# ═══════════════════════════════════════════════════
# الصلاحيات الافتراضية لكل Role
# ═══════════════════════════════════════════════════

DEFAULT_ROLE_PERMISSIONS = {
    'company_admin': [
        # الموظفين
        ('employees.view', 'company'), ('employees.add', 'company'),
        ('employees.edit', 'company'), ('employees.delete', 'company'),
        ('employees.transfer', 'company'),
        # الحضور
        ('attendance.view', 'company'), ('attendance.edit', 'company'),
        ('attendance.checkin', 'self'),
        # الإجازات
        ('leaves.view', 'company'), ('leaves.approve', 'company'),
        ('leaves.request', 'self'),
        # الطلبات
        ('requests.view', 'company'), ('requests.approve', 'company'),
        ('requests.submit', 'self'),
        # المرتبات
        ('payroll.view', 'company'), ('payroll.edit', 'company'),
        ('payroll.view_own', 'self'),
        # التقارير
        ('reports.view', 'company'), ('reports.export', 'company'),
        # المهام
        ('missions.view', 'company'), ('missions.manage', 'company'),
        ('missions.view_own', 'self'),
        # الشركة
        ('company.view', 'company'), ('company.edit', 'company'),
        # الأقسام
        ('departments.view', 'company'), ('departments.add', 'company'),
        ('departments.edit', 'company'), ('departments.delete', 'company'),
        ('departments.transfer_employees', 'company'),
        # الشيفتات
        ('shifts.view', 'company'), ('shifts.manage', 'company'),
        # السياسات
        ('policies.view', 'company'), ('policies.manage', 'company'),
        # الإجازات الرسمية
        ('holidays.view', 'company'), ('holidays.manage', 'company'),
        # التتبع
        ('tracking.view', 'company'), ('tracking.manage', 'company'),
        # إنهاء الخدمة
        ('offboarding.execute', 'company'),
        # الأدوار
        ('roles.manage', 'company'),
        # الملف الشخصي
        ('profile.view', 'self'), ('profile.edit_basic', 'self'),
    ],
    'hr_manager': [
        # الموظفين
        ('employees.view', 'company'), ('employees.add', 'company'),
        ('employees.edit', 'company'), ('employees.delete', 'company'),
        ('employees.transfer', 'company'),
        # الحضور
        ('attendance.view', 'company'), ('attendance.edit', 'company'),
        ('attendance.checkin', 'self'),
        # الإجازات
        ('leaves.view', 'company'), ('leaves.approve', 'company'),
        ('leaves.request', 'self'),
        # الطلبات
        ('requests.view', 'company'), ('requests.approve', 'company'),
        ('requests.submit', 'self'),
        # المرتبات
        ('payroll.view', 'company'), ('payroll.edit', 'company'),
        ('payroll.view_own', 'self'),
        # التقارير
        ('reports.view', 'company'), ('reports.export', 'company'),
        # المهام
        ('missions.view', 'company'), ('missions.manage', 'company'),
        ('missions.view_own', 'self'),
        # الشركة
        ('company.view', 'company'),
        # الأقسام
        ('departments.view', 'company'), ('departments.add', 'company'),
        ('departments.edit', 'company'),
        ('departments.transfer_employees', 'company'),
        # الشيفتات
        ('shifts.view', 'company'), ('shifts.manage', 'company'),
        # السياسات
        ('policies.view', 'company'), ('policies.manage', 'company'),
        # الإجازات الرسمية
        ('holidays.view', 'company'), ('holidays.manage', 'company'),
        # التتبع
        ('tracking.view', 'company'), ('tracking.manage', 'company'),
        # إنهاء الخدمة
        ('offboarding.execute', 'company'),
        # الملف الشخصي
        ('profile.view', 'self'), ('profile.edit_basic', 'self'),
    ],
    'manager': [
        # الموظفين
        ('employees.view', 'team'),
        # الحضور
        ('attendance.view', 'team'), ('attendance.edit', 'team'),
        ('attendance.checkin', 'self'),
        # الإجازات
        ('leaves.view', 'team'), ('leaves.approve', 'team'),
        ('leaves.request', 'self'),
        # الطلبات
        ('requests.view', 'team'), ('requests.approve', 'team'),
        ('requests.submit', 'self'),
        # المرتبات
        ('payroll.view_own', 'self'),
        # التقارير
        ('reports.view', 'team'),
        # المهام
        ('missions.view', 'team'), ('missions.manage', 'team'),
        ('missions.view_own', 'self'),
        # الشيفتات
        ('shifts.view', 'team'),
        # الإجازات الرسمية
        ('holidays.view', 'company'),
        # التتبع
        ('tracking.view', 'team'),
        # الملف الشخصي
        ('profile.view', 'self'), ('profile.edit_basic', 'self'),
    ],
    'employee': [
        # الحضور
        ('attendance.checkin', 'self'),
        # الإجازات
        ('leaves.request', 'self'),
        # الطلبات
        ('requests.submit', 'self'),
        # المرتبات
        ('payroll.view_own', 'self'),
        # المهام
        ('missions.view_own', 'self'),
        # الإجازات الرسمية
        ('holidays.view', 'company'),
        # الملف الشخصي
        ('profile.view', 'self'), ('profile.edit_basic', 'self'),
    ],
}


def has_perm(user, permission, scope=None):
    """
    التحقق من صلاحية يوزر معين.
    الأولوية:
    1. super_admin → كل حاجة
    2. UserPermissionOverride (استثناء شخصي)
    3. CustomRole (دور مخصص)
    4. DEFAULT_ROLE_PERMISSIONS (الصلاحيات الافتراضية للـ role)
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser or getattr(user, 'role', None) == 'super_admin':
        return True

    # فحص الاستثناءات الشخصية
    try:
        override = UserPermissionOverride.objects.filter(
            user=user,
            permission=permission,
        ).first()
        if override:
            return override.is_granted
    except Exception:
        pass

    # فحص الأدوار المخصصة
    try:
        user_role_ids = UserRole.objects.filter(
            user=user
        ).values_list('role_id', flat=True)
        if user_role_ids:
            has_custom = RolePermission.objects.filter(
                role_id__in=user_role_ids,
                permission=permission,
            ).exists()
            if has_custom:
                return True
    except Exception:
        pass

    # فحص الصلاحيات الافتراضية
    role = getattr(user, 'role', None)
    if role and role in DEFAULT_ROLE_PERMISSIONS:
        for perm, perm_scope in DEFAULT_ROLE_PERMISSIONS[role]:
            if perm == permission:
                if scope is None:
                    return True
                return perm_scope == scope or perm_scope == 'company'

    return False


def get_user_permissions(user):
    """
    بيرجع كل صلاحيات اليوزر مع scope بتاع كل صلاحية.
    """
    if not user or not user.is_authenticated:
        return {}

    role = getattr(user, 'role', None)

    if user.is_superuser or role == 'super_admin':
        return {perm: 'company' for perm, _ in PERMISSION_CHOICES}

    result = {}

    # الصلاحيات الافتراضية
    if role and role in DEFAULT_ROLE_PERMISSIONS:
        for perm, scope in DEFAULT_ROLE_PERMISSIONS[role]:
            result[perm] = scope

    # الأدوار المخصصة
    try:
        user_role_ids = UserRole.objects.filter(
            user=user
        ).values_list('role_id', flat=True)
        for rp in RolePermission.objects.filter(role_id__in=user_role_ids):
            result[rp.permission] = rp.scope
    except Exception:
        pass

    # الاستثناءات الشخصية
    try:
        for ov in UserPermissionOverride.objects.filter(user=user):
            if ov.is_granted:
                result[ov.permission] = ov.scope
            else:
                result.pop(ov.permission, None)
    except Exception:
        pass

    return result
