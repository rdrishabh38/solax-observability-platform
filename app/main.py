"""
SolaX Data Sync Orchestrator

Usage:
    source venv/bin/activate
    python3 -m app.main

Description:
    This script synchronizes daily energy data from the SolaX Cloud API
    for all configured inverters. It implements a 'Smart Sync' logic
    that always refreshes today's data and backfills incomplete historical records.
"""

import os
import json
import time
import random
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.client import SolaXClient
from app.database import SessionLocal, upsert_inverter_records

def run_migrations():
    """Executes alembic migrations to ensure the schema is up-to-date."""
    print("Running database migrations...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migrations complete.")
    except Exception as e:
        print(f"Migration error: {e}")

def ingest_historical_data():
    """Scans the data/ directory and loads all existing JSON records into the DB."""
    print("\nStarting historical data ingestion...")
    db = SessionLocal()
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        return

    # Walk through SN directories
    for sn in os.listdir(data_dir):
        sn_path = os.path.join(data_dir, sn)
        if not os.path.isdir(sn_path):
            continue
            
        print(f"  Processing inverter: {sn}")
        # Find all JSON files
        for filename in os.listdir(sn_path):
            if filename.endswith(".json"):
                file_path = os.path.join(sn_path, filename)
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        records = data.get("result", {}).get("records", [])
                        if records:
                            upsert_inverter_records(db, sn, records)
                            print(f"    Loaded {len(records)} records from {filename}")
                except Exception as e:
                    print(f"    Error loading {filename}: {e}")
    
    db.close()
    print("Historical ingestion complete.")

def sync_data():
    load_dotenv()
    threshold = int(os.getenv("SOLAX_RECORD_THRESHOLD", "170"))
    
    # Check if we should skip the API call loop (Default to TRUE for safety)
    if os.getenv("SKIP_API_SYNC", "true").lower() == "true":
        print("\nSKIP_API_SYNC is enabled (default). Skipping SolaX Cloud API calls.")
        return
    
    username = os.getenv("SOLAX_USERNAME")
    password = os.getenv("SOLAX_PASSWORD")
    site_id = os.getenv("SOLAX_SITE_ID")
    sns = os.getenv("SOLAX_INVERTER_SNS", "").split(",")
    start_date_str = os.getenv("SOLAX_START_DATE", "2026-05-09")
    
    if not all([username, password, site_id, sns]):
        print("Error: Missing configuration in .env file.")
        return

    client = SolaXClient(username, password)
    
    # Calculate date range
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.now()
    
    print(f"\n--- SolaX API Sync ---")
    print(f"Range: {start_date_str} to {end_date.strftime('%Y-%m-%d')}")
    
    current_date = start_date
    today_str = datetime.now().strftime("%Y-%m-%d")

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"\nProcessing Date: {date_str}")
        
        for sn in sns:
            sn = sn.strip()
            sn_dir = os.path.join("data", sn)
            os.makedirs(sn_dir, exist_ok=True)
            
            safe_date = date_str.replace("-", "_")
            filepath = os.path.join(sn_dir, f"{sn}_{safe_date}.json")
            
            should_fetch = False
            
            if not os.path.exists(filepath):
                should_fetch = True
                print(f"  [{sn}] {date_str}: New date detected, fetching data...")
            elif date_str == start_date_str:
                # Exception for start date: if file exists, don't re-fetch even if records are low
                print(f"  [{sn}] {date_str}: Start date file exists, skipping.")
                should_fetch = False
            else:
                # Check existing file for completeness
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        result = data.get("result", {})
                        total = result.get("total", 0)
                        is_empty = result.get("empty", True)
                        
                        if is_empty or total < threshold:
                            should_fetch = True
                            reason = "empty" if is_empty else f"incomplete ({total} records)"
                            print(f"  [{sn}] {date_str}: Local data is {reason}, re-fetching...")
                        else:
                            print(f"  [{sn}] {date_str}: Skipping (data is complete with {total} records)")
                except Exception as e:
                    print(f"  [{sn}] Error reading local file, re-fetching: {e}")
                    should_fetch = True
            
            if should_fetch:
                report = client.get_daily_report(sn, site_id, date_str)
                if report:
                    # Save to JSON
                    with open(filepath, "w") as f:
                        json.dump(report, f, indent=2)
                    print(f"  [{sn}] Saved to JSON")
                else:
                    print(f"  [{sn}] Failed to fetch data")
                
                # Anti-bot delay
                delay = random.uniform(2, 5)
                print(f"  ...pausing for {delay:.2f}s...")
                time.sleep(delay)
        
        current_date += timedelta(days=1)

    print(f"\n--- API Sync Complete ---")

if __name__ == "__main__":
    sync_data()
    run_migrations()
    ingest_historical_data()
