from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, Http404, JsonResponse
from django.views.generic import (View, CreateView, ListView, DeleteView)
from .models import PrimerJob
from ensembl.models import Transcript, Gene
from primerblast.management.transcript_info import get_specie
from primerblast.models import Session
from datetime import datetime

# Create your views here.
# View to display the status of the specified job

class JobStatusView(View):
    """
    View to show the status of a job.
    The view has to show the Session ID, the job ID, the job status, 
    the job description, the job result, the job error, and the job time.
    The frim fom the running in seconds should be displayed as well.

    The gene, transcipt, species, and primer type should be displayed as well.
    
    The view should also have a button to delete the job.
    """
    template_name = 'primer_queue/job_status.html'

    def get(self, request, session_slug):
        try:
            session = Session.objects.get(session_id=session_slug)
            job = PrimerJob.objects.get(session_id=session)
            #Get gene, transcript, species, and primer type
            try:
                gene = Gene.objects.get(gene_name=session.symbol, species=get_specie(session.species))
            except:
                gene = None
            # Obtain PrimerJob from session
            #Obtain symbol, transcript and species from the session

        except Exception as error:
            print("[!] Error in JobStatusView",flush=True)
            print(error)
            context = {}

            raise Http404(f'Error in the JobStatusView: {error}...!')
        else:
            # If the job is complete, redirect to the results page
            if job.job_status == 'complete':
                return redirect('runprimerblast', session_slug=session_slug)
            else:
                # Get the job time
                job_time = job.job_start_time
                # Get the current time
                current_time = datetime.now()
                if job_time:
                    # Get the time difference
                    time_difference = current_time - job_time.replace(tzinfo=None)
                    # Get the time difference in seconds
                    time_difference_seconds = time_difference.total_seconds()
                    try:
                        job_predicted_time = job.job_predicted_time
                        # Get the progress percentage
                        progress_percentage = (time_difference_seconds/job_predicted_time)*100
                        # Get the progress percentage rounded to 2 decimal places, and if it is greater than 100, set it to 100
                        progress_percentage = round(progress_percentage, 2)
                        if progress_percentage > 100:
                            progress_percentage = 99
                    except Exception as error:
                        print("[!] Error in JobStatusView",flush=True)
                        print(error)
                        progress_percentage = 60
                        job_predicted_time = False

                context = {
                    'session': session,
                    'job': job,
                    'time_difference_seconds': time_difference_seconds,
                    'progress_percentage': progress_percentage,
                    'job_predicted_time': round(job_predicted_time, 0),
                }
                context["species"] = session.species
                context["symbol"] = session.symbol
                context["transcript"] = session.transcript
                context["primer_config"] = session.primer_config
                context["gene"] = gene
                return render(request, self.template_name, context)

def cancel_job(request, job_id):
    job = get_object_or_404(PrimerJob, id=job_id)
    job.cancel_job()  # cancel the job
    return redirect('jobstatus', session_slug=job.session_id.session_id)

def re_run_job(request, job_id):
    job = get_object_or_404(PrimerJob, id=job_id)
    job.re_run_job()  # re-run the job
    return redirect('jobstatus', session_slug=job.session_id.session_id)