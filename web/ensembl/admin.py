from django.contrib import admin
from .models import Gene, Transcript, HousekeepingGene

class GeneAdmin(admin.ModelAdmin):
    search_fields = ['gene_id', 'gene_name', 'gene_biotype','species']

class TranscriptAdmin(admin.ModelAdmin):
    search_fields = ['transcript_id', 'transcript_name', 'transcript_biotype','gene_name','species']

class HousekeepingGeneAdmin(admin.ModelAdmin):
    list_display = ['species', 'rank', 'gene_name', 'gene_id', 'evidence_tier', 'sources']
    list_filter = ['species', 'evidence_tier']
    search_fields = ['gene_id', 'gene_name', 'species', 'sources', 'citation']


# Register your models here.
admin.site.register(Gene, GeneAdmin)
admin.site.register(Transcript, TranscriptAdmin)
admin.site.register(HousekeepingGene, HousekeepingGeneAdmin)
