# Generated by Django 3.2.7 on 2021-11-15 11:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('freight_shipping', '0012_auto_20211102_1835'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method', models.CharField(max_length=20)),
                ('payment_id', models.CharField(max_length=19)),
                ('completed', models.BooleanField(default=False)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.RESTRICT, to='freight_shipping.order')),
            ],
            options={
                'default_permissions': (),
                'unique_together': {('payment_method', 'payment_id')},
            },
        ),
    ]
