from django.db import models
from primerblast.models import Session
from gene_file.models import GeneFile
import uuid
import django_rq
from django.utils import timezone
import pandas as pd
import uuid
import pandas as pd
from django.db import models
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
# Create your models here.

class PrimerJob(models.Model):
    """
    Model for a primer job.
    Give a session id, this model will store the job information.
    """
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    job_id = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    job_status = models.CharField(max_length=100)
    job_description = models.CharField(max_length=100)
    job_result = models.CharField(max_length=100)
    job_error = models.CharField(max_length=100)
    job_time = models.DateTimeField(auto_now_add=True)
    job_start_time = models.DateTimeField(auto_now_add=True)
    job_finish_time = models.DateTimeField(auto_now_add=True)
    job_running_time = models.FloatField(blank=True, null=True)
    job_predicted_time = models.FloatField(blank=True, null=True)
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
        return job

    def re_run_job(self):
        self.job_status = 'queued'
        self.job_error = ''
        self.job_result = ''
        self.save()
        self.queue_job()

    def cancel_job(self):
        queue = django_rq.get_queue(self.job_queue)
        job = queue.fetch_job(str(self.session_id.enqueued_job_id))
        print("[+] Job id", str(self.session_id.enqueued_job_id), flush=True)
        if job:
            job.delete()
            self.job_status = 'cancelled'
            self.save()
            print("[+] Job cancelled", flush=True)


    def run_session(self, gene_file=None, job=None):
        """
        Run a session for primerblast
        """
        self.get_predicted_time_v2()
        self.set_running()
        self.set_start_time()
        # Run PrimerBlast from session id
        session = self.session_id
        # Obtain primer results from the session
        try:
            df_blast, genomic_blast, df_primers, error_log = session.run_session(gene_file=gene_file)
        except Exception as e:
            print("[!] Error in run_session", e, flush=True)
            self.set_error(str(e))
            return
            
        if (df_primers is None):
            print("[!] Primer design failed", flush=True)
            #Redirect to error page indicating the error_log
            self.set_error(error_log)
        else:
            print("[+] Primer design successful", flush=True)
            #Redirect to results page
            self.set_complete()
            self.set_finish_time()
            self.set_total_time()

    def set_start_time(self):
        self.job_start_time = timezone.now()
        self.save()

    def set_finish_time(self):
        self.job_finish_time = timezone.now()
        self.save()


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

    def set_total_time(self):
        self.job_running_time = self.get_running_time()
        self.save()


    def get_running_time(self):
        """
        Get the running time of the job in seconds
        """
        return (self.job_finish_time - self.job_start_time).total_seconds()
    


    def get_predicted_time_v2(self):
        """
        Get the predicted time of the job in seconds.
        For that, query all the complete jobs in the queue, and fit a linear regression
        Use the species, queue, design, number of transcripts, and number of primers to predict the time
        """
        # Get the number of primers and number of transcripts
        n_primers = self.session_id.primer_config.primer_pairs_number
        n_transcripts = self.session_id.get_number_of_transcripts_for_gene()

        try:
            print("[+] Querying jobs", flush=True)
            PrimerJobs = pd.DataFrame(PrimerJob.objects.filter(job_status='complete').values_list('job_running_time', 'job_queue',
                                                                                                'session_id__primer_config__primer_pairs_number',
                                                                                                'session_id__n_transcript',
                                                                                                'session_id__primer_config__primer_e_cutoff',
                                                                                                'session_id__species'))
            print("[+] Querying jobs successful", flush=True)
            PrimerJobs.columns = ['job_running_time', 'job_queue', 'primer_pairs_number', 'n_transcripts', 'e_value', 'species']
            print("[+] PrimerJobs", PrimerJobs.head(), flush=True)
            PrimerJobs['primer_pairs_number'] = PrimerJobs['primer_pairs_number'].astype(int)
            PrimerJobs['job_running_time'] = PrimerJobs['job_running_time'].astype(float)
            PrimerJobs['n_transcripts'] = PrimerJobs['n_transcripts'].astype(int)
            #Drop the rows with NaN
            PrimerJobs = PrimerJobs.dropna()
            
            print("[+] Obtained PrimerJobs", flush=True)
        except Exception as e:
            print("[!] Error querying jobs", e, flush=True)
            PrimerJobs = pd.DataFrame()

        if not PrimerJobs.empty:
            try:
                # Fit a linear regression
                # Encode the species categorical with a dictionary and map it
                dSp = dict(zip(PrimerJobs['species'].unique(), range(len(PrimerJobs['species'].unique()))))
                PrimerJobs['species'] = PrimerJobs['species'].map(dSp)
                # Encode the queue categorical with a dictionary and map it
                dQ = dict(zip(PrimerJobs['job_queue'].unique(), range(len(PrimerJobs['job_queue'].unique()))))
                PrimerJobs['job_queue'] = PrimerJobs['job_queue'].map(dQ)


                X = PrimerJobs[['job_queue', 'primer_pairs_number', 'n_transcripts','e_value', 'species']]
                Y = PrimerJobs['job_running_time']

                # Create a pipeline
                lr = LinearRegression()

                # Fit the pipeline
                lr.fit(X, Y)
                print("[+] Pipeline fitted", flush=True)
                # Predict the time
                # Create a list with the values to predict, taking in coun the dictionary
                lP = [dQ[self.job_queue], n_primers, n_transcripts, self.session_id.get_e_value(),dSp[self.session_id.species]]
                print(lr.predict([lP]))
                time_predicted = round(lr.predict([lP])[0],3)
                self.job_predicted_time = float(time_predicted)
                self.save()
                print("[+] Time predicted: ", time_predicted, flush=True)
            except Exception as e:
                print("[!] Error predicting time", e, flush=True)
                self.job_predicted_time = 80
                self.save()

        else:
            print("[!] PrimerJobs empty", flush=True)
            self.job_predicted_time = 80
            self.save()
        self.save()
    