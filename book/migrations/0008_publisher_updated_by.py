# Generated by Django 2.2.10 on 2021-07-22 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0007_auto_20210722_2017'),
    ]

    operations = [
        migrations.AddField(
            model_name='publisher',
            name='updated_by',
            field=models.CharField(default='yaozeliang', max_length=20),
        ),
    ]
