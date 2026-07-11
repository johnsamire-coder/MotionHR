from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0007_companypolicy_leave_day_checkin_mode_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_enabled",
            field=models.BooleanField(default=False, verbose_name="تفعيل التتبع الصامت"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_alert_after_minutes",
            field=models.PositiveSmallIntegerField(default=15, verbose_name="تنبيه بعد عدد دقائق"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_notify_manager",
            field=models.BooleanField(default=True, verbose_name="تنبيه المدير المباشر"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_notify_hr",
            field=models.BooleanField(default=False, verbose_name="تنبيه HR"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_notify_company_admin",
            field=models.BooleanField(default=False, verbose_name="تنبيه صاحب الشركة"),
        ),
        migrations.AddField(
            model_name="companypolicy",
            name="stealth_tracking_requires_charter_clause",
            field=models.BooleanField(default=True, verbose_name="إلزام بند المراقبة في الميثاق"),
        ),
    ]
