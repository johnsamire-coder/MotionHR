from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0008_add_stealth_tracking_to_policy"),
    ]

    operations = [
        migrations.AddField(
            model_name="companypolicy",
            name="leave_requires_substitute",
            field=models.BooleanField(default=False, verbose_name="الإجازة تحتاج بديل"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="substitute_same_department_only",
            field=models.BooleanField(default=False, verbose_name="البديل من نفس القسم فقط"),
        ),
    ]
