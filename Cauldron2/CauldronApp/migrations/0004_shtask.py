# Generated by Django 3.0.7 on 2020-06-18 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CauldronApp', '0003_user_workspaces'),
    ]

    operations = [
        migrations.CreateModel(
            name='SHTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_date', models.DateTimeField()),
                ('started_date', models.DateTimeField(null=True)),
                ('completed_date', models.DateTimeField(null=True)),
                ('done', models.BooleanField(default=False)),
                ('log_file', models.CharField(blank=True, max_length=255)),
            ],
        ),
    ]