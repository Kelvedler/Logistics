# Generated by Django 3.2.7 on 2021-10-18 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='group',
            field=models.CharField(choices=[('C', 'Customer'), ('D', 'Driver'), ('O', 'Operator'), ('A', 'Administrator')], default='C', max_length=1),
        ),
    ]
