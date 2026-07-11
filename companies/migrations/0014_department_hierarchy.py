from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0013_alter_notificationpreference_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentHierarchy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('child_department', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='parent_link', to='companies.department', verbose_name='الإدارة الفرعية')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_hierarchies', to='companies.company', verbose_name='الشركة')),
                ('parent_department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='child_links', to='companies.department', verbose_name='الإدارة الأم')),
            ],
            options={
                'verbose_name': 'ربط هيكل إداري',
                'verbose_name_plural': 'الهيكل الإداري',
                'ordering': ['parent_department_id', 'child_department_id', 'id'],
                'unique_together': {('company', 'child_department')},
            },
        ),
    ]
