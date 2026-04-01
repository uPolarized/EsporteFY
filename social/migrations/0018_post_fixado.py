from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0017_expand_gif_url_lengths'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='fixado',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-fixado', '-criado_em'], 'verbose_name': 'Post', 'verbose_name_plural': 'Posts'},
        ),
    ]
