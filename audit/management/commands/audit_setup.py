"""
بيعمل جدول سجل التعديلات لو مش موجود (ومابيلمسش أي جدول تاني).
  python manage.py audit_setup
"""
from django.core.management.base import BaseCommand
from django.db import connection

from audit.models import AuditLog


class Command(BaseCommand):
    help = 'إنشاء جدول سجل التعديلات لو مش موجود'

    def handle(self, *args, **options):
        if AuditLog._meta.db_table in connection.introspection.table_names():
            self.stdout.write('جدول سجل التعديلات موجود بالفعل.')
            return
        with connection.schema_editor() as editor:
            editor.create_model(AuditLog)
        self.stdout.write(self.style.SUCCESS('اتعمل جدول سجل التعديلات.'))
