# Changelog

All notable changes to ExonSurferWeb are documented in this file.

## [2.0.0-rc1] - 2026-11-26

### Added
- Multi-species configuration registry (`species_config.py`) supporting 14 organisms (Ensembl 108, Ensembl Plants 57, WormBase ParaSite WBPS19) and updated FAQ list.
- `fix_table_txt.py` in Docker entrypoint to regenerate `table.txt` from cached Ensembl cDNA FASTAs for affected species.
- `qpcr_analysis` app (`/qpcr/qpcr_analysis/`): ΔΔCt relative expression calculator with technical-replicate averaging, asymmetric error bounds ($2^{-(\Delta\Delta C_t \pm \mathrm{SD}_{\Delta C_t})}$), Welch's *t*-test on ΔCt, downloadable example Excel file (`/qpcr/example/`), and copy-ready manuscript Methods paragraph.
- `web/.dockerignore` excluding `Data/` and caches from Docker builds.

### Changed
- Upgraded base image to Ubuntu 22.04 and Python 3.10 in `web/Dockerfile.prod`; pinned `CrisRu95/ExonSurfer` commit (`2f7e4d1`) and upgraded `pip`/`setuptools`/`wheel` in builder stage so `pamonlan/pyensembl` builds cleanly.
- Updated `web/requirements.txt` to patch CVEs (`Django>=4.2.30,<5.0`, `certifi>=2026.10.19`, `idna>=3.15`, `requests>=2.33.0`, `sqlparse>=0.6.0`, `urllib3>=2.8.0`, `biopython>=1.87`) and removed runtime linter packages (`pylint` and dependencies).
- Switched home page gene dropdowns (`index.html`) to lazy-load per selected species instead of fetching all 14 species on page load.
- Parked housekeeping-gene population in `populate_data.py` (model/migrations kept intact).

### Fixed
- Fixed `qpcr_analysis` error bars (now asymmetric linear bounds instead of raw ΔCt SD), group-column switching (`get_groups`), `NaN` p-value handling, and CSRF cookie initialization on first visit.
