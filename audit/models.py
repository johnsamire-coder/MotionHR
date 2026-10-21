"""
سجل التعديلات: مين عمل إيه وإمتى، وقبل وبعد.

الجدول ده مستقل تماماً: مافيهوش أي ربط (ForeignKey) بجداول تانية، ومالوش ملفات migrations،
وبيتعمل بأمر audit_setup. كده إضافته مابتلمسش أي جدول تاني ولا تاريخ الـ migrations اللي متلخبط.
"""
from django.db import models


class AuditLog(models.Model):
    ACTIONS = [
        ('create', 'إضافة'),
        ('update', 'تعديل'),
        ('delete', 'حذف'),
        ('login', 'تسجيل دخول'),
        ('action', 'إجراء'),
    ]

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    company_id = models.IntegerField(null=True, blank=True, db_index=True)

    # مين عمل التعديل (بنحفظ الاسم كمان عشان يفضل ظاهر حتى لو الحساب اتمسح)
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    username = models.CharField(max_length=150, blank=True, default='')
    user_name = models.CharField(max_length=255, blank=True, default='')
    user_role = models.CharField(max_length=50, blank=True, default='')

    action = models.CharField(max_length=20, choices=ACTIONS, db_index=True)
    model = models.CharField(max_length=100, db_index=True)          # مثلاً employees.Employee
    model_label = models.CharField(max_length=150, blank=True, default='')
    object_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    object_repr = models.CharField(max_length=255, blank=True, default='')

    # الموظف اللي التعديل يخصه (لتقرير "كل اللي اتغير في الموظف ده")
    employee_id = models.IntegerField(null=True, blank=True, db_index=True)
    employee_name = models.CharField(max_length=255, blank=True, default='')

    # [{"field": "basic_salary", "label": "الراتب الأساسي", "old": "5000", "new": "6000"}, ...]
    changes = models.JSONField(default=list, blank=True)
    note = models.CharField(max_length=500, blank=True, default='')

    source = models.CharField(max_length=20, blank=True, default='')   # web / mobile / admin / system
    ip = models.CharField(max_length=64, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'audit_auditlog'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['company_id', 'created_at'], name='audit_company_time'),
            models.Index(fields=['employee_id', 'created_at'], name='audit_employee_time'),
        ]

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} {self.username} {self.action} {self.model}#{self.object_id}'
