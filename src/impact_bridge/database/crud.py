"""
CRUD (Create, Read, Update, Delete) operations for LeadVille Impact Bridge database

Provides high-level database operations for all entities.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from .models import (
    Node, Sensor, Target, Stage, Match, TimerEvent, SensorEvent, 
    Run, Shooter, Note
)


class NodeCRUD:
    """CRUD operations for Node entities"""
    
    @staticmethod
    def create(session: Session, name: str, mode: str = 'online', **kwargs) -> Node:
        """Create a new node"""
        node = Node(name=name, mode=mode, **kwargs)
        session.add(node)
        session.flush()
        return node
    
    @staticmethod
    def get_by_id(session: Session, node_id: int) -> Optional[Node]:
        """Get node by ID"""
        return session.query(Node).filter(Node.id == node_id).first()
    
    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[Node]:
        """Get node by name"""
        return session.query(Node).filter(Node.name == name).first()
    
    @staticmethod
    def list_all(session: Session) -> List[Node]:
        """List all nodes"""
        return session.query(Node).order_by(Node.name).all()
    
    @staticmethod
    def update(session: Session, node_id: int, **kwargs) -> Optional[Node]:
        """Update node"""
        node = session.query(Node).filter(Node.id == node_id).first()
        if node:
            for key, value in kwargs.items():
                if hasattr(node, key):
                    setattr(node, key, value)
            session.flush()
        return node
    
    @staticmethod
    def delete(session: Session, node_id: int) -> bool:
        """Delete node"""
        node = session.query(Node).filter(Node.id == node_id).first()
        if node:
            session.delete(node)
            session.flush()
            return True
        return False


class SensorCRUD:
    """CRUD operations for Sensor entities"""
    
    @staticmethod
    def create(session: Session, hw_addr: str, label: str, **kwargs) -> Sensor:
        """Create a new sensor"""
        sensor = Sensor(hw_addr=hw_addr, label=label, **kwargs)
        session.add(sensor)
        session.flush()
        return sensor
    
    @staticmethod
    def get_by_id(session: Session, sensor_id: int) -> Optional[Sensor]:
        """Get sensor by ID"""
        return session.query(Sensor).filter(Sensor.id == sensor_id).first()
    
    @staticmethod
    def get_by_hw_addr(session: Session, hw_addr: str) -> Optional[Sensor]:
        """Get sensor by hardware address"""
        return session.query(Sensor).filter(Sensor.hw_addr == hw_addr).first()
    
    @staticmethod
    def list_by_target(session: Session, target_id: int) -> List[Sensor]:
        """List sensors assigned to a target"""
        return session.query(Sensor).filter(Sensor.target_id == target_id).all()
    
    @staticmethod
    def list_unassigned(session: Session) -> List[Sensor]:
        """List sensors not assigned to any target"""
        return session.query(Sensor).filter(Sensor.target_id.is_(None)).all()
    
    @staticmethod
    def update_status(session: Session, sensor_id: int, battery: int = None, 
                     rssi: int = None, last_seen: datetime = None) -> Optional[Sensor]:
        """Update sensor status"""
        sensor = session.query(Sensor).filter(Sensor.id == sensor_id).first()
        if sensor:
            if battery is not None:
                sensor.battery = battery
            if rssi is not None:
                sensor.rssi = rssi
            if last_seen is not None:
                sensor.last_seen = last_seen
            session.flush()
        return sensor
    
    @staticmethod
    def assign_to_target(session: Session, sensor_id: int, target_id: int) -> Optional[Sensor]:
        """Assign sensor to target"""
        sensor = session.query(Sensor).filter(Sensor.id == sensor_id).first()
        if sensor:
            sensor.target_id = target_id
            session.flush()
        return sensor


class TimerEventCRUD:
    """CRUD operations for TimerEvent entities"""
    
    @staticmethod
    def create(session: Session, ts_utc: datetime, event_type: str, 
               run_id: int = None, raw: str = None) -> TimerEvent:
        """Create a new timer event"""
        event = TimerEvent(ts_utc=ts_utc, type=event_type, run_id=run_id, raw=raw)
        session.add(event)
        session.flush()
        return event
    
    @staticmethod
    def list_by_run(session: Session, run_id: int) -> List[TimerEvent]:
        """List timer events for a run"""
        return session.query(TimerEvent).filter(
            TimerEvent.run_id == run_id
        ).order_by(TimerEvent.ts_utc).all()
    
    @staticmethod
    def list_recent(session: Session, limit: int = 100) -> List[TimerEvent]:
        """List recent timer events"""
        return session.query(TimerEvent).order_by(
            desc(TimerEvent.ts_utc)
        ).limit(limit).all()


class SensorEventCRUD:
    """CRUD operations for SensorEvent entities"""
    
    @staticmethod
    def create(session: Session, ts_utc: datetime, sensor_id: int, 
               magnitude: float, run_id: int = None, 
               features_json: Dict = None) -> SensorEvent:
        """Create a new sensor event"""
        event = SensorEvent(
            ts_utc=ts_utc, 
            sensor_id=sensor_id, 
            magnitude=magnitude,
            run_id=run_id,
            features_json=features_json
        )
        session.add(event)
        session.flush()
        return event
    
    @staticmethod
    def list_by_run(session: Session, run_id: int) -> List[SensorEvent]:
        """List sensor events for a run"""
        return session.query(SensorEvent).filter(
            SensorEvent.run_id == run_id
        ).order_by(SensorEvent.ts_utc).all()
    
    @staticmethod
    def list_by_sensor(session: Session, sensor_id: int, limit: int = 100) -> List[SensorEvent]:
        """List recent events for a sensor"""
        return session.query(SensorEvent).filter(
            SensorEvent.sensor_id == sensor_id
        ).order_by(desc(SensorEvent.ts_utc)).limit(limit).all()
    
    @staticmethod
    def list_recent(session: Session, limit: int = 100) -> List[SensorEvent]:
        """List recent sensor events"""
        return session.query(SensorEvent).order_by(
            desc(SensorEvent.ts_utc)
        ).limit(limit).all()


class RunCRUD:
    """CRUD operations for Run entities"""
    
    @staticmethod
    def create(session: Session, match_id: int, stage_id: int, 
               shooter_id: int, **kwargs) -> Run:
        """Create a new run"""
        run = Run(match_id=match_id, stage_id=stage_id, shooter_id=shooter_id, **kwargs)
        session.add(run)
        session.flush()
        return run
    
    @staticmethod
    def start_run(session: Session, run_id: int, started_ts: datetime = None) -> Optional[Run]:
        """Start a run"""
        run = session.query(Run).filter(Run.id == run_id).first()
        if run:
            run.status = 'active'
            run.started_ts = started_ts or datetime.utcnow()
            session.flush()
        return run
    
    @staticmethod
    def finish_run(session: Session, run_id: int, ended_ts: datetime = None) -> Optional[Run]:
        """Finish a run"""
        run = session.query(Run).filter(Run.id == run_id).first()
        if run:
            run.status = 'completed'
            run.ended_ts = ended_ts or datetime.utcnow()
            session.flush()
        return run
    
    @staticmethod
    def list_by_match(session: Session, match_id: int) -> List[Run]:
        """List runs for a match"""
        return session.query(Run).filter(Run.match_id == match_id).all()
    
    @staticmethod
    def list_active(session: Session) -> List[Run]:
        """List active runs"""
        return session.query(Run).filter(Run.status == 'active').all()


class DatabaseCRUD:
    """Consolidated CRUD operations"""
    
    nodes = NodeCRUD
    sensors = SensorCRUD
    timer_events = TimerEventCRUD
    sensor_events = SensorEventCRUD
    runs = RunCRUD
    
    @staticmethod
    def get_system_stats(session: Session) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {
            'nodes': session.query(Node).count(),
            'sensors': session.query(Sensor).count(),
            'targets': session.query(Target).count(),
            'matches': session.query(Match).count(),
            'runs': session.query(Run).count(),
            'timer_events': session.query(TimerEvent).count(),
            'sensor_events': session.query(SensorEvent).count(),
            'active_runs': session.query(Run).filter(Run.status == 'active').count(),
        }
        return stats