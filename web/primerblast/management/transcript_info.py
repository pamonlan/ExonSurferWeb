from ExonSurfer.ensembl import ensembl

# example test data
transcripts = {
    'Transcript 1': ['exon1', 'exon2', 'exon3', 'exon4'],
    'Transcript 2': ['exon2', 'exon3', 'exon5', 'exon6'],
    'Transcript 3': ['exon1', 'exon3', 'exon5']
}

exons = {
    'exon1': (10, 30),
    'exon2': (40, 60),
    'exon3': (80, 100),
    'exon4': (110, 130),
    'exon5': (140, 180),
    'exon6': (200, 210)
}
primers = {
    'F': (10, 30),
    'R': (120, 130)
}

def get_transcripts_exons_dict(gene):
    """
    This function takes a gene object and returns a dictionary of transcript
    objects, with transcript ID as keys, and exon objects as values.
    Args:
        gene [in] (gene object)   Gene object
        exclude_noncoding [in] (bool) False if all transcripts, True to exclude non
                          coding
        dTranscripts [out] (dict) Dictionary of transcript objects, with
                     transcript ID as keys, and exon objects as values
    """
    dT = {}
    dE = {}
    
    # get list of transcripts to iterate
    all_transcripts = ensembl.get_transcript_from_gene(gene)

    tcripts = ensembl.get_coding_transcript(all_transcripts)
    

    for tcript in tcripts:
        dT[tcript.id] = ensembl.get_exons_from_transcript(tcript)

        for exon in tcript.exons:
            dE[exon.id] = (exon.start, exon.end)

     
    return dT,dE

def get_exon_transcript_information(species = None, symbol=None,release=108, transcript = None):
    """
    Function that obtain the information of the transcripts and exons positions of a gene
    Args:
        species (string): Species name
        symbol (string): Gene symbol
        release (int): Ensembl release
    Returns:
        transcripts (dictionary): Dictionary with the exons of each transcript
        exons (dictionary): Dictionary with exons positions
    """

    data = ensembl.create_ensembl_data(release, 
                                       species)

    gene_obj = ensembl.get_gene_by_symbol(symbol, data)
        
    dT,dE = get_transcripts_exons_dict(gene_obj)

    # If transcript are provided, only return the information of that transcript
    if transcript != "ALL":
        dT = {transcript: dT[transcript]}


    return dT,dE, gene_obj.contig