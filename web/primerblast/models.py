from django.db import models
import uuid
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import pandas as pd
import numpy as np
from ensembl.models import Transcript
from ExonSurfer import exonsurfer
from ExonSurfer import exonsurfer_fromfile

# Create your models here.
data_root = FileSystemStorage(location=settings.DATA_DIR)


class PrimerConfig(models.Model):

    """
    Class to store the primer configuration
    Attributes
    ----------
    primer_pairs_number: int
        Number of primer pairs to generate
    primer_junction_design: str
        Type of junction design
    primer_opt_size: int
        Optimal size of the primer
    primer_min_size: int
        Minimum size of the primer
    primer_max_size: int
        Maximum size of the primer
    primer_opt_tm: float
        Optimal melting temperature of the primer
    primer_min_tm: float
        Minimum melting temperature of the primer
    primer_max_tm: float
        Maximum melting temperature of the primer
    primer_opt_gc: int
        Optimal GC content of the primer
    primer_min_gc: int
        Minimum GC content of the primer
    primer_max_gc: int
        Maximum GC content of the primer
    primer_product_size_min: int
        Minimum size of the product
    primer_product_size_max: int
        Maximum size of the product
    primer_product_opt_tm: float
        Optimal melting temperature of the product
    primer_product_min_tm: float
        Minimum melting temperature of the product
    primer_product_max_tm: float
        Maximum melting temperature of the product
    primer_salt_divalent: float
        Concentration of divalent cations
    primer_salt_monovalent: float
        Concentration of monovalent cations
    primer_dntp_conc: float
        Concentration of dNTPs
    primer_i_cutoff: Int
        Percentage of identify cutoff from the BLAST search
    primer_e_value: float
        E-value cutoff from the BLAST search
    primer_max_sep: int
        Maximum separation between the primers for off-targets
    Methods
    -------
    """
    def __eq__(self, other):
        """
        Method to compare two PrimerConfig objects
        Parameters
        ----------
        other: PrimerConfig
            PrimerConfig object to compare
        Returns
        -------
        bool
            True if the objects are equal, False otherwise
        """
        b=True
        for attr in self.__dict__:
            if attr.startswith("primer_"):
                if getattr(self, attr) != getattr(other, attr):
                    print("[+] ¡¡¡Sessions not equal!!!")
                    print(attr, getattr(self, attr), getattr(other, attr))
                    b=False
        return b
                                                        
    def from_dict(self, dict):
        """
        Method to create a PrimerConfig object from a dictionary
        Parameters
        ----------
        dict: dict
            Dictionary with the primer configuration
        Returns
        -------
        PrimerConfig
            PrimerConfig object
        """
        primer_config = self
        primer_config.primer_junction_design = dict["primer_junction_design"]
        primer_config.primer_min_3_overlap = dict["primer_min_3_overlap"]
        primer_config.primer_min_5_overlap = dict["primer_min_5_overlap"]
        primer_config.primer_pairs_number = dict["primer_pairs_number"]
        primer_config.primer_opt_size = dict["primer_opt_size"]
        primer_config.primer_min_size = dict["primer_min_size"]
        primer_config.primer_max_size = dict["primer_max_size"]
        primer_config.primer_opt_tm = dict["primer_opt_tm"]
        primer_config.primer_min_tm = dict["primer_min_tm"]
        primer_config.primer_max_tm = dict["primer_max_tm"]
        primer_config.primer_opt_gc = dict["primer_opt_gc"]
        primer_config.primer_min_gc = dict["primer_min_gc"]
        primer_config.primer_max_gc = dict["primer_max_gc"]
        primer_config.primer_product_size_min = dict["primer_product_size_min"]
        primer_config.primer_product_size_opt = dict["primer_product_size_opt"]
        primer_config.primer_product_size_max = dict["primer_product_size_max"]
        primer_config.primer_product_opt_tm = dict["primer_product_opt_tm"]
        primer_config.primer_product_min_tm = dict["primer_product_min_tm"]
        primer_config.primer_product_max_tm = dict["primer_product_max_tm"]
        primer_config.primer_salt_divalent = dict["primer_salt_divalent"]
        primer_config.primer_salt_monovalent = dict["primer_salt_monovalent"]
        primer_config.primer_dntp_conc = dict["primer_dntp_conc"]
        primer_config.primer_i_cutoff = dict["primer_i_cutoff"]
        primer_config.primer_e_cutoff = dict["primer_e_cutoff"]
        primer_config.primer_max_sep = dict["primer_max_sep"]

        
        primer_config.save()

        return primer_config
    
    def get_primer_junction_design(self):
        """
        Method to get the junction design
        Returns
        -------
        str
            Junction design
        """
        print("primer_junction_design", self.primer_junction_design,flush=True)
        if self.primer_junction_design == "spann_junction":
            iDesign = 1
        else:
            iDesign = 2
        return iDesign
    
    #Primer Pairs Number
    primer_pairs_number = models.IntegerField(default=1000)
    #Primer Size
    primer_opt_size = models.IntegerField(default=20)
    primer_min_size = models.IntegerField(default=18)
    primer_max_size = models.IntegerField(default=27)
    #Primer Junction Dessign
    primer_junction_design = models.CharField(max_length=100)
    primer_min_3_overlap = models.IntegerField(default=5)
    primer_min_5_overlap = models.IntegerField(default=6)
    #Primer Tm
    primer_opt_tm = models.FloatField(default=60)
    primer_min_tm = models.FloatField(default=57)
    primer_max_tm = models.FloatField(default=63)
    #Primer GC
    primer_opt_gc = models.IntegerField(default=50)
    primer_min_gc = models.IntegerField(default=20)
    primer_max_gc = models.IntegerField(default=80)
    #Product Size
    primer_product_size_min = models.IntegerField(default=120)
    primer_product_size_opt = models.IntegerField(default=200)
    primer_product_size_max = models.IntegerField(default=250)
    #Product Tm
    primer_product_opt_tm = models.FloatField(default=80)
    primer_product_min_tm = models.FloatField(default=76)
    primer_product_max_tm = models.FloatField(default=90)
    #PCR Parameters
    primer_salt_divalent = models.FloatField(default=1.5)
    primer_salt_monovalent = models.FloatField(default=50)
    primer_dntp_conc = models.FloatField(default=0.6)
    #Blast Parameters
    primer_i_cutoff = models.IntegerField(default=75)
    primer_e_cutoff = models.FloatField(default=100)
    primer_max_sep = models.IntegerField(default=2000)
 
    #Only for Cristina
    primer_wt_gc_percent_gt = models.FloatField(default=1)
    primer_wt_gc_percent_lt = models.FloatField(default=1)
    primer_max_poly_x = models.IntegerField(default=5)
    primer_gc_clamp = models.IntegerField(default=1)
    primer_max_end_gc = models.IntegerField(default=4)



