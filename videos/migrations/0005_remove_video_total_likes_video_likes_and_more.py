# Generated by Django 4.2.6 on 2023-11-13 09:57

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('videos', '0004_rename_comment_comment_text_comment_dislikes_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='total_likes',
        ),
        migrations.AddField(
            model_name='video',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='total_likes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name='video',
            name='dislikes',
        ),
        migrations.AlterField(
            model_name='video',
            name='privacy',
            field=models.CharField(choices=[('PUBLIC', 'public'), ('PRIVATE', 'private'), ('COMMUNITY', 'community'), ('MADE_FOR_KIDS', 'made_for_kids')], default='PUBLIC', max_length=100),
        ),
        migrations.RemoveField(
            model_name='video',
            name='views',
        ),
        migrations.AddField(
            model_name='video',
            name='dislikes',
            field=models.ManyToManyField(blank=True, related_name='total_dislikes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='video',
            name='views',
            field=models.ManyToManyField(blank=True, related_name='post_views', to=settings.AUTH_USER_MODEL),
        ),
    ]