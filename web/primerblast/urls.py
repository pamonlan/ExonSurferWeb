
"""
ExonSurferWeb.PrimerBlast URL

"""
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required, permission_required

urlpatterns = [
    #path('select_gene/', views.SelectGeneSpeciesView.as_view(), name="select_gene"),
    path('primerblast/<str:species>/<str:symbol>/', views.PrimerBlastFormView.as_view(), name="primerblast"),
    path('primerblast/<slug:session_slug>/', views.ExonSurferView.as_view(), name="runprimerblast"),
    path('error/<slug:session_slug>/', views.ErrorDesignView.as_view(), name="ed"),

    path('primerblast/primer_view/<slug:session_slug>/<str:pair>/', views.PrimerPairView.as_view(), name="primer_pair_view"),
    path('primerblast/off_target_view/<slug:session_slug>/<str:pair>/', views.PrimerPairOffTargetView.as_view(), name="off_target_view"),
    path('json_list/<slug:identifier>/', views.ListJson, name = "results_json"),

    path('exonTranscriptAlone/<str:gene>/<str:species>/', views.ExonTranscriptView_gene_species, name='ExonTranscriptView_gene_species'),
    path('exonTranscript/<uuid:session_slug>/<str:pair>/', views.ExonTranscriptView, name='ExonTranscriptView'),

    path('cdna_html/<slug:session_slug>/<str:pair>/', views.cDNATranscriptView, name="cdna_view"),
    path('off_target_html/<slug:session_slug>/<str:pair>/', views.cDNATranscriptOffView, name="off_target_html"),
    path('primerblast/download_pair/<slug:session_slug>/<str:pair>/', views.download_excel_pair, name="download_pair"),
    path('session/<slug:session_slug>/download/', views.download_session_files, name="download_session_files"),
    path('sessions/<slug:session_slug>/command/download/', views.download_session_command, name='download_session_command'),
    path('download-all/', views.download_all_sessions, name='download_all_sessions'),

    path("sessions_list/", views.SessionListView.as_view(), name="session_list"),
    path("sessions_list/<slug:search>", views.SessionListView.as_view(), name="session_list"),
    path('session/<int:pk>/update/', views.SessionUpdateView.as_view(), name='session_update'),
    path('results_table/<slug:session_slug>/', views.ResultTableView.as_view(), name='results_table'),
]
