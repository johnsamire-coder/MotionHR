"""
بيعمل جداول أجهزة البصمة لو مش موجودة (ومابيلمسش أي جدول تاني).
  python manage.py biometric_setup
"""
from django.core.management.base import BaseCommand
from django.db import connection

from biometric.models import BiometricDevice, BiometricPunch, BiometricUserMap


class Command(BaseCommand):
    help = 'إنشاء جداول أجهزة البصمة لو مش موجودة'

    def handle(self, *args, **options):
        existing = set(connection.introspection.table_names())
        made = []
        with connection.schema_editor() as editor:
            for model in (BiometricDevice, BiometricUserMap, BiometricPunch):
                if model._meta.db_table not in existing:
                    editor.create_model(model)
                    made.append(model._meta.db_table)
        self.stdout.write(self.style.SUCCESS(
            'اتعملت جداول البصمة: ' + ', '.join(made)) if made else 'جداول البصمة موجودة بالفعل.')
