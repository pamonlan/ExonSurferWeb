from django.db import models
from ensembl.management.species_config import DISPLAY_NAMES

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
        return self.gene_id

    def get_ensembl_url(self):
        return "http://www.ensembl.org/{}/Gene/Summary?db=core;g={};".format(self.get_species(), self.gene_id)
         
    def get_species(self):
        return DISPLAY_NAMES.get(self.species, self.species)
    
    def get_number_transcripts(self):
        """
        Function to obtain the number of protein coding transcripts 
        for the gene.
        """
        lT = Transcript.objects.filter(gene_name=self.gene_name, species=self.species, transcript_biotype="protein_coding")
        return len(lT)
    
    gene_name = models.CharField(max_length=100)
    gene_id = models.CharField(max_length=100)
    gene_biotype = models.CharField(max_length=100)
    feature = models.CharField(max_length=100)
    seqname = models.CharField(max_length=100)
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
        refseq_id: the RefSeq ID of the transcript
        transcript_biotype: the biotype of the transcript
        gene_id: the gene of the transcript
        gene_name: the gene name of the transcript
    """
    
    def __str__(self):
        return self.transcript_name
    
        
    def get_species(self):
        return DISPLAY_NAMES.get(self.species, self.species)
    

    def get_ensembl_url(self):
        return "http://www.ensembl.org/{}/Transcript/Summary?db=core;t={};".format(self.get_species(), self.transcript_id)


    transcript_name = models.CharField(max_length=100, blank=True, null=True)
    transcript_id = models.CharField(max_length=100)
    transcript_biotype = models.CharField(max_length=100)
    refseq_id = models.CharField(max_length=100, blank=True, null=True)
    gene_id = models.CharField(max_length=100)
    gene_name = models.CharField(max_length=100, blank=True, null=True)
    species = models.CharField(max_length=100, default="homo_sapiens")
    

class HousekeepingGene(models.Model):
    """
    Curated Top-50 reference/housekeeping genes per species for qPCR normalisation,
    100% verified against ExonSurfer's species GTF databases.
    Sources: HRT Atlas, PaGenBase, RED v1, Czechowski 2005, Mughal 2018,
             Cheng 2017, PMID-backed literature GMTs, and Ensembl/ParaSite 1-to-1 orthologs.
    """
    species          = models.CharField(max_length=100, db_index=True)
    rank             = models.IntegerField()                           # 1..50 (1 = highest priority)
    gene_id          = models.CharField(max_length=100, db_index=True)
    gene_name        = models.CharField(max_length=100)
    biotype          = models.CharField(max_length=100, blank=True, default="")
    evidence_tier    = models.CharField(max_length=50, db_index=True)  # validated_qpcr | curated_most_stable | literature_gmt | transcriptome_screen | ortholog_1to1_* | ortholog_1tomany_*
    n_sources        = models.IntegerField(default=1)
    n_datasets       = models.IntegerField(default=1)
    sources          = models.CharField(max_length=255, blank=True, default="")
    stability_metric = models.CharField(max_length=50, blank=True, default="")
    stability_value  = models.FloatField(null=True, blank=True)
    mean_expression  = models.FloatField(null=True, blank=True)
    citation         = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["species", "rank", "gene_name"]
        unique_together = [["species", "gene_id"]]

    def __str__(self):
        return f"#{self.rank} {self.gene_name} ({self.species}, {self.evidence_tier})"
