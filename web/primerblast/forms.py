# Form from which the user can submit a query sequence to Primer-BLAST
from django import forms
from ensembl.models import Gene, Transcript
from primerblast.models import PrimerConfig, Session, Result
from ExonSurfer.ensembl import ensembl


class SpeciesGeneForm(forms.Form):
    """
    Form for selecting the species and the gene
    Attributes:
        Species: the species of the gene String
        Symbol: the gene symbol of the gene String
    """
    # The species of the gene
    SPECIES_CHOICES = [("homo_sapiens","Homo Sapiens"),
                       ("mus_musculus","Mus Musculus"),
                       ("rattus_norvegicus","Rattus Norvegicus"),
                       ("drosophila_melanogaster","Drosophila melanogaster"),
                       ("arabidopsis_thaliana","Arabidopsis thaliana")]
    
    gene_field = forms.CharField(max_length=50)
    use_masked_genomes = forms.BooleanField(label='Maskared Genomes', required=False)

    
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


class SpeciesGeneFormOld(forms.Form):
    """
    Form for selecting the species and the gene
    Attributes:
        Species: the species of the gene
        Symbol: the gene symbol of the gene
    """
    # The species of the gene
    SPECIES_CHOICES = [("homo_sapiens","Homo Sapiens"),
                       ("mus_musculus","Mus Musculus"),
                       ("rattus_norvegicus","Rattus Norvegicus"),
                       ("drosophila_melanogaster","Drosophila melanogaster"),
                       ("arabidopsis_thaliana","Arabidopsis thaliana")]

    species = forms.ChoiceField(label='Species', choices=SPECIES_CHOICES, initial=SPECIES_CHOICES[0][0])
    # The gene symbol of the gene
    try:
        lChrHuman = ('1', '2', '3', '4', '5', '6', '7', 'X', '8', '9', '11', '10', '12','13', '14', '15', '16', '17', '18', '20', '19', 'Y', '22', '21')
        lChrRat = ('1', '2', '4', '3', '5', 'X', '6', '7', '8', '9', '10', '13', '14','15', '17', '11', '16', '18', '19', '20', '12', 'Y')
        lChrMouse = ('1', '2', 'X', '3', '4', '5', '6', '7', '10', '8', '14', '9', '11', '13', '12', '15', '16', '17', 'Y', '18', '19')

        HUMAN_CHOICES = Gene.objects.filter(species="homo_sapiens", gene_biotype = "protein_coding", seqname__in=lChrHuman).values_list("gene_name","gene_name")
        MOUSE_CHOICES = Gene.objects.filter(species="mus_musculus",gene_biotype = "protein_coding", seqname__in=lChrMouse).values_list("gene_name","gene_name")
        RAT_CHOICES = Gene.objects.filter(species="rattus_norvegicus",gene_biotype = "protein_coding",seqname__in=lChrRat).values_list("gene_name","gene_name")
        FLY_CHOICES = Gene.objects.filter(species="drosophila_melanogaster",gene_biotype = "protein_coding").values_list("gene_name","gene_name")
        ARABIDOPSIS_CHOICES = Gene.objects.filter(species="arabidopsis_thaliana",gene_biotype = "protein_coding").values_list("gene_name","gene_name")

        
        #Filter RAT_CHOICES with empty gene_name
        RAT_CHOICES = [x for x in RAT_CHOICES if x[0] != '']
        #Filter MOUSE_CHOICES with empty gene_name
        MOUSE_CHOICES = [x for x in MOUSE_CHOICES if x[0] != '']
        #Filter HUMAN_CHOICES with empty gene_name
        HUMAN_CHOICES = [x for x in HUMAN_CHOICES if x[0] != '']
        #Filter FLY_CHOICES with empty gene_name
        FLY_CHOICES = [x for x in FLY_CHOICES if x[0] != '']
        #Filter ARABIDOPSIS_CHOICES with empty gene_name
        ARABIDOPSIS_CHOICES = [x for x in ARABIDOPSIS_CHOICES if x[0] != '']
        #Sort alphabetically the gene_name of each species
        HUMAN_CHOICES = sorted(HUMAN_CHOICES, key=lambda x: x[0])
        MOUSE_CHOICES = sorted(MOUSE_CHOICES, key=lambda x: x[0])
        RAT_CHOICES = sorted(RAT_CHOICES, key=lambda x: x[0])
        FLY_CHOICES = sorted(FLY_CHOICES, key=lambda x: x[0])
        ARABIDOPSIS_CHOICES = sorted(ARABIDOPSIS_CHOICES, key=lambda x: x[0])

        
    except Exception as error:
        print("[!] Error in SpeciesGeneForm")
        print(error)
        HUMAN_CHOICES = []
        MOUSE_CHOICES = []
        RAT_CHOICES = []
        FLY_CHOICES = []
        ARABIDOPSIS_CHOICES = []
    #SYMBOL_CHOICES = human_symbol + mouse_symbol + rat_symbol
    human_symbol = forms.ChoiceField(label='Gene Symbol', choices=HUMAN_CHOICES, required=False)
    mouse_symbol = forms.ChoiceField(label='Gene Symbol', choices=MOUSE_CHOICES, required=False)
    rat_symbol = forms.ChoiceField(label='Gene Symbol', choices=RAT_CHOICES, required=False)
    fly_symbol = forms.ChoiceField(label='Gene Symbol', choices=FLY_CHOICES, required=False)
    arabidopsis_symbol = forms.ChoiceField(label='Gene Symbol', choices=ARABIDOPSIS_CHOICES, required=False)
    use_masked_genomes = forms.BooleanField(label='Maskared Genomes', required=False)
    #maskared_genomes = forms.BooleanField(label='Maskared Genomes', required=False)


