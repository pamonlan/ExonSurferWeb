from django.contrib import admin
from .models import Gene, Transcript

class GeneAdmin(admin.ModelAdmin):
    search_fields = ['gene_id', 'gene_name', 'gene_biotype','species']

class TranscriptAdmin(admin.ModelAdmin):
    search_fields = ['transcript_id', 'transcript_name', 'transcript_biotype','gene_name','species']


# Register your models here.
admin.site.register(Gene, GeneAdmin)
admin.site.register(Transcript, TranscriptAdmin)
