from django.urls import path

from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('export-csv/', views.ExportSessionsCSV.as_view(), name='export_sessions_csv'),
]