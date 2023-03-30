# Form from which the user can submit a query sequence to Primer-BLAST
from django import forms
from ensembl.models import Gene, Transcript
from primerblast.models import PrimerConfig, Session, Result
from ExonSurfer.ensembl import ensembl

class SpeciesGeneForm(forms.Form):
    """
    Form for selecting the species and the gene
    Attributes:
        Species: the species of the gene
        Symbol: the gene symbol of the gene
    """
    # The species of the gene
    SPECIES_CHOICES = [("homo_sapiens","Homo Sapiens"),
                       ("mus_musculus","Mus Musculus"),
                       ("rattus_norvegicus","Rattus Norvegicus")]

    species = forms.ChoiceField(label='Species', choices=SPECIES_CHOICES, initial=SPECIES_CHOICES[0][0])
    # The gene symbol of the gene
    try:
        HUMAN_CHOICES = Gene.objects.filter(species="homo_sapiens", gene_biotype = "protein_coding").values_list("gene_name","gene_name")
        MOUSE_CHOICES = Gene.objects.filter(species="mus_musculus",gene_biotype = "protein_coding").values_list("gene_name","gene_name")
        RAT_CHOICES = Gene.objects.filter(species="rattus_norvegicus",gene_biotype = "protein_coding").values_list("gene_name","gene_name")
        
        #Filter RAT_CHOICES with empty gene_name
        RAT_CHOICES = [x for x in RAT_CHOICES if x[0] != '']
        #Filter MOUSE_CHOICES with empty gene_name
        MOUSE_CHOICES = [x for x in MOUSE_CHOICES if x[0] != '']
        #Filter HUMAN_CHOICES with empty gene_name
        HUMAN_CHOICES = [x for x in HUMAN_CHOICES if x[0] != '']

        #Sort alphabetically the gene_name of each species
        HUMAN_CHOICES = sorted(HUMAN_CHOICES, key=lambda x: x[0])
        MOUSE_CHOICES = sorted(MOUSE_CHOICES, key=lambda x: x[0])
        RAT_CHOICES = sorted(RAT_CHOICES, key=lambda x: x[0])
        
    except Exception as error:
        print("[!] Error in SpeciesGeneForm")
        print(error)
        HUMAN_CHOICES = []
        MOUSE_CHOICES = []
        RAT_CHOICES = []
    #SYMBOL_CHOICES = human_symbol + mouse_symbol + rat_symbol
    human_symbol = forms.ChoiceField(label='Gene Symbol', choices=HUMAN_CHOICES, required=False)
    mouse_symbol = forms.ChoiceField(label='Gene Symbol', choices=MOUSE_CHOICES, required=False)
    rat_symbol = forms.ChoiceField(label='Gene Symbol', choices=RAT_CHOICES, required=False)
    #maskared_genomes = forms.BooleanField(label='Maskared Genomes', required=False)


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
        exclude = ['id', ]

    def __init__(self, *args, **kwargs):
        self.symbol = kwargs.pop('symbol', None)
        self.species = kwargs.pop('species', None)
        self.lT = kwargs.pop('lT', None)
        super(PrimerBlastForm, self).__init__(*args, **kwargs)

        ### Select Public DataSet ###
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


    



