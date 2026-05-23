# SolaX Data Management System Justfile

# Start the environment in development mode (No API sync, just ingest JSON)
up:
    docker compose up --build -d
    docker compose logs -f extractor

# Stop the environment and wipe all ephemeral data (Postgres & Grafana state)
down:
    docker compose down

# Run a live API sync to pull fresh data from SolaX Cloud
sync:
    docker compose run --rm -e SKIP_API_SYNC=false extractor

# View logs for all services
logs:
    docker compose logs -f

# Get a shell inside the extractor container
shell:
    docker compose exec extractor /bin/bash

# Reset everything: Wipe state and restart fresh from JSON files
reset: down up
