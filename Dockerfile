FROM python:3.8-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and migration files
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Run the extractor
CMD ["python", "-m", "app.main"]
