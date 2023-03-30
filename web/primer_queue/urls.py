
"""
ExonSurferWeb.PrimerBlast URL

"""
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required, permission_required

urlpatterns = [
    #path('select_gene/', views.SelectGeneSpeciesView.as_view(), name="select_gene"),
    path('primerblast/job_queue/<slug:session_slug>/', views.JobStatusView.as_view(), name="jobstatus"),
    path('jobs/<int:job_id>/cancel/', views.cancel_job, name='cancel_job'),


]
