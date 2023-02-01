# Form from which the user can submit a query sequence to Primer-BLAST
from django import forms
from ensembl.models import Gene, Transcript
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
    symbol = forms.CharField(label='Gene Symbol', max_length=100)


class PrimerBlastForm(forms.Form):
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
    def __init__(self, *args, **kwargs):
        self.symbol = kwargs.pop('symbol', None)
        self.species = kwargs.pop('species', None)
        super(PrimerBlastForm, self).__init__(*args, **kwargs)

        ### Select Public DataSet ###
        try:
            data = ensembl.create_ensembl_data(release = 108)
            gene_obj = ensembl.get_gene_by_symbol(self.symbol, data)
            print(gene_obj)
            all_transcripts = ensembl.get_transcript_from_gene(gene_obj)
            coding_transcripts = ensembl.get_coding_transcript(all_transcripts)
            lT = [x.id for x in coding_transcripts]
            TRANSCRIPT_CHOICES = list(zip(lT,lT))
            #TRANSCRIPT_CHOICES = list(Transcript.objects.filter(gene_name=self.symbol).values_list("transcript_id","transcript_id"))

        except Exception as error:
            print("Error in PrimerBlastForm")
            print(error)
            TRANSCRIPT_CHOICES =[]
        
        finally:
            transcript = forms.ChoiceField(label='Transcript', choices=TRANSCRIPT_CHOICES)
            self.fields['transcript'] = transcript

    # The primer size
    primer_opt_size = forms.IntegerField(label='Primer Optimal Size', min_value=17, max_value=35, initial=20)
    primer_min_size = forms.IntegerField(label='Primer Minimum Size', min_value=17, max_value=35, initial=17)
    primer_max_size = forms.IntegerField(label='Primer Maximum Size', min_value=17, max_value=35, initial=35)

    # The primer melting temperature
    primer_opt_tm = forms.FloatField(label='Primer Optimal Melting Temperature', min_value=57.5, max_value=60.5, initial=59)
    primer_min_tm = forms.FloatField(label='Primer Minimum Melting Temperature', min_value=57.5, max_value=60.5, initial=57.5)
    primer_max_tm = forms.FloatField(label='Primer Maximum Melting Temperature', min_value=57.5, max_value=60.5, initial=60.5)

    # The primer GC content
    primer_opt_gc = forms.FloatField(label='Primer Optimal GC Content', min_value=20, max_value=80, initial=50)
    primer_min_gc = forms.FloatField(label='Primer Minimum GC Content', min_value=20, max_value=80, initial=20)
    primer_max_gc = forms.FloatField(label='Primer Maximum GC Content', min_value=20, max_value=80, initial=80)

    # The product size
    primer_product_size_min = forms.IntegerField(label='Product Minimum Size', min_value=80, max_value=170, initial=80)
    primer_product_size_max = forms.IntegerField(label='Product Maximum Size', min_value=80, max_value=170, initial=170)



