while true; 
do 
    python3 /home/app/web/manage.py shell < /home/app/web/scripts/docker/remove_temporal.py;
    sleep 86400;
done;