# Generated by Django 4.2.20 on 2025-04-07 20:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_userprofile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="type",
            field=models.CharField(
                choices=[
                    ("bot", "Bot"),
                    ("internal", "Internal"),
                    ("external", "External"),
                    ("guest", "Guest"),
                ],
                default="internal",
                help_text="Which type of user is this?",
                max_length=10,
                verbose_name="User Type",
            ),
        ),
    ]
