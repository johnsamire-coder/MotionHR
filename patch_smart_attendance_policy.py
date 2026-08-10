import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

p = Path("attendance/company_policy_models.py")
text = p.read_text(encoding="utf-8")

# نضيف الحقول الجديدة بعد auto_checkout_grace
old = """    auto_checkout_grace   = models.IntegerField(
        default=30,
        verbose_name='وقت السماح بعد الشيفت (دقيقة)'
    )

    class Meta:
        verbose_name = 'سياسة عمل الشركة'"""

new = """    auto_checkout_grace   = models.IntegerField(
        default=30,
        verbose_name='وقت السماح بعد الشيفت (دقيقة)'
    )

    # ─── Smart Attendance Policy ───
    TRIGGER_MODES = [
        ('manual',       'يدوي فقط - الموظف يفتح التطبيق ويضغط'),
        ('notification', 'إشعار ذكي - تنبيه للموظف ليؤكد'),
        ('auto',         'تسجيل تلقائي بالكامل'),
    ]
    attendance_trigger_mode = models.CharField(
        max_length=20,
        choices=TRIGGER_MODES,
        default='notification',
        verbose_name='طريقة تسجيل الحضور',
        help_text='يدوي = أأمن. إشعار = موصى به. تلقائي = راجع الاعتبارات.'
    )
    pre_shift_checkin_window = models.PositiveIntegerField(
        default=15,
        verbose_name='السماح بالحضور قبل الشيفت بـ (دقيقة)',
        help_text='الموظف يقدر يسجل حضوره قبل الشيفت بهذا الوقت فقط'
    )
    require_live_location = models.BooleanField(
        default=True,
        verbose_name='الموقع مطلوب بعد الحضور (للميداني)',
        help_text='للحفاظ على جودة بيانات الحضور'
    )
    LOCATION_LOSS_ACTIONS = [
        ('ignore',           'تجاهل'),
        ('alert_only',       'تنبيه الإدارة فقط'),
        ('record_violation', 'تسجيل مخالفة تتبع'),
    ]
    location_loss_action = models.CharField(
        max_length=20,
        choices=LOCATION_LOSS_ACTIONS,
        default='alert_only',
        verbose_name='إجراء فقد الموقع بعد الحضور'
    )
    location_loss_grace_minutes = models.PositiveIntegerField(
        default=5,
        verbose_name='دقائق سماح قبل اعتبار الموقع مفقوداً'
    )

    class Meta:
        verbose_name = 'سياسة عمل الشركة'"""

if old in text:
    text = text.replace(old, new)
    print("[OK] Smart Attendance fields added to CompanyWorkPolicy")
else:
    print("[WARN] Target block not found")

p.write_text(text, encoding="utf-8")
print(f"[OK] Saved: {p.stat().st_size} bytes")
