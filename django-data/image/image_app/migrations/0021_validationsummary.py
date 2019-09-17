# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-13 08:44
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('image_app', '0020_auto_20190527_1729'),
    ]

    operations = [
        migrations.CreateModel(
            name='ValidationSummary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pass_count', models.PositiveIntegerField(default=0)),
                ('warning_count', models.PositiveIntegerField(default=0)),
                ('error_count', models.PositiveIntegerField(default=0)),
                ('json_count', models.PositiveIntegerField(default=0)),
                ('type', models.CharField(blank=True, max_length=6, null=True)),
                ('messages', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(blank=True, max_length=255), default=list, size=None)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='image_app.Submission')),
            ],
        ),
    ]