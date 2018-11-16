# Generated by Django 2.1.1 on 2018-11-16 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('age', models.DecimalField(decimal_places=2, max_digits=6, null=True)),
                ('gender', models.DecimalField(decimal_places=2, max_digits=6, null=True)),
            ],
        ),
    ]
