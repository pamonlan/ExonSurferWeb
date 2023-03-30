"""exonsurfer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from primerblast import views as primerblast_views

urlpatterns = [
    path('', primerblast_views.SelectGeneSpeciesView.as_view(), name = "index"),
    path('privacy/', views.privacy, name = "privacy"),
    path('imprint/', views.imprint, name = "imprint"),
    path('references/', views.references, name = "references"),
    path('admin/', admin.site.urls),
    path('design/', include('primerblast.urls')),
    path('primer_queue/', include('primer_queue.urls')),
    path('gene_file/', include('gene_file.urls')),
    path('django-rq/', include('django_rq.urls')),
    path('download-log-file/', views.download_log_file, name='download_log_file'),
]
