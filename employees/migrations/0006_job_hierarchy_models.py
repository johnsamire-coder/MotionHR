from django.db import migrations, models
import django.db.models.deletion


def seed_default_job_levels(apps, schema_editor):
    Company = apps.get_model('companies', 'Company')
    JobHierarchyLevel = apps.get_model('employees', 'JobHierarchyLevel')

    defaults = [
        (1, 'صاحب الشركة', 'Company Owner'),
        (2, 'مدير عام', 'General Manager'),
        (3, 'مدير', 'Manager'),
        (4, 'مشرف', 'Supervisor'),
        (5, 'أخصائي', 'Specialist'),
        (6, 'موظف', 'Employee'),
        (7, 'عامل', 'Worker'),
    ]

    for company in Company.objects.all():
        for sort_order, name_ar, name_en in defaults:
            JobHierarchyLevel.objects.get_or_create(
                company_id=company.id,
                sort_order=sort_order,
                defaults={
                    'name_ar': name_ar,
                    'name_en': name_en,
                    'is_active': True,
                    'description': '',
                }
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0013_alter_notificationpreference_id'),
        ('employees', '0005_add_stealth_tracking_to_employee'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobHierarchyLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_ar', models.CharField(max_length=150, verbose_name='الاسم بالعربي')),
                ('name_en', models.CharField(blank=True, max_length=150, verbose_name='الاسم بالإنجليزي')),
                ('sort_order', models.PositiveIntegerField(default=1, verbose_name='الترتيب الهرمي')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_hierarchy_levels', to='companies.company', verbose_name='الشركة')),
            ],
            options={
                'verbose_name': 'مستوى وظيفي',
                'verbose_name_plural': 'المستويات الوظيفية',
                'ordering': ['sort_order', 'id'],
                'unique_together': {('company', 'sort_order'), ('company', 'name_ar')},
            },
        ),
        migrations.CreateModel(
            name='DepartmentJobTitleRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('same_department_only', models.BooleanField(default=True, verbose_name='المدير من نفس الإدارة فقط')),
                ('allow_higher_parent_fallback', models.BooleanField(default=True, verbose_name='السماح ببدائل أعلى لو المسمى الأب غير موجود')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_job_title_rules', to='companies.company', verbose_name='الشركة')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_title_rules', to='companies.department', verbose_name='الإدارة')),
                ('job_title', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hierarchy_rules', to='employees.jobtitle', verbose_name='المسمى الوظيفي')),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_title_rules', to='employees.jobhierarchylevel', verbose_name='المستوى الوظيفي')),
                ('parent_job_title', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_hierarchy_rules', to='employees.jobtitle', verbose_name='المسمى الأعلى المباشر')),
            ],
            options={
                'verbose_name': 'قاعدة ربط وظيفي',
                'verbose_name_plural': 'قواعد الربط الوظيفي',
                'ordering': ['department_id', 'level__sort_order', 'job_title_id', 'id'],
                'unique_together': {('company', 'department', 'job_title')},
            },
        ),
        migrations.RunPython(seed_default_job_levels, noop_reverse),
    ]
