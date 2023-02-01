# Generated by Django 3.2 on 2023-01-20 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gene_name', models.CharField(max_length=100)),
                ('gene_version', models.CharField(max_length=100)),
                ('gene_id', models.CharField(max_length=100)),
                ('gene_biotype', models.CharField(max_length=100)),
                ('transcript_id', models.CharField(max_length=100)),
                ('feature', models.CharField(max_length=100)),
                ('start', models.IntegerField()),
                ('end', models.IntegerField()),
                ('strand', models.IntegerField()),
                ('source', models.CharField(max_length=100)),
                ('species', models.CharField(default='homo_sapiens', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Transcript',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transcript_name', models.CharField(max_length=100)),
                ('transcript_version', models.CharField(max_length=100)),
                ('transcript_id', models.CharField(max_length=100)),
                ('transcript_biotype', models.CharField(max_length=100)),
                ('gene_id', models.CharField(max_length=100)),
                ('gene_name', models.CharField(max_length=100)),
                ('species', models.CharField(default='homo_sapiens', max_length=100)),
            ],
        ),
    ]
