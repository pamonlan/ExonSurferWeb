# ExonSurfer

[ExonSurfer](https://exonsurfer.i-med.ac.at/) is a web-based tool for designing high-specific transcript primers, built with Django and powered by the ExonSurfer python package. This tool enables users to customize search options, visualize results, and obtain primers with high specificity and minimal non-specific binding. Designed for user-friendliness, speed, and accuracy, ExonSurfer integrates automated workflows to streamline the primer design process.

## Requirements

- Python 3
- Docker or Docker-podman
- The ExonSurfer python package
- PyEnsembl

## Installation

1. Clone the ExonSurfer repository to your local machine:

   ```bash
   git clone https://github.com/pamonlan/ExonSurferWeb.git
   ```

2. Install the required dependencies using pip:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the service using Docker or Docker-podman with the provided `docker-compose.prod.yml` file:

   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

   or

   ```bash
   podman-compose -f docker-compose.prod.yml up -d
   ```

4. Access the web tool through a web browser at http://localhost:8889.

## Configuration and Usage

### Data Preparation

- **Ensembl Database**: The web tool utilizes the Ensembl database via the PyEnsembl API for accurate and up-to-date genomic data. To set up, run the following in the `entrypoint.sh` script:

   ```bash
   pyensembl install --release 108 --species homo_sapiens
   ```

- **BLAST Database**: Primers are verified using a BLAST search to ensure specificity. The BLAST database is automatically set up using `exonsurfer.py` during the Docker container initialization.

- **Zenodo Downloads**: Additional resources and datasets are downloaded from Zenodo as part of the initialization process to ensure all necessary data is available for primer design.

### Running ExonSurfer

- Primer design is performed by executing `exonsurfer.py`, with task queuing managed via Django RQ to handle background processing efficiently.

## Documentation

Comprehensive documentation for ExonSurfer, including FAQs and a detailed manual, is readily accessible to facilitate setup and usage. The [FAQ section](https://exonsurfer.i-med.ac.at/faq/) provides answers to common questions. For in-depth guidance, the [manual](https://github.com/CrisRu95/ExonSurfer/blob/main/man/ExonSurfer_Manual.pdf) is available for download. Further information about the ExonSurfer Python package can be found on its [GitHub repository](https://github.com/CrisRu95/ExonSurfer/tree/main). Visit the [ExonSurfer web application](https://exonsurfer.i-med.ac.at/) to start designing primers using the online interface.
## License

ExonSurfer is open-source software licensed under the [MIT license](LICENSE).

## Contributing

Contributions to ExonSurfer are welcome and encouraged.

