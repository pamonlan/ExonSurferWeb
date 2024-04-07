#!/bin/sh

#
export PYENSEMBL_CACHE_DIR=/home/app/web/Data/
export EXONSURFER_CACHE_DIR=/home/app/web/Data/
#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi
exec "$@"
