import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

p = Path("attendance/company_policy_models.py")
text = p.read_text(encoding="utf-8")

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

    # Smart Attendance Policy
    TRIGGER_MODES = [
        ('manual',       'يدوي فقط'),
        ('notification', 'إشعار ذكي'),
        ('auto',         'تسجيل تلقائي'),
    ]
    attendance_trigger_mode = models.CharField(
        max_length=20, choices=TRIGGER_MODES, default='notification',
        verbose_name='طريقة تسجيل الحضور'
    )
    pre_shift_checkin_window = models.PositiveIntegerField(
        default=15, verbose_name='السماح بالحضور قبل الشيفت (دقيقة)'
    )
    require_live_location = models.BooleanField(
        default=True, verbose_name='الموقع مطلوب بعد الحضور'
    )
    LOCATION_LOSS_ACTIONS = [
        ('ignore',           'تجاهل'),
        ('alert_only',       'تنبيه الإدارة فقط'),
        ('record_violation', 'تسجيل مخالفة'),
    ]
    location_loss_action = models.CharField(
        max_length=20, choices=LOCATION_LOSS_ACTIONS, default='alert_only',
        verbose_name='إجراء فقد الموقع'
    )
    location_loss_grace_minutes = models.PositiveIntegerField(
        default=5, verbose_name='دقائق سماح قبل اعتبار الموقع مفقوداً'
    )

    class Meta:
        verbose_name = 'سياسة عمل الشركة'"""

if old in text:
    text = text.replace(old, new)
    print("[OK] Fields added to local model")
else:
    print("[WARN] Block not found")

p.write_text(text, encoding="utf-8")
print(f"[OK] Saved: {p.stat().st_size} bytes")
