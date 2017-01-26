# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_auto_20170126_0825'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='concurrentuser',
            name='concurrent_user',
        ),
        migrations.RenameField(
            model_name='profile',
            old_name='is_teacher',
            new_name='is_admin',
        ),
        migrations.AlterField(
            model_name='quiz',
            name='start_date_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 1, 26, 8, 46, 8, 560880), null=True, verbose_name=b'Start Date and Time of the quiz'),
        ),
        migrations.DeleteModel(
            name='ConcurrentUser',
        ),
    ]
