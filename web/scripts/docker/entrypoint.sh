#!/bin/sh

#python3 manage.py flush --no-input
python3 /home/app/web/manage.py makemigrations
python3 /home/app/web/manage.py migrate
#python3 manage.py migrate --database=gdpr_log
python3 /home/app/web/manage.py collectstatic --noinput
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('root', 'user@mail.com', 'user')" | python3 /home/app/web/manage.py shell
export PYENSEMBL_CACHE_DIR=/home/app/web/Data/
export EXONSURFER_CACHE_DIR=/home/app/web/Data/

pyensembl install --release 108 --species homo_sapiens mouse rat
exon_surfer.py -db True

#sh /home/app/web/scripts/docker/remove_temporal.sh &
exec "$@"
