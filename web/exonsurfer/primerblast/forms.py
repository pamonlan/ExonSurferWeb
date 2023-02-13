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
    
    HUMAN_CHOICES = Gene.objects.filter(species="Homo_sapiens", gene_biotype = "protein_coding").values_list("gene_name","gene_name")
    MOUSE_CHOICES = Gene.objects.filter(species="Mus_musculus",gene_biotype = "protein_coding").values_list("gene_name","gene_name")
    RAT_CHOICES = Gene.objects.filter(species="Rattus_norvegicus",gene_biotype = "protein_coding").values_list("gene_name","gene_name")
    #SYMBOL_CHOICES = human_symbol + mouse_symbol + rat_symbol
    print("[+] Human Symbol")
    print(RAT_CHOICES)
    human_symbol = forms.ChoiceField(label='Gene Symbol', choices=HUMAN_CHOICES, required=True)
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
        super(PrimerBlastForm, self).__init__(*args, **kwargs)

        ### Select Public DataSet ###
        try:
            data = ensembl.create_ensembl_data(release = 108, species = self.species)
            gene_obj = ensembl.get_gene_by_symbol(self.symbol, data)
            print(gene_obj)
            all_transcripts = ensembl.get_transcript_from_gene(gene_obj)
            coding_transcripts = ensembl.get_coding_transcript(all_transcripts)
            lT = [x.id for x in coding_transcripts]
            if len(lT) > 1:
                lT = ["ALL",] + lT
            TRANSCRIPT_CHOICES = list(zip(lT,lT))
            #TRANSCRIPT_CHOICES = list(Transcript.objects.filter(gene_name=self.symbol).values_list("transcript_id","transcript_id"))

        except Exception as error:
            print("Error in PrimerBlastForm")
            print(error)
            TRANSCRIPT_CHOICES =[]
        
        finally:
            transcript = forms.ChoiceField(label='Transcript', choices=TRANSCRIPT_CHOICES)
            self.fields['transcript'] = transcript


    



