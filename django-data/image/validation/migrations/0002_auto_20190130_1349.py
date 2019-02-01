# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-30 12:49
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('validation', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='validationresult',
            name='data',
        ),
        migrations.AddField(
            model_name='validationresult',
            name='messages',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=255), default=list, size=None),
        ),
    ]