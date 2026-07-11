from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_add_must_change_password"),
        ("attendance", "0003_latenotification_disciplinaryaction_lateincident"),
        ("employees", "0004_employee_attendance_mode_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmployeeNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="العنوان")),
                ("message", models.TextField(verbose_name="الرسالة")),
                ("notification_type", models.CharField(
                    max_length=20,
                    default="general_notice",
                    verbose_name="نوع الإشعار",
                    choices=[
                        ("late_warning", "تحذير تأخير"),
                        ("deduction_notice", "إشعار خصم"),
                        ("general_notice", "إشعار عام"),
                        ("policy_reminder", "تذكير بسياسة"),
                        ("charter_reminder", "تذكير بالميثاق"),
                        ("request_update", "تحديث طلب"),
                    ],
                )),
                ("severity", models.CharField(
                    max_length=10,
                    default="info",
                    verbose_name="الأهمية",
                    choices=[
                        ("info", "معلومة"),
                        ("warning", "تحذير"),
                        ("danger", "هام"),
                    ],
                )),
                ("is_read", models.BooleanField(default=False, verbose_name="تمت القراءة")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notifications",
                    to="employees.employee",
                    verbose_name="الموظف"
                )),
                ("related_action", models.ForeignKey(
                    null=True,
                    blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="employee_notifications",
                    to="attendance.disciplinaryaction",
                    verbose_name="الإجراء المرتبط"
                )),
                ("sent_by", models.ForeignKey(
                    null=True,
                    blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="sent_employee_notifications",
                    to="accounts.user",
                    verbose_name="مرسل بواسطة"
                )),
            ],
            options={
                "verbose_name": "إشعار موظف",
                "verbose_name_plural": "إشعارات الموظفين",
                "ordering": ["-created_at"],
            },
        ),
    ]
