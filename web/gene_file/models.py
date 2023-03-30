from django.db import models
import os
from primerblast.models import Session
from exonsurfer.settings import DATA_DIR
from django.core.files.storage import FileSystemStorage

data_root = FileSystemStorage(location=DATA_DIR)

# Create your models here.
class GeneFile(models.Model):
    def __str__(self):
        return self.file_name
    
    def from_file(self, file, session):
        print("[+] Creating GeneFile instance", flush=True)
        self.set_session(session)
        self.file = file
        self.set_file_type()
        self.set_name()
        self.set_sequence()
        self.save()
        print("[+] GeneFile instance created", flush=True)
    
    def get_gene_file_path(self):
        return os.path.join(DATA_DIR, str(self.session_id.session_id), "gene_file", self.file_name)
    
    def get_session_path(instance, filename):
        return os.path.join(str(instance.session_id.session_id),"gene_file", filename)
    
    def set_file_type(self):
        """
        Given a file, returns the file type based on its extension.
        """
        _, extension = os.path.splitext(self.file.name)
        if extension.lower() == ".gb" or extension.lower() == ".gbk":
            file_type = "GeneBank"
        elif extension.lower() == ".fasta" or extension.lower() == ".fa":
            file_type = "Fasta"
        else:
            file_type = None
        self.file_type = file_type
        self.save()


    def set_name(self):
        """
        Given a file, returns the file name.
        """
        self.file_name = os.path.basename(self.file.name)
        self.save()


    def set_sequence(self):
        """
        Given a file, returns the sequence.
        """
        if self.file_type == "GeneBank":
            self.sequence = self.get_sequence_from_gb()
        elif self.file_type == "Fasta":
            self.sequence = self.get_sequence_from_fasta()
        else:
            self.sequence = None
        self.save()

    def set_session(self, session):
        self.session_id = session
        self.save()

    def get_sequence_from_gb(self):
        """
        Given a GeneBank file, returns the sequence.
        """
        from Bio import SeqIO
        with open(self.file.path) as handle:
            for record in SeqIO.parse(handle, "genbank"):
                sequence = record.seq
        return sequence
    
    def get_sequence_from_fasta(self):
        """
        Given a Fasta file, returns the sequence.
        """
        from Bio import SeqIO
        with open(self.file.path) as handle:
            for record in SeqIO.parse(handle, "fasta"):
                sequence = record.seq
        return sequence

    file = models.FileField(storage=data_root, upload_to=get_session_path, blank=False, null=False, max_length=250)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    upload_date = models.DateTimeField(auto_now_add=True)
    sequence = models.TextField(blank=True)
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
