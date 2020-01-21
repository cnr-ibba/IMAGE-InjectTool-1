# Generated by Django 2.2.9 on 2020-01-21 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biosample', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrphanSample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('biosample_id', models.CharField(max_length=255, unique=True)),
                ('found_at', models.DateTimeField(auto_now_add=True)),
                ('ignore', models.BooleanField(default=False, help_text='Should I ignore this record or not?')),
                ('name', models.CharField(max_length=255)),
                ('removed', models.BooleanField(default=False, help_text='Is this sample still available?')),
                ('removed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
