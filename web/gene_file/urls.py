
"""
ExonSurferWeb.PrimerBlast URL

"""
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required, permission_required

urlpatterns = [
    #path('select_gene/', views.SelectGeneSpeciesView.as_view(), name="select_gene"),
    path('primerblast/upload/', views.GeneFileUploadView.as_view(), name="primerblast_upload"),

]
