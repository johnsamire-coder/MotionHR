from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyLoginSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('login_by_email',         models.BooleanField(default=True,
                                            verbose_name='الدخول بالإيميل')),
                ('login_by_employee_code', models.BooleanField(default=True,
                                            verbose_name='الدخول بالرقم الوظيفي')),
                ('login_by_phone',         models.BooleanField(default=False,
                                            verbose_name='الدخول بالموبايل')),
                ('login_by_username',      models.BooleanField(default=True,
                                            verbose_name='الدخول باسم المستخدم')),
                ('min_password_length',    models.PositiveSmallIntegerField(default=8,
                                            verbose_name='الحد الأدنى لطول كلمة المرور')),
                ('require_uppercase',      models.BooleanField(default=False,
                                            verbose_name='إجبار حروف كبيرة')),
                ('require_numbers',        models.BooleanField(default=False,
                                            verbose_name='إجبار أرقام')),
                ('require_symbols',        models.BooleanField(default=False,
                                            verbose_name='إجبار رموز')),
                ('password_expiry_days',   models.PositiveSmallIntegerField(default=0,
                                            verbose_name='مدة انتهاء كلمة المرور (يوم)')),
                ('max_login_attempts',     models.PositiveSmallIntegerField(default=5,
                                            verbose_name='أقصى محاولات دخول')),
                ('lockout_duration_minutes', models.PositiveSmallIntegerField(default=15,
                                              verbose_name='مدة القفل (دقيقة)')),
                ('force_change_on_first_login', models.BooleanField(default=True,
                                                 verbose_name='إجبار تغيير كلمة المرور عند أول دخول')),
                ('company', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='login_settings',
                    to='companies.company',
                    verbose_name='الشركة'
                )),
            ],
            options={
                'verbose_name':        'إعدادات تسجيل الدخول',
                'verbose_name_plural': 'إعدادات تسجيل الدخول',
            },
        ),
    ]
