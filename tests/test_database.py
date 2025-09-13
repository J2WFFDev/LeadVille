"""Tests for database functionality."""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from src.impact_bridge.config import DatabaseConfig
from src.impact_bridge.database import (
    initialize_database,
    get_database_session,
    get_database_info,
    DatabaseCRUD,
    Node, Sensor, Match, Stage, Run, Shooter, TimerEvent, SensorEvent
)


@pytest.fixture
def temp_db_config():
    """Create a temporary database configuration for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = DatabaseConfig(
            dir=temp_dir,
            file="test.db",
            enable_ingest=True,
            echo_sql=False
        )
        yield config


@pytest.fixture
def initialized_db(temp_db_config):
    """Initialize database with test configuration."""
    initialize_database(temp_db_config)
    yield temp_db_config


def test_database_initialization(temp_db_config):
    """Test database initialization creates tables."""
    # Initialize database
    initialize_database(temp_db_config)
    
    # Check that database file was created
    db_path = Path(temp_db_config.dir) / temp_db_config.file
    assert db_path.exists()
    
    # Get database info
    info = get_database_info(temp_db_config)
    assert "sqlite_version" in info
    assert "tables" in info
    assert len(info["tables"]) > 0


def test_node_crud(initialized_db):
    """Test Node CRUD operations."""
    config = initialized_db
    
    with get_database_session(config) as session:
        # Create node
        node = DatabaseCRUD.nodes.create(
            session, 
            name="test-pi-1",
            mode="simulation",
            ssid="leadville-test",
            ip_addr="192.168.1.100"
        )
        assert node.id is not None
        assert node.name == "test-pi-1"
        assert node.mode == "simulation"
        
        # Get by ID
        retrieved = DatabaseCRUD.nodes.get_by_id(session, node.id)
        assert retrieved.name == "test-pi-1"
        
        # Get by name
        by_name = DatabaseCRUD.nodes.get_by_name(session, "test-pi-1")
        assert by_name.id == node.id
        
        # List nodes
        nodes = DatabaseCRUD.nodes.list_nodes(session)
        assert len(nodes) == 1
        
        # Update node
        updated = DatabaseCRUD.nodes.update(
            session, node.id, 
            mode="online", 
            ip_addr="192.168.1.101"
        )
        assert updated.mode == "online"
        assert updated.ip_addr == "192.168.1.101"


def test_sensor_crud(temp_db_config):
    """Test Sensor CRUD operations."""
    initialize_database(temp_db_config)
    
    with get_database_session(temp_db_config) as session:
        # Create a node first
        node = DatabaseCRUD.nodes.create(
            session, 
            name="test-pi-sensor",  # Use unique name
            mode="simulation"
        )
        
        # Create sensor
        sensor = DatabaseCRUD.sensors.create(
            session,
            hw_addr="F8:FE:92:31:12:E3",
            label="BT50-001",
            node_id=node.id,
            battery=85.5,
            rssi=-45
        )
        
        assert sensor.id is not None
        assert sensor.hw_addr == "F8:FE:92:31:12:E3"
        assert sensor.label == "BT50-001"
        assert sensor.battery == 85.5
        
        # Get by hardware address
        by_hw = DatabaseCRUD.sensors.get_by_hw_addr(session, "F8:FE:92:31:12:E3")
        assert by_hw.id == sensor.id
        
        # Update sensor status
        DatabaseCRUD.sensors.update_status(
            session, 
            sensor.id,
            battery=82.3,
            rssi=-50,
            last_seen=datetime.utcnow()
        )
        
        updated = DatabaseCRUD.sensors.get_by_id(session, sensor.id)
        assert updated.battery == 82.3
        assert updated.rssi == -50
        assert updated.last_seen is not None


def test_match_stage_crud(initialized_db):
    """Test Match and Stage CRUD operations."""
    config = initialized_db
    
    with get_database_session(config) as session:
        # Create match
        match_date = datetime(2024, 1, 15, 9, 0, 0)
        match = DatabaseCRUD.matches.create(
            session,
            name="Test Match 2024",
            date=match_date,
            location="Test Range",
            metadata_json={"type": "practice", "rounds": 6}
        )
        
        assert match.id is not None
        assert match.name == "Test Match 2024"
        
        # Create stages for the match
        stage1 = DatabaseCRUD.stages.create(
            session,
            match_id=match.id,
            name="Stage 1 - El Presidente",
            number=1,
            layout_json={"targets": 3, "distance": "7 yards"}
        )
        
        stage2 = DatabaseCRUD.stages.create(
            session,
            match_id=match.id,
            name="Stage 2 - Bill Drill",
            number=2,
            layout_json={"targets": 1, "distance": "25 yards"}
        )
        
        # List stages by match
        stages = DatabaseCRUD.stages.list_by_match(session, match.id)
        assert len(stages) == 2
        assert stages[0].number == 1  # Should be ordered by number
        assert stages[1].number == 2


def test_run_lifecycle(temp_db_config):
    """Test Run lifecycle operations."""
    initialize_database(temp_db_config)
    
    with get_database_session(temp_db_config) as session:
        # Create required entities
        match = DatabaseCRUD.matches.create(
            session,
            name="Test Match",
            date=datetime.utcnow()
        )
        
        stage = DatabaseCRUD.stages.create(
            session,
            match_id=match.id,
            name="Test Stage",
            number=1
        )
        
        shooter = DatabaseCRUD.shooters.create(
            session,
            name="John Doe",
            squad="Alpha",
            metadata_json={"division": "Production", "class": "A"}
        )
        
        # Create run
        run = DatabaseCRUD.runs.create(
            session,
            match_id=match.id,
            stage_id=stage.id,
            shooter_id=shooter.id
        )
        
        assert run.status == "pending"
        assert run.started_ts is None
        
        # Start run
        DatabaseCRUD.runs.start_run(session, run.id)
        updated_run = DatabaseCRUD.runs.get_by_id(session, run.id)
        assert updated_run.status == "active"
        assert updated_run.started_ts is not None
        
        # Finish run
        DatabaseCRUD.runs.finish_run(session, run.id, "completed")
        finished_run = DatabaseCRUD.runs.get_by_id(session, run.id)
        assert finished_run.status == "completed"
        assert finished_run.ended_ts is not None
        assert finished_run.ended_ts >= finished_run.started_ts


def test_timer_and_sensor_events(temp_db_config):
    """Test TimerEvent and SensorEvent operations."""
    initialize_database(temp_db_config)
    
    with get_database_session(temp_db_config) as session:
        # Create required entities
        node = DatabaseCRUD.nodes.create(session, name="test-pi-events", mode="simulation")
        sensor = DatabaseCRUD.sensors.create(
            session, 
            hw_addr="F8:FE:92:31:12:E4",  # Use different MAC
            label="BT50-002",
            node_id=node.id
        )
        
        match = DatabaseCRUD.matches.create(
            session, name="Test Match Events", date=datetime.utcnow()
        )
        stage = DatabaseCRUD.stages.create(
            session, match_id=match.id, name="Test Stage Events", number=1
        )
        shooter = DatabaseCRUD.shooters.create(
            session, name="Test Shooter Events", squad="Test"
        )
        run = DatabaseCRUD.runs.create(
            session, match_id=match.id, stage_id=stage.id, shooter_id=shooter.id
        )
        
        # Create timer events
        start_time = datetime.utcnow()
        timer_start = DatabaseCRUD.timer_events.create(
            session,
            ts_utc=start_time,
            event_type="START",
            raw="START_EVENT_DATA",
            run_id=run.id
        )
        
        # Create sensor event
        sensor_event = DatabaseCRUD.sensor_events.create(
            session,
            ts_utc=start_time,
            sensor_id=sensor.id,
            magnitude=15.7,
            features_json={"peak": 15.7, "duration_ms": 45},
            run_id=run.id
        )
        
        # List events by run
        timer_events = DatabaseCRUD.timer_events.list_by_run(session, run.id)
        sensor_events = DatabaseCRUD.sensor_events.list_by_run(session, run.id)
        
        assert len(timer_events) == 1
        assert len(sensor_events) == 1
        assert timer_events[0].type == "START"
        assert sensor_events[0].magnitude == 15.7


def test_database_constraints(temp_db_config):
    """Test database constraints are enforced."""
    initialize_database(temp_db_config)
    
    with get_database_session(temp_db_config) as session:
        # Test unique constraint on node name
        DatabaseCRUD.nodes.create(session, name="duplicate-node", mode="online")
        session.commit()  # Commit first node
        
    # Create a new session for the constraint test
    try:
        with get_database_session(temp_db_config) as session:
            DatabaseCRUD.nodes.create(session, name="duplicate-node", mode="offline")
            session.commit()  # This should raise an exception
        assert False, "Should have raised constraint violation"
    except Exception as e:
        # Expected - unique constraint violation
        assert "UNIQUE constraint failed" in str(e)


if __name__ == "__main__":
    # Basic test runner for manual testing
    import sys
    sys.path.append("..")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = DatabaseConfig(dir=temp_dir, file="manual_test.db")
        initialize_database(config)
        
        print("Database initialized successfully")
        print(f"Database info: {get_database_info(config)}")
        
        # Test basic operations
        with get_database_session(config) as session:
            node = DatabaseCRUD.nodes.create(
                session, name="manual-test-pi", mode="simulation"
            )
            print(f"Created node: {node.id} - {node.name}")
        
        print("Manual test completed successfully")