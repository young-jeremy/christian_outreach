# Generated by Django 4.2.6 on 2023-11-08 08:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='name',
        ),
    ]