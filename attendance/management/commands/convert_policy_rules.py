"""
نقل قواعد التأخير والغياب والأوفر تايم من سياسات الحضور المعتمدة لكروت مركز السياسات
(لائحة الجزاءات PenaltyRule وقواعد الأوفر تايم BonusRule) بنفس الأرقام بالظبط.

    python manage.py convert_policy_rules            # تجربة بس: بيوري هيعمل إيه ومابيحفظش
    python manage.py convert_policy_rules --apply    # ينقل ويحفظ

قبل الحفظ بيحسب مرتب الشهر الحالي لكل موظف في الشركات اللي اتنقلت قواعدها قبل وبعد النقل،
ولو أي صافي اتغير بأكتر من قرش مابيحفظش أي حاجة.
السياسات الأصلية وقواعدها بتفضل زي ما هي (للرجوع)، والقواعد الجديدة ليها الأولوية في الحساب.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

MARK = 'converted_from_policy:'


from attendance.payroll_rules import normalize_rule_type


class _Undo(Exception):
    pass


def _late_tiers(rules):
    """LateRule → شرائح لائحة الجزاءات. الفجوات بين القواعد بتتسد بالقاعدة اللي قبلها (نفس سلوك LateRule)."""
    rules = sorted(rules, key=lambda r: (r.from_minutes, r.display_order))
    tiers = []
    for i, r in enumerate(rules):
        to = int(r.to_minutes)
        if i + 1 < len(rules) and rules[i + 1].from_minutes > to + 1:
            to = rules[i + 1].from_minutes - 1
        kind, value = normalize_rule_type(r.deduction_type, r.deduction_value)
        if kind == 'day_fraction':
            tier = {'deduction_type': 'day_fraction', 'value': value}
        elif kind == 'fixed_amount':
            tier = {'deduction_type': 'fixed_total', 'value': value}
        elif kind == 'per_minute':
            tier = {'deduction_type': 'fixed_per_unit', 'value': value}
        else:  # none/warning أو نوع مش معروف = من غير خصم
            tier = {'deduction_type': 'fixed_total', 'value': 0}
        tier.update({'from': int(r.from_minutes), 'to': to})
        tiers.append(tier)
    return tiers


def _absence_tiers(rule):
    kind, value = normalize_rule_type(rule.deduction_type, rule.deduction_value)
    if kind == 'day_fraction':
        t = {'deduction_type': 'day_fraction', 'value': value}
    elif kind == 'fixed_amount':
        t = {'deduction_type': 'fixed_per_unit', 'value': value}
    else:  # warning = إنذار بس من غير خصم
        t = {'deduction_type': 'fixed_total', 'value': 0}
    t.update({'from': 1, 'to': None})
    return [t]


def _scopes(policy):
    from attendance.models import AttendancePolicyAssignment
    out = []
    for a in AttendancePolicyAssignment._base_manager.filter(policy=policy):
        if a.assignment_type == 'branch' and a.branch_id:
            out.append({'scope': 'branch', 'branch_id': a.branch_id})
        elif a.assignment_type == 'department' and a.department_id:
            out.append({'scope': 'department', 'department_id': a.department_id})
        else:
            out.append({'scope': 'company'})
    return out or [{'scope': 'company'}]


class Command(BaseCommand):
    help = 'نقل قواعد سياسات الحضور لكروت مركز السياسات المنفصلة'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='احفظ النقل (من غيرها تجربة بس)')
        parser.add_argument('--year', type=int, help='شهر المراجعة (الافتراضي الشهر الحالي)')
        parser.add_argument('--month', type=int)

    def handle(self, *args, **opts):
        from employees.models import Employee
        from attendance.models import AttendancePolicy, LateRule, AbsenceRule, OvertimeRule
        from attendance.company_policy_models import PenaltyRule, BonusRule
        from attendance.payroll_rules import calculate_effective_payroll

        today = timezone.localdate()
        year, month = opts.get('year') or today.year, opts.get('month') or today.month
        out = self.stdout.write

        policies = list(AttendancePolicy._base_manager.filter(status='active').order_by('company_id', 'effective_from'))
        plan = []
        for pol in policies:
            tag = f'{MARK}{pol.id}'
            if PenaltyRule._base_manager.filter(company=pol.company, change_reason=tag).exists() or \
                    BonusRule._base_manager.filter(company=pol.company, change_reason=tag).exists():
                out(f'  [{pol.company_id}] {pol.name}: اتنقلت قبل كده — هتتخطى')
                continue
            late = list(LateRule.objects.filter(policy=pol))
            absence = AbsenceRule.objects.filter(policy=pol, absence_type='unexcused').order_by('display_order').first() or \
                AbsenceRule.objects.filter(policy=pol).order_by('display_order').first()
            ot = OvertimeRule.objects.filter(policy=pol, overtime_type='after_shift').order_by('display_order').first()
            if not (late or absence or ot):
                continue
            plan.append((pol, tag, late, absence, ot))

        if not plan:
            out(self.style.SUCCESS('مفيش قواعد محتاجة تتنقل.'))
            return

        companies = sorted({p[0].company_id for p in plan})
        employees = list(Employee._base_manager.filter(company_id__in=companies).exclude(status__in=['terminated', 'resigned']))

        def _nets():
            res = {}
            try:
                with transaction.atomic():
                    for e in employees:
                        res[e.id] = (e.employee_code or str(e.id), e.company_id, calculate_effective_payroll(e, year, month)['net_salary'])
                    raise _Undo
            except _Undo:
                pass
            return res

        before = _nets()
        diffs = []

        try:
            with transaction.atomic():
                for pol, tag, late, absence, ot in plan:
                    company = pol.company
                    out(f'\n[{company.id}] {company.name_ar} — من سياسة "{pol.name}" (من {pol.effective_from} لـ {pol.effective_to or "مفتوح"}):')
                    common = dict(company=company, start_date=pol.effective_from, end_date=pol.effective_to,
                                  change_reason=tag, is_active=True)
                    for sc in _scopes(pol):
                        if late:
                            tiers = _late_tiers(late)
                            PenaltyRule._base_manager.create(name=f'تأخير — {pol.name}', penalty_type='late_arrival',
                                                             grace_amount=0, tiers=tiers, **common, **sc)
                            out(f'   تأخير ({sc["scope"]}): ' + ' | '.join(
                                f'{t["from"]}-{t["to"]} {t["deduction_type"]} {t["value"]}' for t in tiers))
                        if absence:
                            PenaltyRule._base_manager.create(name=f'غياب — {pol.name}', penalty_type='absence',
                                                             grace_amount=0, tiers=_absence_tiers(absence), **common, **sc)
                            out(f'   غياب ({sc["scope"]}): {absence.get_deduction_type_display()} {absence.deduction_value}')
                        if ot:
                            BonusRule._base_manager.create(
                                name=f'أوفر تايم — {pol.name}', bonus_type='overtime',
                                tiers=[{'from': 0, 'to': None, 'value_type': 'multiplier', 'value': float(ot.multiplier),
                                        'min_minutes_per_day': int(ot.min_minutes or 0)}],
                                max_per_day=Decimal(str(ot.max_hours_per_day or 0)),
                                max_per_month=Decimal(str(ot.max_hours_per_month or 0)),
                                requires_approval=bool(ot.requires_approval), **common, **sc)
                            out(f'   أوفر تايم ({sc["scope"]}): × {ot.multiplier} | أقل مدة {ot.min_minutes} دقيقة في اليوم')

                after = _nets()
                diffs = [(before[k][0], before[k][2], after[k][2]) for k in before
                         if abs(float(before[k][2]) - float(after[k][2])) > 0.01]
                out(f'\nمراجعة مرتبات {month}/{year}: {len(before)} موظف')
                if diffs:
                    for code, b, a in diffs:
                        out(self.style.ERROR(f'   ✘ {code}: قبل {b} — بعد {a}'))
                    out(self.style.ERROR('في أرقام اتغيرت — مفيش حاجة اتحفظت.'))
                    raise _Undo
                out(self.style.SUCCESS('   ✔ ولا صافي مرتب اتغير'))
                if not opts['apply']:
                    out('\nده كان تجربة بس. للحفظ: python manage.py convert_policy_rules --apply')
                    raise _Undo
        except _Undo:
            if opts['apply'] and diffs:
                raise SystemExit(1)
            return
        out(self.style.SUCCESS('\n✔ القواعد اتنقلت واتحفظت'))
