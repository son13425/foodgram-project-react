# Generated by Django 2.2.16 on 2022-09-17 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20220917_2045'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_subscribed',
        ),
        migrations.AlterField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False),
        ),
    ]