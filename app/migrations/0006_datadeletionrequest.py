from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("app", "0005_seed_missing_lgpd_documents"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataDeletionRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("motivo", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("canceled", "Cancelada"),
                            ("completed", "Concluida"),
                            ("expired", "Expirada"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("confirm_token", models.CharField(max_length=80, unique=True)),
                ("data_solicitacao", models.DateTimeField(auto_now_add=True)),
                ("data_expiracao", models.DateTimeField()),
                ("data_confirmacao", models.DateTimeField(blank=True, null=True)),
                ("data_cancelamento", models.DateTimeField(blank=True, null=True)),
                ("data_processamento", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        db_column="usuario_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="data_deletion_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Solicitacao de exclusao de conta",
                "verbose_name_plural": "Solicitacoes de exclusao de conta",
                "ordering": ("-data_solicitacao",),
            },
        ),
    ]
