# Generated by Django 3.2.18 on 2023-07-18 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaseslicensing', '0216_auto_20230718_1019'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='basket_id',
            field=models.IntegerField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='invoice_reference',
            field=models.CharField(max_length=36, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='order_number',
            field=models.CharField(max_length=128, null=True, unique=True),
        ),
    ]
