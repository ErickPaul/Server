# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('account_key', models.CharField(max_length=255)),
                ('passphrase', models.CharField(max_length=80)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('location', models.CharField(max_length=100, blank=True)),
                ('bio', models.TextField(blank=True)),
                ('img_data', models.TextField(blank=True)),
                ('account', models.ForeignKey(related_name=b'profile', to='worx.Account')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
