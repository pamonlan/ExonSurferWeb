from django_cron import CronJobBase, Schedule
from django.core.management import call_command

class PrimerJobRunner(CronJobBase):
    RUN_EVERY_MINS = 0.1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'primer_queue.primer_job_runner'

    def do(self):
        print("Running job queue...")
        
        call_command('job_queue')