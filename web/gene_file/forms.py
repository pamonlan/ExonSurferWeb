from django import forms
from primerblast.models import PrimerConfig

class GeneFileForm(forms.ModelForm):
    """
    Form to indicate the parameters to apply to the primerblast.
    The form is based on the PrimerConfig model.
    But include the gene_file, gene_symbol, and species field.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'] = forms.FileField()

        self.fields['species'] = forms.CharField(
            label='Species',
            max_length=100)
        
    
    ### Data From DB###
    class Meta:
        model = PrimerConfig
        exclude = ['id', 'primer_gc_clamp','primer_max_poly_x','primer_max_end_gc','primer_wt_gc_percent_gt','primer_wt_gc_percent_lt']
    