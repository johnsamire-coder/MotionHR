# صافي مرتب كل موظف بالكود الحالي — قراية بس.
# بيتشغل: SNAP_OUT=/path SNAP_MONTHS=2026-10,2026-9 python manage.py shell < net_snapshot.py
# حساب المرتب بيكتب حاجات جانبية (تسويات الشيفت المرن ورصيد الأذونات)، فكله جوه transaction بترجع
# في الآخر، والإشعارات مقفولة، فمفيش أي تغيير على قاعدة البيانات ولا رسايل بتتبعت.
import json
import os

from django.db import transaction

import accounts.fcm_service as _fcm
_fcm.send_notification_to_user = lambda *a, **k: {'success': False}
try:
    import attendance.fcm_logic as _fl
    _fl.send_fcm_notification = lambda *a, **k: False
except Exception:
    pass

from employees.models import Employee
from attendance.payroll_rules import calculate_effective_payroll


class _Rollback(Exception):
    pass


months = [tuple(int(x) for x in m.split('-')) for m in os.environ['SNAP_MONTHS'].split(',')]
out = {}
try:
    with transaction.atomic():
        emps = Employee._base_manager.exclude(status__in=('terminated', 'resigned', 'retired')).select_related('company')
        for e in emps.order_by('company_id', 'employee_code'):
            row = out.setdefault(str(e.company_id), {'company': getattr(e.company, 'name_ar', '') or '', 'emps': {}})
            nets = {}
            for y, m in months:
                try:
                    with transaction.atomic():
                        nets[f'{y}-{m:02d}'] = round(float(calculate_effective_payroll(e, y, m)['net_salary'] or 0), 2)
                except Exception as ex:
                    nets[f'{y}-{m:02d}'] = f'خطأ: {str(ex)[:60]}'
            row['emps'][str(e.id)] = {'name': f'{e.first_name_ar or ""} {e.last_name_ar or ""}'.strip(),
                                      'code': e.employee_code or '', 'net': nets}
        raise _Rollback()
except _Rollback:
    pass

with open(os.environ['SNAP_OUT'], 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
print('SNAPSHOT_OK', sum(len(c['emps']) for c in out.values()))
