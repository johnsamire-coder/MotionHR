import pathlib, re

BASE = pathlib.Path('.')
file_path = BASE / 'attendance' / 'payroll_rules.py'
content = file_path.read_text(encoding='utf-8')

new_func = """def _apply_absence_rule(policy, absent_days, daily_salary, consecutive_days=0, occurrences=0):
    \"\"\"
    يطبق قواعد خصم الغياب بدقة:
    - يدعم خصم أكثر من يوم (مثلاً deduction_value = 2.0 يعني يومين خصم عن كل يوم غياب)
    - يدعم الغياب المتتالي (consecutive) والمتكرر (repeated) وبدون إذن (unexcused)
    \"\"\"
    if not policy or absent_days <= 0:
        return 0.0, 0.0

    daily_sal = float(daily_salary)
    total_absent = float(absent_days)

    try:
        from attendance.models import AbsenceRule
        
        # 1. البحث عن قاعدة الغياب المتتالي أولاً إن وجدت
        if consecutive_days > 1:
            rule_c = AbsenceRule._base_manager.filter(
                policy=policy,
                absence_type='consecutive',
                consecutive_days__lte=consecutive_days
            ).order_by('-consecutive_days', 'display_order').first()
            if rule_c:
                mult = float(rule_c.deduction_value)
                if rule_c.deduction_type == 'day_fraction':
                    return round(total_absent * daily_sal * mult, 2), round(total_absent * mult, 2)
                elif rule_c.deduction_type == 'fixed_amount':
                    return round(total_absent * mult, 2), total_absent

        # 2. البحث عن قاعدة الغياب المتكرر في الشهر
        if occurrences > 1:
            rule_r = AbsenceRule._base_manager.filter(
                policy=policy,
                absence_type='repeated',
                occurrences_in_month__lte=occurrences
            ).order_by('-occurrences_in_month', 'display_order').first()
            if rule_r:
                mult = float(rule_r.deduction_value)
                if rule_r.deduction_type == 'day_fraction':
                    return round(total_absent * daily_sal * mult, 2), round(total_absent * mult, 2)
                elif rule_r.deduction_type == 'fixed_amount':
                    return round(total_absent * mult, 2), total_absent

        # 3. القاعدة العامة (بدون إذن - unexcused)
        rule_u = AbsenceRule._base_manager.filter(
            policy=policy,
            absence_type='unexcused'
        ).order_by('display_order').first()

        if rule_u:
            mult = float(rule_u.deduction_value)
            if rule_u.deduction_type == 'day_fraction':
                return round(total_absent * daily_sal * mult, 2), round(total_absent * mult, 2)
            elif rule_u.deduction_type == 'fixed_amount':
                return round(total_absent * mult, 2), total_absent
            elif rule_u.deduction_type == 'warning':
                return 0.0, 0.0

    except Exception:
        pass

    # الافتراضي: خصم يوم بيوم (1.0)
    return round(total_absent * daily_sal, 2), total_absent
"""

pattern = r'def _apply_absence_rule\(.*?\):.*?(?=\ndef |\Z)'
content = re.sub(pattern, new_func + '\n\n', content, count=1, flags=re.DOTALL)
file_path.write_text(content, encoding='utf-8')
print("[OK] attendance/payroll_rules.py updated with flexible absence rules.")
