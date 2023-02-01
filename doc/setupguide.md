# Setup guide

### Clone this project
Select a local directory and clone the main repository. Note that the Data directory will be on the same level as this repository.
  
```git clone  https://github.com/icbi-lab/mio/```

### Prerequisites
MIO supports `python3` only and is developed and tested on 3.6 and 3.7. 
[`miopy`](https://github.com/icbi-lab/miopy/) python library is needed to run all the analysis from MIO. You will also need to have [`Docker`](https://www.docker.com/) and ['docker-compose'](https://github.com/docker/compose) installed to run all the modules.

#### Required pyhton packages

To install/check python packages, in `./web` run `pip3 install -r requirements.txt`  
Note that you will need to have pip3 installed

### Config local setting file
Copy and modify the setting file for the webportal which is located under `./web/mirweb/settings.py`. 

Few things need to be modified in the new setting file.
  * Add the desired domain or ip address to the `ALLOWED_HOST` list  
    eg. `set ALLOWED_HOST = ["*"]` to allow all possible addresses


### Migrate database
From `./web/` directory, run `python3 manage.py makemigrations` then `python3 manage.py migrate`

### Start the webserver
From `python3 manage.py runserver` will bind to all address and the default TCP port 8080.  
Check the website in the following link:
['http://127.0.0.1:8000/'](http://127.0.0.1:8000/)

### Create a superuser
In order to create a superuser run `python3 web/manage.py createsuperuser` and fill the different values.

### Populate the database

The tables in txt format to populate the database are in `./Tables`. We allow the user to directly copy this data in the database following the link `/create_gene` inside the webportal.

### Activate django-rq

All the analysis are handle with [`django-rq`](https://github.com/rq/django-rq). Django-rq need redis to share the information between the queues. To activate the queue run:
`python3 web/manage.py rqworker default slow normal faster`

## Create docker
To create directly the docker container with the nginx, gunicorn, django-rq, and the mio webtool the user only need to run the script run-docker.sh
```sudo sh scripts/run-docker.sh```. The link for the webtool will be https.//localhost:8889, and the super-user: user.