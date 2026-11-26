#!/bin/sh

if [ "$(id -u)" = "0" ]; then
    exec runuser -u nobody -g nogroup -- "$0" "$@"
fi

export PYENSEMBL_CACHE_DIR=/home/app/web/Data/
export EXONSURFER_CACHE_DIR=/home/app/web/Data/

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi
exec "$@"
