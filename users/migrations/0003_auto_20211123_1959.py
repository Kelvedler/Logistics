# Generated by Django 3.2.7 on 2021-11-23 17:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_group'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_admin',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_staff',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_superuser',
        ),
    ]