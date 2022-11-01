# Generated by Django 3.2.4 on 2022-01-28 06:20

from django.db import migrations, models
import django.db.models.deletion
import leaseslicensing.components.proposals.models


class Migration(migrations.Migration):

    dependencies = [
        ("leaseslicensing", "0017_auto_20220128_0901"),
    ]

    operations = [
        migrations.AlterField(
            model_name="proposaldocument",
            name="proposal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="supporting_documents",
                to="leaseslicensing.proposal",
            ),
        ),
        migrations.CreateModel(
            name="WetlandsImpactDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wetlands_impact_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="SignificantChangeDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="significant_change_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="NativeTitleConsultationDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="native_title_consultation_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="MiningTenementDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mining_tenement_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="LongTermUseDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="long_term_use_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="HeritageSiteDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="heritage_site_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="GroundDisturbingWorksDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ground_disturbing_works_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="ExclusiveUseDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exclusive_use_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="EnvironmentallySensitiveDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="environmentally_sensitive_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="ConsistentPurposeDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consistent_purpose_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="ConsistentPlanDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consistent_plan_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="ClearingVegetationDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="clearing_vegetation_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="BuildingRequiredDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="building_required_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
        migrations.CreateModel(
            name="AboriginalSiteDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("uploaded_date", models.DateTimeField(auto_now_add=True)),
                (
                    "_file",
                    models.FileField(
                        max_length=512,
                        upload_to=leaseslicensing.components.proposals.models.update_proposal_doc_filename,
                    ),
                ),
                ("input_name", models.CharField(blank=True, max_length=255, null=True)),
                ("can_delete", models.BooleanField(default=True)),
                ("can_hide", models.BooleanField(default=False)),
                ("hidden", models.BooleanField(default=False)),
                (
                    "proposal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aboriginal_site_documents",
                        to="leaseslicensing.proposal",
                    ),
                ),
            ],
            options={
                "verbose_name": "Application Document",
            },
        ),
    ]
