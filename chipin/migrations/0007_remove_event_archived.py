# Generated by Django 5.1.5 on 2025-03-26 06:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chipin", "0006_event_archived"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="event",
            name="archived",
        ),
    ]
