from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0016_post_gif_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='gif_url',
            field=models.URLField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='gif_url',
            field=models.URLField(blank=True, max_length=1000, null=True),
        ),
    ]
