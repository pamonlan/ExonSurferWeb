from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from .forms import SpeciesGeneForm, PrimerBlastForm   
from primer_queue.models import PrimerJob
from django.views.generic import (View, CreateView, ListView, DeleteView)
from django.contrib import messages
from .models import Session, PrimerConfig, Result
from gene_file.models import GeneFile
from ensembl.models import Transcript, Gene
from .management.transcript_info import get_exon_transcript_information
from .management.visualization import plot_primerpair_aligment, plot_cdna, plot_off_target
from django.http import HttpResponse
import pandas as pd
### Sharing Parameters
# This parameters are shared between the views
#
lCol = ['pair_num', 'forward',  'reverse', 'amplicon_size', 'amplicon_tm',
         'forward_tm', 'reverse_tm', 'forward_gc',  'reverse_gc', 'indiv_als',
         'detected', 'not_detected', 'pair_score', 'off_targets']

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
                }

lColors = ['#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', \
     '#999999', '#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#666666']

## Landing page view
## This view is the first one to be loaded
## It allows the user to select the species and the gene
class SelectGeneSpeciesView(CreateView):
    template_name = 'exonsurfer/index.html'

    def get(self, request):
        try:
            # Obtain the spcies and gene from the form
            form = SpeciesGeneForm()
            context = {'form': form}
            context["title"] = "Gene and Species Selection"

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



## View to assign the parameters for the primer design
## Allows the user to select the transcript and the parameters for the primer design

class PrimerBlastFormView(CreateView):
    template_name = 'primerblast/primer_config_forms.html'

    def get(self, request, species, symbol):
        try:
            # Obtain the session from the DB with the session_slug (identifier)
            print("[+] Obtaining transcript list for in view: ", species, symbol, "")
            self.species = species
            gene = Gene.objects.get(gene_name=symbol, species=species)
            print(gene)
            self.symbol = symbol
            lT = Transcript.objects.filter(gene_name=symbol, species=species, transcript_biotype="protein_coding")
            #Invert list
            print(lT)

            if len(lT) == 0:
                messages.warning(request, "There is no transcript for this gene in the selected species")
                return redirect('index')

            form = PrimerBlastForm(species=species, symbol=symbol, lT=list(lT.values_list('transcript_id', flat=True)))

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
            lT = Transcript.objects.filter(gene_name=symbol, species=species, transcript_biotype="protein_coding")
        except Exception as error:
            print("[!] Error obtaining the transcript list: ", error, "")
            raise Http404('Session not found...!')
        else:
            form = PrimerBlastForm(request.POST, request.FILES, species=species, symbol=symbol,lT=list(lT.values_list('transcript_id', flat=True)))
        context = {'form': form}
        print("[+] Obtaing POST data:")
        print(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            dForm = form.cleaned_data

            try:
                # Obtain gene, and species from the form
                transcript = dForm["transcript"]
                #Create Session with Species, Gene and Transcript
                primer_config = PrimerConfig().from_dict(dForm)
                # Get all session fo the gene and species, and check if the PrimerConfig is the same
                # If it is the same, we redirect to the next step
                # If it is not the same, we create a new session
                lSession = Session.objects.filter(symbol=symbol, species=species,transcript= transcript)
                #Check the primer config 
                lSession = [s for s in lSession if s.primer_config == primer_config]

                if len(lSession) > 0:
                    print("[+] Session already exists", flush=True)
                    return redirect('runprimerblast', session_slug=lSession[0].session_id)
                else:
                    print("[+] Creating new session", flush=True)
                    if "ALL" in transcript:
                        transcript = "ALL"
                    print("[+] Creating session for: ", species, symbol, transcript, flush=True)
                    session = Session.create_session(species, symbol, transcript)
                    session.set_design_config(primer_config)
                    session.save()
                      
                    # Queu the primer design
                    job = PrimerJob()
                    job.set_session(session)
                    job.queue_job()            

            except Exception as error:
                print("[!] Error creating session")
                print(error)

            else:
                # Redirect to the next step sending the gene and species
                print("[+] Redirecting to the next step")
                return redirect('jobstatus', session_slug=session.session_id)
        else:
            print("[!] Error in the form")
            print(form.errors)
            messages.warning(request,form.errors)
            context["title"] = "Assign design parameters"
            context["species"] = species
            context["symbol"] = symbol
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
            
            session = Session.objects.get(session_id=session_slug)
            try:
                gene = Gene.objects.get(gene_name=session.symbol, species=session.species)
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

                df_blast, df_primers, error_log = session.run_session()
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
            context["pair"] = pair
            context["title"] = "Primer Pair Results"
             
            session = Session.objects.get(session_id=session_slug)
            try:
                gene = Gene.objects.get(gene_name=session.symbol, species=session.species)
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
                #request.session["primer_pair"] = pair

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
            context["pair"] = pair
            context["title"] = "Primer Pair Results"
             
            session = Session.objects.get(session_id=session_slug)
            try:
                gene = Gene.objects.get(gene_name=session.symbol, species=session.species)
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


## Transcript Exon View
## Show the transcript and exon information

def ExonTranscriptView(request):
    try:
        # Obtain the symbol, and species from the rqeuest.session
        symbol = request.session["symbol"]
        species = request.session["species"]
        #Obtain the transcript from the request, if not, set to ALL
        transcript = "ALL"
        #Obtain the primer_pair from the request, if not, set to []
        if "primer_pair" in request.session:
            primer_pair = request.session["primer_pair"]
        else:
            primer_pair = []

        #Obtain symbol, transcript and species from the session
        dT,dE, contig = get_exon_transcript_information(symbol=symbol,species=species, transcript=transcript)
        html = plot_primerpair_aligment(transcripts=dT, exons=dE, primers=primer_pair, contig=contig)
    except Exception as error:
        print(error)
        context = {}

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

## Function to download the primer pair results as excel file


def download_excel_pair(request, session_slug, pair):
    # Retrieve the results from the database
    session = Session.objects.get(session_id=session_slug)
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
    filename = f"{symbol}_{species}_{transcript}_primer_pair_{pair}.xlsx"
    # Set the content type and headers for the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    # Write the workbook to the response
    primer_pair_df.to_excel(response)
    # Return the response
    return response

def download_all(request, session_slug):
    # Retrieve the results from the database
    session = Session.objects.get(session_id=session_slug)
    # Obtain symbol, transcript and species from the session
    df = Result.objects.get(session_id=session).get_primer_file()
    # Obtain the primer pair
    filename = f"{session_slug}.csv"
    # Set the content type and headers for the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    # Write the workbook to the response
    df.to_csv(response)
    # Return the response
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
