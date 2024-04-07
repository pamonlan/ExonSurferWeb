### Prerequisites
- Docker and Docker Compose installed on your machine.
- Basic understanding of Docker, Docker Compose, and command line operations.

### Directory Structure
Ensure your project directory is structured as follows:

```
ExonSurferWeb/
│
├── web/
│   ├── Dockerfile.prod
│   ├── entrypoint.sh
│   ├── entrypoint_2.sh
│   └── ...
│
├── nginx/
│   └── Dockerfile
│
├── scripts/
│   └── docker/
│       ├── entrypoint.sh
│       └── entrypoint_2.sh
│
├── bin/
│   └── blastn
│
├── .env.prod
├── .env.prod.db
└── docker-compose.yml
```

### Docker Configuration
#### Dockerfile.prod
This Dockerfile builds the production image for the ExonSurferWeb app, including setting up the necessary environment, installing dependencies, and preparing the application.

#### Entry Scripts
- **`entrypoint.sh`**: Initializes the application by setting up database connections, running migrations, and downloading necessary datasets.
- **`entrypoint_2.sh`**: Used for worker processes that need to ensure database connectivity.

### Docker Compose Configuration
`docker-compose.yml` defines services such as web, Redis, workers, Nginx, and database. Each service is configured with specific build parameters, environment settings, and volume mappings.

#### Services Overview
- **Web**: Runs the Django application using Gunicorn.
- **Workers**: Process background jobs using Django RQ.
- **Nginx**: Serves static files and proxies other requests to the Django app.
- **Redis**: Manages task queues for Django RQ.
- **Database**: Hosts the PostgreSQL database with persistent data storage.

### Setup Instructions
1. **Entry Script Modifications (`entrypoint.sh`)**:
   - Include commands to download and set up the Ensembl database using PyEnsembl. For example:
     ```bash
     pyensembl install --release 108 --species homo_sapiens
     ```
   - Ensure the script also handles the construction of the BLAST database using `exonsurfer.py`, and manage the download of necessary files from Zenodo.

2. **Running ExonSurfer**:
   - Primer design is executed using `exonsurfer.py` integrated into the workflow, with task queuing handled by Django RQ, configured to run through the worker services defined in Docker Compose.

### Running the Application
1. **Building and Launching Services**:
   ```bash
   docker-compose up -d --build
   ```

2. **Web Access**:
   - Access the ExonSurferWeb interface via `http://localhost:8000` or through Nginx at port `8889`.

3. **Use Django RQ for Task Management**:
   - Monitor and manage queued tasks using Django's admin interface or directly through the Redis service.

### Maintenance and Management
- Regularly update the Ensembl database as new releases come out using the `pyensembl` command in the entry script.
- Monitor the health and performance of services using Docker Compose logs and management commands.

### Cleanup
- To stop and remove all containers and volumes:
  ```bash
  docker-compose down -v
  ```