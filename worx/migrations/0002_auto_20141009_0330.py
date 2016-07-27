# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('worx', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('written_on', models.DateTimeField(auto_now_add=True)),
                ('message_text', models.TextField()),
            ],
            options={
                'ordering': ['-written_on'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MessageImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('img_data', models.TextField()),
                ('on_message', models.ForeignKey(related_name=b'images', to='worx.Message')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reported_on', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=128)),
                ('longitude', models.FloatField()),
                ('latitude', models.FloatField()),
                ('reported_by', models.ForeignKey(related_name=b'reports', to='worx.Account')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('account', models.ForeignKey(related_name=b'watching', to='worx.Account')),
                ('report', models.ForeignKey(related_name=b'observers', to='worx.Report')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='message',
            name='about_report',
            field=models.ForeignKey(related_name=b'messages', to='worx.Report'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='reply_to',
            field=models.ForeignKey(related_name=b'replies', blank=True, to='worx.Message', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='written_by',
            field=models.ForeignKey(related_name=b'messages', to='worx.Account'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='account',
            name='passphrase',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='profile',
            name='account',
            field=models.OneToOneField(related_name=b'profile', to='worx.Account'),
        ),
    ]
