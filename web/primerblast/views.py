import io
from math import exp
from multiprocessing import context
import os
from platform import release
import zipfile

import pandas as pd

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View, CreateView, ListView, DeleteView, UpdateView
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy

from ensembl.models import Transcript, Gene
from gene_file.models import GeneFile
from primer_queue.models import PrimerJob
from .forms import SpeciesGeneForm, PrimerBlastForm, SessionUpdateForm
from .management.form_control import add_css_classes_to_form_fields
from .management.transcript_info import get_exon_transcript_information, get_specie
from .management.visualization import (plot_primerpair_aligment, plot_cdna, plot_off_target, 
                                        plot_transcripts_alone, plot_transcripts_marked)
from .models import Session, PrimerConfig, Result


### Sharing Parameters
# This parameters are shared between the views
#
lCol = ['pair_num', 'forward',  'reverse', 'amplicon_size', 'amplicon_tm',
         'forward_tm', 'reverse_tm', 'forward_gc',  'reverse_gc','dimers','indiv_als',
         'detected', 'not_detected', 'pair_score', 'off_targets']

canonical_chr = {
    "homo_sapiens": [str(i) for i in range(1, 23)] + ['X', 'Y'],  # This species has chromosomes 1-22, X, and Y.
    "rattus_norvegicus": [str(i) for i in range(1, 21)] + ['X', 'Y'],
    "mus_musculus": [str(i) for i in range(1, 20)] + ['X', 'Y']  
}


pretty_names = {
            'pair_num': 'Primer Pair',
            'forward': 'Forward Primer',
            'reverse': 'Reverse Primer',
            'amplicon_size': 'Amplicon Size',
            'forward_tm': 'Forward Tm',
            'reverse_tm': 'Reverse Tm',
            'forward_gc': 'Forward GC',
            'reverse_gc': 'Reverse GC',
            'amplicon_tm': 'Amplicon Tm',
            'indiv_als': 'Individual Alignment Score',
            'other_transcripts': 'Transcript Off-target',
            'other_genes': 'Gene Off-target',
            'pair_score': 'Pair Score',
            'detected': 'Detected Transcripts',
            'not_detected': 'Not Detected Transcripts',
            'off_targets': 'Off-target Transcripts/Genes',
            'dimers': 'Dimers'
                }

lColors = ['#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#333aff', '#a65628', '#f781bf', \
     '#999999', '#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#666666']

## Landing page view
## This view is the first one to be loaded
## It allows the user to select the species and the gene

class SelectGeneSpeciesView(CreateView):
    template_name = 'exonsurfer/index.html'
    form_class = SpeciesGeneForm

    def get(self, request, *args, **kwargs):
        try:
            form = self.form_class()
            context = {
                'form': form,
                "title": "Gene and Species Selection"
            }

            # Optionally, add additional context such as REDIS_URL from environment
            context["REDIS_URL"] = os.environ.get("REDIS_URL", "")

            return render(request, self.template_name, context)
        except Exception as e:
            # Log the exception or handle it as needed
            print(f"[!] Error in GET request handling: {e}")
            raise Http404('Error while processing the request.')

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Extract the validated data
            gene_field = form.cleaned_data['gene_field']
            species = form.cleaned_data.get('species')
            use_masked_genomes = form.cleaned_data.get('use_masked_genomes', False)

            context = {
                'form': form,
                "title": "Gene and Species Selection",
                "species": species,
                "gene_field": gene_field,
                "use_masked_genomes": use_masked_genomes
            }
            # Querying your Gene model:
            try:
                gene = Gene.objects.filter((Q(gene_name=gene_field) | Q(gene_id=gene_field)) & Q(species=species) & Q(seqname__in=canonical_chr[species])).first()
                if gene:
                    # Render this view with the gene information
                    context["gene"] = gene
                    return render(request, self.template_name, context)
                else:
                    # If no gene is found,render the form with a warning message indicating the gene and species that the user input
                    messages.warning(request, f"No gene found for the specified criteria: {gene_field} in {species}")
                    return render(request, self.template_name, context)
            except Exception as e:
                # Log the exception or handle it as needed
                print(f"[!] Error in POST request handling: {e}")
                messages.error(request, "An error occurred while processing the request.")
                return render(request, self.template_name, context)
        else:
            # If form is not valid, render the form with errors
            messages.error(request, "Please correct the errors below.")
            return render(request, self.template_name, context)


