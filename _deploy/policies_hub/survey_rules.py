# حصر: كل شركة بتحط قواعد التأخير والغياب والأوفر تايم فين — قراءة فقط.
#   cd /var/www/motionhr && sudo ./venv/bin/python manage.py shell < /tmp/s.py
from companies.models import Company
from attendance.models import AttendancePolicy, LateRule, AbsenceRule, OvertimeRule
from attendance.company_policy_models import PenaltyRule, BonusRule

print('الشركة | سياسة حضور معتمدة: (تأخير/غياب/أوفر تايم) | لائحة الجزاءات: (تأخير/غياب/انصراف/بصمة) | قواعد المكافآت: (أوفر/ليلي/ويك إند)')
for c in Company._base_manager.all().order_by('id'):
    pols = AttendancePolicy._base_manager.filter(company=c, status='active')
    late = LateRule.objects.filter(policy__in=pols).count()
    absn = AbsenceRule.objects.filter(policy__in=pols).count()
    ot = OvertimeRule.objects.filter(policy__in=pols).count()
    pr = PenaltyRule._base_manager.filter(company=c, is_active=True)
    br = BonusRule._base_manager.filter(company=c, is_active=True)
    cnt = lambda qs, f, v: qs.filter(**{f: v}).count()
    row = (
        f'({late}/{absn}/{ot})',
        f'({cnt(pr, "penalty_type", "late_arrival")}/{cnt(pr, "penalty_type", "absence")}/'
        f'{cnt(pr, "penalty_type", "early_leave")}/{cnt(pr, "penalty_type", "missing_checkout")})',
        f'({cnt(br, "bonus_type", "overtime")}/{cnt(br, "bonus_type", "night_shift")}/{cnt(br, "bonus_type", "weekend_work")})',
    )
    both = []
    if late and cnt(pr, 'penalty_type', 'late_arrival'):
        both.append('تأخير')
    if absn and cnt(pr, 'penalty_type', 'absence'):
        both.append('غياب')
    if ot and cnt(br, 'bonus_type', 'overtime'):
        both.append('أوفر تايم')
    flag = f'  ⚠ متكرر: {"، ".join(both)}' if both else ''
    print(f'{c.id} {c.name_ar} | {pols.count()} سياسة {row[0]} | {row[1]} | {row[2]}{flag}')
