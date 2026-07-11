from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("requests_app", "0001_initial"),
        ("companies", "0001_initial"),
        ("accounts", "0001_initial"),
        ("employees", "0001_initial"),
    ]

    operations = [
        # ApprovalFlow
        migrations.CreateModel(
            name="ApprovalFlow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("step_1_role", models.CharField(max_length=20, default="direct_manager")),
                ("step_2_role", models.CharField(max_length=20, default="hr_manager")),
                ("step_3_role", models.CharField(max_length=20, default="skip")),
                ("escalation_enabled", models.BooleanField(default=True)),
                ("escalation_to", models.CharField(max_length=20, default="hr_manager")),
                ("notify_employee_on_each_step", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="companies.company")),
                ("request_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approval_flows", to="requests_app.requesttype")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="accounts.user")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="accounts.user")),
            ],
            options={"verbose_name": "مسار موافقة", "verbose_name_plural": "مسارات الموافقة"},
        ),
        migrations.AlterUniqueTogether(
            name="approvalflow",
            unique_together={("company", "request_type")},
        ),

        # ApprovalDelegation
        migrations.CreateModel(
            name="ApprovalDelegation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("delegator_role", models.CharField(max_length=20)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("scope", models.CharField(max_length=20, default="all_approvals")),
                ("reason", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="companies.company")),
                ("delegator", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delegations_given", to="accounts.user")),
                ("delegate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delegations_received", to="accounts.user")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="accounts.user")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="accounts.user")),
            ],
            options={"verbose_name": "تفويض صلاحيات", "verbose_name_plural": "تفويضات الصلاحيات", "ordering": ["-start_date"]},
        ),

        # EmployeeRequest approval steps
        migrations.AddField(model_name="employeerequest", name="current_step",
            field=models.PositiveSmallIntegerField(default=1)),
        migrations.AddField(model_name="employeerequest", name="step_1_status",
            field=models.CharField(max_length=20, blank=True, default="pending")),
        migrations.AddField(model_name="employeerequest", name="step_1_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="step1_approvals", to="accounts.user")),
        migrations.AddField(model_name="employeerequest", name="step_1_at",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="employeerequest", name="step_1_notes",
            field=models.TextField(blank=True)),

        migrations.AddField(model_name="employeerequest", name="step_2_status",
            field=models.CharField(max_length=20, blank=True, default="")),
        migrations.AddField(model_name="employeerequest", name="step_2_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="step2_approvals", to="accounts.user")),
        migrations.AddField(model_name="employeerequest", name="step_2_at",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="employeerequest", name="step_2_notes",
            field=models.TextField(blank=True)),

        migrations.AddField(model_name="employeerequest", name="step_3_status",
            field=models.CharField(max_length=20, blank=True, default="")),
        migrations.AddField(model_name="employeerequest", name="step_3_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="step3_approvals", to="accounts.user")),
        migrations.AddField(model_name="employeerequest", name="step_3_at",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="employeerequest", name="step_3_notes",
            field=models.TextField(blank=True)),

        migrations.AddField(model_name="employeerequest", name="substitute_employee",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                     related_name="substituted_requests", to="employees.employee")),
        migrations.AddField(model_name="employeerequest", name="substitute_notified",
            field=models.BooleanField(default=False)),
    ]
