# Generated by Django 4.2.6 on 2023-11-09 11:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_remove_customuser_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='registration_date',
        ),
    ]
