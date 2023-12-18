# Generated by Django 3.2.23 on 2023-12-18 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaseslicensing', '0304_alter_organisationcontact_user_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisationrequest',
            name='status',
            field=models.CharField(choices=[('with_assessor', 'With Assessor'), ('approved', 'Approved'), ('declined', 'Declined'), ('unlinked', 'Unlinked')], default='with_assessor', max_length=100),
        ),
        migrations.AlterField(
            model_name='percentageofgrossturnover',
            name='estimated_gross_turnover',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='percentageofgrossturnover',
            name='gross_turnover',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='proposalrequirement',
            name='due_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
