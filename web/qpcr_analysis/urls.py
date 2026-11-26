from django.urls import path
from . import views
 
app_name = "qpcr_analysis"
 
urlpatterns = [
    path("qpcr_analysis/", views.index, name="qpcr_analysis"),
    path("example/", views.download_example, name="download_example"),
    path("parse/", views.parse_excel, name="parse_excel"),
    path("groups/", views.get_groups, name="get_groups"),
    path("run/", views.run_analysis, name="run_analysis"),
]
 