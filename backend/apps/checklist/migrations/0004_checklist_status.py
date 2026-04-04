# Generated manually for checklist workflow (draft / submitted)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checklist", "0003_checklist_incomplete"),
    ]

    operations = [
        migrations.AddField(
            model_name="checklist",
            name="status",
            field=models.CharField(
                default="draft",
                max_length=20,
                help_text="draft | submitted",
            ),
        ),
    ]
