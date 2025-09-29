#!/usr/bin/env python3
import sys
import os
sys.path.append('/home/jrwest/projects/LeadVille')

from src.impact_bridge.database.database import init_database, get_database_session
from src.impact_bridge.database.models import Sensor

# Initialize database
init_database("db/leadville.db")

with get_database_session() as session:
    specialpie_sensor = session.query(Sensor).filter(Sensor.hw_addr == '50:54:7B:AD:4F:03').first()
    if specialpie_sensor:
        print(f'Sensor ID: {specialpie_sensor.id}')
        print(f'Label: {specialpie_sensor.label}')
        print(f'Calibration data: {specialpie_sensor.calib}')
        print(f'Bridge ID: {specialpie_sensor.bridge_id}')
        print(f'Last seen: {specialpie_sensor.last_seen}')
        
        # Check if it should be detected as SpecialPie
        print(f'Address: {specialpie_sensor.hw_addr}')
        print(f'Label contains SP: {"SP" in specialpie_sensor.label.upper()}')
    else:
        print('SpecialPie sensor not found in database')