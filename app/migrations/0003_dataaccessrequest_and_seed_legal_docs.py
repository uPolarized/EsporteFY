from datetime import date

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_legal_docs(apps, schema_editor):
    DocumentoLGPD = apps.get_model("app", "DocumentoLGPD")
    vigencia = date(2026, 3, 30)

    politica_texto = """1. Controlador e contato\nO controlador dos dados pessoais tratados no EsporteFY e a propria plataforma EsporteFY.\nContato para assuntos de privacidade: contato.esportefy@gmail.com.\n\n2. Dados pessoais tratados\nPodemos tratar dados fornecidos no cadastro, dados de perfil esportivo, dados de uso da plataforma,\nregistros de interacoes sociais, participacao em partidas, informacoes tecnicas de acesso e logs\nde seguranca.\n\n3. Finalidades do tratamento\nOs dados sao tratados para:\n- executar funcionalidades da plataforma e cumprir o contrato de uso;\n- autenticar usuarios e proteger contas;\n- organizar partidas, conexoes e recursos sociais;\n- prevencao a fraude, abuso e incidentes de seguranca;\n- cumprimento de obrigacoes legais e regulatorias;\n- melhoria de produto, experiencia e suporte ao usuario.\n\n4. Bases legais aplicaveis\nConforme a LGPD, o tratamento pode ocorrer com base em:\n- execucao de contrato e procedimentos preliminares;\n- cumprimento de obrigacao legal ou regulatoria;\n- exercicio regular de direitos em processo judicial, administrativo ou arbitral;\n- legitimo interesse, observadas as liberdades fundamentais do titular;\n- consentimento, quando essa for a base legal aplicavel.\n\n5. Compartilhamento de dados\nOs dados podem ser compartilhados com operadores e fornecedores essenciais para\nhospedagem, infraestrutura, envio de comunicacoes e suporte operacional, sempre com obrigacoes de\nconfidencialidade e seguranca. O compartilhamento com autoridades ocorre quando houver base legal.\n\n6. Retencao e eliminacao\nMantemos os dados pelo tempo necessario para cumprir as finalidades de tratamento e\nobrigacoes legais. Quando aplicavel, os dados sao anonimizados ou eliminados de modo seguro.\n\n7. Direitos do titular (art. 18 da LGPD)\nVoce pode solicitar:\n- confirmacao da existencia de tratamento;\n- acesso aos dados;\n- correcao de dados incompletos, inexatos ou desatualizados;\n- anonimização, bloqueio ou eliminacao de dados desnecessarios;\n- portabilidade dos dados, observadas regras aplicaveis;\n- informacao sobre compartilhamentos;\n- revogacao do consentimento, quando essa for a base legal.\n\n8. Seguranca da informacao\nAdotamos medidas tecnicas e administrativas de seguranca compativeis com o risco,\ncom controles de acesso, monitoramento e boas praticas de desenvolvimento.\n\n9. Atualizacoes deste documento\nEsta politica pode ser atualizada para refletir mudancas legais, regulatorias ou funcionais\nda plataforma. A versao vigente fica sempre disponivel na central LGPD."""

    termos_texto = """1. Aceite dos termos\nAo criar conta ou utilizar o EsporteFY, voce declara que leu e concorda com estes Termos de\nServico e com a Politica de Privacidade vigente.\n\n2. Uso adequado da plataforma\nO usuario se compromete a utilizar os recursos da plataforma de forma licita, respeitosa e\ncompatível com a finalidade esportiva e social do EsporteFY.\n\n3. Conta e responsabilidade\nCada usuario e responsavel por manter suas credenciais em sigilo e por toda atividade realizada\nem sua conta. O compartilhamento de senha e desaconselhado.\n\n4. Conteudo e conduta\nNao e permitido publicar conteudo ilegal, ofensivo, discriminatorio, fraudulento ou que viole\ndireitos de terceiros. A plataforma pode moderar conteudo e aplicar medidas cabiveis.\n\n5. Partidas e interacoes\nO EsporteFY atua como ambiente de conexao entre usuarios. Responsabilidades por encontros,\ncombinacoes presenciais e conduta em quadras sao dos participantes envolvidos.\n\n6. Disponibilidade e melhorias\nBuscamos alta disponibilidade, mas podem ocorrer indisponibilidades temporarias por manutencao,\natualizacoes, falhas de terceiros ou eventos fora do nosso controle.\n\n7. Suspensao e encerramento\nPodemos restringir funcionalidades, suspender ou encerrar contas em caso de violacao destes\ntermos, risco de seguranca ou exigencia legal.\n\n8. Privacidade e protecao de dados\nO tratamento de dados pessoais segue a legislacao aplicavel e a Politica de Privacidade do\nEsporteFY.\n\n9. Alteracoes dos termos\nEstes termos podem ser atualizados periodicamente. A versao vigente e publicada na central LGPD\npara consulta permanente."""

    def upsert_documento(tipo_documento, titulo, versao, conteudo):
        instance, _ = DocumentoLGPD.objects.get_or_create(
            tipo_documento=tipo_documento,
            versao=versao,
            defaults={
                "titulo": titulo,
                "conteudo": conteudo,
                "ativo": True,
                "data_vigencia": vigencia,
            },
        )

        instance.titulo = titulo
        instance.conteudo = conteudo
        instance.ativo = True
        instance.data_vigencia = vigencia
        instance.save(update_fields=["titulo", "conteudo", "ativo", "data_vigencia", "atualizado_em"])

        DocumentoLGPD.objects.filter(tipo_documento=tipo_documento).exclude(pk=instance.pk).update(ativo=False)

    upsert_documento(
        tipo_documento="privacy_policy",
        titulo="Politica de Privacidade",
        versao="1.1",
        conteudo=politica_texto,
    )
    upsert_documento(
        tipo_documento="terms_of_service",
        titulo="Termos de Servico",
        versao="1.1",
        conteudo=termos_texto,
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("app", "0002_documentolgpd"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataAccessRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("motivo", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("processing", "Em processamento"),
                            ("completed", "Concluida"),
                            ("denied", "Negada"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("data_solicitacao", models.DateTimeField(auto_now_add=True)),
                ("data_processamento", models.DateTimeField(blank=True, null=True)),
                ("arquivo_exportacao", models.FileField(blank=True, null=True, upload_to="data_exports/")),
                ("observacoes_admin", models.TextField(blank=True, default="")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="data_access_requests",
                        to=settings.AUTH_USER_MODEL,
                        db_column="usuario_id",
                    ),
                ),
            ],
            options={
                "verbose_name": "Solicitacao de acesso a dados",
                "verbose_name_plural": "Solicitacoes de acesso a dados",
                "ordering": ("-data_solicitacao",),
            },
        ),
        migrations.RunPython(seed_legal_docs, migrations.RunPython.noop),
    ]
