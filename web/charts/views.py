# charts/views.py
import csv
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, View
from primerblast.models import Session
from primer_queue.models import PrimerJob
import pandas as pd
from datetime import timedelta

class DashboardView(UserPassesTestMixin, ListView):
    model = Session
    template_name = 'chart/dashboard.html'
    context_object_name = 'sessions'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        
        # --- Search Filter ---
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(session_id__icontains=search) |
                Q(species__icontains=search) |
                Q(symbol__icontains=search) |
                Q(transcript__icontains=search)
            )
            
        # --- Date Range Filter (New) ---
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date and end_date:
            try:
                # Assuming simple YYYY-MM-DD string from HTML input
                queryset = queryset.filter(created_at__range=[start_date, end_date])
            except:
                pass # Fallback if invalid date
                
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Fetch Job Data
        job_df = PrimerJob().query_table_data()

        # --- FIX: TypeError (Timezone Handling) ---
        if not job_df.empty:
            # Force UTC conversion to avoid mismatch errors
            job_df['job_time'] = pd.to_datetime(job_df['job_time'], utc=True)
            
            # Create a UTC-aware timestamp for comparison
            one_year_ago = pd.Timestamp.now(tz='UTC') - pd.DateOffset(days=365)
            
            # Now both sides are UTC-aware
            recent_df = job_df[job_df['job_time'] >= one_year_ago].copy()
        else:
            recent_df = pd.DataFrame()

        # 2. Key Metrics
        total_sessions = Session.objects.count()
        error_jobs = PrimerJob.objects.filter(job_status='error').count()
        
        # Success Rate
        success_rate = 0
        if total_sessions > 0:
            success_rate = round(((total_sessions - error_jobs) / total_sessions) * 100, 1)

        # Avg Jobs Per Day
        avg_jobs_day = 0
        if not job_df.empty:
            days_active = (job_df['job_time'].max() - job_df['job_time'].min()).days
            if days_active < 1: days_active = 1
            avg_jobs_day = round(len(job_df) / days_active, 1)

        # 3. System Status Indicator (New)
        # If last job was within 24 hours = Online (Green), else Offline (Red)
        system_status = "Offline"
        if not job_df.empty:
            last_job_time = job_df['job_time'].max()
            if (pd.Timestamp.now(tz='UTC') - last_job_time).days < 1:
                system_status = "Online"

        # 4. Charts Data (Using the fixed 'recent_df')
        area_data = []
        if not recent_df.empty:
            recent_df['job_month'] = recent_df['job_time'].dt.to_period('M')
            monthly_counts = recent_df.groupby('job_month').size().reset_index(name='count')
            monthly_counts = monthly_counts.sort_values('job_month')
            area_data = [{"label": str(row['job_month']), "y": row['count']} for _, row in monthly_counts.iterrows()]

        column_data = []
        pie_data = []
        if not job_df.empty:
            # Top 10 Genes
            gene_counts = job_df['symbol'].value_counts().head(10).reset_index()
            gene_counts.columns = ['symbol', 'count']
            column_data = [{"label": row['symbol'], "y": row['count']} for row in gene_counts.to_dict(orient='records')]

            # Top 5 Species
            species_counts = job_df['species'].value_counts().head(5).reset_index()
            species_counts.columns = ['species', 'count']
            # Add colors for specific species if desired
            pie_data = [{"y": row['count'], "name": row['species']} for row in species_counts.to_dict(orient='records')]

        context.update({
            "total_sessions": total_sessions,
            "error_jobs": error_jobs,
            "success_rate": success_rate,
            "avg_jobs_day": avg_jobs_day,
            "system_status": system_status,
            "area_data": area_data,
            "column_data": column_data,
            "pie_data": pie_data,
            # Pass filters back to template
            "search": self.request.GET.get('search', ''),
            "start_date": self.request.GET.get('start_date', ''),
            "end_date": self.request.GET.get('end_date', ''),
        })
        return context

# --- New View: Export CSV ---
class ExportSessionsCSV(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="exonsurfer_sessions.csv"'

        writer = csv.writer(response)
        writer.writerow(['Session ID', 'Species', 'Symbol', 'Transcript', 'Created At'])

        sessions = Session.objects.all().values_list('session_id', 'species', 'symbol', 'transcript', 'created_at')
        for session in sessions:
            writer.writerow(session)

        return response