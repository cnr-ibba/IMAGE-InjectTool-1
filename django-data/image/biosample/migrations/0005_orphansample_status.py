# Generated by Django 2.2.10 on 2020-05-29 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biosample', '0004_auto_20200127_1615'),
    ]

    operations = [
        migrations.AddField(
            model_name='orphansample',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Waiting'), (1, 'Loaded'), (2, 'Submitted'), (3, 'Error'), (4, 'Need Revision'), (5, 'Ready'), (6, 'Completed')], default=5, help_text='example: Waiting'),
        ),
    ]