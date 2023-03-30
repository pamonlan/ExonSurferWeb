from django.shortcuts import render
from django.http import HttpResponse, FileResponse
import os

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