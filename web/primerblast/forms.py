# Form from which the user can submit a query sequence to Primer-BLAST
from django import forms
from ensembl.models import Gene, Transcript
from primerblast.models import PrimerConfig, Session, Result
from ExonSurfer.ensembl import ensembl
from ensembl.management.species_config import SPECIES_CHOICES, SPECIES_FIELD_MAP


class SpeciesGeneForm(forms.Form):
    """
    Form for selecting the species and the gene.
    Gene input fields are generated automatically from SPECIES_FIELD_MAP
    so adding a new species only requires updating species_config.py.
    """
    species = forms.ChoiceField(choices=SPECIES_CHOICES)
    use_masked_genomes = forms.BooleanField(label='Masked Genomes', required=False)
    use_non_protein_coding = forms.BooleanField(label="Show also non-coding protein transcripts", required=False)

# Dynamically add one CharField per species — no hardcoding needed
for _field_name in SPECIES_FIELD_MAP.values():
    if _field_name:
        SpeciesGeneForm.base_fields[_field_name] = forms.CharField(max_length=50, required=False)

    
class PrimerBlastForm(forms.ModelForm):
    """
    Form for submitting a query sequence to Primer-BLAST
    Attributes:
        Species: the species of the query sequence
        Symbol: the gene symbol of the query sequence
        Transcript: the list of transcript of the gene
        
        PRIMER_OPT_SIZE: the optimal size of the primer
        PRIMER_MIN_SIZE: the minimum size of the primer
        PRIMER_MAX_SIZE: the maximum size of the primer

        PRIMER_OPT_TM: the optimal melting temperature of the primer
        PRIMER_MIN_TM: the minimum melting temperature of the primer
        PRIMER_MAX_TM: the maximum melting temperature of the primer

        PRIMER_OPT_GC_PERCENT: the optimal GC content of the primer
        PRIMER_MIN_GC: the minimum GC content of the primer
        PRIMER_MAX_GC: the maximum GC content of the primer

        PRIMER_PRODUCT_SIZE_MIN: the minimum size of the product
        PRIMER_PRODUCT_SIZE_MAX: the maximum size of the product

    """
        ### Data From DB###
    class Meta:
        model = PrimerConfig
        exclude = ['id', 'primer_gc_clamp','primer_max_poly_x','primer_max_end_gc','primer_wt_gc_percent_gt','primer_wt_gc_percent_lt']

    def __init__(self, *args, **kwargs):
        self.symbol = kwargs.pop('symbol', None)
        self.species = kwargs.pop('species', None)
        self.lT = kwargs.pop('lT', None)
        super(PrimerBlastForm, self).__init__(*args, **kwargs)

        try:
            lT = self.lT
            print(lT)
            if len(lT) > 1:
                lT = ["ALL",] + lT
            TRANSCRIPT_CHOICES = list(zip(lT,lT))
            #TRANSCRIPT_CHOICES = list(Transcript.objects.filter(gene_name=self.symbol).values_list("transcript_id","transcript_id"))

        except Exception as error:
            print("Error in PrimerBlastForm")
            print(error)
            TRANSCRIPT_CHOICES =[]
        
        finally:
            transcript = forms.MultipleChoiceField(label='Transcript', choices=TRANSCRIPT_CHOICES)
            self.fields['transcript'] = transcript


class SessionUpdateForm(forms.ModelForm):
    blast_file = forms.FileField(required=False, label='Blast File')
    genomic_blast_file = forms.FileField(required=False, label='Genomic Blast File')
    primer_file = forms.FileField(required=False, label='Primer File')

    class Meta:
        model = Session
        fields = ['session_id', 'symbol']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        result = Result.objects.get(session=self.instance)
        self.fields['blast_file'].initial = result.BlastFile
        self.fields['genomic_blast_file'].initial = result.GenomicBlastFile
        self.fields['primer_file'].initial = result.PrimerFile


