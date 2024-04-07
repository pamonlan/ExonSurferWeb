podman pull docker.io/redis
podman pull docker.io/postgres
podman pull docker.io/nginx
podman pull docker.io/icbi/exonsurfer
podman login docker.io
podman pull docker.io/icbi/exonsurfer
podman-compose -f docker-compose.prod.yml up -d --build
podman-compose -f docker-compose.prod.yml logs -f

