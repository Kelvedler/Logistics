# Generated by Django 3.2.7 on 2021-11-28 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freight_shipping', '0017_auto_20211127_2133'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=5.0, max_digits=6),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payment',
            name='currency_code',
            field=models.CharField(default='USD', max_length=3),
            preserve_default=False,
        ),
    ]
