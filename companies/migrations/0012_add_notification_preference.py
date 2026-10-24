from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0011_add_notification_preference"),
    ]

    # 0012 was a byte-identical duplicate of 0011 (same CreateModel + AlterUniqueTogether),
    # which breaks building a fresh database from scratch ("table already exists").
    # No-op kept in the graph so deployed databases that already recorded it stay consistent.
    operations = []
