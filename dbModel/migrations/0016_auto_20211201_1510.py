# Generated by Django 3.1.6 on 2021-12-01 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbModel', '0015_emp_info_entrydate'),
    ]

    operations = [
        migrations.AddField(
            model_name='day',
            name='ot_reason',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='day',
            name='ot_type',
            field=models.SmallIntegerField(choices=[(1, '不想回家'), (2, '补时长'), (3, '工作原因')], default=1),
        ),
        migrations.AlterField(
            model_name='leave',
            name='leave_type',
            field=models.SmallIntegerField(choices=[(1, '法定年假'), (2, '福利年假'), (3, '病假'), (4, '倒休'), (5, 'Compassionate leave'), (6, '计划生育假'), (7, '陪产假'), (8, '无薪假'), (9, '产检假')]),
        ),
    ]
