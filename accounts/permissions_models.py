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