class Session(models.Model):
    """
    Class to store the sessions
    Attributes
    ----------
    session_id: str
        Session id
    species: str
        Species
    symbol: str
        Gene symbol
    transcript: str
        Transcript

    Methods
    -------
    __str__(self)
        Return the session id
    """
    def __str__(self):
        return f"{self.session_id}: {self.species} {self.symbol} {self.transcript}"

    def run_session(self, gene_file = None):           
        print("[!] ### Checking if the session has been run ###")
        print(self.is_run)
        if not self.is_run:
            print("[!] ### Session not run, running it ###")
            print("[+] Running primer design for: ", self.species, self.symbol, self.transcript, "")
            # Run primer design
            if self.from_file:
                print("[!] ### Running primer design from file ###", flush=True)
                # Run primer design from file
                df_blast, genomic_blast, df_primers, error_log = exonsurfer_fromfile.CreatePrimers(file = gene_file,
                    species = self.species,
                    design_dict = self.get_design_config(),
                    opt_prod_size = self.get_opt_prod_size(),
                    e_value = self.get_e_value(),
                    i_cutoff=self.get_i_cutoff(),
                    max_sep=self.get_max_sep(),
                    NPRIMERS=self.get_nprimers(),
                    d_option=self.get_primer_junction_design(),
                    min_3_overlap = self.get_primer_min_3_overlap(), 
                    min_5_overlap = self.get_primer_min_5_overlap(),
                    save_files=False)

            else:
                df_blast, genomic_blast, df_primers, error_log = exonsurfer.CreatePrimers(gene = self.symbol, 
                                    transcripts = self.get_transcript(), 
                                    species = self.species,
                                    design_dict = self.get_design_config(),
                                    opt_prod_size = self.get_opt_prod_size(),
                                    e_value = self.get_e_value(),
                                    i_cutoff=self.get_i_cutoff(),
                                    max_sep=self.get_max_sep(),
                                    NPRIMERS=self.get_nprimers(),
                                    d_option=self.get_primer_junction_design(),
                                    min_3_overlap = self.get_primer_min_3_overlap(), 
                                    min_5_overlap = self.get_primer_min_5_overlap(),
                                    save_files=False)
                                
            #Print the How we call the CreatePrimers function
            print(f"Calls: exonsurfer.CreatePrimers(gene = {self.symbol}, transcripts = {self.get_transcript()}, species = {self.species}, design_dict = {self.get_design_config()}, opt_prod_size = {self.get_opt_prod_size()}, e_value = {self.get_e_value()}, i_cutoff={self.get_i_cutoff()}, max_sep={self.get_max_sep()}, NPRIMERS={self.get_nprimers()}, d_option={self.get_primer_junction_design()}, min_3_overlap = {self.get_primer_min_3_overlap()}, min_5_overlap = {self.get_primer_min_5_overlap()}, save_files=False)")                     
            print("[!] Print df_primers",flush=True)
            print(df_primers)
            # Check if the primer design has been successful
            # If not, redirect to error page
            # Check id df_primers is none
            
            if not (df_primers is None):
                print("[!] Primer design successful")
                #Save the results in the DB
                result = Result.create_result(self, df_blast, df_primers, genomic_blast)
                self.set_run()
                # Create a new column with the pair_num
                df_primers["pair_num"] = df_primers.index
            else:
                print("[!] Primer design failed",flush=True)
                #Redirect to error page indicating the error_log
        else:
            print("[!] ### Session already run, getting results ###", flush=True)
            df_primers = Result.objects.get(session_id=self).get_primer_file()
            df_blast = Result.objects.get(session_id=self).get_blast_file()
            genomic_blast = Result.objects.get(session_id=self).get_genomic_blast_file()
            error_log = None
        return df_blast, genomic_blast, df_primers, error_log 
    
    def get_call_command(self):
        """
        Method to get the call command
        Returns
        -------
        str
            Call command
        """
        call_command = f"exonsurfer.CreatePrimers(gene = '{self.symbol}', transcripts = {self.get_transcript()}, species = '{self.species}', design_dict = {self.get_design_config()}, opt_prod_size = {self.get_opt_prod_size()}, e_value = {self.get_e_value()}, i_cutoff={self.get_i_cutoff()}, max_sep={self.get_max_sep()}, NPRIMERS={self.get_nprimers()}, d_option={self.get_primer_junction_design()}, min_3_overlap = {self.get_primer_min_3_overlap()}, min_5_overlap = {self.get_primer_min_5_overlap()}, save_files=False)"
        return call_command

    def get_run_parameters(self):
        """
        Method to obtain a dictionary with the run parameters
        """
        primer_config = self.get_design_config()

        for key, value in (("gene", self.symbol),
                           ("transcripts", self.transcript),
                           ("species", self.species),
                           ("opt_prod_size", self.get_opt_prod_size()),
                           ("e_value", self.get_e_value()),
                           ("i_cutoff", self.get_i_cutoff()),
                           ("max_sep", self.get_max_sep()),
                           ("NPRIMERS", self.get_nprimers()),
                           ("d_option", self.get_primer_junction_design()),
                           ("min_3_overlap", self.get_primer_min_3_overlap()),
                           ("min_5_overlap", self.get_primer_min_5_overlap())):
            primer_config[key] = value
        
        return primer_config

    def get_session_data_path(self):
        """
        Method to get the session data path
        Returns
        -------
        str
            Session data path
        """
        return os.path.join(settings.DATA_DIR, self.session_id)

    def get_primer_min_3_overlap(self):
        """
        Method to get the primer 3' overlap
        Returns
        -------
        int
            Primer 3' overlap
        """
        return self.primer_config.primer_min_3_overlap
    
    def get_primer_min_5_overlap(self):
        """
        Method to get the primer 5' overlap
        Returns
        -------
        int
            Primer 5' overlap
        """
        return self.primer_config.primer_min_5_overlap
    
    def get_transcript(self):
            """
            Method to get the transcript
            Returns
            -------
            Transcript
                Transcript object
            """
            print("[!] Getting transcript", flush=True)
            print(self.transcript, flush=True)
            #Print the class type from the transcript
            print(type(self.transcript), flush=True)
            if self.transcript == "ALL":
                return "ALL"
            #If self.transcript is a list return the list
            elif type(self.transcript) == list:
                return self.transcript
            else:
                return eval(self.transcript)

    def get_session_url(self):
        """
        Method to get the session url
        Returns
        -------
        str
            Session url
        """
        session_link = f"https://exonsurfer.i-med.ac.at/design/primerblast/{self.session_id}/"
        return session_link
    
    def get_e_value(self):
        return self.primer_config.primer_e_cutoff

    def get_i_cutoff(self):
        return self.primer_config.primer_i_cutoff

    def get_max_sep(self):
        return self.primer_config.primer_max_sep
    
    def get_nprimers(self):
        return self.primer_config.primer_pairs_number
              
    def get_primer_junction_design(self):
        return self.primer_config.get_primer_junction_design()
    
    def get_number_of_transcripts_for_gene(self):
        """
        Function to obtain the number of transcripts for the gene.
        """
        gene_name = self.symbol
        species = self.species
        n_transcripts = Transcript.objects.filter(gene_name=gene_name, species=species, transcript_biotype="protein_coding").count()
        return n_transcripts
    
    def remove_temporal(self):
        """
        Method to remove session and session files
        for session older than 1 day
        """
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if (now - self.date_joined).days > 7:
            import shutil
            try:
                shutil.rmtree(self.get_session_data_path())
            except:
                pass
            self.delete()


    def create_session(species, symbol, transcript):
        """
        Method to create a session
        Parameters
        ----------
        species: str
            Species
        symbol: str
            Gene symbol
        transcript: str
            Transcript
        Returns
        -------
        Session
            Session object
        """
        session = Session()
        session.species = species
        session.symbol = symbol
        session.transcript = transcript
        session.set_n_transcript()
        session.save()

        return session
    
    def set_run(self):
        """
        Method to set the run
        """
        self.is_run = True
        self.save()

    def set_design_config(self, primer_config):
        """
        Method to set the design configuration
        """
        self.primer_config = primer_config
        self.save()

    def set_from_file(self):
        """
        Method to set the from file
        """
        self.from_file = True
        self.save()
        
    def set_n_transcript(self):
        """
        Method to set the number of transcripts
        """
        self.n_transcript = self.get_number_of_transcripts_for_gene()
        self.save()

    def get_opt_prod_size(self):
        """
        Method to get the optimal product size
        Returns
        -------
        int
            Optimal product size
        """
        return self.primer_config.primer_product_size_opt
    
    def get_design_config(self):
        """
        Method to get the design configuration
        Returns
        -------
        dict
            Dictionary with the design configuration
        """

        config = self.primer_config
        print("[+] Getting design config")
        print(config)
        design_dict = {
            'PRIMER_OPT_SIZE': config.primer_opt_size,
            'PRIMER_MIN_SIZE': config.primer_min_size,
            'PRIMER_MAX_SIZE': config.primer_max_size,
            'PRIMER_OPT_TM': config.primer_opt_tm,
            'PRIMER_MIN_TM': config.primer_min_tm,
            'PRIMER_MAX_TM': config.primer_max_tm,
            'PRIMER_OPT_GC_PERCENT': config.primer_opt_gc,
            'PRIMER_MIN_GC': config.primer_min_gc,
            'PRIMER_MAX_GC': config.primer_max_gc,
            'PRIMER_PRODUCT_SIZE_RANGE': [[config.primer_product_size_min, config.primer_product_size_max]],
            'PRIMER_PRODUCT_OPT_TM': config.primer_product_opt_tm,
            'PRIMER_PRODUCT_MIN_TM': config.primer_product_min_tm,
            'PRIMER_PRODUCT_MAX_TM': config.primer_product_max_tm,
            'PRIMER_SALT_DIVALENT': config.primer_salt_divalent,
            'PRIMER_SALT_MONOVALENT': config.primer_salt_monovalent,
            'PRIMER_DNTP_CONC': config.primer_dntp_conc,
            # not shown to user
            'PRIMER_MAX_POLY_X': config.primer_max_poly_x,
            'PRIMER_GC_CLAMP': config.primer_gc_clamp,
            'PRIMER_MAX_END_GC': config.primer_max_end_gc,
            'PRIMER_WT_GC_PERCENT_GT': config.primer_wt_gc_percent_gt,
            'PRIMER_WT_GC_PERCENT_LT': config.primer_wt_gc_percent_lt,
            }
        return design_dict

    def get_primer_pair(self, primer_pair_id):
        """
        Method to get a primer pair, from the result primer file
        Parameters
        ----------
        primer_pair_id: str
            Primer pair id
        Returns
        -------
        PrimerPair: dict
            Primer pair dictionary
        """
        try:
            print("[+] Getting session file")
            primer_df = Result.objects.get(session=self).get_primer_file()
            primer_df = round(primer_df, 2)
            primer_df.index = primer_df["pair_num"]
            print("[+] Getting primer pair, ", primer_pair_id)
           
            # Obtain the row with pair_num == primer_pair_id
            
            primer_pair = primer_df.loc[str(primer_pair_id), :].to_dict()            

        except Exception as e:
            print(e)
            print("[!] Primer pair not found")
            primer_pair = None
        return primer_pair

    def update_queue_job_id(self, job):
        """
        Method to update the queue job id
        Parameters
        ----------
        job: Job
            Job object
        """
        self.enqueued_job_id = job.id
        self.save()
        
    def get_primer_pair_blast(self,primer_pair_id):
        """
        Method to get the primer pair blast
        Returns
        -------
        PrimerPair: DF
            Primer pair DF
        
        """
        try:
            print("[+] Getting session file")
            blast_df = Result.objects.get(session=self).get_blast_file()
            blast_df = round(blast_df, 2)
            print("[+] Getting primer pair blast")
            blast_df["pair_num"] = blast_df["query id"].apply(lambda x: x.split("_")[0])
            primer_pair = blast_df.query(f"pair_num == '{primer_pair_id}'")

        except Exception as e:
            print(e)
            print("[!] Primer pair not found")
            primer_pair = None
        return primer_pair

    session_id = models.UUIDField(default = uuid.uuid4, editable = True, unique = True)
    enqueued_job_id = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    species = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)
    transcript = models.CharField(max_length=1000)
    primer_config = models.ForeignKey('PrimerConfig', on_delete=models.CASCADE, null=True)
    is_run = models.BooleanField(default=False)
    from_file = models.BooleanField(default=False)
    n_transcript = models.IntegerField(default=0)

    
