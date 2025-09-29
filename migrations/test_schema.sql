-- Bridge Configuration Migration SQL
-- Test SQL syntax for creating the new bridge config tables

BEGIN TRANSACTION;

-- Create bridge_configurations table
CREATE TABLE IF NOT EXISTS bridge_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bridge_id INTEGER NOT NULL UNIQUE,
    stage_config_id INTEGER NOT NULL,
    timer_address VARCHAR(17),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY(bridge_id) REFERENCES bridges(id),
    FOREIGN KEY(stage_config_id) REFERENCES stage_configs(id)
);

-- Create bridge_target_assignments table
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
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bridge_config_bridge ON bridge_configurations(bridge_id);
CREATE INDEX IF NOT EXISTS idx_bridge_config_stage ON bridge_configurations(stage_config_id);
CREATE INDEX IF NOT EXISTS idx_bridge_assignments_bridge ON bridge_target_assignments(bridge_id);
CREATE INDEX IF NOT EXISTS idx_bridge_assignments_target ON bridge_target_assignments(target_number);

-- Create trigger to update timestamps
CREATE TRIGGER IF NOT EXISTS update_bridge_config_timestamp
AFTER UPDATE ON bridge_configurations
BEGIN
    UPDATE bridge_configurations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Test the schema with sample data
INSERT INTO bridge_configurations (bridge_id, stage_config_id, timer_address)
VALUES (1, 1, '60:09:C3:1F:DC:1A');

INSERT INTO bridge_target_assignments (bridge_id, target_number, sensor_address, sensor_label)
VALUES (1, 1, 'EA:18:3D:6D:BA:E5', 'BT50 Target 1');

-- Verify the tables were created
.schema bridge_configurations
.schema bridge_target_assignments

-- Show sample data
SELECT 'Bridge Configurations:' as info;
SELECT * FROM bridge_configurations;

SELECT 'Target Assignments:' as info;
SELECT * FROM bridge_target_assignments;

ROLLBACK; -- Don't commit the test data