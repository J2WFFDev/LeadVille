"""CRUD operations for LeadVille Impact Bridge database."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

from .models import (
    Node, Sensor, Target, Stage, Match, TimerEvent, SensorEvent, 
    Run, Shooter, Note
)


# Node CRUD operations
class NodeCRUD:
    """CRUD operations for Node model."""
    
    @staticmethod
    def create(session: Session, name: str, mode: str, **kwargs) -> Node:
        """Create a new node."""
        node = Node(name=name, mode=mode, **kwargs)
        session.add(node)
        session.flush()
        return node
    
    @staticmethod
    def get_by_id(session: Session, node_id: int) -> Optional[Node]:
        """Get node by ID."""
        return session.query(Node).filter(Node.id == node_id).first()
    
    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[Node]:
        """Get node by name."""
        return session.query(Node).filter(Node.name == name).first()
    
    @staticmethod
    def list_nodes(session: Session, mode: Optional[str] = None) -> List[Node]:
        """List all nodes, optionally filtered by mode."""
        query = session.query(Node)
        if mode:
            query = query.filter(Node.mode == mode)
        return query.order_by(Node.name).all()
    
    @staticmethod
    def update(session: Session, node_id: int, **kwargs) -> Optional[Node]:
        """Update node by ID."""
        node = session.query(Node).filter(Node.id == node_id).first()
        if node:
            for key, value in kwargs.items():
                setattr(node, key, value)
            node.updated_at = datetime.utcnow()
            session.flush()
        return node
    
    @staticmethod
    def delete(session: Session, node_id: int) -> bool:
        """Delete node by ID."""
        node = session.query(Node).filter(Node.id == node_id).first()
        if node:
            session.delete(node)
            session.flush()
            return True
        return False


# Sensor CRUD operations
class SensorCRUD:
    """CRUD operations for Sensor model."""
    
    @staticmethod
    def create(session: Session, hw_addr: str, label: str, **kwargs) -> Sensor:
        """Create a new sensor."""
        sensor = Sensor(hw_addr=hw_addr, label=label, **kwargs)
        session.add(sensor)
        session.flush()
        return sensor
    
    @staticmethod
    def get_by_id(session: Session, sensor_id: int) -> Optional[Sensor]:
        """Get sensor by ID."""
        return session.query(Sensor).filter(Sensor.id == sensor_id).first()
    
    @staticmethod
    def get_by_hw_addr(session: Session, hw_addr: str) -> Optional[Sensor]:
        """Get sensor by hardware address."""
        return session.query(Sensor).filter(Sensor.hw_addr == hw_addr).first()
    
    @staticmethod
    def list_sensors(session: Session, target_id: Optional[int] = None) -> List[Sensor]:
        """List all sensors, optionally filtered by target."""
        query = session.query(Sensor)
        if target_id:
            query = query.filter(Sensor.target_id == target_id)
        return query.order_by(Sensor.label).all()
    
    @staticmethod
    def update_status(session: Session, sensor_id: int, battery: float = None, 
                     rssi: int = None, last_seen: datetime = None) -> Optional[Sensor]:
        """Update sensor status information."""
        sensor = session.query(Sensor).filter(Sensor.id == sensor_id).first()
        if sensor:
            if battery is not None:
                sensor.battery = battery
            if rssi is not None:
                sensor.rssi = rssi
            if last_seen is not None:
                sensor.last_seen = last_seen
            sensor.updated_at = datetime.utcnow()
            session.flush()
        return sensor
    
    @staticmethod
    def update(session: Session, sensor_id: int, **kwargs) -> Optional[Sensor]:
        """Update sensor by ID."""
        sensor = session.query(Sensor).filter(Sensor.id == sensor_id).first()
        if sensor:
            for key, value in kwargs.items():
                setattr(sensor, key, value)
            sensor.updated_at = datetime.utcnow()
            session.flush()
        return sensor


# Match CRUD operations
class MatchCRUD:
    """CRUD operations for Match model."""
    
    @staticmethod
    def create(session: Session, name: str, date: datetime, location: str = None, 
               metadata_json: Dict = None) -> Match:
        """Create a new match."""
        match = Match(
            name=name, 
            date=date, 
            location=location,
            metadata_json=metadata_json or {}
        )
        session.add(match)
        session.flush()
        return match
    
    @staticmethod
    def get_by_id(session: Session, match_id: int) -> Optional[Match]:
        """Get match by ID."""
        return session.query(Match).filter(Match.id == match_id).first()
    
    @staticmethod
    def list_matches(session: Session, limit: int = None) -> List[Match]:
        """List all matches, ordered by date descending."""
        query = session.query(Match).order_by(desc(Match.date))
        if limit:
            query = query.limit(limit)
        return query.all()


# Stage CRUD operations  
class StageCRUD:
    """CRUD operations for Stage model."""
    
    @staticmethod
    def create(session: Session, match_id: int, name: str, number: int,
               layout_json: Dict = None) -> Stage:
        """Create a new stage."""
        stage = Stage(
            match_id=match_id,
            name=name,
            number=number,
            layout_json=layout_json or {}
        )
        session.add(stage)
        session.flush()
        return stage
    
    @staticmethod
    def get_by_id(session: Session, stage_id: int) -> Optional[Stage]:
        """Get stage by ID."""
        return session.query(Stage).filter(Stage.id == stage_id).first()
    
    @staticmethod
    def list_by_match(session: Session, match_id: int) -> List[Stage]:
        """List all stages for a match."""
        return (session.query(Stage)
                .filter(Stage.match_id == match_id)
                .order_by(Stage.number)
                .all())


# Run CRUD operations
class RunCRUD:
    """CRUD operations for Run model."""
    
    @staticmethod
    def create(session: Session, match_id: int, stage_id: int, shooter_id: int,
               status: str = "pending") -> Run:
        """Create a new run."""
        run = Run(
            match_id=match_id,
            stage_id=stage_id,
            shooter_id=shooter_id,
            status=status
        )
        session.add(run)
        session.flush()
        return run
    
    @staticmethod
    def get_by_id(session: Session, run_id: int) -> Optional[Run]:
        """Get run by ID."""
        return session.query(Run).filter(Run.id == run_id).first()
    
    @staticmethod
    def start_run(session: Session, run_id: int) -> Optional[Run]:
        """Start a run by setting started_ts and status."""
        run = session.query(Run).filter(Run.id == run_id).first()
        if run:
            run.started_ts = datetime.utcnow()
            run.status = "active"
            session.flush()
        return run
    
    @staticmethod
    def finish_run(session: Session, run_id: int, status: str = "completed") -> Optional[Run]:
        """Finish a run by setting ended_ts and final status."""
        run = session.query(Run).filter(Run.id == run_id).first()
        if run:
            run.ended_ts = datetime.utcnow()
            run.status = status
            session.flush()
        return run
    
    @staticmethod
    def list_by_match(session: Session, match_id: int) -> List[Run]:
        """List all runs for a match."""
        return (session.query(Run)
                .filter(Run.match_id == match_id)
                .order_by(Run.created_at)
                .all())


# TimerEvent CRUD operations
class TimerEventCRUD:
    """CRUD operations for TimerEvent model."""
    
    @staticmethod
    def create(session: Session, ts_utc: datetime, event_type: str, 
               raw: str = None, run_id: int = None) -> TimerEvent:
        """Create a new timer event."""
        event = TimerEvent(
            ts_utc=ts_utc,
            type=event_type,
            raw=raw,
            run_id=run_id
        )
        session.add(event)
        session.flush()
        return event
    
    @staticmethod
    def list_by_run(session: Session, run_id: int) -> List[TimerEvent]:
        """List all timer events for a run."""
        return (session.query(TimerEvent)
                .filter(TimerEvent.run_id == run_id)
                .order_by(TimerEvent.ts_utc)
                .all())
    
    @staticmethod
    def list_recent(session: Session, limit: int = 100) -> List[TimerEvent]:
        """List recent timer events."""
        return (session.query(TimerEvent)
                .order_by(desc(TimerEvent.ts_utc))
                .limit(limit)
                .all())


# SensorEvent CRUD operations
class SensorEventCRUD:
    """CRUD operations for SensorEvent model."""
    
    @staticmethod
    def create(session: Session, ts_utc: datetime, sensor_id: int, 
               magnitude: float, features_json: Dict = None, run_id: int = None) -> SensorEvent:
        """Create a new sensor event."""
        event = SensorEvent(
            ts_utc=ts_utc,
            sensor_id=sensor_id,
            magnitude=magnitude,
            features_json=features_json or {},
            run_id=run_id
        )
        session.add(event)
        session.flush()
        return event
    
    @staticmethod
    def list_by_run(session: Session, run_id: int) -> List[SensorEvent]:
        """List all sensor events for a run."""
        return (session.query(SensorEvent)
                .filter(SensorEvent.run_id == run_id)
                .order_by(SensorEvent.ts_utc)
                .all())
    
    @staticmethod
    def list_by_sensor(session: Session, sensor_id: int, limit: int = None) -> List[SensorEvent]:
        """List sensor events by sensor ID."""
        query = (session.query(SensorEvent)
                .filter(SensorEvent.sensor_id == sensor_id)
                .order_by(desc(SensorEvent.ts_utc)))
        if limit:
            query = query.limit(limit)
        return query.all()


# Note CRUD operations
class NoteCRUD:
    """CRUD operations for Note model."""
    
    @staticmethod
    def create(session: Session, run_id: int, author_role: str, content: str,
               shooter_id: int = None) -> Note:
        """Create a new note."""
        note = Note(
            run_id=run_id,
            author_role=author_role,
            content=content,
            shooter_id=shooter_id
        )
        session.add(note)
        session.flush()
        return note
    
    @staticmethod
    def list_by_run(session: Session, run_id: int) -> List[Note]:
        """List all notes for a run."""
        return (session.query(Note)
                .filter(Note.run_id == run_id)
                .order_by(Note.ts_utc)
                .all())


# Shooter CRUD operations
class ShooterCRUD:
    """CRUD operations for Shooter model."""
    
    @staticmethod
    def create(session: Session, name: str, squad: str = None, 
               metadata_json: Dict = None) -> Shooter:
        """Create a new shooter."""
        shooter = Shooter(
            name=name,
            squad=squad,
            metadata_json=metadata_json or {}
        )
        session.add(shooter)
        session.flush()
        return shooter
    
    @staticmethod
    def get_by_id(session: Session, shooter_id: int) -> Optional[Shooter]:
        """Get shooter by ID."""
        return session.query(Shooter).filter(Shooter.id == shooter_id).first()
    
    @staticmethod
    def list_shooters(session: Session, squad: str = None) -> List[Shooter]:
        """List all shooters, optionally filtered by squad."""
        query = session.query(Shooter)
        if squad:
            query = query.filter(Shooter.squad == squad)
        return query.order_by(Shooter.name).all()


# Target CRUD operations
class TargetCRUD:
    """CRUD operations for Target model."""
    
    @staticmethod
    def create(session: Session, stage_id: int, name: str, 
               geometry: Dict = None, notes: str = None) -> Target:
        """Create a new target."""
        target = Target(
            stage_id=stage_id,
            name=name,
            geometry=geometry or {},
            notes=notes
        )
        session.add(target)
        session.flush()
        return target
    
    @staticmethod
    def get_by_id(session: Session, target_id: int) -> Optional[Target]:
        """Get target by ID."""
        return session.query(Target).filter(Target.id == target_id).first()
    
    @staticmethod
    def list_by_stage(session: Session, stage_id: int) -> List[Target]:
        """List all targets for a stage."""
        return (session.query(Target)
                .filter(Target.stage_id == stage_id)
                .order_by(Target.name)
                .all())


# Convenience class that aggregates all CRUD operations
class DatabaseCRUD:
    """Main CRUD interface for database operations."""
    
    nodes = NodeCRUD
    sensors = SensorCRUD
    targets = TargetCRUD
    matches = MatchCRUD
    stages = StageCRUD
    runs = RunCRUD
    shooters = ShooterCRUD
    timer_events = TimerEventCRUD
    sensor_events = SensorEventCRUD
    notes = NoteCRUD