class Result(models.Model):
    """
    Class to store the results
    Attributes
    ----------
    session: Session
        Session ForeignKey
    result: str
        Result
    """
    def get_session_path(self, filename): 
        
        path = os.path.join('Sessions', \
            str(self.session.session_id),"file",filename) # version with dash
        # return os.path.join(self.identifier.hex, filename) # version without dash
        return path
    
    def set_blast_file(self, df):
        self.BlastFile = ContentFile(df.to_csv())
        self.BlastFile.name = "blast_%s_%s.csv"%(self.session.symbol,self.session.transcript)

    def set_primer_file(self, df):
        self.PrimerFile = ContentFile(df.to_csv())
        self.PrimerFile.name = "primer_%s_%s.csv"%(self.session.symbol,self.session.transcript)

    def set_genomic_blast_file(self, df):
        self.GenomicBlastFile = ContentFile(df.to_csv())
        self.GenomicBlastFile.name = "genomic_blast_%s_%s.csv"%(self.session.symbol,self.session.transcript)


    def get_primer_file(self):
        df = pd.read_csv(self.PrimerFile.path)
        df["other_transcripts"].fillna(False, inplace=True)
        return df

    def get_blast_file(self):
        df = pd.read_csv(self.BlastFile.path, index_col=0)
        return df

    def get_genomic_blast_file(self):
        df = pd.read_csv(self.GenomicBlastFile.path, index_col=0)
        return df

    def create_result(session, df_blast, df_primers, genomic_blast):
        """
        Method to create a result
        Parameters
        ----------
        session: Session
            Session object
        df_blast: pd.DataFrame
            DataFrame with the BLAST results
        df_primers: pd.DataFrame
            DataFrame with the primers
        Returns
        -------
        Result
            Result object
        """
        result = Result()
        result.session = session
        result.set_blast_file(df_blast)
        result.set_genomic_blast_file(genomic_blast)
        result.set_primer_file(df_primers)
        result.save()
        return result
        
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    BlastFile = models.FileField(storage=data_root, upload_to=get_session_path, blank=False, null=False, max_length=250)
    GenomicBlastFile = models.FileField(storage=data_root, upload_to=get_session_path, blank=False, null=False, max_length=250)
    PrimerFile = models.FileField(storage=data_root, upload_to=get_session_path, blank=False, null=False, max_length=250)