## View to assign the parameters for the primer design
## Allows the user to select the transcript and the parameters for the primer design

class PrimerBlastFormView(CreateView):
    template_name = 'primerblast/primer_config_forms.html'

    def get(self, request, species, symbol):
        try:
            # Obtain the session from the DB with the session_slug (identifier)
            print("[+] Obtaining transcript list for in view: ", species, symbol, "")
            
            self.species = species
            gene = Gene.objects.get(gene_name=symbol, species=get_specie(species))
            print(gene)
            self.symbol = symbol
            lT = Transcript.objects.filter(gene_name=symbol, species=get_specie(species), transcript_biotype="protein_coding")
            #Invert list
            print(lT)

            if len(lT) == 0:
                messages.warning(request, "There is no transcript for this gene in the selected species")
                return redirect('index')

            form = PrimerBlastForm(species=get_specie(species), symbol=symbol, lT=list(lT.values_list('transcript_id', flat=True)))
            form = add_css_classes_to_form_fields(form, "form-control")
            context = {'form': form}
            context["title"] = "Assign design parameters"
            context["species"] = species
            context["gene"] = gene
            context["transcripts"] = lT

            ## Add symbol and species to the request.session
            request.session["species"] = species
            request.session["symbol"] = symbol

        except Exception as error:
            print("[!] Error in view: PrimerBlastFormView", flush=True)
            print("[!] Error: ", error, "")
            messages.warning(request, f"There is no transcript for the gene {symbol} in the {species}")
            return redirect('index')

        else:
            # We pase the session to the template with the Context Dyct

            return render(request, self.template_name, context)


    def post(self, request,species, symbol):
        # We get the filter condition
        try:
            gene = Gene.objects.get(gene_name=symbol, species=get_specie(species))
            print(gene)
            self.symbol = symbol
            lT = Transcript.objects.filter(gene_name=symbol, species=get_specie(species), transcript_biotype="protein_coding")
        except Exception as error:
            print("[!] Error obtaining the transcript list: ", error, "")
            raise Http404('Session not found...!')
        else:
            form = PrimerBlastForm(request.POST, request.FILES, species=get_specie(species), symbol=symbol,lT=list(lT.values_list('transcript_id', flat=True)))
            form = add_css_classes_to_form_fields(form, "form-control")

        context = {'form': form}
        print("[+] Obtaing POST data:")
        print(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            dForm = form.cleaned_data

            try:
                # Obtain gene, species, and transcript from the form
                transcript = dForm["transcript"]
                if "ALL" in transcript:
                    transcript_add = "ALL"
                else:
                    transcript_add = transcript
                # Create a new session with Species, Gene, and Transcript
                primer_config = PrimerConfig().from_dict(dForm)
                session = Session.create_session(species, symbol, transcript_add)
                session.set_design_config(primer_config)
                session.save()

                # Get all sessions for the gene, species, and transcript
                existing_sessions = Session.objects.filter(symbol=symbol, species=species, transcript=transcript_add)

                # Filter sessions to check if any of them have the same primer_config
                matching_sessions = [s for s in existing_sessions if (s.primer_config == primer_config and s.session_id != session.session_id)]

                if matching_sessions:
                    # If there are matching sessions, redirect to the first one found
                    existing_session = matching_sessions[0]
                    print("[+] Session already exists, redirecting", flush=True)
                    session.delete()  # Remove the newly created session
                    return redirect('runprimerblast', session_slug=existing_session.session_id)
                else:
                    print("[+] Creating new session", flush=True)

                    print("[+] Creating session for:", species, symbol, transcript, flush=True)
                    
                    # Queue the primer design
                    job = PrimerJob()
                    job.set_session(session)
                    job.save()
                    enqueue_job = job.queue_job()
                    job.save()
                    session.update_queue_job_id(enqueue_job)

                    # Save the newly created session
                    session.save()

            except Exception as error:
                print("[!] Error in PrimerBlastFormView", flush=True)
                print(error, flush=True)

            else:
                # Redirect to the next step sending the gene and species
                print("[+] Redirecting to the next step")
                return redirect('jobstatus', session_slug=session.session_id)
        else:
            print("[!] Error in the form")
            print(form.errors)
            messages.warning(request,form.errors)
            form = add_css_classes_to_form_fields(form, "form-control")
            context["title"] = "Assign design parameters"
            context["species"] = species
            context["gene"] = gene
            context["transcripts"] = lT


        return render(request, template_name=self.template_name, context=context)


## View to run the primer design
## Take the parameters from the previous view and run the primer design

class ExonSurferView(CreateView):
    template_name = 'primerblast/results_view.html'

    def get(self, request, session_slug):
        try:
            # Obtain the gene, symbol and species from the form
            context = {}
            context["identifier"] = session_slug
            context["title"] = "Primer Blast Results"
            context["session_slug"] = session_slug

            session = Session.objects.get(session_id=session_slug)
            try:
                gene = Gene.objects.get(gene_name=session.symbol, species=get_specie(session.species))
            except:
                gene = None
            # Obtain PrimerJob from session
            primer_job = PrimerJob.objects.get(session_id=session)
            #Obtain symbol, transcript and species from the session
            context["species"] = session.species
            context["symbol"] = session.symbol
            context["transcript"] = session.transcript
            context["primer_config"] = session.primer_config
            context["gene"] = gene

            
            # Obtain primer results from the session
            # Check if the primer design has been completed
            # If not, redirect to the job status page
            # If yes, obtain the results and display them
            if primer_job.job_status == "complete":   

                df_blast, genomic_blast, df_primers, error_log  = session.run_session()
                print("[+] Primer design completed")
                # Sort results by pair_score
                df_primers = df_primers.sort_values(by=["pair_score"], ascending=False)
                #Get the top 5 primers, from different junctions
                top_primers = df_primers.drop_duplicates(subset=["junction"], keep="first")
                top_primers = df_primers.head(5)
                #Round to two decimals
                top_primers = top_primers.round(2)
                top_primers.loc[:,"num"] = [x.replace("Pair","") for x in top_primers.pair_num.tolist()]
                context["top_primers"] = top_primers.to_dict(orient="records")
                # Select columns to show in the table
                #Write pretty names for the columns
                pretty_cols = [pretty_names[col] for col in lCol]
                #Remove Off-Target Score
                pretty_cols.remove("Off-target Transcripts/Genes")
                context["pretty_cols"] = pretty_cols
            else:
                print("[+] Primer design not completed")
                return redirect('jobstatus', session_slug=session.session_id)
            
        except Exception as error:
            print("[!] Error in the ExonSurferView")
            print(error)
            context = {}

            raise Http404('Session not found...!')

        else:
            # We pase the session to the template with the Context Dyct
            #print(df_primers)
            return render(request, template_name=self.template_name, context=context)



class ResultTableView(CreateView):
    template_name = 'primerblast/full_screen_table.html'

    def get(self, request, session_slug):
        try:
            # Obtain the gene, symbol and species from the form
            context = {}
            context["identifier"] = session_slug
            context["session_slug"] = session_slug

            session = Session.objects.get(session_id=session_slug)
            try:
                gene = Gene.objects.get(gene_name=session.symbol, species=get_specie(session.species))
            except:
                gene = None
            # Obtain PrimerJob from session
            primer_job = PrimerJob.objects.get(session_id=session)
            #Obtain symbol, transcript and species from the session
            context["species"] = session.species
            context["symbol"] = session.symbol
            context["transcript"] = session.transcript
            context["primer_config"] = session.primer_config
            context["gene"] = gene

            
            # Obtain primer results from the session
            # Check if the primer design has been completed
            # If not, redirect to the job status page
            # If yes, obtain the results and display them
            if primer_job.job_status == "complete":   

                df_blast, genomic_blast, df_primers, error_log  = session.run_session()
                print("[+] Primer design completed")
                # Sort results by pair_score
                df_primers = df_primers.sort_values(by=["pair_score"], ascending=False)
                #Get the top 5 primers, from different junctions
                top_primers = df_primers.drop_duplicates(subset=["junction"], keep="first")
                top_primers = df_primers.head(5)
                #Round to two decimals
                top_primers = top_primers.round(2)
                top_primers.loc[:,"num"] = [x.replace("Pair","") for x in top_primers.pair_num.tolist()]
                context["top_primers"] = top_primers.to_dict(orient="records")
                # Select columns to show in the table
                #Write pretty names for the columns
                pretty_cols = [pretty_names[col] for col in lCol]
                #Remove Off-Target Score
                pretty_cols.remove("Off-target Transcripts/Genes")
                context["pretty_cols"] = pretty_cols
            else:
                print("[+] Primer design not completed")
                return redirect('jobstatus', session_slug=session.session_id)
            
        except Exception as error:
            print("[!] Error in the ExonSurferView")
            print(error)
            context = {}

            raise Http404('Session not found...!')

        else:
            # We pase the session to the template with the Context Dyct
            #print(df_primers)
            return render(request, template_name=self.template_name, context=context)


## View to obtain the primer pair results
## Take one of the primer pairs and show the results

class PrimerPairView(CreateView):
    """
    View to show the primer pair results

    """
    template_name = 'primerblast/primer_pair_view.html'

    def get(self, request, session_slug, pair):
        try:
            # Obtain the session, and pair_id from get

            context = {}
            context["identifier"] = session_slug
            context["session_slug"] = session_slug

            context["pair"] = pair
            context["title"] = "Primer Pair Results"
             
            session = Session.objects.get(session_id=session_slug)
            try:
                gene = Gene.objects.get(gene_name=session.symbol, species=get_specie(session.species))
            except:
                gene = None
            #Obtain symbol, transcript and species from the session
            context["species"] = session.species
            context["symbol"] = session.symbol
            context["transcript"] = session.transcript
            context["gene"] = gene

            # Check if the session has been run, if not sent error
            print("[!] ### Checking if the session has been run ###")
            if not session.is_run:
                raise Http404('Session not run...!')
            else:
                print(pair)
                primer_pair = session.get_primer_pair(pair)
                primer_pair_blast = session.get_primer_pair_blast(pair)
                context["primer_pair"] = primer_pair
                #List exons and colors
                lExons = primer_pair["junction"].split("-")
                dExons = dict(zip(lExons, lColors))
                context["dExons"] = dExons
                #List transcript that detect the primer pair
                
                try:
                    lTranscripts = primer_pair["detected"].split(";")
                    lTranscripts = Transcript.objects.filter(transcript_id__in=lTranscripts)
                except:
                    lTranscripts = []

                context["lTranscripts"] = lTranscripts
                #Add symbol, species, primers and transcript to the request.session
                request.session["symbol"] = session.symbol
                request.session["species"] = session.species
                request.session["primer_pair"] = pair
                request.session["session_id"] = session_slug

        except Exception as error:
            print("[!] Error in the PrimerPairView",flush=True)
            print(error,flush=True)
            context = {}

            raise Http404('Session not found...!')
        
        return render(request, template_name=self.template_name, context=context)


class PrimerPairOffTargetView(CreateView):
    """
    View to show the primer pair off-target results
    """
    template_name = 'primerblast/primer_pair_offtarget_view.html'

    def get(self, request, session_slug, pair):

        try:
            # Obtain the session, and pair_id from get

            context = {}
            context["identifier"] = session_slug
            context["session_slug"] = session_slug
            context["pair"] = pair
            context["title"] = "Primer Pair Results"
             
            session = Session.objects.get(session_id=session_slug)
            try:
                gene = Gene.objects.get(gene_name=session.symbol, species=get_specie(session.species))
            except:
                gene = None
            #Obtain symbol, transcript and species from the session
            context["species"] = session.species
            context["symbol"] = session.symbol
            context["gene"] = gene

            # Check if the session has been run, if not sent error
            print("[!] ### Checking if the session has been run ###")
            if not session.is_run:
                raise Http404('Session not run...!')
            else:
                print(pair)
                primer_pair = session.get_primer_pair(pair)
                try:
                    lTranscripts = primer_pair["detected"].split(";")
                    lTranscripts = Transcript.objects.filter(transcript_id__in=lTranscripts)
                except:
                    lTranscripts = []
                context["lTranscripts"] = lTranscripts
        except Exception as error:
            print("[!] Error in the PrimerPairOffTargetView", flush=True)
            print(error, flush=True)
            context = {}
            raise Http404(f'"[!] Error in the PrimerPairOffTargetView" {error}')
        else:
            context["primer_pair"] = primer_pair
        return render(request, template_name=self.template_name, context=context)



class SessionListView(ListView):
    model = Session
    template_name = 'session_list.html'
    context_object_name = 'sessions'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(session_id__icontains=search) |
                                       Q(species__icontains=search) |
                                       Q(symbol__icontains=search) |
                                       Q(transcript__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Session List'
        context['search'] = self.request.GET.get('search', '')
        return context



class SessionUpdateView(UpdateView):
    model = Session
    form_class = SessionUpdateForm
    template_name = 'primerblast/session_update.html'
    success_url = reverse_lazy('session_list')

    def form_valid(self, form):
        # Retrieve the existing session object
        session = self.get_object()

        # Update the session object with the new form data
        session.session_id = form.cleaned_data['session_id']
        session.save()

        # Update the Result object with the new session_id
        result = Result.objects.filter(session=session)
        result.update(session_id=form.cleaned_data['session_id'])

        # Save the uploaded files to the Result object
        result = result.first()
        blast_file = self.request.FILES.get('blast_file', None)
        genomic_blast_file = self.request.FILES.get('genomic_blast_file', None)
        primer_file = self.request.FILES.get('primer_file', None)

        if blast_file:
            result.blast_file = blast_file
        if genomic_blast_file:
            result.genomic_blast_file = genomic_blast_file
        if primer_file:
            result.primer_file = primer_file

        result.save()

        # Display a success message
        messages.success(self.request, 'Session updated successfully.')

        return super().form_valid(form)

    
#################
## Request
#################

## Transcript Exon View
## Show the transcript and exon information
def ExonTranscriptView_gene_species(request, gene, species):
    try:
        # Obtain the symbol, and species from the request.session
        symbol = gene
        species = get_specie(species)
        #Obtain the transcript from the request, if not, set to ALL
        transcripts = "ALL"
        release = 57 if species in ("arabidopsis_thaliana","oryza_sativa") else 108
        html = plot_transcripts_alone(species, symbol, transcripts, release)
    except Exception as error:
        print("[!] Error in the ExonTranscriptView_gene_species", flush=True)
        print(error, flush=True)
        raise Http404('Session not found...!')

    return HttpResponse(html)

## Transcript Exon View
def ExonTranscriptView(request, session_slug, pair):
    try:
        session = Session.objects.get(session_id=session_slug)
        symbol = session.symbol
        species = session.species
        species = get_specie(species)
        final_df = Result.objects.get(session=session).get_primer_file()
        final_df.index = final_df.pair_num
        final_df.fillna("", inplace=True)
        final_df["for_pos"] = final_df["for_pos"].apply(lambda x: eval(x))
        final_df["rev_pos"] = final_df["rev_pos"].apply(lambda x: eval(x))
        release = 57 if species in ("arabidopsis_thaliana","oryza_sativa") else 108

        html = plot_transcripts_marked(species, symbol, "ALL", release, pair, final_df)
    except Exception as error:
        print("[!] Error in the ExonTranscriptView",flush=True)
        print(error,flush=True)
        raise Http404('Session not found...!')

    return HttpResponse(html)

## cDNA Transcript View
## Show the cDNA and the primers aligned

def cDNATranscriptView(request, session_slug, pair):
    """
    Function to show the cDNA, and the primers aligned
    Args:
        request ([type]): [description]
        session_slug (uuid): Session identifier
    Returns:
        html: html with the cDNA and the primers aligned
    """
    try:
        #Obtain the session
        print("[!] Obtaining session",flush=True)
        session = Session.objects.get(session_id=session_slug)
        #Obtain symbol, transcript and species from the session
        species = session.species
        species = get_specie(species)
        print("[!] Obtaining primer df",flush=True)
        final_df = Result.objects.get(session_id=session).get_primer_file()
        final_df.index = final_df.pair_num
        print(final_df.head())
        print("[!] Obtaining cDNA",flush=True)
        #pair_id = int(pair_id.replace("Pair",""))
        #If session is from_file get file path else false
        if session.from_file:
            print("[!] Obtaining gene file",flush=True)
            gene_path = GeneFile.objects.get(session_id=session)
            gene_path = gene_path.get_gene_file_path()
            print(gene_path, flush=True)
        else:
            gene_path = False
        print("[!] Obtaining cDNA",flush=True)
        html = plot_cdna(pair, final_df, species, file=gene_path)
        print("[!] Obtained cDNA",flush=True)
        print(html)

    except Exception as error:
        print("[!] Error in the cDNATranscriptView",flush=True)
        print(error, flush=True)

    return HttpResponse(html)


def cDNATranscriptOffView(request, session_slug, pair):
    """
    Function to show the cDNA, and the primers aligned
    Args:
        request ([type]): [description]
        session_slug (uuid): Session identifier
    Returns:
        html: html with the cDNA and the primers aligned
    """
    try:
        #Obtain the session
        print("[!] Obtaining session",flush=True)
        session = Session.objects.get(session_id=session_slug)
        #Obtain symbol, transcript and species from the session
        species = session.species
        species = get_specie(species)
        print("[!] Obtaining primer df",flush=True)
        final_df = Result.objects.get(session_id=session).get_primer_file()
        final_df.index = final_df.pair_num
        final_df.fillna("", inplace=True)
        print(final_df.head())
        print((final_df.to_string()),flush=True)
        print("[!] Obtaining cDNA",flush=True)
        #pair_id = int(pair_id.replace("Pair",""))
        print(final_df.loc[pair].to_dict(),flush=True)

        if session.from_file:
            t = ""
        else:
            t = session.get_transcript()
        #change final_df other_transcripts False to ""
        final_df["other_transcripts"] = final_df["other_transcripts"].apply(lambda x: "" if x == False else x)
        html = plot_off_target(pair, final_df, session.species, t)
        print(html)

    except Exception as error:
        print("[!] Error in the cDNATranscriptOffView",flush=True)
        print(error)
        context = {}

    return HttpResponse(html)
    
    ############
    ### JSON ###
    ############

def ListJson(request, identifier):
    import json
    """
        Function that transform a DF in JsonResponse
        View list to populate the Html Table.
        The Datatable work with Ajax. We need a Json file.
    """

    #Read DF

    #Tranform DF to Json
    try:
        print("Reading DF")
        session = Session.objects.get(session_id=identifier)
        df = Result.objects.get(session_id=session).get_primer_file()
        # Round the values to two decimals
        df = df.round(2)
        df = df[lCol]
        df.columns = [pretty_names[col] for col in lCol]
        # Drop "Off-target Transcripts/Genes" column
        df.drop(columns=["Off-target Transcripts/Genes"], inplace=True)
        result = df.to_json(orient='values')
        json_dict = {}
        json_dict["data"] = json.loads(result)
    except Exception as error:
        print(f"[!] Error: {error}")
        json_dict = {}
        json_dict["data"] = []
        
    return JsonResponse(json_dict, safe = False)

############
### Download ###
############

## Function to download the primer pair results as excel file

def download_excel_pair(request, session_slug, pair):
    # Retrieve the results from the database
    session = Session.objects.get(session_id=session_slug)
    # Retrieve the configuration
    primer_config = session.get_run_parameters()
    primer_config = pd.DataFrame(primer_config, index=[0])
    # Obtain symbol, transcript and species from the session
    symbol = session.symbol
    species = session.species
    transcript = session.transcript
    # Obtain the primer pair
    primer_pair = session.get_primer_pair(pair)
    # Create a dataframe with the primer pair
    primer_pair_df = pd.DataFrame(primer_pair, index=[0])
    # Rename the columns
    primer_pair_df = primer_pair_df[lCol]
    primer_pair_df.columns = [pretty_names[col] for col in lCol]
    # Add a citation for the primer design tool
    primer_pair_df.loc[1, "Primer Pair"] = """The primer pair was designed using the ExonSurfer tool (Monfort-Lanzas & Rusu, 2023), 
    which is a web-based tool for designing primers at exon-exon junctions. Please cite the following reference 
    when using the primer pair in your research: Monfort-Lanzas, P., & Rusu, E. C. (2023). ExonSurfer: A Web-tool to Design Primers at Exon–Exon Junctions.
      In 10th Gene Quantification Event 2023 qPCR dPCR & NGS (Po-54). Freising-Weihenstephan, School of Life Sciences, Technical University of Munich, Weihenstephan, Germany. """
    # Set the filename for the Excel file
    filename = f"{symbol}_{species}_primer_pair_{pair}.xlsx"
    # Create an in-memory output file for the Excel workbook
    output = io.BytesIO()
    # Create a Pandas Excel writer using the in-memory output file
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    # Write each dataframe to a separate worksheet in the Excel workbook
    primer_pair_df.to_excel(writer, sheet_name="Primer Pair", index=False)
    ## Write the primer design configuration to a separate worksheet in the Excel workbook
    ## where the excel is write in two columns (key, value)
    primer_config = primer_config.T 
    primer_config.columns = ["Value"]
    primer_config.index.name = "Parameter"
    primer_config.reset_index(inplace=True)  
    primer_config.to_excel(writer, sheet_name="Primer Design Configuration", index=False)
    # Close the Pandas Excel writer
    writer.close()
    # Set the content type and headers for the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    # Write the in-memory output file to the response
    response.write(output.getvalue())
    # Return the response
    return response


def download_session_files(request, session_slug):
    session = Session.objects.get(session_id=session_slug)
    session_path = os.path.join(settings.DATA_DIR, "Sessions", str(session.session_id))

    # Create a zip file
    zip_filename = f"{session.session_id}.zip"
    zip_file_path = os.path.join(session_path, zip_filename)
    with zipfile.ZipFile(zip_file_path, "w") as zip_file:
        # Add the BLAST file to the zip file
        blast_file = session.result_set.first().BlastFile.path
        zip_file.write(blast_file, os.path.basename(blast_file))

        # Add the genomic BLAST file to the zip file
        genomic_blast_file = session.result_set.first().GenomicBlastFile.path
        zip_file.write(genomic_blast_file, os.path.basename(genomic_blast_file))

        # Add the primer file to the zip file
        primer_file = session.result_set.first().PrimerFile.path
        zip_file.write(primer_file, os.path.basename(primer_file))

    # Create a response with the zip file and return it
    with open(zip_file_path, "rb") as zip_file:
        response = HttpResponse(zip_file, content_type="application/zip")
        response["Content-Disposition"] = f"attachment; filename={zip_filename}"
        return response


def download_session_command(request, session_slug):
    try:
        session = Session.objects.get(session_id=session_slug)
        filename = f"session_{session_slug}_command.txt"
        content = session.get_call_command()
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Session.DoesNotExist:
        raise Http404("Session does not exist")
    

import os
import zipfile
from django.conf import settings
from django.http import HttpResponse

def download_all_sessions(request):
    # Define el nombre del archivo ZIP a descargar
    filename = 'all_sessions.zip'

    # Crea un objeto HttpResponse con el tipo de contenido adecuado
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)

    # Crea un archivo ZIP en memoria para almacenar las sesiones
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Recorre la carpeta Data/Session para añadir cada sesión al archivo ZIP
        session_dir = os.path.join(settings.DATA_DIR, "Sessions")
        for root, dirs, files in os.walk(session_dir):
            for file in files:
                session_path = os.path.join(root, file)
                zip_file.write(session_path, arcname=os.path.relpath(session_path, session_dir))

    # Escribe el contenido del archivo ZIP en el objeto HttpResponse y devuelve la respuesta
    zip_buffer.seek(0)
    response.write(zip_buffer.read())
    return response

    
    #############
    ### ERROR ###
    #############

## View to hanfle the error in the primer design
## Show the error log

class ErrorDesignView(CreateView):
    """
    View to show the primer pair results

    """
    template_name = 'primerblast/error_design_view.html'

    def get(self, request, session_slug):
        try:
            #Obtain the session, and the error_log
            context = {}
            print("[!] ### Error Design View ###")
            session = Session.objects.get(session_id=session_slug)
            context["title"] = "Error Page"
            context["error_log"] = request.session["error_log"]
            context["symbol"] = session.symbol
            context["transcript"] = session.transcript
            context["species"] = session.species
            session.delete()

        except Exception as error:
            print("[!] Error in ErrorDesignView")
            print(error)
            context = {}

            raise Http404('Session not found...!')
        return render(request, template_name=self.template_name, context=context)


class SelectGeneSpeciesViewOld(CreateView):
    template_name = 'exonsurfer/index.html'

    def get(self, request):
        try:
            # Obtain the spcies and gene from the form
            form = SpeciesGeneForm()
            context = {'form': form}
            context["title"] = "Gene and Species Selection"

            # Obtain REDIS_URL from the environment
            if "REDIS_URL" in os.environ:
                context["REDIS_URL"] = os.environ["REDIS_URL"]

        except:
            raise Http404('Session not found...!')

        else:
            # We pase the session to the template with the Context Dyct

            return render(request, self.template_name, context)


    def post(self, request):
        # We get the filter condition
        form = SpeciesGeneForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            dForm = form.cleaned_data
            try:

                #check if there is a gene in the field for the selected species,
                #and obtain the gene and species
                if dForm["species"] == "homo_sapiens":
                    if dForm["human_symbol"] == "":
                        messages.warning(request, "Please, write a gene")
                        return redirect('index')
                    else:
                        if dForm["use_masked_genomes"] != []:
                            human_symbol = dForm["human_symbol"]
                            species = "homo_sapiens_masked"
                        else:
                            human_symbol = dForm["human_symbol"]
                            species = dForm["species"]
                elif dForm["species"] == "mus_musculus":
                    if dForm["mouse_symbol"] == "":
                        messages.warning(request, "Please, write a gene")
                        return redirect('index')
                    else:
                        human_symbol = dForm["mouse_symbol"]
                        species = dForm["species"]
                elif dForm["species"] == "rattus_norvegicus":
                    if dForm["rat_symbol"] == "":
                        messages.warning(request, "Please, write a gene")
                        return redirect('index')
                    else:
                        human_symbol = dForm["rat_symbol"]
                        species = dForm["species"]
                elif dForm["species"] == "fly_symbol":
                    if dForm["fly_symbol"] == "":
                        messages.warning(request, "Please, write a gene")
                        return redirect('index')
                    else:
                        human_symbol = dForm["fly_symbol"]
                        species = dForm["species"]
                elif dForm["species"] == "arabidopsis_thaliana":
                    if dForm["arabidopsis_symbol"] == "":
                        messages.warning(request, "Please, write a gene")
                        return redirect('index')
                    else:
                        human_symbol = dForm["arabidopsis_symbol"]
                        species = dForm["species"]
                else:
                    messages.warning(request, "Please, write a gene name")
                    return redirect('index')
                


            except Exception as error:
                messages.warning(request, "Please, write a gene name")
                print("[!] Error in the form, in view: SelectGeneSpeciesView", flush=True)
                print("[!] Error: ", error, flush=True)
                return redirect('index')
            else:
                # Redirect to the next step sending the gene and species
                return redirect('primerblast', species=species, symbol=human_symbol)
        else:
            print("[!] Error in the form, in view: SelectGeneSpeciesView", flush=True)
            print("[!] Form not valid", form.errors, flush=True)
            print(form.errors, flush=True)
            messages.warning(request,form.errors)

        return render(request, self.template_name, {'form': form})

