# Generated by Django 2.2.10 on 2021-07-22 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0008_publisher_updated_by'),
    ]

    operations = [
        migrations.RenameField(
            model_name='publisher',
            old_name='created',
            new_name='created_at',
        ),
        migrations.AddField(
            model_name='publisher',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
