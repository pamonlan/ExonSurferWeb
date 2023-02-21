podman-compose -t 1podfw -f docker-compose.prod.yml up -d --build
podman-compose -f docker-compose.prod.yml exec web python3 manage.py flush --noinput
podman-compose -f docker-compose.prod.yml exec web python3 manage.py makemigrations --noinput
podman-compose -f docker-compose.prod.yml exec web python3 manage.py migrate --noinput
podman-compose -f docker-compose.prod.yml exec web python3 manage.py collectstatic --noinput

