# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-15 12:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('image_app', '0009_auto_20190208_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animal',
            name='father',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='father_of', to='image_app.Name'),
        ),
        migrations.AlterField(
            model_name='animal',
            name='mother',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mother_of', to='image_app.Name'),
        ),
    ]