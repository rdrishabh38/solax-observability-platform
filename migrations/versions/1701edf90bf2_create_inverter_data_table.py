"""create_inverter_data_table

Revision ID: 1701edf90bf2
Revises: 
Create Date: 2026-05-23 13:02:11.405902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1701edf90bf2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'inverter_data',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('inverter_sn', sa.String(50), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=False),
        sa.Column('upload_time_ms', sa.BigInteger()),
        sa.Column('device_working_condition', sa.String(50)),
        sa.Column('daily_inverter_output_kwh', sa.Float()),
        sa.Column('total_inverter_output_kwh', sa.Float()),
        sa.Column('total_exported_energy_kwh', sa.Float()),
        sa.Column('total_imported_energy_kwh', sa.Float()),
        sa.Column('realtime_power_watts', sa.Float()),
        sa.Column('total_pv_power_watts', sa.Float()),
        sa.Column('grid_power_watts', sa.Float()),
        sa.Column('grid_frequency_hz', sa.Float()),
        sa.Column('mppt1_power_watts', sa.Float()),
        sa.Column('mppt1_voltage_volts', sa.Float()),
        sa.Column('mppt1_current_amps', sa.Float()),
        sa.Column('mppt2_power_watts', sa.Float()),
        sa.Column('mppt2_voltage_volts', sa.Float()),
        sa.Column('mppt2_current_amps', sa.Float()),
        sa.Column('ac_power_watts', sa.Float()),
        sa.Column('ac_voltage_volts', sa.Float()),
        sa.Column('ac_current_amps', sa.Float()),
        sa.Column('ac_frequency_hz', sa.Float()),
        sa.Column('inverter_temperature_celsius', sa.Float()),
        sa.Column('eps_power_watts', sa.Float()),
        sa.Column('eps_active_power_watts', sa.Float()),
        sa.Column('total_eps_power_watts', sa.Float()),
        sa.Column('raw_data', sa.JSON()),
        sa.UniqueConstraint('inverter_sn', 'update_time', name='uq_sn_timestamp')
    )
    op.create_index('ix_inverter_data_update_time', 'inverter_data', ['update_time'])


def downgrade() -> None:
    op.drop_table('inverter_data')
