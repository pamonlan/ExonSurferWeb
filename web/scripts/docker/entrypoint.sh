#!/bin/sh
#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi
#python3 manage.py flush --no-input
python3 /home/app/web/manage.py makemigrations
python3 /home/app/web/manage.py migrate
#python3 manage.py migrate --database=gdpr_log
python3 /home/app/web/manage.py collectstatic --noinput
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('root', 'user@mail.com', 'calicoelectronico!')" | python3 /home/app/web/manage.py shell
export PYENSEMBL_CACHE_DIR=/home/app/web/Data/
export EXONSURFER_CACHE_DIR=/home/app/web/Data/

# Vertebrates release 108
pyensembl install --release 108 --species homo_sapiens mus_musculus rattus_norvegicus \
    danio_rerio drosophila_melanogaster xenopus_tropicalis \
    caenorhabditis_elegans saccharomyces_cerevisiae

# Plants release 57
pyensembl install --release 57 --species arabidopsis_thaliana oryza_sativa \
    solanum_lycopersicum zea_mays glycine_max
    
python3 /home/app/web/DownloadWorm.py
exon_surfer.py -db True

# Regenerate table.txt for species whose Zenodo-bundled version was built with
# the gene_symbol/gene tag-priority bug (falls back to the stable Ensembl ID
# instead of the real gene symbol - breaks BLAST self/off-target detection).
# Reuses the cDNA FASTA pyensembl already cached above, no extra download.
python3 /home/app/web/scripts/docker/fix_table_txt.py \
    caenorhabditis_elegans drosophila_melanogaster saccharomyces_cerevisiae \
    xenopus_tropicalis oryza_sativa solanum_lycopersicum glycine_max zea_mays

echo "from ensembl.management.populate_data import main; main()" | python3 /home/app/web/manage.py shell

#sh /home/app/web/scripts/docker/remove_temporal.sh &
exec "$@"
