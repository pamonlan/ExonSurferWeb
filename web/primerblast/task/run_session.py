import pandas as pd
from ExonSurfer.exonsurfer import CreatePrimers
from primerblast.models import Session, Result

def run_session(session):           
    print("[!] ### Checking if the session has been run ###")
    print(session.is_run)
    if not session.is_run:
        print("[!] ### Session not run, running it ###")
        print("[+] Running primer design for: ", session.species, session.symbol, session.transcript, "")
        df_blast, df_primers, error_log = CreatePrimers(gene = session.symbol, 
                            transcripts = session.get_transcript(), 
                            species = session.species,
                            design_dict = session.get_design_config(),
                            opt_prod_size = session.get_opt_prod_size(),
                            save_files=False)
                            
        print("[!] Print df_primers",flush=True)
        print(df_primers)
        # Check if the primer design has been successful
        # If not, redirect to error page
        # Check id df_primers is none
        
        if not (df_primers is None):
            print("[!] Primer design successful")
            #Save the results in the DB
            result = Result.create_result(session, df_blast, df_primers)
            session.set_run()
            # Create a new column with the pair_num
            df_primers["pair_num"] = df_primers.index
        else:
            print("[!] Primer design failed",flush=True)
            #Redirect to error page indicating the error_log
    else:
        print("[!] ### Session already run, getting results ###", flush=True)
        df_primers = Result.objects.get(session_id=session).get_primer_file()
    return df_blast, df_primers, error_log
