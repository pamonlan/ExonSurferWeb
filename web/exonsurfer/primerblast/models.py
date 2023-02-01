from django.db import models
import uuid
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import pandas as pd

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
    """



    def from_dict(dict):
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
        primer_config = PrimerConfig()
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
        primer_config.save()
        return primer_config

    primer_opt_size = models.IntegerField()
    primer_min_size = models.IntegerField()
    primer_max_size = models.IntegerField()
    primer_opt_tm = models.FloatField()
    primer_min_tm = models.FloatField()
    primer_max_tm = models.FloatField()
    primer_opt_gc = models.IntegerField()
    primer_min_gc = models.IntegerField()
    primer_max_gc = models.IntegerField()
    primer_product_size_min = models.IntegerField()
    primer_product_size_max = models.IntegerField()



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

    def set_config(self, primer_config):
        """
        Method to set the primer configuration
        Parameters
        ----------
        primer_config: PrimerConfig
            PrimerConfig object
        """
        self.primer_config = primer_config

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

    session_id = models.UUIDField(default = uuid.uuid4, editable = False, unique = True)
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
        return pd.read_csv(self.PrimerFile.path)

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

