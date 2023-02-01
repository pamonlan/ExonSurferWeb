# ExonSurfer

ExonSurfer is a web-based tool for designing high-specific transcript primers, built with Django and powered by the ExonSurfer python package. The tool allows users to set search options, visualize results, and obtain specific primers with low non-specific binding. The tool is designed to be user-friendly, fast, and accurate, with automated workflows.

## Requirements

- Python 3
- Docker or Docker-podman
- The ExonSurfer python package
- PyEnsembl

## Installation

1. Clone the ExonSurfer repository to your local machine:

```bash
git clone https://github.com/ExonSurfer/ExonSurfer.git
```

2. Install the required dependencies using pip:

```pip install -r requirements.txt```

3. Start the service using Docker or Docker-podman with the provided `docker-compose.prod.yml` file:

```docker-compose -f docker-compose.prod.yml up -d```

or

```podman-compose -f docker-compose.prod.yml up -d```

4. Access the web tool through a web browser at [http://localhost:8000](http://localhost:8000).

## Documentation

The documentation for ExonSurfer is available in the [doc](doc/) directory, and the manual is available in the [man](man/) directory. Additionally, a [user guide](https://exonsurfer.github.io/ExonSurfer/user-guide.html) is available online and a [setup guide](https://exonsurfer.github.io/ExonSurfer/setup-guide.html) is provided to assist with the installation process.

## License

ExonSurfer is open-source software licensed under the [MIT license](LICENSE).

## Contributing

Contributions to ExonSurfer are welcome and encouraged. Please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file for information on how to contribute.