# Generated by Django 2.2.9 on 2020-01-31 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uid', '0003_auto_20200129_1630'),
    ]

    operations = [
        migrations.AddField(
            model_name='animal',
            name='same_as',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='sample',
            name='same_as',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]