from datetime import date

from django.db import migrations


def seed_missing_lgpd_documents(apps, schema_editor):
    DocumentoLGPD = apps.get_model("app", "DocumentoLGPD")
    vigencia = date(2026, 3, 30)

    politica = """1. Controlador e contato\nO controlador dos dados pessoais tratados no EsporteFY e a propria plataforma.\nContato de privacidade: contato.esportefy@gmail.com.\n\n2. Dados tratados\nPodemos tratar dados de cadastro, perfil esportivo, uso da plataforma, participacao em partidas,\ninteracoes sociais e logs tecnicos de seguranca.\n\n3. Finalidades\nTratamos dados para executar o servico, proteger contas, prevenir fraude, oferecer suporte e\nmelhorar produto e experiencia.\n\n4. Bases legais\nAs bases legais incluem execucao de contrato, obrigacao legal, legitimo interesse e consentimento\nquando aplicavel, nos termos da LGPD.\n\n5. Direitos do titular\nVoce pode solicitar confirmacao de tratamento, acesso, correcao, portabilidade e revogacao de\nconsentimento quando cabivel.\n\n6. Retencao e seguranca\nOs dados sao mantidos pelo periodo necessario para as finalidades e obrigacoes legais, com medidas\ntecnicas e administrativas de seguranca.\n\n7. Atualizacoes\nEsta politica pode ser atualizada. A versao vigente fica disponivel na central LGPD."""

    termos = """1. Aceite\nAo criar conta ou utilizar o EsporteFY, voce concorda com estes termos e com a Politica de\nPrivacidade vigente.\n\n2. Uso adequado\nO usuario se compromete a utilizar a plataforma de forma licita, respeitosa e compativel com os\nobjetivos esportivos e sociais do produto.\n\n3. Conta e responsabilidade\nCada usuario e responsavel pela seguranca das proprias credenciais e pelas acoes realizadas em\nsua conta.\n\n4. Conteudo e conduta\nNao e permitido publicar conteudo ilegal, ofensivo, discriminatorio ou fraudulento.\n\n5. Disponibilidade\nPodem ocorrer indisponibilidades temporarias por manutencao, atualizacoes ou fatores externos.\n\n6. Moderacao\nA plataforma pode moderar conteudo e aplicar medidas em caso de violacao de regras.\n\n7. Alteracoes\nOs termos podem ser atualizados periodicamente, mantendo publicacao da versao vigente na central\nLGPD."""

    docs = [
        ("privacy_policy", "Politica de Privacidade", "1.1", politica),
        ("terms_of_service", "Termos de Servico", "1.1", termos),
    ]

    for tipo_documento, titulo, versao, conteudo in docs:
        doc, _ = DocumentoLGPD.objects.get_or_create(
            tipo_documento=tipo_documento,
            versao=versao,
            defaults={
                "titulo": titulo,
                "conteudo": conteudo,
                "ativo": True,
                "data_vigencia": vigencia,
            },
        )

        doc.titulo = titulo
        doc.conteudo = conteudo
        doc.ativo = True
        doc.data_vigencia = vigencia
        doc.save()

        DocumentoLGPD.objects.filter(tipo_documento=tipo_documento).exclude(pk=doc.pk).update(ativo=False)


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_userconsentlog"),
    ]

    operations = [
        migrations.RunPython(seed_missing_lgpd_documents, migrations.RunPython.noop),
    ]
