from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('partidas', '0006_merge_20260328_0953'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComentarioPartidaLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('comentario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='partidas.comentariopartida')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curtidas_comentario_partida', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Curtida em comentário de partida',
                'verbose_name_plural': 'Curtidas em comentários de partida',
                'ordering': ['-criado_em'],
                'unique_together': {('comentario', 'usuario')},
            },
        ),
    ]
