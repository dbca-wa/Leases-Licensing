# Generated by Django 3.2.13 on 2022-08-12 06:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaseslicensing', '0063_auto_20220812_1418'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='approvaltypedocumenttype',
            name='approval_type',
        ),
        migrations.AddField(
            model_name='approvaltype',
            name='approval_type_document_types',
            field=models.ManyToManyField(to='leaseslicensing.ApprovalType'),
        ),
    ]
