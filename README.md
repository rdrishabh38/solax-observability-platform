# SolaX Observability Platform

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/python-3.8-blue.svg)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=flat&logo=postgresql&logoColor=white)
![Grafana](https://img.shields.io/badge/grafana-%23F46800.svg?style=flat&logo=grafana&logoColor=white)

An automated data extraction and observability platform for SolaX solar inverters. This system reverse-engineers the SolaX Cloud web portal API to retrieve high-resolution telemetry data (MPPT, AC/DC power, temperatures) that is often missing from the official API.

## Features

* **Automated Extraction**: Periodically fetches data from SolaX Cloud using reverse-engineered AES-128-CBC encrypted protocols.
* **Smart Sync Engine**: 
    * **Volatile Today**: Always refreshes the current day's data to capture real-time updates.
    * **Historical Backfill**: Automatically detects and re-fetches incomplete historical days (based on a configurable record threshold).
    * **Start-Date Exception**: Intelligent handling of the plant's first day to prevent redundant fetches of naturally low-volume data.
* **Zero-State Architecture**: 
    * **JSON Source of Truth**: All raw data is persisted in a structured directory (`data/<SN>/<SN>_<yyyy_mm_dd>.json`).
    * **Ephemeral Database**: PostgreSQL is used as a query-accelerator for Grafana but is rebuilt from JSON files on every startup.
* **Full Observability**: Pre-provisioned Grafana dashboards for Daily, Monthly, and Lifetime performance tracking.
* **Anti-Bot Protection**: Implements random jitter delays and browser-mimicking headers to prevent API rate-limiting or detection.

## System Architecture

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Extractor** | Python 3.8 | Core logic for API interaction, crypto, and DB ingestion. |
| **Database** | PostgreSQL 15 | Time-series storage for dashboard performance. |
| **Migrations** | Alembic | Manages the descriptive schema for telemetry data. |
| **Visualization**| Grafana | Automated dashboards provided as code. |

## Quick Start

### 1. Prerequisites
* Docker and Docker Compose
* [`just`](https://github.com/casey/just)

### 2. Configuration
Copy the example environment file and fill in your SolaX credentials:
```bash
cp .env.example .env
```
Edit `.env` and provide:
* `SOLAX_USERNAME`: Your SolaX login (usually email or username).
* `SOLAX_PASSWORD`: Your SolaX password.
* `SOLAX_SITE_ID`: Your Solar Plant ID.
* `SOLAX_INVERTER_SNS`: Comma-separated serial numbers of your inverters.

### 3. Launch
```bash
just up
```
The system will:
1. Start the PostgreSQL and Grafana containers.
2. Run database migrations via Alembic.
3. Ingest all local JSON files from `data/` into the database.
4. Launch Grafana at [http://localhost:3001](http://localhost:3001) (default login: `admin` / `admin`).

## Common Commands (Justfile)

| Recipe | Description | Command |
| :--- | :--- | :--- |
| `just up` | Start the stack and ingest local data (Dev Mode). | `docker compose up --build -d` |
| `just sync` | Trigger a live API fetch and update DB/JSON. | `docker compose run --rm -e SKIP_API_SYNC=false extractor` |
| `just logs` | Follow logs for the extractor service. | `docker compose logs -f extractor` |
| `just down` | Stop containers and wipe ephemeral DB state. | `docker compose down` |
| `just reset` | Performs a `down` followed by an `up`. | `just down && just up` |

## Directory Structure
```text
.
├── app/                # Python application (Main, Client, Crypto, Database)
├── data/               # Persistent JSON storage (Source of Truth)
├── docs/               # Architectural & Technical specifications
├── grafana/            # Grafana provisioning and dashboard definitions
├── migrations/         # Alembic database migration scripts
├── docker-compose.yml  # Container orchestration
├── Dockerfile          # Extractor container definition
└── justfile            # Command runner
```

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.

## License & Copyright

**Copyright (c) 2026 Rishabh Dixit.**

Licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for the full license text.
