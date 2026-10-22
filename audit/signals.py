"""
تسجيل أي إضافة أو تعديل أو حذف في الجداول المهمة: مين، إمتى، ومنين، وقبل وبعد لكل حقل.

- قبل الحفظ بنقرا النسخة القديمة من قاعدة البيانات، وبعد الحفظ بنقارن.
- التسجيل عمره ما يوقّف الحفظ الأصلي: أي خطأ فيه بيتبلع جوه savepoint منفصل.
- التحديثات الجماعية (QuerySet.update) مابتعديش على هنا، فالأماكن المهمة منها
  (الموافقة على الإجازة، قرار الطلب) بتسجّل بنفسها عن طريق log_change.
"""
import datetime
import decimal
import json
import logging

from django.apps import apps
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save

logger = logging.getLogger(__name__)

# الجداول اللي بتتسجل (التتبع اللحظي والإشعارات والجداول المحسوبة مش منهم عشان الحجم)
TRACKED = [
    'accounts.User', 'accounts.CustomRole', 'accounts.RolePermission', 'accounts.UserRole',
    'accounts.UserPermissionOverride', 'accounts.CompanyAnnouncement',
    'companies.Company', 'companies.Branch', 'companies.Department', 'companies.WorkCharter',
    'companies.CompanyPolicy',
    'employees.JobTitle', 'employees.Employee', 'employees.EmployeeDocument', 'employees.Deduction',
    'leaves.LeavePolicy', 'leaves.LeaveType', 'leaves.LeaveBalance', 'leaves.LeaveBalanceAdjustment',
    'leaves.LeaveRequest', 'leaves.LeaveRecallRequest', 'leaves.OfficialHoliday', 'leaves.OfficialHolidayRule',
    'leaves.ManagerSubstitution',
    'requests_app.RequestType', 'requests_app.EmployeeRequest', 'requests_app.PermissionPolicy',
    'attendance.Shift', 'attendance.AttendancePolicy', 'attendance.LateRule', 'attendance.AbsenceRule',
    'attendance.OvertimeRule', 'attendance.ShiftAssignment', 'attendance.EmployeeShift', 'attendance.ShiftOverride',
    'attendance.ShiftRotation', 'attendance.Attendance', 'attendance.LocationCheckIn',
    'attendance.DisciplinaryRule', 'attendance.DisciplinaryAction', 'attendance.Mission', 'attendance.MissionAssignment',
    'attendance.CompanyWorkPolicy', 'attendance.PayrollAllowance', 'attendance.PayrollDeduction',
    'attendance.CompanyAllowancePolicy', 'attendance.CompanyDeductionPolicy', 'attendance.CompanyBonusPolicy',
    'attendance.CompanyInsurancePolicy', 'attendance.CompanyPayrollCyclePolicy', 'attendance.PenaltyRule',
    'attendance.BonusRule', 'attendance.AllowanceRule', 'attendance.LeaveRule', 'attendance.ManualPenalty',
    'attendance.ManualBonus', 'attendance.ManualAllowance', 'attendance.TaxPolicy', 'attendance.EndOfServicePolicy',
    'attendance.PayrollSettings', 'attendance.PayrollRun', 'attendance.EmployeeWorkLocation',
    'subscriptions.SubscriptionPlan', 'subscriptions.CompanySubscription',
]

# حقول مالهاش لازمة في السجل (بتتغير لوحدها)
SKIP_FIELDS = {'updated_at', 'modified_at', 'last_login', 'last_activity', 'date_joined'}
SECRET_FIELDS = {'password'}

MAX_TEXT = 300


# ─────────────────────────── مين وإمتى ومنين ───────────────────────────

