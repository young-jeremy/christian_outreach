# Generated by Django 4.2.6 on 2023-11-13 07:32

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('videos', '0003_remove_video_dislikes_video_dislikes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='comment',
            new_name='text',
        ),
        migrations.AddField(
            model_name='comment',
            name='dislikes',
            field=models.ManyToManyField(related_name='disliked_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='videos.comment', validators=[django.core.validators.MinLengthValidator(150)]),
        ),
    ]
