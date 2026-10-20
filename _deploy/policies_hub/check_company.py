# فحص سياسات شركة وأرقام مرتبات الشهر الحالي — قراءة فقط.
# أي حاجة بيكتبها حساب المرتب (زي حركات رصيد الأذونات) بتترجع في الآخر (rollback).
#
# التشغيل على السيرفر:
#   cd /var/www/motionhr && sudo env COMPANY="جاكي" ./venv/bin/python manage.py shell < /tmp/c.py
import os
from datetime import date

from django.db import transaction
from django.utils import timezone

from companies.models import Company
from employees.models import Employee
from attendance.models import AttendancePolicy, AttendancePolicyAssignment, LateRule, AbsenceRule, OvertimeRule
from attendance.company_policy_models import PenaltyRule, BonusRule
from attendance.payroll_settings_model import PayrollSettings
from attendance import payroll_rules as pr


class _Rollback(Exception):
    pass


def line(t=''):
    print(t)


q = os.environ.get('COMPANY', '').strip()
today = timezone.localdate()
year, month = int(os.environ.get('YEAR', today.year)), int(os.environ.get('MONTH', today.month))

companies = list(Company._base_manager.filter(name_ar__icontains=q)) + \
    [c for c in Company._base_manager.filter(name_en__icontains=q) if q]
companies = list({c.id: c for c in companies}.values())
if not q or not companies:
    line('مش لاقي شركة بالاسم ده. الشركات الموجودة:')
    for c in Company._base_manager.all().order_by('id'):
        line(f'  {c.id}: {c.name_ar} / {c.name_en}')
    raise SystemExit

for company in companies:
    line('=' * 60)
    line(f'الشركة: {company.name_ar} (رقم {company.id}) — شهر {month}/{year}')
    line('=' * 60)

    s = PayrollSettings._base_manager.filter(company=company).first()
    if s:
        line(f'إعدادات الرواتب: خصم الدقيقة {s.late_deduction_per_minute} | يوم الغياب {s.absence_deduction_per_day} (صفر = أجر اليوم) | ساعة الإضافي {s.overtime_rate_per_hour}')
    else:
        line('إعدادات الرواتب: مش متسجلة → الافتراضي: الدقيقة 1 جنيه | الغياب أجر اليوم | مفيش أوفر تايم')

    line('\nسياسات الحضور والغياب:')
    pols = AttendancePolicy._base_manager.filter(company=company).order_by('-effective_from')
    if not pols:
        line('  مفيش')
    for p in pols:
        asg = AttendancePolicyAssignment._base_manager.filter(policy=p)
        scope = ', '.join(
            {'company': 'كل الشركة', 'branch': f'فرع {a.branch_id}', 'department': f'قسم {a.department_id}'}[a.assignment_type]
            for a in asg
        ) or ('كل الشركة (مش مربوطة)' if p.status == 'active' else 'مش مربوطة')
        status = {'draft': 'مسودة ❌ مش بتتطبق', 'active': 'معتمدة ✅', 'archived': 'مؤرشفة ❌', 'approved': 'معتمدة'}.get(p.status, p.status)
        line(f'  [{p.id}] {p.name} | {status} | من {p.effective_from} لـ {p.effective_to or "مفتوح"} | النطاق: {scope}')
        line(f'       قواعد تأخير: {LateRule.objects.filter(policy=p).count()} | غياب: {AbsenceRule.objects.filter(policy=p).count()} | أوفر تايم: {OvertimeRule.objects.filter(policy=p).count()} | أذونات: {"مفعلة" if p.permission_enabled else "لا"}')

    line('\nلائحة الجزاءات (ليها الأولوية على سياسة الحضور):')
    prs = PenaltyRule._base_manager.filter(company=company, is_active=True).order_by('penalty_type', '-version_number')
    if not prs:
        line('  مفيش')
    for r in prs:
        line(f'  [{r.id}] {r.get_penalty_type_display()} | {r.name} | سماح {r.grace_amount} | من {r.start_date} لـ {r.end_date or "مفتوح"} | النطاق {r.scope} | شرائح {len(r.tiers or [])}')

    line('\nقواعد الأوفر تايم والليلي والويك إند:')
    brs = BonusRule._base_manager.filter(company=company, is_active=True)
    if not brs:
        line('  مفيش')
    for r in brs:
        line(f'  [{r.id}] {r.get_bonus_type_display()} | {r.name} | من {r.start_date} لـ {r.end_date or "مفتوح"} | شرائح {len(r.tiers or [])}')

    line('\nالموظفين (كود | الأساسي | دقايق تأخير | خصم التأخير | أيام غياب | خصم الغياب | الصافي | مصدر قاعدة التأخير):')
    first_day, last_day = pr.get_payroll_period_bounds(company, year, month)
    try:
        with transaction.atomic():
            emps = Employee._base_manager.filter(company=company).exclude(status__in=['terminated', 'resigned']).order_by('id')
            only = os.environ.get('EMP', '').strip()
            if only:
                emps = emps.filter(employee_code=only)
            for emp in emps:
                p = pr.calculate_effective_payroll(emp, year, month)
                if only:
                    line(f'  تفاصيل {only} يوم بيوم (التاريخ | الحالة | حضور | انصراف | تأخير بعد السماح | تأخير بيتخصم | أوفر تايم ساعات):')
                    for dd in p['daily_details']:
                        line(f"    {dd['date']} | {dd.get('effective_status')} | {dd.get('check_in') or '-'} | {dd.get('check_out') or '-'} | "
                             f"{dd.get('late_minutes', 0)} | {dd.get('deductible_late_minutes', 0)} | {dd.get('overtime_hours', 0)}")
                    line(f"  إجمالي: أوفر تايم {p['overtime_hours']} ساعة = {p['overtime_bonus']} جنيه | خصم التأخير {p['late_deduction']} | الإجمالي {p['gross_salary']} | الخصومات {p['total_deductions']} | الصافي {p['net_salary']}")
                rules = pr._load_scoped_rules(PenaltyRule, company, emp, first_day, last_day, 'penalty_type')
                late_rule = pr._rule_for_day(rules.get('late_arrival'), min(today, last_day))
                pol = pr._get_active_policy(company, min(today, last_day), department=emp.department, branch=emp.branch)
                if late_rule and late_rule.tiers:
                    src = f'لائحة الجزاءات: {late_rule.name}'
                elif pol and pr._policy_has_late_rules(pol):
                    src = f'سياسة الحضور: {pol.name}'
                else:
                    src = 'الافتراضي (خصم الدقيقة من إعدادات الرواتب)'
                line(f'  {emp.employee_code or emp.id} | {p["basic_salary"]} | {p["total_late_minutes"]} | {p["late_deduction"]} | '
                     f'{p["absent_days"]} | {p["absence_deduction"]} | {p["net_salary"]} | {src}')
            raise _Rollback
    except _Rollback:
        pass
    line('')
