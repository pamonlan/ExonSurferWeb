from django.db import models
import uuid
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import pandas as pd
import numpy as np
# Create your models here.
data_root = FileSystemStorage(location=settings.DATA_DIR)


class PrimerConfig(models.Model):

    """
    Class to store the primer configuration
    Attributes
    ----------
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
    Methods
    -------
    """

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
        print(dict)
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
        primer_config.primer_product_size_max = dict["primer_product_size_max"]
        primer_config.primer_product_opt_tm = dict["primer_product_opt_tm"]
        primer_config.primer_product_min_tm = dict["primer_product_min_tm"]
        primer_config.primer_product_max_tm = dict["primer_product_max_tm"]
        primer_config.primer_salt_divalent = dict["primer_salt_divalent"]
        primer_config.primer_salt_monovalent = dict["primer_salt_monovalent"]
        primer_config.primer_dntp_conc = dict["primer_dntp_conc"]

        
        primer_config.save()

        return primer_config
    #Primer Size
    primer_opt_size = models.IntegerField(default=20)
    primer_min_size = models.IntegerField(default=17)
    primer_max_size = models.IntegerField(default=35)
    #Primer Tm
    primer_opt_tm = models.FloatField(default=59)
    primer_min_tm = models.FloatField(default=57.5)
    primer_max_tm = models.FloatField(default=60.5)
    #Primer GC
    primer_opt_gc = models.IntegerField(default=50)
    primer_min_gc = models.IntegerField(default=20)
    primer_max_gc = models.IntegerField(default=80)
    #Product Size
    primer_product_size_min = models.IntegerField(default=60)
    primer_product_size_opt = models.IntegerField(default=200)
    primer_product_size_max = models.IntegerField(default=250)
    #Product Tm
    primer_product_opt_tm = models.FloatField(default=80)
    primer_product_min_tm = models.FloatField(default=65)
    primer_product_max_tm = models.FloatField(default=90)
    #PCR Parameters
    primer_salt_divalent = models.FloatField(default=1.5)
    primer_salt_monovalent = models.FloatField(default=50)
    primer_dntp_conc = models.FloatField(default=0.6)



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

    session_id = models.UUIDField(default = uuid.uuid4, editable = False, unique = True)
    created_at = models.DateTimeField(auto_now_add=True)
    species = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)
    transcript = models.CharField(max_length=100)
    primer_config = models.ForeignKey('PrimerConfig', on_delete=models.CASCADE, null=True)
    is_run = models.BooleanField(default=False)

    
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

    def get_primer_file(self):
        df = pd.read_csv(self.PrimerFile.path)
        df["other_transcripts"].fillna(False, inplace=True)
        return df

    def get_blast_file(self):
        df = pd.read_csv(self.BlastFile.path, index_col=0)
        return df

    def create_result(session, df_blast, df_primers):
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
        result.set_primer_file(df_primers)
        result.save()
        return result
        
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    BlastFile = models.FileField(storage=data_root, upload_to=get_session_path, blank=False, null=False, max_length=250)
    PrimerFile = models.FileField(storage=data_root, upload_to=get_session_path, blank=False, null=False, max_length=250)

