from django.shortcuts import render
from django.shortcuts import render, redirect
from django.urls import reverse_lazy,reverse

from django.http import HttpResponse, Http404, JsonResponse
from .forms import SpeciesGeneForm, PrimerBlastForm   
from django.views.generic import (View, CreateView, ListView, DeleteView)
from django.contrib import messages
import os
from ExonSurfer.exonsurfer import CreatePrimers
from .models import Session, PrimerConfig, Result



# Create your views here.
class SelectGeneSpeciesView(CreateView):
    template_name = 'forms.html'

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
                        messages.warning(request, "Please, select a gene")
                        return redirect('selectgenespecies')
                    else:
                        human_symbol = dForm["human_symbol"]
                        species = dForm["species"]
                elif dForm["species"] == "mus_musculus":
                    if dForm["mouse_symbol"] == "":
                        messages.warning(request, "Please, select a gene")
                        return redirect('selectgenespecies')
                    else:
                        human_symbol = dForm["mouse_symbol"]
                        species = dForm["species"]
                elif dForm["species"] == "rattus_norvegicus":
                    if dForm["rat_symbol"] == "":
                        messages.warning(request, "Please, select a gene")
                        return redirect('selectgenespecies')
                    else:
                        human_symbol = dForm["rat_symbol"]
                        species = dForm["species"]
                


            except Exception as error:
                print(error)

            finally:
                # Redirect to the next step sending the gene and species
                return redirect('primerblast', species=species, symbol=human_symbol)
        else:
            print("Algo ha ido mal")
            print(form.errors)
            messages.warning(request,form.errors)

        return render(request, self.template_name, {'form': form})


# View to run Primer Blast
class PrimerBlastView(CreateView):
    template_name = 'primer_config_forms.html'

    def get(self, request, species, symbol):
        try:
            # Obtain the session from the DB with the session_slug (identifier)
            self.species = species
            self.symbol = symbol
            form = PrimerBlastForm(species=species, symbol=symbol)
            context = {'form': form}
            context["title"] = "Assign Primers parameters"
            context["species"] = species
            context["symbol"] = symbol

        except:
            raise Http404('Session not found...!')

        else:
            # We pase the session to the template with the Context Dyct

            return render(request, self.template_name, context)


    def post(self, request,species, symbol):
        # We get the filter condition
        form = PrimerBlastForm(request.POST, request.FILES, species=species, symbol=symbol)
        context = {'form': form}

        if form.is_valid():
            print(form.cleaned_data)
            dForm = form.cleaned_data

            try:
                # Obtain gene, and species from the form
                transcript = dForm["transcript"]
                #Create Session with Species, Gene and Transcript
                primer_config = PrimerConfig().from_dict(dForm)
                session = Session.create_session(species, symbol, transcript)
                session.set_design_config(primer_config)
                print(primer_config.primer_opt_size)
                
                print(session)

            except Exception as error:
                print("[!] Error creating session")
                print(error)

            else:
                # Redirect to the next step sending the gene and species
                print("[+] Redirecting to the next step")
                return redirect('runprimerblast', session_slug=session.session_id)
        else:
            print("[!] Error in the form")
            print(form.errors)
            messages.warning(request,form.errors)
            context["title"] = "Blablabla"
            context["species"] = species
            context["symbol"] = symbol


        return render(request, template_name=self.template_name, context=context)


# View to run ExonSurfer and Show results
class ExonSurferView(CreateView):
    template_name = 'results_view.html'

    def get(self, request, session_slug):
        try:
            # Obtain the gene, symbol and species from the form

            context = {}
            context["identifier"] = session_slug
            context["title"] = "Primer Blast Results"
             
            session = Session.objects.get(session_id=session_slug)
            #Obtain symbol, transcript and species from the session
            context["species"] = session.species
            context["symbol"] = session.symbol
            context["transcript"] = session.transcript

            # Check if the session has been run, if not run it
            print("[!] ### Checking if the session has been run ###")
            print(session.is_run)
            if not session.is_run:
                df_blast, df_primers = CreatePrimers(gene = session.symbol, 
                                    transcripts = session.transcript, 
                                    species = session.species,
                                    design_dict = session.get_design_config())

                #Get the score for each primer pair, 100 * (value - min_penalty) / (max_penalty - min_penalty)
                min_penalty = 0
                max_penalty = 20
                value = df_primers["pair_penalty"]
                df_primers["Score"] = 100 * (value - min_penalty) / (max_penalty - min_penalty)
                df_primers["Score"] = 100 - df_primers["Score"]

                result = Result.create_result(session, df_blast, df_primers)
                session.set_run()
                context["col"] = ["Pair",] + df_primers.columns.tolist()
                # Create a new column with the pair_num
                df_primers["pair_num"] = df_primers.index
            else:
                df_primers = Result.objects.get(session_id=session).get_primer_file()
                context["col"] = df_primers.columns.tolist()
            

            
            #Sort by pair_penalty
            df_primers = df_primers.sort_values(by=["pair_penalty"], ascending=True)

            #Get the top 5 primers, from different junctions

            top_primers = df_primers.drop_duplicates(subset=["junction"], keep="first")
            top_primers = df_primers.head(5)

            #Round to two decimals
            top_primers = top_primers.round(2)
            

            context["top_primers"] = top_primers.to_dict(orient="records")



        except Exception as error:
            print(error)
            context = {}

            raise Http404('Session not found...!')

        else:
            # We pase the session to the template with the Context Dyct
            #print(df_primers)
            return render(request, template_name=self.template_name, context=context)

class PrimerPairView(CreateView):
    """
    View to show the primer pair results

    """
    template_name = 'primer_pair_view.html'

    def get(self, request, session_slug, pair):
        try:
            # Obtain the session, and pair_id from get

            context = {}
            context["identifier"] = session_slug
            context["title"] = "Primer Pair Results"
             
            session = Session.objects.get(session_id=session_slug)
            #Obtain symbol, transcript and species from the session
            context["species"] = session.species
            context["symbol"] = session.symbol
            context["transcript"] = session.transcript

            # Check if the session has been run, if not sent error
            print("[!] ### Checking if the session has been run ###")
            if not session.is_run:
                raise Http404('Session not run...!')
            else:
                print(pair)
                primer_pair = session.get_primer_pair(pair)
                context["primer_pair"] = primer_pair
        except Exception as error:
            print(error)
            context = {}

            raise Http404('Session not found...!')
        
        return render(request, template_name=self.template_name, context=context)




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
        result = df.to_json(orient='values')
        json_dict = {}
        json_dict["data"] = json.loads(result)
    except Exception as error:
        print(f"[!] Error: {error}")
        json_dict = {}
        json_dict["data"] = []
        
    return JsonResponse(json_dict, safe = False)