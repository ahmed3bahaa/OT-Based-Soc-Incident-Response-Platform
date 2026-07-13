from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("soc", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LiveAlert",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("source", models.CharField(max_length=80)),
                ("fingerprint", models.CharField(max_length=64, unique=True)),
                ("timestamp", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("rule_id", models.CharField(blank=True, db_index=True, max_length=20)),
                ("agent", models.CharField(blank=True, max_length=100)),
                ("location", models.TextField(blank=True)),
                ("raw", models.JSONField(blank=True, default=dict)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("correlated_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ("-timestamp", "-received_at", "-id"),
            },
        ),
        migrations.AddIndex(
            model_name="livealert",
            index=models.Index(fields=["source", "timestamp"], name="soc_liveale_source_0a5aa5_idx"),
        ),
        migrations.AddIndex(
            model_name="livealert",
            index=models.Index(fields=["rule_id", "timestamp"], name="soc_liveale_rule_id_ca8713_idx"),
        ),
    ]
