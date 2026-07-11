from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0001_initial"),
        ("employees", "0001_initial"),
        ("accounts",  "0001_initial"),
    ]

    operations = [

        migrations.CreateModel(
            name="LeaveType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("created_at",  models.DateTimeField(auto_now_add=True)),
                ("updated_at",  models.DateTimeField(auto_now=True)),
                ("name",        models.CharField(max_length=100, verbose_name="الاسم")),
                ("category",    models.CharField(max_length=20, default="other",
                                                  verbose_name="الفئة",
                                                  choices=[
                                                      ("annual","إجازة سنوية"),
                                                      ("sick","إجازة مرضية"),
                                                      ("emergency","إجازة طارئة"),
                                                      ("maternity","إجازة أمومة"),
                                                      ("paternity","إجازة أبوة"),
                                                      ("unpaid","إجازة بدون مرتب"),
                                                      ("other","أخرى"),
                                                  ])),
                ("days_allowed",      models.PositiveSmallIntegerField(default=0)),
                ("is_paid",           models.BooleanField(default=True)),
                ("requires_approval", models.BooleanField(default=True)),
                ("requires_document", models.BooleanField(default=False)),
                ("carry_forward",     models.BooleanField(default=False)),
                ("max_carry_days",    models.PositiveSmallIntegerField(default=0)),
                ("color",             models.CharField(max_length=7, default="#06B6D4")),
                ("is_active",         models.BooleanField(default=True)),
                ("description",       models.TextField(blank=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user",
                    verbose_name="أنشئ بواسطة")),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user",
                    verbose_name="عدّل بواسطة")),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="companies.company", verbose_name="الشركة")),
            ],
            options={"verbose_name": "نوع إجازة",
                     "verbose_name_plural": "أنواع الإجازات"},
        ),

        migrations.CreateModel(
            name="LeaveBalance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("created_at",    models.DateTimeField(auto_now_add=True)),
                ("updated_at",    models.DateTimeField(auto_now=True)),
                ("year",          models.PositiveSmallIntegerField(default=2025)),
                ("total_days",    models.DecimalField(max_digits=5, decimal_places=1, default=0)),
                ("used_days",     models.DecimalField(max_digits=5, decimal_places=1, default=0)),
                ("pending_days",  models.DecimalField(max_digits=5, decimal_places=1, default=0)),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="companies.company")),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user")),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user")),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="leave_balances",
                    to="employees.employee")),
                ("leave_type", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="balances",
                    to="leaves.leavetype")),
            ],
            options={"verbose_name": "رصيد إجازة",
                     "verbose_name_plural": "أرصدة الإجازات"},
        ),

        migrations.AddConstraint(
            model_name="leavebalance",
            constraint=models.UniqueConstraint(
                fields=["company", "employee", "leave_type", "year"],
                name="unique_leave_balance"
            ),
        ),

        migrations.CreateModel(
            name="LeaveRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("created_at",    models.DateTimeField(auto_now_add=True)),
                ("updated_at",    models.DateTimeField(auto_now=True)),
                ("start_date",    models.DateField()),
                ("end_date",      models.DateField()),
                ("days_count",    models.DecimalField(max_digits=4,
                                                       decimal_places=1, default=1)),
                ("reason",        models.TextField()),
                ("document",      models.FileField(blank=True, null=True,
                                                    upload_to="leave_documents/")),
                ("notes",         models.TextField(blank=True)),
                ("status",        models.CharField(max_length=20, default="pending",
                                                    choices=[
                                                        ("pending","قيد الانتظار"),
                                                        ("approved","موافق عليه"),
                                                        ("rejected","مرفوض"),
                                                        ("cancelled","ملغي"),
                                                    ])),
                ("reviewed_at",   models.DateTimeField(null=True, blank=True)),
                ("review_notes",  models.TextField(blank=True)),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to="companies.company")),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user")),
                ("updated_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="accounts.user")),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="leave_requests",
                    to="employees.employee")),
                ("leave_type", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="requests",
                    to="leaves.leavetype")),
                ("reviewed_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="reviewed_leaves",
                    to="accounts.user")),
            ],
            options={"verbose_name": "طلب إجازة",
                     "verbose_name_plural": "طلبات الإجازات",
                     "ordering": ["-created_at"]},
        ),
    ]
