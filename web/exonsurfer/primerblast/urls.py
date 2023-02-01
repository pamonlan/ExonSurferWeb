
"""
ExonSurferWeb.PrimerBlast URL

"""
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required, permission_required

urlpatterns = [
    path('select_gene/', views.SelectGeneSpeciesView.as_view(), name="select_gene"),
    path('primerblast/<str:species>/<str:symbol>/', views.PrimerBlastView.as_view(), name="primerblast"),
    path('primerblast/<slug:session_slug>/', views.ExonSurferView.as_view(), name="runprimerblast"),
    path('json_list/<slug:identifier>/', views.ListJson, name = "results_json"),
]
