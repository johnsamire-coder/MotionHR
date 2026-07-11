from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0015_charter_digital_signature'),
        ('employees', '0006_job_hierarchy_models'),
        ('accounts', '0006_alter_pushsubscription_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('id_card', 'بطاقة الهوية / الرقم القومي'), ('employment_contract', 'عقد التعيين'), ('contract_renewal', 'عقد تجديد'), ('contract_amendment', 'ملحق عقد / تعديل'), ('qualification', 'شهادة المؤهل الدراسي'), ('experience_cert', 'شهادة الخبرة'), ('personal_photo', 'صورة شخصية'), ('birth_cert', 'شهادة الميلاد'), ('criminal_record', 'فيش وتشبيه'), ('medical_report', 'تقرير طبي'), ('medical_insurance', 'بطاقة التأمين الصحي'), ('social_insurance', 'مستند التأمينات الاجتماعية'), ('promotion_letter', 'خطاب ترقية'), ('transfer_letter', 'خطاب نقل'), ('salary_adjustment', 'خطاب تعديل راتب'), ('warning_letter', 'إنذار'), ('disciplinary', 'إجراء تأديبي'), ('resignation', 'استقالة'), ('termination', 'إنهاء خدمة'), ('clearance', 'إخلاء طرف'), ('leave_request', 'طلب إجازة مرفق'), ('marriage_cert', 'عقد زواج'), ('military_cert', 'شهادة الخدمة العسكرية / الإعفاء'), ('driving_license', 'رخصة قيادة'), ('passport', 'جواز سفر'), ('training_cert', 'شهادة تدريب'), ('performance_review', 'تقييم أداء'), ('other', 'أخرى')], default='other', max_length=30, verbose_name='تصنيف المستند')),
                ('custom_name', models.CharField(blank=True, help_text='يمكن ترك هذا الحقل فارغًا لو اخترت تصنيف ثابت', max_length=200, verbose_name='اسم المستند (لو أخرى أو اسم مخصص)')),
                ('related_event', models.CharField(blank=True, choices=[('hiring', 'التعيين'), ('contract_renewal', 'تجديد العقد'), ('promotion', 'ترقية'), ('transfer', 'نقل'), ('salary_change', 'تعديل راتب'), ('leave', 'إجازة'), ('medical', 'حالة طبية'), ('warning', 'إنذار / تأديب'), ('resignation', 'استقالة'), ('termination', 'إنهاء خدمة'), ('training', 'تدريب'), ('personal', 'شخصي'), ('other', 'أخرى')], max_length=30, verbose_name='الحدث المرتبط')),
                ('event_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الحدث')),
                ('event_notes', models.TextField(blank=True, verbose_name='ملاحظات الحدث')),
                ('file', models.FileField(upload_to='employee_folders/%Y/%m/', verbose_name='الملف')),
                ('file_size_kb', models.PositiveIntegerField(default=0, verbose_name='حجم الملف (KB)')),
                ('issue_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الإصدار')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='تاريخ الانتهاء')),
                ('is_confidential', models.BooleanField(default=False, verbose_name='سري')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_folder_docs', to='companies.company', verbose_name='الشركة')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='folder_documents', to='employees.employee', verbose_name='الموظف')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user', verbose_name='رفع بواسطة')),
            ],
            options={
                'verbose_name': 'مستند في ملف الموظف',
                'verbose_name_plural': 'مستندات ملفات الموظفين',
                'ordering': ['-created_at'],
            },
        ),
    ]
