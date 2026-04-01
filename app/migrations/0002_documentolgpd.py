from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentoLGPD",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tipo_documento",
                    models.CharField(
                        db_column="tipo",
                        choices=[
                            ("privacy_policy", "Politica de Privacidade"),
                            ("terms_of_service", "Termos de Servico"),
                        ],
                        max_length=20,
                    ),
                ),
                ("titulo", models.CharField(max_length=200)),
                ("versao", models.CharField(blank=True, default="", max_length=40)),
                ("conteudo", models.TextField()),
                ("ativo", models.BooleanField(default=True)),
                ("data_vigencia", models.DateField(blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Documento LGPD",
                "verbose_name_plural": "Documentos LGPD",
                "ordering": ("tipo_documento", "-data_vigencia", "-atualizado_em"),
            },
        ),
    ]
