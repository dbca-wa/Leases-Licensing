# Generated by Django 3.2.18 on 2023-07-14 08:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leaseslicensing', '0212_auto_20230714_1535'),
    ]

    operations = [
        migrations.AddField(
            model_name='approval',
            name='approval_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='leaseslicensing.approvaltype'),
        ),
    ]
