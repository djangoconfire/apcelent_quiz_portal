# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionset',
            name='questions',
        ),
        migrations.RemoveField(
            model_name='questionpaper',
            name='random_questions',
        ),
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(max_length=24, choices=[(b'mcq', b'Multiple Choice'), (b'subj_ques', b'Subjective Question')]),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='start_date_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 1, 26, 8, 25, 41, 828794), null=True, verbose_name=b'Start Date and Time of the quiz'),
        ),
        migrations.DeleteModel(
            name='QuestionSet',
        ),
    ]
