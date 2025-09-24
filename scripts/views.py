"""
Database views for LeadVille Impact Bridge

Creates unified views that combine timer and sensor data for reporting and analysis.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def create_shot_log_view(engine: Engine) -> None:
    """
    Create shot_log view that combines timer_events and sensor_events for unified reporting.
    
    This view provides a comprehensive shot log that includes:
    - Timer events (START, SHOT, STOP) with timing data
    - Sensor events (impacts) correlated by time
    - Run context and metadata
    - Shot sequence and analysis
    
    The view is designed for web app consumption and BI tool integration.
    """
    
    create_view_sql = text("""
    CREATE VIEW IF NOT EXISTS shot_log AS
    WITH timer_shots AS (
        -- Extract shot events with timing context
        SELECT 
            te.id as timer_event_id,
            te.ts_utc as event_time,
            te.type as event_type,
            te.raw as timer_raw,
            te.run_id,
            te.created_at,
            -- Parse JSON data if available (AMG rich data)
            CASE 
                WHEN te.raw LIKE '%{%' THEN json_extract(te.raw, '$.current_shot')
                ELSE NULL 
            END as shot_number,
            CASE 
                WHEN te.raw LIKE '%{%' THEN json_extract(te.raw, '$.shot_time')
                ELSE NULL 
            END as shot_time,
            CASE 
                WHEN te.raw LIKE '%{%' THEN json_extract(te.raw, '$.string_time') 
                ELSE NULL
            END as string_time,
            -- Determine shot sequence within run
            ROW_NUMBER() OVER (
                PARTITION BY te.run_id, te.type 
                ORDER BY te.ts_utc
            ) as sequence_in_run
        FROM timer_events te
        WHERE te.type IN ('START', 'SHOT', 'STOP')
    ),
    
    correlated_impacts AS (
        -- Find sensor impacts that correlate with timer shots
        SELECT 
            se.id as sensor_event_id,
            se.ts_utc as impact_time,
            se.sensor_id,
            se.magnitude as impact_magnitude,
            se.features_json as impact_features,
            se.run_id,
            ts.timer_event_id,
            ts.event_time as timer_event_time,
            ts.event_type,
            ts.shot_number,
            ts.shot_time,
            ts.string_time,
            ts.sequence_in_run,
            -- Calculate time difference between timer and impact
            (julianday(se.ts_utc) - julianday(ts.event_time)) * 86400.0 as time_diff_seconds,
            -- Rank impacts by proximity to timer events
            ROW_NUMBER() OVER (
                PARTITION BY ts.timer_event_id 
                ORDER BY ABS((julianday(se.ts_utc) - julianday(ts.event_time)) * 86400.0)
            ) as impact_rank
        FROM timer_shots ts
        LEFT JOIN sensor_events se ON (
            se.run_id = ts.run_id 
            AND ABS((julianday(se.ts_utc) - julianday(ts.event_time)) * 86400.0) <= 2.0  -- Within 2 seconds
        )
        WHERE ts.event_type = 'SHOT'  -- Only correlate with shot events
    )
    
    SELECT 
        -- Primary identifiers
        COALESCE(ci.timer_event_id, 'impact_' || ci.sensor_event_id) as log_id,
        ci.run_id,
        ci.sequence_in_run as shot_sequence,
        
        -- Timer data
        ci.timer_event_time,
        ci.event_type,
        ci.shot_number,
        ci.shot_time,
        ci.string_time,
        
        -- Impact data
        ci.impact_time,
        ci.sensor_event_id,
        ci.sensor_id,
        ci.impact_magnitude,
        ci.impact_features,
        
        -- Correlation analysis
        ci.time_diff_seconds,
        CASE 
            WHEN ci.time_diff_seconds IS NULL THEN 'no_impact'
            WHEN ABS(ci.time_diff_seconds) <= 0.5 THEN 'excellent'
            WHEN ABS(ci.time_diff_seconds) <= 1.0 THEN 'good'
            WHEN ABS(ci.time_diff_seconds) <= 2.0 THEN 'fair'
            ELSE 'poor'
        END as correlation_quality,
        
        -- Metadata
        CASE 
            WHEN ci.sensor_event_id IS NOT NULL AND ci.timer_event_id IS NOT NULL THEN 'correlated'
            WHEN ci.timer_event_id IS NOT NULL THEN 'timer_only'
            WHEN ci.sensor_event_id IS NOT NULL THEN 'impact_only'
            ELSE 'unknown'
        END as event_status,
        
        -- Target context (when available)
        s.label as sensor_label,
        tc.target_number,
        tc.category as target_category,
        
        -- Run context
        r.started_ts as run_started,
        r.ended_ts as run_ended,
        r.status as run_status,
        sh.name as shooter_name,
        st.name as stage_name
        
    FROM correlated_impacts ci
    LEFT JOIN sensors s ON ci.sensor_id = s.id
    LEFT JOIN target_configs tc ON s.target_config_id = tc.id
    LEFT JOIN runs r ON ci.run_id = r.id
    LEFT JOIN shooters sh ON r.shooter_id = sh.id
    LEFT JOIN stages st ON r.stage_id = st.id
    
    WHERE ci.impact_rank = 1 OR ci.impact_rank IS NULL  -- Best impact match per timer event
    
    UNION ALL
    
    -- Include timer START/STOP events (no impact correlation needed)
    SELECT 
        'timer_' || te.id as log_id,
        te.run_id,
        CASE te.type 
            WHEN 'START' THEN 0 
            WHEN 'STOP' THEN 999 
            ELSE NULL 
        END as shot_sequence,
        
        -- Timer data
        te.ts_utc as timer_event_time,
        te.type as event_type,
        CASE 
            WHEN te.raw LIKE '%{%' THEN json_extract(te.raw, '$.current_shot')
            ELSE NULL 
        END as shot_number,
        CASE 
            WHEN te.raw LIKE '%{%' THEN json_extract(te.raw, '$.shot_time')
            ELSE NULL 
        END as shot_time,
        CASE 
            WHEN te.raw LIKE '%{%' THEN json_extract(te.raw, '$.string_time')
            ELSE NULL 
        END as string_time,
        
        -- No impact data for START/STOP
        NULL as impact_time,
        NULL as sensor_event_id,
        NULL as sensor_id,
        NULL as impact_magnitude,
        NULL as impact_features,
        
        -- No correlation for START/STOP
        NULL as time_diff_seconds,
        'n/a' as correlation_quality,
        'timer_control' as event_status,
        
        -- No target context for START/STOP
        NULL as sensor_label,
        NULL as target_number,
        NULL as target_category,
        
        -- Run context
        r.started_ts as run_started,
        r.ended_ts as run_ended,
        r.status as run_status,
        sh.name as shooter_name,
        st.name as stage_name
        
    FROM timer_events te
    LEFT JOIN runs r ON te.run_id = r.id
    LEFT JOIN shooters sh ON r.shooter_id = sh.id
    LEFT JOIN stages st ON r.stage_id = st.id
    
    WHERE te.type IN ('START', 'STOP')
    
    ORDER BY 
        run_id, 
        COALESCE(timer_event_time, impact_time),
        shot_sequence NULLS LAST
    """)
    
    with engine.connect() as conn:
        conn.execute(create_view_sql)
        conn.commit()


def create_string_summary_view(engine: Engine) -> None:
    """
    Create string_summary view that aggregates shot data by run/string.
    
    Provides high-level string statistics for leaderboards and analysis.
    """
    
    create_view_sql = text("""
    CREATE VIEW IF NOT EXISTS string_summary AS
    SELECT 
        run_id,
        shooter_name,
        stage_name,
        run_started,
        run_ended,
        run_status,
        
        -- Shot counts
        COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) as total_shots,
        COUNT(CASE WHEN event_status = 'correlated' THEN 1 END) as confirmed_hits,
        COUNT(CASE WHEN event_status = 'timer_only' THEN 1 END) as missed_shots,
        COUNT(CASE WHEN event_status = 'impact_only' THEN 1 END) as extra_impacts,
        
        -- Timing analysis
        MAX(CASE WHEN event_type = 'STOP' THEN string_time END) as final_time,
        AVG(CASE WHEN event_type = 'SHOT' AND shot_time IS NOT NULL THEN shot_time END) as avg_split,
        MIN(CASE WHEN event_type = 'SHOT' AND shot_time IS NOT NULL THEN shot_time END) as first_shot,
        MAX(CASE WHEN event_type = 'SHOT' AND shot_time IS NOT NULL THEN shot_time END) as last_shot,
        
        -- Impact analysis
        AVG(CASE WHEN impact_magnitude IS NOT NULL THEN impact_magnitude END) as avg_impact,
        MAX(impact_magnitude) as max_impact,
        
        -- Correlation quality
        AVG(CASE 
            WHEN correlation_quality = 'excellent' THEN 4
            WHEN correlation_quality = 'good' THEN 3
            WHEN correlation_quality = 'fair' THEN 2
            WHEN correlation_quality = 'poor' THEN 1
            ELSE 0
        END) as avg_correlation_score,
        
        -- Target analysis
        COUNT(DISTINCT sensor_id) as targets_hit,
        
        -- Metadata
        COUNT(*) as total_events,
        MIN(COALESCE(timer_event_time, impact_time)) as first_event,
        MAX(COALESCE(timer_event_time, impact_time)) as last_event
        
    FROM shot_log
    WHERE run_id IS NOT NULL
    GROUP BY run_id, shooter_name, stage_name, run_started, run_ended, run_status
    ORDER BY run_started DESC, final_time ASC NULLS LAST
    """)
    
    with engine.connect() as conn:
        conn.execute(create_view_sql)
        conn.commit()


def drop_views(engine: Engine) -> None:
    """Drop all views (useful for development/testing)"""
    drop_sql = text("""
    DROP VIEW IF EXISTS string_summary;
    DROP VIEW IF EXISTS shot_log;
    """)
    
    with engine.connect() as conn:
        conn.execute(drop_sql)
        conn.commit()


def refresh_views(engine: Engine) -> None:
    """Refresh all views (recreate with latest schema)"""
    drop_views(engine)
    create_shot_log_view(engine)
    create_string_summary_view(engine)