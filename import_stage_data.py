#!/usr/bin/env python3
"""
Import stage configuration data into LeadVille database
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.impact_bridge.database.models import Base, League, StageConfig, TargetConfig

# Stage data from user input
STAGE_DATA = [
    # League, Stage, Target, Shape, Type, Category, Distance, Offset, Height
    ("SASP", "Exclamation", 1, "12\" Circle", "Plate", "Primary", 30, -12, 5),
    ("SASP", "Exclamation", 2, "12\" Circle", "Plate", "Primary", 36, -8, 4),
    ("SASP", "Exclamation", 3, "10\" Circle", "Plate", "Primary", 42, -4, 3),
    ("SASP", "Exclamation", 4, "10\" Circle", "Plate", "Primary", 48, 0, 3),
    ("SASP", "Exclamation", 5, "18\"x24\" Rectangle", "Gong", "Stop", 30, 12, 5),
    ("SASP", "V", 1, "12\" Circle", "Plate", "Primary", 54, -6, 3),
    ("SASP", "V", 2, "10\" Circle", "Plate", "Primary", 36, -2.5, 4),
    ("SASP", "V", 3, "12\" Circle", "Plate", "Stop", 24, 0, 5),
    ("SASP", "V", 4, "10\" Circle", "Plate", "Primary", 36, 2.5, 4),
    ("SASP", "V", 5, "12\" Circle", "Plate", "Primary", 54, 6, 3),
    ("SASP", "Go Fast", 1, "18\"x24\" Rectangle", "Gong", "Primary", 30, -8, 5.5),
    ("SASP", "Go Fast", 2, "18\"x24\" Rectangle", "Gong", "Primary", 30, -4, 5.5),
    ("SASP", "Go Fast", 3, "12\" Circle", "Plate", "Stop", 24, 0, 5),
    ("SASP", "Go Fast", 4, "18\"x24\" Rectangle", "Gong", "Primary", 30, 4, 5.5),
    ("SASP", "Go Fast", 5, "18\"x24\" Rectangle", "Gong", "Primary", 30, 8, 5.5),
    ("SASP", "Focus", 1, "12\" Circle", "Plate", "Primary", 24, -16, 5),
    ("SASP", "Focus", 2, "12\" Circle", "Plate", "Primary", 30, -8, 5),
    ("SASP", "Focus", 3, "12\" Circle", "Plate", "Primary", 36, 0, 5),
    ("SASP", "Focus", 4, "12\" Circle", "Plate", "Primary", 42, 8, 5),
    ("SASP", "Focus", 5, "12\" Circle", "Plate", "Stop", 48, 16, 5),
    ("SASP", "In & Out", 1, "12\" Circle", "Plate", "Primary", 54, -6, 5),
    ("SASP", "In & Out", 2, "10\" Circle", "Plate", "Primary", 24, -6, 5),
    ("SASP", "In & Out", 3, "12\" Circle", "Plate", "Stop", 36, 0, 5),
    ("SASP", "In & Out", 4, "10\" Circle", "Plate", "Primary", 24, 6, 5),
    ("SASP", "In & Out", 5, "12\" Circle", "Plate", "Primary", 54, 6, 5),
    ("SASP", "Speedtrap", 1, "12\" Circle", "Plate", "Primary", 30, -14, 5),
    ("SASP", "Speedtrap", 2, "10\" Circle", "Plate", "Primary", 36, -7, 5),
    ("SASP", "Speedtrap", 3, "18\"x24\" Rectangle", "Gong", "Primary", 75, 0, 5.5),
    ("SASP", "Speedtrap", 4, "10\" Circle", "Plate", "Primary", 36, 7, 5),
    ("SASP", "Speedtrap", 5, "12\" Circle", "Plate", "Stop", 30, 14, 5),
    ("SASP", "M", 1, "12\" Circle", "Plate", "Stop", 43, -6, 3),
    ("SASP", "M", 2, "12\" Circle", "Plate", "Primary", 47, -3, 5),
    ("SASP", "M", 3, "12\" Circle", "Plate", "Primary", 45, 0, 4),
    ("SASP", "M", 4, "12\" Circle", "Plate", "Primary", 47, 3, 5),
    ("SASP", "M", 5, "12\" Circle", "Plate", "Primary", 43, 6, 3),
    ("SASP", "Popquiz", 1, "10\" Circle", "Plate", "Primary", 25, -8, 5),
    ("SASP", "Popquiz", 2, "12\" Circle", "Plate", "Primary", 45, -1.5, 5),
    ("SASP", "Popquiz", 3, "18\"x24\" Rectangle", "Gong", "Penalty", 40, 0, 5),
    ("SASP", "Popquiz", 4, "12\" Circle", "Plate", "Stop", 35, 0, 5),
    ("SASP", "Popquiz", 5, "12\" Circle", "Plate", "Primary", 45, 1.5, 5),
    ("SASP", "Popquiz", 6, "10\" Circle", "Plate", "Primary", 25, 8, 5),
    ("Steel Challenge", "5 to Go", 1, "12\" Circle", "Plate", "Primary", 21, -10, 5),
    ("Steel Challenge", "5 to Go", 2, "12\" Circle", "Plate", "Primary", 27, -5, 5),
    ("Steel Challenge", "5 to Go", 3, "12\" Circle", "Plate", "Primary", 33, 5, 5),
    ("Steel Challenge", "5 to Go", 4, "12\" Circle", "Plate", "Primary", 39, 10, 5),
    ("Steel Challenge", "5 to Go", 5, "12\" Circle", "Plate", "Stop", 30, 0, 5),
    ("Steel Challenge", "Showdown", 1, "12\" Circle", "Plate", "Primary", 21, -7, 5),
    ("Steel Challenge", "Showdown", 2, "12\" Circle", "Plate", "Primary", 21, 7, 5),
    ("Steel Challenge", "Showdown", 3, "12\" Circle", "Plate", "Primary", 30, -7, 5),
    ("Steel Challenge", "Showdown", 4, "12\" Circle", "Plate", "Primary", 30, 7, 5),
    ("Steel Challenge", "Showdown", 5, "12\" Circle", "Plate", "Stop", 25, 0, 5),
    ("Steel Challenge", "Smoke & Hope", 1, "18\"x24\" Rect", "Gong", "Primary", 21, -12, 5),
    ("Steel Challenge", "Smoke & Hope", 2, "18\"x24\" Rect", "Gong", "Primary", 21, -6, 5),
    ("Steel Challenge", "Smoke & Hope", 3, "18\"x24\" Rect", "Gong", "Primary", 21, 6, 5),
    ("Steel Challenge", "Smoke & Hope", 4, "18\"x24\" Rect", "Gong", "Primary", 21, 12, 5),
    ("Steel Challenge", "Smoke & Hope", 5, "12\" Circle", "Plate", "Stop", 21, 0, 5),
    ("Steel Challenge", "Outer Limits", 1, "12\" Circle", "Plate", "Primary", 35, -12, 5),
    ("Steel Challenge", "Outer Limits", 2, "12\" Circle", "Plate", "Primary", 35, 12, 5),
    ("Steel Challenge", "Outer Limits", 3, "12\" Circle", "Plate", "Primary", 35, -6, 5),
    ("Steel Challenge", "Outer Limits", 4, "12\" Circle", "Plate", "Primary", 35, 6, 5),
    ("Steel Challenge", "Outer Limits", 5, "12\" Circle", "Plate", "Stop", 35, 0, 5),
    ("Steel Challenge", "Accelerator", 1, "12\" Circle", "Plate", "Primary", 20, -8, 5),
    ("Steel Challenge", "Accelerator", 2, "18\"x24\" Rect", "Gong", "Primary", 30, -4, 5),
    ("Steel Challenge", "Accelerator", 3, "18\"x24\" Rect", "Gong", "Primary", 30, 4, 5),
    ("Steel Challenge", "Accelerator", 4, "12\" Circle", "Plate", "Primary", 20, 8, 5),
    ("Steel Challenge", "Accelerator", 5, "12\" Circle", "Plate", "Stop", 25, 0, 5),
    ("Steel Challenge", "Pendulum", 1, "12\" Circle", "Plate", "Primary", 35, -10, 5),
    ("Steel Challenge", "Pendulum", 2, "12\" Circle", "Plate", "Primary", 40, -5, 5),
    ("Steel Challenge", "Pendulum", 3, "12\" Circle", "Plate", "Primary", 40, 5, 5),
    ("Steel Challenge", "Pendulum", 4, "12\" Circle", "Plate", "Primary", 35, 10, 5),
    ("Steel Challenge", "Pendulum", 5, "12\" Circle", "Plate", "Stop", 30, 0, 5),
    ("Steel Challenge", "Speed Option", 1, "12\" Circle", "Plate", "Primary", 20, -10, 5),
    ("Steel Challenge", "Speed Option", 2, "18\"x24\" Rect", "Gong", "Primary", 30, -5, 5),
    ("Steel Challenge", "Speed Option", 3, "18\"x24\" Rect", "Gong", "Primary", 30, 5, 5),
    ("Steel Challenge", "Speed Option", 4, "12\" Circle", "Plate", "Primary", 20, 10, 5),
    ("Steel Challenge", "Speed Option", 5, "12\" Circle", "Plate", "Stop", 25, 0, 5),
    ("Steel Challenge", "Roundabout", 1, "12\" Circle", "Plate", "Primary", 20, -8, 5),
    ("Steel Challenge", "Roundabout", 2, "12\" Circle", "Plate", "Primary", 25, -4, 5),
    ("Steel Challenge", "Roundabout", 3, "12\" Circle", "Plate", "Primary", 25, 4, 5),
    ("Steel Challenge", "Roundabout", 4, "12\" Circle", "Plate", "Primary", 20, 8, 5),
    ("Steel Challenge", "Roundabout", 5, "12\" Circle", "Plate", "Stop", 23, 0, 5),
]


def main():
    """Import stage configuration data"""
    print("🎯 Importing LeadVille stage configuration data...")
    
    # Create database connection
    db_path = Path(__file__).parent / "leadville.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create leagues
        leagues = {}
        for league_name in ["SASP", "Steel Challenge"]:
            league = session.query(League).filter_by(name=league_name).first()
            if not league:
                abbreviation = "SC" if league_name == "Steel Challenge" else league_name
                league = League(
                    name=league_name,
                    abbreviation=abbreviation,
                    description=f"{league_name} competition stages"
                )
                session.add(league)
                session.flush()  # Get the ID
                print(f"✅ Created league: {league_name}")
            leagues[league_name] = league
        
        # Group data by league and stage
        stages = {}
        for row in STAGE_DATA:
            league_name, stage_name, target_num, shape, type_, category, distance, offset, height = row
            
            stage_key = (league_name, stage_name)
            if stage_key not in stages:
                stages[stage_key] = []
            
            stages[stage_key].append({
                'target_number': target_num,
                'shape': shape,
                'type': type_,
                'category': category,
                'distance_feet': distance,
                'offset_feet': float(offset),
                'height_feet': float(height)
            })
        
        # Create stage configs and targets
        for (league_name, stage_name), targets in stages.items():
            league = leagues[league_name]
            
            # Check if stage config already exists
            stage_config = session.query(StageConfig).filter_by(
                league_id=league.id,
                name=stage_name
            ).first()
            
            if not stage_config:
                stage_config = StageConfig(
                    league_id=league.id,
                    name=stage_name,
                    description=f"{league_name} {stage_name} stage configuration"
                )
                session.add(stage_config)
                session.flush()  # Get the ID
                print(f"✅ Created stage config: {league_name} - {stage_name}")
                
                # Add targets
                for target_data in targets:
                    target_config = TargetConfig(
                        stage_config_id=stage_config.id,
                        **target_data
                    )
                    session.add(target_config)
                
                print(f"   Added {len(targets)} targets")
            else:
                print(f"⚠️  Stage config already exists: {league_name} - {stage_name}")
        
        # Commit all changes
        session.commit()
        print(f"🎉 Successfully imported {len(stages)} stage configurations!")
        
        # Print summary
        total_leagues = session.query(League).count()
        total_stages = session.query(StageConfig).count()
        total_targets = session.query(TargetConfig).count()
        
        print(f"\n📊 Database Summary:")
        print(f"   Leagues: {total_leagues}")
        print(f"   Stage Configs: {total_stages}")
        print(f"   Target Configs: {total_targets}")
        
    except Exception as e:
        print(f"❌ Error importing data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()