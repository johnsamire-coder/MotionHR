from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0015_charter_digital_signature'),
        ('accounts', '0006_alter_pushsubscription_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrialSignupLead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=200, verbose_name='اسم الشركة')),
                ('contact_name', models.CharField(max_length=200, verbose_name='اسم المسؤول')),
                ('phone', models.CharField(max_length=30, verbose_name='رقم الموبايل')),
                ('whatsapp', models.CharField(max_length=30, verbose_name='رقم الواتساب')),
                ('email', models.EmailField(max_length=254, verbose_name='البريد الإلكتروني')),
                ('employees_count', models.PositiveIntegerField(default=1, verbose_name='عدد الموظفين المتوقع')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='المدينة')),
                ('industry', models.CharField(blank=True, max_length=150, verbose_name='نوع النشاط')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات العميل')),
                ('source', models.CharField(blank=True, default='free_trial', max_length=100, verbose_name='مصدر التسجيل')),
                ('status', models.CharField(
                    choices=[
                        ('new', 'جديد'),
                        ('activated', 'تم التفعيل'),
                        ('contacted', 'تم التواصل'),
                        ('converted', 'تم التحويل لعميل'),
                        ('expired', 'انتهت التجربة'),
                        ('rejected', 'مرفوض'),
                    ],
                    default='new',
                    max_length=20,
                    verbose_name='حالة الطلب'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التسجيل')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trial_start_date', models.DateField(blank=True, null=True, verbose_name='بداية التجربة')),
                ('trial_end_date', models.DateField(blank=True, null=True, verbose_name='نهاية التجربة')),
                ('generated_username', models.CharField(blank=True, max_length=100, verbose_name='اسم المستخدم المولّد')),
                ('generated_password', models.CharField(blank=True, max_length=100, verbose_name='كلمة المرور المولّدة')),
                ('sales_notes', models.TextField(blank=True, verbose_name='ملاحظات فريق المبيعات')),
                ('created_company', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='trial_leads',
                    to='companies.company',
                    verbose_name='الشركة المنشأة'
                )),
                ('created_user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='trial_leads',
                    to='accounts.user',
                    verbose_name='الحساب المنشأ'
                )),
            ],
            options={
                'verbose_name': 'طلب تجربة مجانية',
                'verbose_name_plural': 'طلبات التجربة المجانية',
                'ordering': ['-created_at'],
            },
        ),
    ]
