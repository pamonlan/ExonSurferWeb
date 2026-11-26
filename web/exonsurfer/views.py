from django.shortcuts import render
from django.http import HttpResponse, FileResponse
import os
from .settings import DATA_DIR
from primer_queue.models import PrimerJob
import pandas as pd

#Index view
def index(request):
    """
    Index view
    """
    return render(request, 'exonsurfer/index.html')

def privacy(request):
    """
    Privacy view
    """
    return render(request, 'exonsurfer/privacy_en.html')

def imprint(request):
    """
    Imprint view
    """
    return render(request, 'exonsurfer/imprint.html')

def references(request):
    """
    References view
    """
    return render(request, 'exonsurfer/references.html')

def news(request):
    """
    References view
    """
    return render(request, 'exonsurfer/news.html')

def faq(request):
    """
    FAQ view
    """
       # Query the database for completed jobs and include related fields
    PrimerJobs = pd.DataFrame(PrimerJob.objects.filter(job_status='complete').values_list('job_running_time', 'job_queue',
                                                                                                'session_id__primer_config__primer_pairs_number'))

    # Convert the QuerySet to a DataFrame
    PrimerJobs.columns = ['job_running_time', 'job_queue', 'primer_pairs_number']
    # Group by 'primer_pairs_number' and calculate the mean of 'job_running_time'
    average_times_df = PrimerJobs.groupby('primer_pairs_number').job_running_time.mean().reset_index()

    # Convert DataFrame to list of tuples (if needed for the template)
    average_times_list = list(average_times_df.itertuples(index=False, name=None))
    # Filter to keep only equal to 3000, 1000, and 100
    average_times_list = [x for x in average_times_list if x[0] in [3000, 1000, 100]]

    # Pass the averages to the template context
    context = {
        'average_times': average_times_list
    }
    return render(request, 'exonsurfer/FAQ.html', context)


def download_log_file(request):
    log_file_path = '/home/app/web/gunicorn-access.log'
    
    if not os.path.exists(log_file_path):
        return HttpResponse("Log file does not exist.")
    #Check that user is super_user
    if not request.user.is_superuser:
        return HttpResponse("You are not allowed to download log files.")
    else:
        with open(log_file_path, 'rb') as log_file:
            response = HttpResponse(log_file.read(), content_type='application/force-download')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(log_file_path)}'

        return response
    
def download_django_log_file(request):
    log_file_path = os.path.join(DATA_DIR, 'django.log')

    
    if not os.path.exists(log_file_path):
        return HttpResponse("Log file does not exist.")
    #Check that user is super_user
    if not request.user.is_superuser:
        return HttpResponse("You are not allowed to download log files.")
    else:
        with open(log_file_path, 'rb') as log_file:
            response = HttpResponse(log_file.read(), content_type='application/force-download')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(log_file_path)}'

        return response