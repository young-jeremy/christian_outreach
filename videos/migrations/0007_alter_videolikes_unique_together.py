# Generated by Django 4.2.6 on 2023-11-14 08:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0006_remove_video_likes_subscribe_video_likes'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='videolikes',
            unique_together=set(),
        ),
    ]
