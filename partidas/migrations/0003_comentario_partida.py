# Generated migration for ComentarioPartida

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('partidas', '0002_avaliacao'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComentarioPartida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conteudo', models.TextField(verbose_name='Comentário')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios_partida', to=settings.AUTH_USER_MODEL)),
                ('partida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='partidas.partida')),
                ('resposta_a', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='respostas', to='partidas.comentariopartida', verbose_name='Resposta a')),
            ],
            options={
                'verbose_name': 'Comentário de Partida',
                'verbose_name_plural': 'Comentários de Partida',
                'ordering': ['data_criacao'],
            },
        ),
        migrations.CreateModel(
            name='CancelamentoPartida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.CharField(choices=[('chuva', '🌧️ Chuva'), ('falta_quorum', '👥 Falta de pessoas'), ('problemas_quadra', '🏗️ Problemas com a quadra'), ('emergencia', '🚨 Emergência'), ('outro', '❓ Outro motivo')], max_length=20, verbose_name='Motivo')),
                ('descricao', models.TextField(blank=True, null=True, verbose_name='Descrição adicional')),
                ('data_cancelamento', models.DateTimeField(auto_now_add=True)),
                ('partida', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cancelamento', to='partidas.partida')),
                ('quem_cancelou', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partidas_canceladas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Cancelamento de Partida',
                'verbose_name_plural': 'Cancelamentos de Partida',
            },
        ),
    ]
