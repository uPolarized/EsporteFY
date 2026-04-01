# Generated migration for adding fixado field to Comment model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0014_comment_gif_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='fixado',
            field=models.BooleanField(default=False, help_text='Se o comentário está fixado no topo do post'),
        ),
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-fixado', 'criado_em'], 'verbose_name': 'Comentário', 'verbose_name_plural': 'Comentários'},
        ),
    ]
