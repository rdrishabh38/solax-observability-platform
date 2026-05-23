import os
from sqlalchemy import create_engine, Column, BigInteger, String, DateTime, Float, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

# Load database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://solax:solax_pass@db:5432/solax")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class InverterData(Base):
    __tablename__ = "inverter_data"

    id = Column(BigInteger, primary_key=True)
    inverter_sn = Column(String(50), nullable=False)
    update_time = Column(DateTime, nullable=False)
    upload_time_ms = Column(BigInteger)
    device_working_condition = Column(String(50))
    daily_inverter_output_kwh = Column(Float)
    total_inverter_output_kwh = Column(Float)
    total_exported_energy_kwh = Column(Float)
    total_imported_energy_kwh = Column(Float)
    realtime_power_watts = Column(Float)
    total_pv_power_watts = Column(Float)
    grid_power_watts = Column(Float)
    grid_frequency_hz = Column(Float)
    mppt1_power_watts = Column(Float)
    mppt1_voltage_volts = Column(Float)
    mppt1_current_amps = Column(Float)
    mppt2_power_watts = Column(Float)
    mppt2_voltage_volts = Column(Float)
    mppt2_current_amps = Column(Float)
    ac_power_watts = Column(Float)
    ac_voltage_volts = Column(Float)
    ac_current_amps = Column(Float)
    ac_frequency_hz = Column(Float)
    inverter_temperature_celsius = Column(Float)
    eps_power_watts = Column(Float)
    eps_active_power_watts = Column(Float)
    total_eps_power_watts = Column(Float)
    raw_data = Column(JSON)

    __table_args__ = (
        UniqueConstraint('inverter_sn', 'update_time', name='uq_sn_timestamp'),
    )

def safe_float(value):
    """Converts string to float, handling commas and empty values."""
    if value is None or value == "":
        return 0.0
    try:
        if isinstance(value, str):
            value = value.replace(",", "")
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def upsert_inverter_records(db_session, sn, records):
    """
    Performs a bulk UPSERT into PostgreSQL for a list of records.
    """
    for rec in records:
        try:
            # Map JSON keys to DB columns
            # Strip whitespace and trailing dots from time strings
            time_str = rec.get("uploadTimeValue", "").strip().rstrip(".")
            
            data = {
                "inverter_sn": sn,
                "update_time": datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S"),
                "upload_time_ms": rec.get("uploadTimeVal"),
                "device_working_condition": rec.get("inverterStatus"),
                "daily_inverter_output_kwh": safe_float(rec.get("yieldtoday")),
                "total_inverter_output_kwh": safe_float(rec.get("yieldtotal")),
                "total_exported_energy_kwh": safe_float(rec.get("feedinenergy")),
                "total_imported_energy_kwh": safe_float(rec.get("consumeenergy")),
                "realtime_power_watts": safe_float(rec.get("gridpower")),
                "total_pv_power_watts": safe_float(rec.get("pvPower")),
                "grid_power_watts": safe_float(rec.get("feedinpower")),
                "grid_frequency_hz": safe_float(rec.get("gridFreq")),
                "mppt1_power_watts": safe_float(rec.get("powerdc1")),
                "mppt1_voltage_volts": safe_float(rec.get("vdc1")),
                "mppt1_current_amps": safe_float(rec.get("idc1")),
                "mppt2_power_watts": safe_float(rec.get("powerdc2")),
                "mppt2_voltage_volts": safe_float(rec.get("vdc2")),
                "mppt2_current_amps": safe_float(rec.get("idc2")),
                "ac_power_watts": safe_float(rec.get("pac1")),
                "ac_voltage_volts": safe_float(rec.get("vac1")),
                "ac_current_amps": safe_float(rec.get("iac1")),
                "ac_frequency_hz": safe_float(rec.get("fac1")),
                "inverter_temperature_celsius": safe_float(rec.get("inverterTemperature")),
                "eps_power_watts": safe_float(rec.get("epsPower")),
                "eps_active_power_watts": safe_float(rec.get("EpsActivePower")),
                "total_eps_power_watts": safe_float(rec.get("totalEpsPower")),
                "raw_data": rec
            }

            stmt = insert(InverterData).values(**data)
            # On conflict (SN + timestamp), update everything to latest
            stmt = stmt.on_conflict_do_update(
                constraint="uq_sn_timestamp",
                set_=data
            )
            db_session.execute(stmt)
        except Exception as e:
            print(f"      Error parsing record at {rec.get('uploadTimeValue')}: {e}")
            continue
    
    db_session.commit()
