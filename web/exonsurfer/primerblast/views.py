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
                # Obtain gene, and species from the form
                symbol = dForm["symbol"]
                species = dForm["species"]

            except Exception as error:
                print(error)

            finally:
                # Redirect to the next step sending the gene and species
                return redirect('primerblast', species=species, symbol=symbol)
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
                primer_config = PrimerConfig.from_dict(dForm)
                session = Session.create_session(species, symbol, transcript)
                session.set_config(primer_config)
                
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

            print("caracaas!!!!!!!!")
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
                df_blast, df_primers = CreatePrimers(session.symbol, session.transcript)
                result = Result.create_result(session, df_blast, df_primers)
                session.set_run()
                context["col"] = ["Pair",] + df_primers.columns.tolist()
            else:
                df_primers = Result.objects.get(session_id=session).get_primer_file()
                context["col"] = df_primers.columns.tolist()
            

            #Sort the DF by the pair_penalty
            df_primers = df_primers.sort_values(by=["pair_penalty"], ascending=True)
            top_primers = df_primers.head(4)
            #Round to two decimals
            top_primers = top_primers.round(2)
            context["top_primers"] = top_primers.to_dict(orient="records")

            print(df_primers)


        except Exception as error:
            print(error)
            context = {}

            raise Http404('Session not found...!')

        else:
            # We pase the session to the template with the Context Dyct
            #print(df_primers)
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