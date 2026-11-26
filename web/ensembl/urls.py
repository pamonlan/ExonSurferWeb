
"""
ExonSurferWeb.Ensembl URL

"""
from django.urls import path
from . import views
from ensembl.management.species_config import API_SPECIES


urlpatterns = [
    path(f'api/{api_url}/', views.get_genes_for_species,
         {'species_key': species_key}, name=f'api-{api_url}')
    for species_key, api_url in API_SPECIES.items()
]
