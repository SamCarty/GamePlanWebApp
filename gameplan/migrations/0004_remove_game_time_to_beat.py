# Generated by Django 2.2.5 on 2020-01-09 21:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gameplan', '0003_auto_20200109_2106'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='time_to_beat',
        ),
    ]
