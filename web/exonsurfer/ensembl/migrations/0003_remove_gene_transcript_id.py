# Generated by Django 3.2 on 2023-02-01 10:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ensembl', '0002_remove_gene_gene_version'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gene',
            name='transcript_id',
        ),
    ]