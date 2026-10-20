"""
إيقاف / تشغيل شركة (مابيمسحش أي بيانات):

  ./venv/bin/python manage.py company_access 61 status
  ./venv/bin/python manage.py company_access 61 suspend
  ./venv/bin/python manage.py company_access 61 resume

  # مرة واحدة: يرجّع حسابات الموظفين النشطين اللي اتقفلت يدوي، والشركة لازم تكون موقوفة
  ./venv/bin/python manage.py company_access 61 reactivate-accounts
"""
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from companies.models import Company
from employees.models import Employee

logger = logging.getLogger(__name__)


def set_company_active(company, active):
    """الإيقاف والتشغيل: خانة is_active بس — مفيش أي بيانات بتتمسح"""
    Company._base_manager.filter(pk=company.pk).update(is_active=active)
    company.is_active = active
    logger.warning('company_access: company %s (%s) is_active=%s', company.pk, company.name_ar, active)


class Command(BaseCommand):
    help = 'إيقاف أو تشغيل شركة من غير ما أي بيانات تتمسح'

    def add_arguments(self, parser):
        parser.add_argument('company_id', type=int)
        parser.add_argument('action', choices=['status', 'suspend', 'resume', 'reactivate-accounts'])

    def handle(self, company_id, action, **options):
        company = Company._base_manager.filter(pk=company_id).first()
        if not company:
            raise CommandError(f'مفيش شركة رقم {company_id}')

        User = get_user_model()
        employees = Employee._base_manager.filter(company=company, status='active')
        self.stdout.write(f'الشركة: {company.id} — {company.name_ar} / {company.name_en}')
        self.stdout.write(f'موظفين نشطين: {employees.count()} — حسابات مستخدمين: {User._base_manager.filter(company=company).count()}')

        if action == 'suspend':
            set_company_active(company, False)
        elif action == 'resume':
            set_company_active(company, True)
        elif action == 'reactivate-accounts':
            if company.is_active:
                raise CommandError('الشركة شغالة — أوقفها الأول (suspend) عشان محدش يدخل قبل ما تقرر')
            users = User._base_manager.filter(
                pk__in=employees.exclude(user=None).values('user_id'), is_active=False,
            ).exclude(role='super_admin')
            n = users.update(is_active=True)
            self.stdout.write(f'رجّعت {n} حساب نشط (لموظفين حالتهم "نشط" بس).')

        state = 'شغالة ✅' if company.is_active else 'موقوفة ⛔ (محدش من موظفينها يقدر يدخل)'
        self.stdout.write(self.style.SUCCESS(f'حالة الشركة دلوقتي: {state}'))
