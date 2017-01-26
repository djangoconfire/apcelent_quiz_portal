# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0003_auto_20170126_0846'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quiz',
            name='start_date_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 1, 26, 9, 15, 56, 483238), null=True, verbose_name=b'Start Date and Time of the quiz'),
        ),
    ]
