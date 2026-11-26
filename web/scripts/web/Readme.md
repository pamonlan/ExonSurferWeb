## 1. Sequences

#### 1.1 Download Genomes (L. sigmodontis)

You need the genomic sequence (DNA) and the transcript sequence (RNA/cDNA).

```bash
# Create a directory for the new species
mkdir -p L_sigmodontis/dna
cd L_sigmodontis

# 1. Genomic DNA (The reference genome)
wget https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.genomic.fa.gz

# 2. Transcripts (cDNA equivalent)
wget https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.mRNA_transcripts.fa.gz

# Decompress
gzip -d *.gz

```

#### 1.2 Separate genome into one file per scaffold

*L. sigmodontis* is not assembled into chromosomes 1-22 like humans; it consists of "scaffolds" (e.g., `nLs.2.1.scaf00001`). The original script searched for "chromosome" text which doesn't exist here.

Use this adapted script to split the scaffolds:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# Configuration
species_name = "L_sigmodontis"
genome_file = "litomosoides_sigmodontis.PRJEB3075.WBPS19.genomic.fa"
output_dir = "dna_split"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"Reading {genome_file}...")

with open(genome_file, "r") as op:
    content = op.read()

# Split by the FASTA header indicator ">"
# The first element is usually empty if the file starts with >
split_content = content.split(">")

count = 0
for item in split_content:
    if not item.strip():
        continue
        
    # Extract the first word as the ID (e.g., nLs.2.1.scaf00001)
    # Headers in ParaSite look like: "nLs.2.1.scaf00001"
    header_line = item.split("\n", 1)[0]
    scaffold_id = header_line.split()[0]
    
    # Clean up the ID for the filename
    safe_id = scaffold_id.replace("|", "_").replace(":", "_")
    
    # Get the sequence (rest of the item)
    # We join it back just in case, though usually we just want to write it out
    sequence = item.split("\n", 1)[1].replace("\n", "")
    
    filename = f"{output_dir}/{species_name}_{safe_id}.txt"
    
    with open(filename, "w") as f_out:
        f_out.write(sequence)
        
    count += 1

print(f"Done! Created {count} scaffold files in {output_dir}/")

```

---

### 2. BLAST DB creation

#### 2.1 Process files (RNA) and Create Index Table

This step links Transcript IDs to Gene Names. Since we are using a custom genome, we cannot use `EnsemblRelease`. We must use the `Genome` object we created in the previous step.

**Script: `create_ls_index.py**`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyensembl import Genome
import os

# --- 1. SETUP THE CUSTOM GENOME (SAME AS BEFORE) ---
ls_data = Genome(
    reference_name='Litomosoides_sigmodontis_nLs.2.1',
    annotation_name='WormBase_ParaSite_WBPS19',
    gtf_path_or_url='https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.canonical_geneset.gtf.gz',
    transcript_fasta_paths_or_urls=['https://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS19/species/litomosoides_sigmodontis/PRJEB3075/litomosoides_sigmodontis.PRJEB3075.WBPS19.mRNA_transcripts.fa.gz']
)

# Ensure it's indexed
ls_data.download()
ls_data.index()

# --- 2. DEFINE THE TABLE CREATION FUNCTION ---

def create_index_table(fasta_path, output_table_path, genome_data):
    """
    Creates a table with transcript_id and gene_name using the custom genome object.
    """
    print(f"Processing {fasta_path}...")
    
    with open(output_table_path, "w") as table_out, open(fasta_path, "r") as fasta_in:
        for line in fasta_in:
            if line.startswith(">"):
                # Header format example: >nLs.2.1.2.t03847-RA
                # We strip the '>' and take the first word
                header_parts = line[1:].strip().split()
                t_id = header_parts[0]
                
                symbol = "NA"
                
                # Try to find the gene name via pyensembl
                try:
                    # Lookup transcript in our local database
                    t_obj = genome_data.transcript_by_id(t_id)
                    symbol = t_obj.gene_name
                except Exception:
                    # Fallback 1: Try finding it in the header text if pyensembl fails
                    # ParaSite headers often don't have "gene_symbol:", so we might default to gene_id
                    try:
                        t_obj = genome_data.transcript_by_id(t_id)
                        symbol = t_obj.gene_id 
                    except:
                        symbol = t_id # Worst case, use transcript ID as symbol
                
                table_out.write(f"{t_id}\t{symbol}\n")

    print(f"Finished. Table saved to {output_table_path}")

# --- 3. RUN IT ---

fasta_file = "litomosoides_sigmodontis.PRJEB3075.WBPS19.mRNA_transcripts.fa"
output_txt = "L_SIGMODONTIS.txt"

create_index_table(fasta_file, output_txt, ls_data)

```

#### 2.2 Build BLAST Databases

Finally, run the BLAST commands.

**For RNA (Transcripts):**

```bash
makeblastdb -dbtype nucl \
-in litomosoides_sigmodontis.PRJEB3075.WBPS19.mRNA_transcripts.fa \
-out l_sigmodontis.rna.fna

```

**For DNA (Genomic):**

```bash
makeblastdb -dbtype nucl \
-in litomosoides_sigmodontis.PRJEB3075.WBPS19.genomic.fa \
-out l_sigmodontis.dna.fna

```

### Summary of file locations

Update your ExonSurfer configuration to point to these new files:

* **Genome Split Dir:** `./L_sigmodontis/dna_split/`
* **Index Table:** `./L_sigmodontis/L_SIGMODONTIS.txt`
* **BLAST RNA:** `./L_sigmodontis/l_sigmodontis.rna.fna`
* **BLAST DNA:** `./L_sigmodontis/l_sigmodontis.dna.fna`
