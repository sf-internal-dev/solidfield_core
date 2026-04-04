# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_companytenant_primary_contact_phone"),
    ]

    operations = [
        migrations.AddField(
            model_name="offlinesyncqueue",
            name="client_mutation_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Idempotência: mesmo valor + mesmo técnico não duplica sucesso (ex.: UUID do app).",
                max_length=64,
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="offlinesyncqueue",
            constraint=models.UniqueConstraint(
                condition=models.Q(client_mutation_id__isnull=False)
                & ~models.Q(client_mutation_id=""),
                fields=("technician", "client_mutation_id"),
                name="core_offlinesyncqueue_technician_clientmutation_uidx",
            ),
        ),
    ]
