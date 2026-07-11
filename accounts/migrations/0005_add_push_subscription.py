from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_add_employee_notification"),
    ]

    operations = [
        migrations.CreateModel(
            name="PushSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("endpoint", models.TextField(verbose_name="Endpoint URL")),
                ("p256dh", models.TextField(verbose_name="P256DH Key")),
                ("auth", models.TextField(verbose_name="Auth Key")),
                ("user_agent", models.TextField(blank=True, verbose_name="المتصفح")),
                ("is_active", models.BooleanField(default=True, verbose_name="نشط")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="push_subscriptions",
                    to="accounts.user",
                    verbose_name="المستخدم"
                )),
            ],
            options={
                "verbose_name": "اشتراك Push",
                "verbose_name_plural": "اشتراكات Push",
            },
        ),
        migrations.AlterUniqueTogether(
            name="pushsubscription",
            unique_together={("user", "endpoint")},
        ),
    ]
