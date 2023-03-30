from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .forms import GeneFileForm
from .models import GeneFile
from primerblast.models import PrimerConfig, Session
from primer_queue.models import PrimerJob
from django.contrib import messages


class GeneFileUploadView(TemplateView):
    template_name = "gene_file/gene_file_upload.html"

    def get(self, request):
        
        form = GeneFileForm()
        #Context
        context = {}
        context["form"] = form
        context["title"] = "Assign design parameters"

        return render(request, self.template_name, context)

    def post(self, request):
        form = GeneFileForm(request.POST, request.FILES)
        context = {'form': form}

        if form.is_valid():
            dForm = form.cleaned_data
            print("[+] Form is valid", flush=True)
            #Obtain Species, Gene Symbol
            species = dForm['species']
            symbol = dForm['gene_symbol']
            transcript = ["ALL"]
            try:
                # Create an instance of PrimerConfig model
                primer_config = PrimerConfig().from_dict(dForm)
                print("[+] Creating session for: ", species, symbol, transcript, flush=True)
                session = Session.create_session(species, symbol, transcript)
                session.set_design_config(primer_config)
                session.set_from_file()
                session.save()
                # Create an instance of GeneFile model
                gene_file = GeneFile()
                gene_file.from_file(dForm['file'], session)

            except Exception as e:
                print("[-] Error in GeneFileUploadView: ", e, flush=True)
            else:
                print("[+] Session created: ", session.session_id, flush=True)
                # Render success message
                        # Queu the primer design
                job = PrimerJob()
                job.set_session(session)
                job.queue_job()  
        
                print("[+] Redirecting to the next step", flush=True)
                return redirect('jobstatus', session_slug=session.session_id)
        else:
            print("[!] Error in the form", flush=True)
            print(form.errors, flush=True)
            messages.warning(request,form.errors)
            context["title"] = "Assign design parameters"



        return render(request, template_name=self.template_name, context=context)
