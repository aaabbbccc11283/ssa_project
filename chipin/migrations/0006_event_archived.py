# Generated by Django 5.1.5 on 2025-03-26 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chipin", "0005_event"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="archived",
            field=models.BooleanField(default=False),
        ),
    ]
