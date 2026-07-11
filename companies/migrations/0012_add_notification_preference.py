from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0011_add_notification_preference"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False)),
                ("role", models.CharField(max_length=20, verbose_name="الدور",
                    choices=[
                        ("employee","موظف"),("manager","مدير"),
                        ("hr_manager","مدير HR"),("company_admin","صاحب الشركة"),
                    ]
                )),
                ("notification_type", models.CharField(max_length=30,
                    verbose_name="نوع الإشعار",
                    choices=[
                        ("request_approved","تمت الموافقة على الطلب"),
                        ("request_rejected","تم رفض الطلب"),
                        ("new_request_to_approve","طلب جديد يحتاج موافقة"),
                        ("late_warning","تحذير تأخير"),
                        ("late_threshold","تجاوز حد التأخير"),
                        ("deduction_notice","إشعار خصم"),
                        ("stealth_alert","تنبيه تتبع صامت"),
                        ("charter_reminder","تذكير بالميثاق"),
                        ("subscription_expiry","انتهاء الاشتراك"),
                        ("general_notice","إشعار عام"),
                    ]
                )),
                ("push_enabled", models.BooleanField(default=True,
                                                      verbose_name="إرسال Push")),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notification_preferences",
                    to="companies.company",
                    verbose_name="الشركة"
                )),
            ],
            options={
                "verbose_name": "إعداد إشعار",
                "verbose_name_plural": "إعدادات الإشعارات",
            },
        ),
        migrations.AlterUniqueTogether(
            name="notificationpreference",
            unique_together={("company", "role", "notification_type")},
        ),
    ]
