# Application Architecture: SolaX Data Management System

## 1. Overview
This document outlines the containerized deployment and data synchronization strategy for the SolaX Cloud API extractor. The system is designed to handle multiple inverters, ensure data integrity through idempotent syncing, and provide real-time visualization via Grafana.

## 2. Container Orchestration (Docker Compose)
The system consists of three primary services:
*   **`solax-extractor`**: A Python-based service that executes the sync logic and manages migrations via Alembic.
*   **`postgres`**: An **ephemeral** PostgreSQL database. Data is re-ingested from the local JSON files on every container startup.
*   **`grafana`**: A visualization dashboard pre-configured to read from the PostgreSQL container.

### Persistence Strategy
To maintain a "Zero-State" container environment:
1.  **JSON as Source of Truth**: All telemetry data is persisted on the host machine in the `data/` directory.
2.  **Ephemeral DB**: The PostgreSQL container does **not** use persistent volumes. It is wiped on `docker-compose down` and rebuilt on `up`.
3.  **Startup Ingestion**: On boot, the `solax-extractor` runs a sync job that parses all historical JSON files and populates the fresh database instance.

## 3. Data Extraction & Migration Logic

### A. Database Migrations (Alembic)
The system uses Alembic to manage the schema of the PostgreSQL database. This ensures that every time the container spins up, the tables are at the latest version. Initial data loading scripts will read existing JSON files and sync them into the database.

### B. Multi-Inverter Support
The application reads a comma-separated list of Serial Numbers from the `SOLAX_INVERTER_SNS` environment variable. All inverters are assumed to belong to the same `SOLAX_SITE_ID`.

Example: `SOLAX_INVERTER_SNS=SN12345,SN67890`

### C. Smart Sync & Idempotency
To solve the "incomplete data" problem, the extractor follows these rules:
1.  **Today is Volatile**: The current day's data is **always** re-fetched and overwritten to capture real-time updates as the sun generates power.
2.  **Completeness Threshold**: For historical dates, the application inspects existing JSON files. A re-sync is triggered if:
    *   The file does not exist.
    *   The `"empty"` flag is `true`.
    *   The total records count (`"total"`) is less than **180** (indicating a partial day).
3.  **Finalized Data**: Once a historical day reaches the threshold or the day is over and has a reasonable count, it is skipped in future runs to minimize API overhead.

## 4. Storage Layer (PostgreSQL)
A persistent PostgreSQL database is used for time-series storage.
*   **Table Schema**: `inverter_data`
    *   `id` (BigInt, PK)
    *   `inverter_sn` (String)
    *   `update_time` (DateTime) - Primary Timestamp
    *   `daily_inverter_output_kwh` (Float) - `yieldtoday`
    *   `total_inverter_output_kwh` (Float) - `yieldtotal`
    *   `realtime_power_watts` (Float) - `gridpower`
    *   `total_pv_power_watts` (Float) - `pvPower`
    *   `mppt1_voltage_volts` (Float) - `vdc1`
    *   `mppt1_current_amps` (Float) - `idc1`
    *   `ac_voltage_volts` (Float) - `vac1`
    *   `inverter_temperature_celsius` (Float) - `inverterTemperature`
    *   `raw_data` (JSON) - Fallback for future-proofing

## 5. Visualization (Grafana)
Grafana is provisioned automatically with:
*   **PostgreSQL Datasource**: Points to the `postgres` container.
*   **Dashboards**: Modular dashboards showing:
    *   Aggregate generation (Inverter A + B).
    *   Individual inverter performance.
    *   Daily/Weekly/Monthly comparisons.

## 6. Project Structure
```
/
├── app/
│   ├── main.py              # Orchestrator & Scheduler
│   ├── client.py            # SolaX API
│   ├── crypto.py            # AES/MD5 logic
│   └── requirements.txt
├── data/                    # JSON source of truth
├── migrations/              # Alembic migration scripts
├── grafana/
│   ├── provisioning/        # Auto-config
│   └── dashboards/          # JSON definitions
├── .env                     # Credentials
├── inverters.json           # Hardware config
├── alembic.ini              # Migration config
└── docker-compose.yml
```
