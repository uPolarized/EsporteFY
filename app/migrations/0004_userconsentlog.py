from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("app", "0003_dataaccessrequest_and_seed_legal_docs"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserConsentLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "consent_type",
                    models.CharField(
                        choices=[
                            ("terms_of_service", "Termos de Servico"),
                            ("privacy_policy", "Politica de Privacidade"),
                            ("cookies", "Cookies Opcionais"),
                        ],
                        max_length=40,
                    ),
                ),
                ("accepted", models.BooleanField(default=False)),
                ("document_version", models.CharField(blank=True, default="", max_length=40)),
                ("source", models.CharField(blank=True, default="web", max_length=20)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, default="")),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        db_column="usuario_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consent_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Log de consentimento",
                "verbose_name_plural": "Logs de consentimento",
                "ordering": ("-timestamp",),
            },
        ),
        migrations.AddIndex(
            model_name="userconsentlog",
            index=models.Index(fields=["user", "consent_type", "-timestamp"], name="app_usercon_user_id_6e698f_idx"),
        ),
    ]
