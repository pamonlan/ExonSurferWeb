from pyensembl import Genome

ls_data = Genome(
    reference_name='Litomosoides_sigmodontis_nLs.2.1',
    annotation_name='WormBase_ParaSite_WBPS19',
    gtf_path_or_url='https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.canonical_geneset.gtf.gz',
    transcript_fasta_paths_or_urls=['https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.mRNA_transcripts.fa.gz']
)

# --- ADD THIS LINE ---
ls_data.download() 
# ---------------------

ls_data.index()

