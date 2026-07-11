from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0004_dailyassignment"),
        ("companies", "0001_initial"),
        ("employees", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackingAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField(verbose_name="التاريخ")),
                ("started_at", models.DateTimeField(verbose_name="وقت بداية الخروج")),
                ("last_seen_at", models.DateTimeField(blank=True, null=True, verbose_name="آخر وقت رصد")),
                ("minutes_outside", models.PositiveSmallIntegerField(default=0, verbose_name="دقائق خارج النطاق")),
                ("last_latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("last_longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("last_address", models.TextField(blank=True)),
                ("status", models.CharField(
                    choices=[("open","مفتوح"),("resolved","تمت المعالجة"),("ignored","تم التجاهل")],
                    default="open", max_length=20, verbose_name="الحالة"
                )),
                ("notified_manager", models.BooleanField(default=False)),
                ("notified_hr", models.BooleanField(default=False)),
                ("notified_company_admin", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="companies.company"
                )),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="tracking_alerts",
                    to="employees.employee",
                    verbose_name="الموظف"
                )),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user"
                )),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user"
                )),
                ("resolved_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="resolved_tracking_alerts",
                    to="accounts.user"
                )),
            ],
            options={
                "verbose_name": "تنبيه تتبع",
                "verbose_name_plural": "تنبيهات التتبع",
                "ordering": ["-started_at"],
            },
        ),
    ]
