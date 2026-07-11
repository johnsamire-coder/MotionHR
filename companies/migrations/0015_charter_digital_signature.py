from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0014_department_hierarchy'),
        ('employees', '0006_job_hierarchy_models'),
        ('accounts', '0006_alter_pushsubscription_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharterVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.PositiveIntegerField(default=1, verbose_name='رقم الإصدار')),
                ('content_snapshot', models.TextField(verbose_name='محتوى الإصدار')),
                ('changes_summary', models.TextField(blank=True, verbose_name='ملخص التغييرات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('charter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='companies.workcharter', verbose_name='الميثاق')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user', verbose_name='أنشأ بواسطة')),
            ],
            options={
                'verbose_name': 'إصدار ميثاق',
                'verbose_name_plural': 'إصدارات الميثاق',
                'ordering': ['-version_number'],
                'unique_together': {('charter', 'version_number')},
            },
        ),
        migrations.CreateModel(
            name='CharterDigitalSignature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name_typed', models.CharField(max_length=200, verbose_name='الاسم الكامل كما كتبه الموظف')),
                ('national_id_typed', models.CharField(blank=True, max_length=30, verbose_name='الرقم القومي كما كتبه الموظف')),
                ('agreement_text', models.TextField(default='أقر بأنني قرأت وفهمت ميثاق العمل وأوافق على الالتزام بكل بنوده.', verbose_name='نص الموافقة')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='عنوان IP')),
                ('user_agent', models.TextField(blank=True, verbose_name='متصفح الموظف')),
                ('signed_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التوقيع')),
                ('is_valid', models.BooleanField(default=True, verbose_name='توقيع صالح')),
                ('invalidated_reason', models.TextField(blank=True, verbose_name='سبب الإلغاء')),
                ('charter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='digital_signatures', to='companies.workcharter', verbose_name='الميثاق')),
                ('charter_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signatures', to='companies.charterversion', verbose_name='إصدار الميثاق')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charter_signatures', to='companies.company', verbose_name='الشركة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charter_signatures', to='employees.employee', verbose_name='الموظف')),
            ],
            options={
                'verbose_name': 'توقيع رقمي على الميثاق',
                'verbose_name_plural': 'التوقيعات الرقمية',
                'ordering': ['-signed_at'],
            },
        ),
        migrations.CreateModel(
            name='CharterNotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('quarterly_reminder', 'تذكير ربع سنوي'), ('new_employee', 'موظف جديد'), ('charter_updated', 'تحديث الميثاق')], max_length=30, verbose_name='نوع الإشعار')),
                ('sent_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ القراءة')),
                ('charter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_logs', to='companies.workcharter', verbose_name='الميثاق')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charter_notification_logs', to='companies.company', verbose_name='الشركة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charter_notification_logs', to='employees.employee', verbose_name='الموظف')),
            ],
            options={
                'verbose_name': 'سجل إشعار ميثاق',
                'verbose_name_plural': 'سجلات إشعارات الميثاق',
                'ordering': ['-sent_at'],
            },
        ),
    ]
