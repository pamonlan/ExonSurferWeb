from django.db import models

# Create your models here.
#Create a Gene model

class Gene(models.Model):
    """
    A gene model
    Attributes:
        strand: the strand of the gene
        gene_version: the version of the gene
        source: the source of the gene
        end: the end of the gene
        start: the start of the gene
        gene_biotype: the gene biotype of the gene
        gene_id: the gene id of the gene
        gene_name: the gene name of the gene
        feature: the feature of the gene
        species: the species of the gene
    """

    def __str__(self):
        return self.gene_name

    
    gene_name = models.CharField(max_length=100)
    gene_id = models.CharField(max_length=100)
    gene_biotype = models.CharField(max_length=100)
    feature = models.CharField(max_length=100)
    start = models.IntegerField()
    end = models.IntegerField()
    strand = models.CharField(max_length=10)
    source = models.CharField(max_length=100)
    species = models.CharField(max_length=100, default='homo_sapiens')
    
    
class Transcript(models.Model):

    """
    A transcript model
    Attributes:
        transcript_version: the version of the transcript
        transcript_id: the id of the transcript
        transcript_name: the name of the transcript
        transcript_biotype: the biotype of the transcript
        gene_id: the gene of the transcript
        gene_name: the gene name of the transcript
    """
    
    def __str__(self):
        return self.transcript_name

    transcript_name = models.CharField(max_length=100)
    transcript_id = models.CharField(max_length=100)
    transcript_biotype = models.CharField(max_length=100)
    gene_id = models.CharField(max_length=100)
    gene_name = models.CharField(max_length=100)
    species = models.CharField(max_length=100, default="homo_sapiens")
    


