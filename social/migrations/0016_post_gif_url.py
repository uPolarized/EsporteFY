from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0015_comment_fixado'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='gif_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
