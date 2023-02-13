# Generated by Django 3.2 on 2023-02-01 19:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('primerblast', '0005_primerconfig_primer_product_size_opt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='primerconfig',
            name='primer_product_size_max',
            field=models.IntegerField(default=250),
        ),
        migrations.AlterField(
            model_name='primerconfig',
            name='primer_product_size_min',
            field=models.IntegerField(default=170),
        ),
        migrations.AlterField(
            model_name='primerconfig',
            name='primer_product_size_opt',
            field=models.IntegerField(default=200),
        ),
    ]