"""
اختبارات دفعة 14: تقرير الزيارات الميدانية

التشغيل:
  python manage.py test attendance.test_group14_reports --settings=motionhr.settings_test
"""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from attendance.test_action_scope import ScopeBase

M = '/attendance/api/mobile/'


class FieldVisitsReportTests(ScopeBase):
    def visit(self, emp, minutes=90, **kw):
        from attendance.models import LocationCheckIn
        start = timezone.now() - timedelta(hours=3)
        return LocationCheckIn._base_manager.create(
            company=emp.company, employee=emp, visit_type='client_visit', location_name='عميل 1',
            arrival_time=start, arrival_latitude=Decimal('30.0444'), arrival_longitude=Decimal('31.2357'),
            arrival_address='وسط البلد', departure_time=start + timedelta(minutes=minutes) if minutes else None,
            departure_latitude=Decimal('30.0450') if minutes else None,
            departure_longitude=Decimal('31.2357') if minutes else None,
            status='completed' if minutes else 'in_progress', **kw)

    def test_duration_distance_and_tracking(self):
        from attendance.models import LocationLog
        v = self.visit(self.team_a, minutes=90)
        for i in range(3):   # 3 نقط جوه الزيارة ونقطة برة
            LocationLog._base_manager.create(company=self.a, employee=self.team_a, latitude=30.0444, longitude=31.2357,
                                             timestamp=v.arrival_time + timedelta(minutes=20 * (i + 1)))
        LocationLog._base_manager.create(company=self.a, employee=self.team_a, latitude=30.1, longitude=31.3,
                                         timestamp=v.arrival_time + timedelta(minutes=200))
        r = self.api(self.hr_a).get(f'{M}manager/reports/field-visits/')
        self.assertEqual(r.status_code, 200, r.data)
        row = [x for x in r.data['visits'] if x['id'] == v.id][0]
        self.assertEqual(row['duration_minutes'], 90)
        self.assertEqual(row['tracking_points'], 3)
        self.assertTrue(60 <= row['distance_arrival_departure_m'] <= 70)   # 0.0006 درجة عرض ≈ 67 متر
        self.assertEqual(r.data['per_employee'][0]['total_minutes'], 90)

        d = self.api(self.hr_a).get(f'{M}manager/reports/field-visits/{v.id}/')
        self.assertEqual(len(d.data['tracking']), 3)

    def test_ongoing_visit_counts_until_now(self):
        v = self.visit(self.team_a, minutes=None)
        r = self.api(self.hr_a).get(f'{M}manager/reports/field-visits/')
        row = [x for x in r.data['visits'] if x['id'] == v.id][0]
        self.assertTrue(row['is_ongoing'])
        self.assertGreaterEqual(row['duration_minutes'], 179)

    def test_manager_sees_only_team(self):
        mine = self.visit(self.team_a)
        other = self.visit(self.other_a)
        r = self.api(self.mgr_a).get(f'{M}manager/reports/field-visits/')
        ids = [x['id'] for x in r.data['visits']]
        self.assertIn(mine.id, ids)
        self.assertNotIn(other.id, ids)
        self.assertEqual(self.api(self.mgr_a).get(f'{M}manager/reports/field-visits/{other.id}/').status_code, 404)

    def test_other_company_and_employee_blocked(self):
        b = self.visit(self.emp_b)
        r = self.api(self.hr_a).get(f'{M}manager/reports/field-visits/')
        self.assertNotIn(b.id, [x['id'] for x in r.data['visits']])
        self.assertEqual(self.api(self.team_a).get(f'{M}manager/reports/field-visits/').status_code, 403)

    def test_excel_export(self):
        self.visit(self.team_a)
        r = self.api(self.hr_a).get(f'{M}manager/reports/field-visits/?export=xlsx')
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheet', r['Content-Type'])
