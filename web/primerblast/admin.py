from django.contrib import admin
from .models import PrimerConfig, Session, Result
# Register your models here.
admin.site.register(PrimerConfig)
admin.site.register(Session)
admin.site.register(Result)

