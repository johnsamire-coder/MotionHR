from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "0004_employee_attendance_mode_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="stealth_tracking_enabled",
            field=models.BooleanField(default=False, verbose_name="التتبع الصامت مفعل"),
        ),
    ]
