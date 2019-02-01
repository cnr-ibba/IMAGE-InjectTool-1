# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-25 11:34
from __future__ import unicode_literals

import common.fields
import common.storage
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import image_app.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Animal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alternative_id', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('material', models.CharField(default='Organism', editable=False, max_length=255, null=True)),
                ('birth_location', models.CharField(blank=True, max_length=255, null=True)),
                ('birth_location_latitude', models.FloatField(blank=True, null=True)),
                ('birth_location_longitude', models.FloatField(blank=True, null=True)),
                ('birth_location_accuracy', models.SmallIntegerField(choices=[(0, 'missing geographic information'), (1, 'country level'), (2, 'region level'), (3, 'precise coordinates'), (4, 'unknown accuracy level')], default=0, help_text='example: unknown accuracy level, country level')),
            ],
            bases=(image_app.models.BioSampleMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictBreed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
                ('supplied_breed', models.CharField(max_length=255)),
                ('mapped_breed', models.CharField(max_length=255, null=True)),
                ('mapped_breed_term', models.CharField(help_text='Example: LBO_0000347', max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Breed',
            },
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictCountry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
            ],
            options={
                'verbose_name': 'country',
                'verbose_name_plural': 'countries',
            },
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'role',
            },
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictSex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'sex',
                'verbose_name_plural': 'sex',
            },
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictSpecie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
            ],
            options={
                'verbose_name': 'specie',
            },
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Name',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('biosample_id', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.SmallIntegerField(choices=[(1, 'Loaded'), (2, 'Submitted'), (4, 'Need Revision'), (5, 'Ready'), (6, 'Completed')], default=1, help_text='example: Submitted')),
                ('last_changed', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_submitted', models.DateTimeField(blank=True, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Ontology',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('library_name', models.CharField(help_text='Each value must be unique', max_length=255, unique=True)),
                ('library_uri', models.URLField(blank=True, help_text='Each value must be unique and with a valid URL', max_length=500, null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name_plural': 'ontologies',
            },
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(blank=True, help_text='One line, comma separated', max_length=255, null=True)),
                ('URI', models.URLField(blank=True, help_text='Web site', max_length=500, null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='image_app.DictCountry')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='image_app.DictRole')),
            ],
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('initials', models.CharField(blank=True, max_length=255, null=True)),
                ('affiliation', models.ForeignKey(help_text='The institution you belong to', null=True, on_delete=django.db.models.deletion.PROTECT, to='image_app.Organization')),
                ('role', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='image_app.DictRole')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doi', models.CharField(help_text='Valid Digital Object Identifier', max_length=255)),
            ],
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alternative_id', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('material', models.CharField(default='Specimen from Organism', editable=False, max_length=255, null=True)),
                ('protocol', models.CharField(blank=True, max_length=255, null=True)),
                ('collection_date', models.DateField(blank=True, null=True)),
                ('collection_place_latitude', models.FloatField(blank=True, null=True)),
                ('collection_place_longitude', models.FloatField(blank=True, null=True)),
                ('collection_place', models.CharField(blank=True, max_length=255, null=True)),
                ('collection_place_accuracy', models.SmallIntegerField(choices=[(0, 'missing geographic information'), (1, 'country level'), (2, 'region level'), (3, 'precise coordinates'), (4, 'unknown accuracy level')], default=0, help_text='example: unknown accuracy level, country level')),
                ('organism_part', models.CharField(blank=True, max_length=255, null=True)),
                ('organism_part_term', models.CharField(help_text='Example: UBERON_0001968', max_length=255, null=True)),
                ('developmental_stage', models.CharField(blank=True, max_length=255, null=True)),
                ('developmental_stage_term', models.CharField(help_text='Example: EFO_0001272', max_length=255, null=True)),
                ('physiological_stage', models.CharField(blank=True, max_length=255, null=True)),
                ('animal_age_at_collection', models.IntegerField(blank=True, null=True)),
                ('availability', models.CharField(blank=True, max_length=255, null=True)),
                ('storage', models.CharField(blank=True, max_length=255, null=True)),
                ('storage_processing', models.CharField(blank=True, max_length=255, null=True)),
                ('preparation_interval', models.IntegerField(blank=True, null=True)),
                ('animal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='image_app.Animal')),
                ('name', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='image_app.Name')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to=settings.AUTH_USER_MODEL)),
            ],
            bases=(image_app.models.BioSampleMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Example: Roslin Sheep Atlas', max_length=255, verbose_name='Submission title')),
                ('project', models.CharField(default='IMAGE', editable=False, max_length=25)),
                ('description', models.CharField(help_text='Example: The Roslin Institute Sheep Gene Expression Atlas Project', max_length=255)),
                ('gene_bank_name', models.CharField(help_text='example: CryoWeb', max_length=255)),
                ('datasource_type', models.SmallIntegerField(choices=[(0, 'CryoWeb'), (1, 'Template'), (2, 'CRB-Anim')], help_text='example: CryoWeb')),
                ('datasource_version', models.CharField(help_text='examples: "2018-04-27", "version 1.5"', max_length=255)),
                ('uploaded_file', common.fields.ProtectedFileField(storage=common.storage.ProtectedFileSystemStorage(), upload_to='data_source/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.SmallIntegerField(choices=[(0, 'Waiting'), (1, 'Loaded'), (2, 'Submitted'), (3, 'Error'), (4, 'Need Revision'), (5, 'Ready'), (6, 'Completed')], default=0, help_text='example: Waiting')),
                ('message', models.TextField(blank=True, null=True)),
                ('biosample_submission_id', models.CharField(blank=True, db_index=True, help_text='Biosample submission id', max_length=255, null=True, unique=True)),
                ('gene_bank_country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='image_app.DictCountry')),
                ('organization', models.ForeignKey(help_text='Who owns the data', on_delete=django.db.models.deletion.PROTECT, to='image_app.Organization')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to=settings.AUTH_USER_MODEL)),
            ],
            bases=(image_app.models.BaseMixin, models.Model),
        ),
        migrations.AddField(
            model_name='publication',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publications', to='image_app.Submission'),
        ),
        migrations.AddField(
            model_name='name',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='name_set', to='image_app.Submission'),
        ),
        migrations.AlterUniqueTogether(
            name='dictspecie',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictrole',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictcountry',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AddField(
            model_name='dictbreed',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='image_app.DictCountry'),
        ),
        migrations.AddField(
            model_name='dictbreed',
            name='specie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='image_app.DictSpecie'),
        ),
        migrations.AddField(
            model_name='animal',
            name='breed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='image_app.DictBreed'),
        ),
        migrations.AddField(
            model_name='animal',
            name='father',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='father_set', to='image_app.Name'),
        ),
        migrations.AddField(
            model_name='animal',
            name='mother',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mother_set', to='image_app.Name'),
        ),
        migrations.AddField(
            model_name='animal',
            name='name',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='image_app.Name'),
        ),
        migrations.AddField(
            model_name='animal',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='animals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='animal',
            name='sex',
            field=models.ForeignKey(blank=True, default=-1, null=True, on_delete=django.db.models.deletion.PROTECT, to='image_app.DictSex'),
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together=set([('gene_bank_name', 'gene_bank_country', 'datasource_type', 'datasource_version')]),
        ),
        migrations.AlterUniqueTogether(
            name='name',
            unique_together=set([('name', 'submission')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictbreed',
            unique_together=set([('supplied_breed', 'specie')]),
        ),
    ]