def _request_info():
    from audit.middleware import current_request
    req = current_request()
    if req is None:
        return None, {'source': 'system', 'ip': '', 'path': ''}
    user = getattr(req, '_audit_user', False)
    if user is False:
        user = None
        u = getattr(req, 'user', None)
        if u is not None and getattr(u, 'is_authenticated', False):
            user = u
        else:
            try:
                from core.middleware import _user_from_auth_header
                user = _user_from_auth_header(req)
            except Exception:
                user = None
        req._audit_user = user
    path = req.path or ''
    agent = req.META.get('HTTP_USER_AGENT', '').lower()
    if path.startswith('/admin'):
        source = 'admin'
    elif 'dart' in agent or 'okhttp' in agent:
        source = 'mobile'
    elif '/api/' in path:
        source = 'web'
    else:
        source = 'old_site'
    ip = (req.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
          or req.META.get('REMOTE_ADDR', ''))
    return user, {'source': source, 'ip': ip[:64], 'path': path[:255]}


def _user_fields(user):
    if not user:
        return {'user_id': None, 'username': '', 'user_name': '', 'user_role': ''}
    name = ''
    try:
        name = user.get_full_name() or ''
    except Exception:
        pass
    return {
        'user_id': user.pk,
        'username': (getattr(user, 'username', '') or '')[:150],
        'user_name': name[:255],
        'user_role': (getattr(user, 'role', '') or '')[:50],
    }


# ─────────────────────────── الموظف والشركة ───────────────────────────

def _employee_of(instance):
    from employees.models import Employee
    if isinstance(instance, Employee):
        return instance.pk, instance
    if instance.__class__.__name__ == 'User' and instance._meta.app_label == 'accounts':
        emp = Employee._base_manager.filter(user_id=instance.pk).first()
        return (emp.pk, emp) if emp else (None, None)
    eid = getattr(instance, 'employee_id', None)
    if eid:
        return eid, None
    return None, None


def _employee_name(eid, emp=None):
    if not eid:
        return ''
    try:
        if emp is None:
            from employees.models import Employee
            emp = Employee._base_manager.filter(pk=eid).only(
                'first_name_ar', 'last_name_ar', 'employee_code').first()
        if not emp:
            return ''
        name = ' '.join(p for p in [emp.first_name_ar or '', emp.last_name_ar or ''] if p).strip()
        return (name or emp.employee_code or '')[:255]
    except Exception:
        return ''


def _company_of(instance, user):
    if instance._meta.label == 'companies.Company':
        return instance.pk
    cid = getattr(instance, 'company_id', None)
    if cid:
        return cid
    return getattr(user, 'company_id', None) if user else None


# ─────────────────────────── القيم ───────────────────────────

def _fields(model):
    return [f for f in model._meta.concrete_fields
            if f.name not in SKIP_FIELDS and not f.primary_key]


def _fmt(field, value):
    if value is None or value == '':
        return ''
    if field.choices:
        label = dict(field.flatchoices).get(value)
        if label is not None:
            return str(label)
    if isinstance(value, bool):
        return 'نعم' if value else 'لا'
    if isinstance(value, float):
        value = decimal.Decimal(str(value))
    if isinstance(value, decimal.Decimal):
        return format(value.normalize(), 'f') if value == value.to_integral() else str(value.normalize())
    if isinstance(value, datetime.datetime):
        from django.utils import timezone
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime('%Y-%m-%d %H:%M')
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, default=str)
    else:
        text = str(value)
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + '…'


def _fk_text(field, value):
    """الحقل اللي بيشاور على جدول تاني: بنكتب اسمه مش رقمه بس"""
    if value in (None, ''):
        return ''
    try:
        obj = field.related_model._base_manager.filter(pk=value).first()
        return f'{obj} (#{value})' if obj is not None else f'#{value}'
    except Exception:
        return f'#{value}'


def _label(field):
    return str(field.verbose_name or field.name)[:150]


def _diff(model, old, instance):
    changes = []
    for f in _fields(model):
        new_v = getattr(instance, f.attname, None)
        old_v = old.get(f.attname)
        if _norm(old_v) == _norm(new_v):
            continue
        if f.name in SECRET_FIELDS:
            changes.append({'field': f.name, 'label': 'كلمة السر', 'old': '***', 'new': 'اتغيرت'})
            continue
        if f.is_relation:
            changes.append({'field': f.name, 'label': _label(f), 'old': _fk_text(f, old_v), 'new': _fk_text(f, new_v)})
        else:
            changes.append({'field': f.name, 'label': _label(f), 'old': _fmt(f, old_v), 'new': _fmt(f, new_v)})
    return changes


