from django.db import models
from primerblast.models import Session
from gene_file.models import GeneFile
import uuid
import django_rq

# Create your models here.

class PrimerJob(models.Model):
    """
    Model for a primer job.
    Give a session id, this model will store the job information.
    """
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    job_id = models.UUIDField(editable = True, unique = True, null=True, blank = True, default = uuid.uuid4)
    job_status = models.CharField(max_length=100)
    job_description = models.CharField(max_length=100)
    job_result = models.CharField(max_length=100)
    job_error = models.CharField(max_length=100)
    job_time = models.DateTimeField(auto_now_add=True)
    job_queue = models.CharField(max_length=100)


    def __str__(self):
        return str(self.session_id.session_id)
    
    def set_session(self, session):
        self.session_id = session
        self.save()

    def queue_job(self):
        self.job_status = 'queued'
        #Depend in the number of primers to design, the job will be queued
        #in a different queue (High,Low)

        #Get the number of primers to design (High >= 3000)
        num_primers = self.session_id.get_nprimers()

        #Check is session is from_file if it get the GeneFile object
        if self.session_id.from_file:
            gene_path = GeneFile.objects.get(session_id=self.session_id)
            gene_path = gene_path.get_gene_file_path()
        else:
            gene_path = None

        if num_primers >= 3000:
            self.job_queue = 'high'
            queue = django_rq.get_queue('high')
        else:
            self.job_queue = 'low'
            queue = django_rq.get_queue('low')
        #Enqueue the job, with the gene file path
        print("[+] Enqueuing job", flush=True)
        print("[+] Gene file path", gene_path, flush=True)
        job = queue.enqueue(self.run_session,gene_file=gene_path)
        print("[+] Job queued", flush=True)
        print(job.id, flush=True)
        print(job, flush=True)
        self.job_id = job.id
        self.save()

    def rerun_job(self):
        self.job_status = 'queued'
        self.job_error = ''
        self.job_result = ''
        self.save()
        self.queue_job()

    def cancel_job(self):
        queue = django_rq.get_queue('default')
        job = queue.fetch_job(str(self.job_id))
        if job:
            job.delete()
            self.job_status = 'cancelled'
            self.save()
            print("[+] Job cancelled", flush=True)

    def run_session(self, gene_file=None):
        """
        Run a session for primerblast
        """
        self.set_running()
        # Run PrimerBlast from session id
        session = self.session_id
        # Obtain primer results from the session
        df_blast, df_primers, error_log = session.run_session(gene_file=gene_file)
            
        if (df_primers is None):
            print("[!] Primer design failed", flush=True)
            #Redirect to error page indicating the error_log
            self.set_error(error_log)
        else:
            print("[+] Primer design successful", flush=True)
            #Redirect to results page
            self.set_complete()

    def set_running(self):
        self.job_status = 'running'
        self.save()

    def set_error(self, error_log):
        self.job_status = 'error'
        self.job_error = error_log
        self.save()

    def set_complete(self):
        self.job_status = 'complete'
        self.save()

    