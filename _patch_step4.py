import pathlib, re

BASE = pathlib.Path('.')

# ============================================================
# 1) تعديل attendance/models.py — إضافة حقول المرونة لموديل Shift
# ============================================================
models_path = BASE / 'attendance' / 'models.py'
content = models_path.read_text(encoding='utf-8')

if 'early_checkout_allowed' not in content:
    target = '    grace_early_leave = models.IntegerField('
    fields_to_add = """    # مرونة الانصراف (مفيدة لمهندسي المواقع والميدانيين)
    early_checkout_allowed = models.BooleanField(
        default=False,
        verbose_name='السماح بالانصراف المبكر'
    )
    early_checkout_minutes = models.IntegerField(
        default=0,
        verbose_name='الانصراف المبكر المسموح (دقائق)',
        help_text='مثال: 60 = السماح بالانصراف قبل ميعاد الشيفت بساعة'
    )
    late_checkout_allowed = models.BooleanField(
        default=False,
        verbose_name='السماح بالانصراف المتأخر'
    )
    late_checkout_minutes = models.IntegerField(
        default=0,
        verbose_name='الانصراف المتأخر المسموح (دقائق)',
        help_text='مثال: 180 = السماح بالانصراف بعد ميعاد الشيفت بـ 3 ساعات'
    )

"""
    if target in content:
        content = content.replace(target, fields_to_add + target, 1)
        models_path.write_text(content, encoding='utf-8')
        print("[OK] attendance/models.py: Added flex checkout fields to Shift model.")
    else:
        print("[!] Could not find grace_early_leave target in attendance/models.py")
else:
    print("[SKIP] Shift flex checkout fields already exist in attendance/models.py")


# ============================================================
# 2) تعديل attendance/api_mobile.py — تطبيق منطق مرونة الانصراف
# ============================================================
mobile_path = BASE / 'attendance' / 'api_mobile.py'
mobile_content = mobile_path.read_text(encoding='utf-8')

old_logic = """    if shift_end and now < shift_end:
        early_leave_minutes = int((shift_end - now).total_seconds() // 60)"""

new_logic = """    if shift_end and now < shift_end:
        raw_early = int((shift_end - now).total_seconds() // 60)
        # فحص سماحية الانصراف المبكر للشيفت
        allowed_early_grace = 0
        if shift and getattr(shift, 'early_checkout_allowed', False):
            allowed_early_grace = getattr(shift, 'early_checkout_minutes', 0) or 0
        elif shift and getattr(shift, 'grace_early_leave', 0):
            allowed_early_grace = getattr(shift, 'grace_early_leave', 0) or 0
        
        if raw_early <= allowed_early_grace:
            early_leave_minutes = 0
        else:
            early_leave_minutes = raw_early - allowed_early_grace"""

if 'raw_early <= allowed_early_grace' not in mobile_content:
    if old_logic in mobile_content:
        mobile_content = mobile_content.replace(old_logic, new_logic, 1)
        mobile_path.write_text(mobile_content, encoding='utf-8')
        print("[OK] attendance/api_mobile.py: Applied shift flex checkout logic.")
    else:
        print("[!] Warning: Could not match exact old_logic block in api_mobile.py")
else:
    print("[SKIP] Shift flex checkout logic already applied in api_mobile.py")