def _norm(v):
    if isinstance(v, decimal.Decimal):
        return v.normalize()
    if isinstance(v, float):
        return decimal.Decimal(str(v)).normalize()
    if isinstance(v, datetime.datetime):
        return v.replace(microsecond=0)
    return v


def _snapshot(model, instance):
    out = []
    for f in _fields(model):
        v = getattr(instance, f.attname, None)
        if v in (None, '', False) or f.name in SECRET_FIELDS:
            continue
        out.append({'field': f.name, 'label': _label(f), 'old': '',
                    'new': _fk_text(f, v) if f.is_relation else _fmt(f, v)})
    return out[:60]


# ─────────────────────────── الكتابة ───────────────────────────

def write_log(instance, action, changes, note=''):
    from audit.models import AuditLog
    try:
        user, info = _request_info()
        eid, emp = _employee_of(instance)
        try:
            repr_ = str(instance)[:255]
        except Exception:
            repr_ = f'#{instance.pk}'
        with transaction.atomic():
            AuditLog.objects.create(
                company_id=_company_of(instance, user),
                action=action,
                model=instance._meta.label[:100],
                model_label=str(instance._meta.verbose_name)[:150],
                object_id=str(instance.pk or '')[:64],
                object_repr=repr_,
                employee_id=eid,
                employee_name=_employee_name(eid, emp),
                changes=changes,
                note=note[:500],
                **_user_fields(user), **info,
            )
    except Exception as e:  # التسجيل عمره ما يوقّف الشغل الأصلي
        logger.warning('audit log failed: %s', e)


def log_change(instance, changes, action='update', note=''):
    """للأماكن اللي بتحدّث بـ QuerySet.update (مابتعديش على الإشارات)"""
    write_log(instance, action, changes, note)


def log_event(action, user=None, note='', employee_id=None, company_id=None, model='', object_id=''):
    """حدث من غير جدول معيّن (زي تسجيل الدخول)"""
    from audit.models import AuditLog
    try:
        req_user, info = _request_info()
        user = user or req_user
        with transaction.atomic():
            AuditLog.objects.create(
                company_id=company_id or (getattr(user, 'company_id', None) if user else None),
                action=action, model=model[:100], object_id=str(object_id)[:64],
                employee_id=employee_id, employee_name=_employee_name(employee_id),
                note=note[:500], changes=[], **_user_fields(user), **info,
            )
    except Exception as e:
        logger.warning('audit event failed: %s', e)


# ─────────────────────────── الإشارات ───────────────────────────

def _pre_save(sender, instance, raw=False, **kwargs):
    if raw or not instance.pk:
        instance._audit_old = None
        return
    try:
        names = [f.attname for f in _fields(sender)]
        instance._audit_old = sender._base_manager.filter(pk=instance.pk).values(*names).first()
    except Exception:
        instance._audit_old = None


def _post_save(sender, instance, created=False, raw=False, **kwargs):
    if raw:
        return
    old = getattr(instance, '_audit_old', None)
    instance._audit_old = None
    if created or old is None:
        write_log(instance, 'create', _snapshot(sender, instance))
        return
    changes = _diff(sender, old, instance)
    if changes:
        write_log(instance, 'update', changes)


def _post_delete(sender, instance, **kwargs):
    write_log(instance, 'delete', _snapshot(sender, instance))


_connected = False


def connect_all():
    global _connected
    if _connected:
        return
    for label in TRACKED:
        try:
            model = apps.get_model(label)
        except LookupError:
            continue
        uid = f'audit_{label}'
        pre_save.connect(_pre_save, sender=model, dispatch_uid=uid + '_pre')
        post_save.connect(_post_save, sender=model, dispatch_uid=uid + '_post')
        post_delete.connect(_post_delete, sender=model, dispatch_uid=uid + '_del')
    _connected = True
