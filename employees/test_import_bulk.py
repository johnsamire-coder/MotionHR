"""
اختبار استيراد الموظفين من الإكسيل (124 و125):
صف "جديد" لشركة عندها أنواع إجازات، وبعده صف "تحديث" بيغيّر المرتب.

التشغيل:
  python manage.py test employees.test_import_bulk --settings=motionhr.settings_test
"""
import os
import shutil
import tempfile
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from openpyxl import Workbook

from companies.models import Branch, Company, Department
from employees.models import Employee, JobTitle
from leaves.models import LeaveType


class BulkImportTests(TestCase):
    def setUp(self):
        self.co = Company.objects.create(name_ar='شركة الاستيراد', name_en='Imp')
        Branch.objects.create(company=self.co, name_ar='الرئيسي', name_en='Main')
        Department.objects.create(company=self.co, name_ar='المبيعات', name_en='Sales')
        JobTitle._base_manager.create(company=self.co, name_ar='مندوب', name_en='Rep')
        LeaveType._base_manager.create(company=self.co, name='سنوي', category='annual', days_allowed=21)
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def sheet(self, rows):
        wb = Workbook()
        ws = wb.active
        ws.title = 'الموظفين'
        ws.append(['بيانات'])          # 3 صفوف عناوين زي القالب
        ws.append(['labels'])
        ws.append(['keys'])
        for r in rows:
            ws.append(r)
        path = os.path.join(self.tmp, 'emps.xlsx')
        wb.save(path)
        return path

    def run_import(self, path):
        out = StringIO()
        call_command('import_employees_bulk', file=path, company_id=self.co.id, stdout=out)
        return out.getvalue()

    def test_new_then_update(self):
        new = ['جديد', 'أحمد محمد علي', 'Ahmed Mohamed Ali', '29501011234567', '01012345678',
               '1995-01-01', '2026-01-01', 'الرئيسي', 'المبيعات', 'مندوب', 'مكتبي', 7000, '']
        out = self.run_import(self.sheet([new]))
        emp = Employee._base_manager.filter(company=self.co, national_id='29501011234567').first()
        self.assertIsNotNone(emp, out)
        self.assertEqual(emp.basic_salary, Decimal('7000'))

        upd = ['تحديث', '', '', '29501011234567', '', '', '', '', '', '', '', 8500, '']
        out = self.run_import(self.sheet([upd]))
        emp.refresh_from_db()
        self.assertEqual(emp.basic_salary, Decimal('8500'), out)
