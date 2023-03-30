from ExonSurfer.exonsurfer import CreatePrimers
import pandas as pd
import time

lGenes = ["CLCA2", "TP53", "BRCA1", "BRCA2","CYP2D6"]

#Range of N primers to test the speed
#Range (10,2000) step of 300
lPrimers = [10, 300, 600, 900, 1200, 1500, 1800, 2000]
lRes = []

for gene in lGenes:
    for i in lPrimers:
        t0 = time.time()
        df_blast, df_primers, error_log = CreatePrimers(gene = gene, 
                                species = "homo_sapiens",
                                transcripts = "ALL",
                                NPRIMERS = i, 
                                save_files=False)
        t1 = time.time()
        # Create a df storing the gene, nro in df_primers, number of primers and time
        if df_primers is not None:
            nrows = len(df_primers.index)
        else:
            nrows = 0
        df = pd.DataFrame([[gene, nrows, i, t1-t0]],
                            columns = ["gene", "nro_primers", "nro_design", "time"])
        lRes.append(df)
        print("[!] Gene: {}, nro primers: {}, time: {}".format(gene, i, t1-t0))
res = pd.concat(lRes)
res.to_csv("test_speed_2.csv", index=False)