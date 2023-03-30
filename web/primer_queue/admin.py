from django.contrib import admin
from .models import PrimerJob

class PrimerJobAdmin(admin.ModelAdmin):
    # ... list_display and other settings ...

    def cancel_jobs(self, request, queryset):
        for job in queryset:
            job.cancel_job()
    cancel_jobs.short_description = 'Cancel selected jobs'

    def rerun_jobs(self, request, queryset):
        for job in queryset:
            job.rerun_job()
    rerun_jobs.short_description = 'Rerun selected jobs'

    actions = [cancel_jobs, rerun_jobs]

admin.site.register(PrimerJob, PrimerJobAdmin)
