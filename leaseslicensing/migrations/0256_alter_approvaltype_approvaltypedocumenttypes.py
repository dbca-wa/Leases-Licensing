# Generated by Django 3.2.18 on 2023-08-31 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaseslicensing', '0255_merge_20230828_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='approvaltype',
            name='approvaltypedocumenttypes',
            field=models.ManyToManyField(related_name='approval_type', through='leaseslicensing.ApprovalTypeDocumentTypeOnApprovalType', to='leaseslicensing.ApprovalTypeDocumentType'),
        ),
    ]
