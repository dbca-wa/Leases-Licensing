# Generated by Django 3.2.4 on 2022-01-24 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leaseslicensing", "0013_alter_proposalgeometry_proposal"),
    ]

    operations = [
        migrations.AddField(
            model_name="proposal",
            name="aboriginal_site",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="building_required",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="clearing_vegetation",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="consistent_plan",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="consistent_purpose",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="environmentally_sensitive",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="exclusive_use",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proposal",
            name="ground_disturbing_works",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="heritage_site",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="long_term_use",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proposal",
            name="mining_tenement",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="native_title_consultation",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="significant_change",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="proposal",
            name="wetlands_impact",
            field=models.BooleanField(null=True),
        ),
    ]
