#!/usr/bin/env python3
"""
Migration: Create Bridge Configuration Tables
Description: Creates unified bridge config tables and migrates existing assignment data
Created: 2025-09-27
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BridgeConfigMigration:
    def __init__(self, db_path: str, json_config_path: str):
        self.db_path = db_path
        self.json_config_path = json_config_path
        self.conn = None
        
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")
        
    def disconnect(self):
        """Disconnect from the database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
            
    def backup_existing_data(self) -> Dict:
        """Backup existing assignment data before migration"""
        logger.info("Creating backup of existing assignment data...")
        
        backup_data = {
            'device_leases': [],
            'sensors': [],
            'bridge_device_config': None,
            'bridges': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Backup device_leases
        cursor = self.conn.execute("SELECT * FROM device_leases")
        backup_data['device_leases'] = [dict(row) for row in cursor.fetchall()]
        
        # Backup sensors with target assignments
        cursor = self.conn.execute("SELECT * FROM sensors WHERE target_id IS NOT NULL OR bridge_id IS NOT NULL")
        backup_data['sensors'] = [dict(row) for row in cursor.fetchall()]
        
        # Backup bridges
        cursor = self.conn.execute("SELECT * FROM bridges")
        backup_data['bridges'] = [dict(row) for row in cursor.fetchall()]
        
        # Backup JSON config
        try:
            if Path(self.json_config_path).exists():
                with open(self.json_config_path, 'r') as f:
                    backup_data['bridge_device_config'] = json.load(f)
        except Exception as e:
            logger.warning(f"Could not backup JSON config: {e}")
            
        # Save backup to file
        backup_file = f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
            
        logger.info(f"Backup saved to: {backup_file}")
        return backup_data
        
    def create_bridge_config_tables(self):
        """Create the new bridge configuration tables"""
        logger.info("Creating bridge configuration tables...")
        
        # Create bridge_configurations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bridge_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bridge_id INTEGER NOT NULL UNIQUE,
                stage_config_id INTEGER NOT NULL,
                timer_address VARCHAR(17),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY(bridge_id) REFERENCES bridges(id),
                FOREIGN KEY(stage_config_id) REFERENCES stage_configs(id)
            )
        """)
        
        # Create bridge_target_assignments table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bridge_target_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bridge_id INTEGER NOT NULL,
                target_number INTEGER NOT NULL,
                sensor_address VARCHAR(17) NOT NULL,
                sensor_label VARCHAR(100),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY(bridge_id) REFERENCES bridges(id),
                UNIQUE(bridge_id, target_number),
                UNIQUE(bridge_id, sensor_address)
            )
        """)
        
        # Create indexes for performance
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_bridge_config_bridge ON bridge_configurations(bridge_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_bridge_config_stage ON bridge_configurations(stage_config_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_bridge_assignments_bridge ON bridge_target_assignments(bridge_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_bridge_assignments_target ON bridge_target_assignments(target_number)")
        
        # Create trigger to update timestamps
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_bridge_config_timestamp
            AFTER UPDATE ON bridge_configurations
            BEGIN
                UPDATE bridge_configurations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        
        self.conn.commit()
        logger.info("Bridge configuration tables created successfully")
        
    def migrate_existing_data(self, backup_data: Dict):
        """Migrate existing assignment data to new tables"""
        logger.info("Migrating existing assignment data...")
        
        # Get the main bridge (assuming single bridge for now)
        bridges = backup_data['bridges']
        if not bridges:
            logger.warning("No bridges found in backup data")
            return
            
        main_bridge = bridges[0]  # Take the first bridge
        bridge_id = main_bridge['id']
        stage_config_id = main_bridge.get('current_stage_id', 1)  # Default to stage 1 if not set
        
        logger.info(f"Migrating data for bridge_id: {bridge_id}, stage_config_id: {stage_config_id}")
        
        # 1. Create bridge configuration record
        timer_address = None
        if backup_data['bridge_device_config']:
            timer_address = backup_data['bridge_device_config'].get('timer')
            
        self.conn.execute("""
            INSERT OR REPLACE INTO bridge_configurations 
            (bridge_id, stage_config_id, timer_address)
            VALUES (?, ?, ?)
        """, (bridge_id, stage_config_id, timer_address))
        
        # 2. Migrate sensor assignments from device_leases
        device_leases = backup_data['device_leases']
        sensor_assignments = []
        
        for lease in device_leases:
            target_assignment = lease.get('target_assignment')
            if target_assignment and target_assignment.startswith('Target '):
                try:
                    target_number = int(target_assignment.split(' ')[1])
                    
                    # Get device info from device_pool
                    cursor = self.conn.execute(
                        "SELECT hw_addr, label FROM device_pool WHERE id = ?",
                        (lease['device_id'],)
                    )
                    device_row = cursor.fetchone()
                    
                    if device_row:
                        sensor_assignments.append({
                            'target_number': target_number,
                            'sensor_address': device_row['hw_addr'],
                            'sensor_label': device_row['label']
                        })
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse target assignment: {target_assignment}, error: {e}")
                    
        # Insert sensor assignments
        for assignment in sensor_assignments:
            self.conn.execute("""
                INSERT OR REPLACE INTO bridge_target_assignments 
                (bridge_id, target_number, sensor_address, sensor_label)
                VALUES (?, ?, ?, ?)
            """, (bridge_id, assignment['target_number'], assignment['sensor_address'], assignment['sensor_label']))
            
        # 3. Alternative: Migrate from JSON config if device_leases is empty
        if not sensor_assignments and backup_data['bridge_device_config']:
            json_config = backup_data['bridge_device_config']
            sensors = json_config.get('sensors', [])
            
            # Assign sensors to targets sequentially (Target 1, Target 2, etc.)
            for i, sensor_address in enumerate(sensors):
                target_number = i + 1
                
                # Get sensor label from device_pool
                cursor = self.conn.execute(
                    "SELECT label FROM device_pool WHERE hw_addr = ?",
                    (sensor_address,)
                )
                device_row = cursor.fetchone()
                sensor_label = device_row['label'] if device_row else f'Sensor {sensor_address[-4:]}'
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO bridge_target_assignments 
                    (bridge_id, target_number, sensor_address, sensor_label)
                    VALUES (?, ?, ?, ?)
                """, (bridge_id, target_number, sensor_address, sensor_label))
                
                logger.info(f"Migrated sensor {sensor_address} to Target {target_number}")
                
        self.conn.commit()
        logger.info("Data migration completed successfully")
        
    def update_json_config(self):
        """Update JSON config from new database tables"""
        logger.info("Updating JSON configuration file...")
        
        # Get current bridge configuration
        cursor = self.conn.execute("""
            SELECT bc.timer_address,
                   GROUP_CONCAT(bta.sensor_address) as sensor_addresses
            FROM bridge_configurations bc
            LEFT JOIN bridge_target_assignments bta ON bc.bridge_id = bta.bridge_id
            WHERE bc.bridge_id = 1
            GROUP BY bc.id
        """)
        
        result = cursor.fetchone()
        
        if result:
            timer_address = result['timer_address']
            sensor_addresses = result['sensor_addresses'].split(',') if result['sensor_addresses'] else []
            
            # Remove any None or empty values
            sensor_addresses = [addr for addr in sensor_addresses if addr]
            
            json_config = {
                "timer": timer_address,
                "sensors": sensor_addresses
            }
            
            # Write to JSON file
            with open(self.json_config_path, 'w') as f:
                json.dump(json_config, f, indent=2)
                
            logger.info(f"Updated JSON config: {json_config}")
        else:
            logger.warning("No bridge configuration found to update JSON")
            
    def verify_migration(self):
        """Verify that migration completed successfully"""
        logger.info("Verifying migration results...")
        
        # Check bridge_configurations
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM bridge_configurations")
        config_count = cursor.fetchone()['count']
        logger.info(f"Bridge configurations created: {config_count}")
        
        # Check bridge_target_assignments
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM bridge_target_assignments")
        assignment_count = cursor.fetchone()['count']
        logger.info(f"Target assignments created: {assignment_count}")
        
        # Show current configuration
        cursor = self.conn.execute("""
            SELECT bc.bridge_id, bc.stage_config_id, bc.timer_address,
                   bta.target_number, bta.sensor_address, bta.sensor_label
            FROM bridge_configurations bc
            LEFT JOIN bridge_target_assignments bta ON bc.bridge_id = bta.bridge_id
            ORDER BY bta.target_number
        """)
        
        logger.info("Current bridge configuration:")
        for row in cursor.fetchall():
            logger.info(f"  Bridge {row['bridge_id']}, Stage {row['stage_config_id']}, "
                       f"Timer: {row['timer_address']}, "
                       f"Target {row['target_number']}: {row['sensor_address']} ({row['sensor_label']})")
                       
        # Verify JSON config
        if Path(self.json_config_path).exists():
            with open(self.json_config_path, 'r') as f:
                json_config = json.load(f)
            logger.info(f"JSON config updated: {json_config}")
        else:
            logger.warning("JSON config file not found")
            
        logger.info("Migration verification completed")
        
    def run_migration(self):
        """Run the complete migration process"""
        try:
            logger.info("Starting bridge configuration migration...")
            
            self.connect()
            
            # Step 1: Backup existing data
            backup_data = self.backup_existing_data()
            
            # Step 2: Create new tables
            self.create_bridge_config_tables()
            
            # Step 3: Migrate existing data
            self.migrate_existing_data(backup_data)
            
            # Step 4: Update JSON config
            self.update_json_config()
            
            # Step 5: Verify migration
            self.verify_migration()
            
            logger.info("Migration completed successfully! 🎉")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.disconnect()

def main():
    """Main migration entry point"""
    import sys
    
    # Default paths - can be overridden via command line
    db_path = "db/leadville.db"
    json_config_path = "bridge_device_config.json"
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    if len(sys.argv) > 2:
        json_config_path = sys.argv[2]
        
    # Run migration
    migration = BridgeConfigMigration(db_path, json_config_path)
    migration.run_migration()

if __name__ == "__main__":
    main()