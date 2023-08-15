# Generated by Django 3.2.18 on 2023-07-19 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaseslicensing', '0221_rename_invoice_amount_includes_gst_approvaltype_gst_free'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='inc_gst',
        ),
        migrations.AddField(
            model_name='invoice',
            name='gst_free',
            field=models.BooleanField(default=False),
        ),
    ]
