-- Example Web App Queries for LeadVille Timer System
-- Use these queries in your web application to display timer data

-- 1. LIVE DASHBOARD - Current/Recent Activity
-- Shows the most recent timer events for live monitoring
SELECT 
    log_id,
    event_time,
    event_type,
    shot_number,
    shot_time,
    string_total_time,
    timer_device
FROM shot_log_simple 
WHERE event_time >= datetime('now', '-1 hour')
ORDER BY log_id DESC 
LIMIT 20;

-- 2. CURRENT STRING PROGRESS
-- Shows shots in the active/most recent string
SELECT 
    shot_number,
    shot_time,
    string_total_time,
    event_time,
    CASE 
        WHEN shot_time <= 0.30 THEN 'excellent'
        WHEN shot_time <= 0.50 THEN 'good' 
        WHEN shot_time <= 0.70 THEN 'fair'
        ELSE 'slow'
    END as shot_rating
FROM shot_log_simple 
WHERE event_type = 'SHOT' 
    AND log_id >= (
        SELECT MAX(log_id) 
        FROM shot_log_simple 
        WHERE event_type = 'START'
    )
ORDER BY shot_number;

-- 3. LEADERBOARD - Best Strings Today
-- Shows fastest complete strings from today
WITH string_times AS (
    SELECT 
        timer_device,
        string_total_time,
        event_time,
        COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) OVER (
            PARTITION BY timer_device,
            datetime(event_time, 'start of day')
        ) as shots_today
    FROM shot_log_simple 
    WHERE event_type = 'STOP' 
        AND date(event_time) = date('now')
        AND string_total_time IS NOT NULL
)
SELECT 
    timer_device,
    MIN(string_total_time) as best_time,
    COUNT(*) as strings_completed,
    MAX(event_time) as last_string
FROM string_times
GROUP BY timer_device
ORDER BY best_time ASC;

-- 4. SHOT ANALYSIS - Split Times Distribution
-- Analyzes shot timing patterns for coaching
SELECT 
    shot_number,
    COUNT(*) as frequency,
    AVG(shot_time) as avg_split,
    MIN(shot_time) as best_split,
    MAX(shot_time) as worst_split,
    ROUND(AVG(shot_time), 2) || 's ±' || 
    ROUND(
        SQRT(AVG((shot_time - (SELECT AVG(shot_time) FROM shot_log_simple s2 
                              WHERE s2.shot_number = shot_log_simple.shot_number)) * 
                 (shot_time - (SELECT AVG(shot_time) FROM shot_log_simple s2 
                              WHERE s2.shot_number = shot_log_simple.shot_number)))), 2
    ) || 's' as consistency
FROM shot_log_simple 
WHERE event_type = 'SHOT' 
    AND shot_time > 0
    AND date(event_time) >= date('now', '-7 days')
GROUP BY shot_number
ORDER BY shot_number;

-- 5. PERFORMANCE TRENDS - Daily Improvement
-- Shows daily performance trends
SELECT 
    date(event_time) as practice_date,
    COUNT(CASE WHEN event_type = 'STOP' THEN 1 END) as strings_completed,
    MIN(string_total_time) as best_time,
    AVG(string_total_time) as avg_time,
    AVG(CASE WHEN event_type = 'SHOT' THEN shot_time END) as avg_split,
    COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) as total_shots
FROM shot_log_simple 
WHERE date(event_time) >= date('now', '-30 days')
    AND string_total_time IS NOT NULL
GROUP BY date(event_time)
ORDER BY practice_date DESC;

-- 6. EQUIPMENT STATUS - Timer Health
-- Shows timer device status and data quality
SELECT 
    timer_device,
    total_events,
    shot_events,
    ROUND(100.0 * events_with_json / total_events, 1) as json_data_pct,
    ROUND(100.0 * events_with_raw_data / total_events, 1) as raw_data_pct,
    max_string_time,
    ROUND(avg_split_time, 3) as avg_split,
    first_event,
    last_event,
    CASE 
        WHEN datetime(last_event) >= datetime('now', '-1 hour') THEN 'active'
        WHEN datetime(last_event) >= datetime('now', '-1 day') THEN 'recent'
        ELSE 'idle'
    END as status
FROM timer_summary
ORDER BY last_event DESC;

-- 7. REAL-TIME API - Latest Events (for WebSocket)
-- Optimized query for real-time updates
SELECT 
    log_id,
    event_time,
    event_type,
    shot_number,
    total_shots,
    shot_time,
    string_total_time,
    timer_device,
    json_extract(parsed_json, '$.shot_state') as shot_state
FROM shot_log_simple 
WHERE log_id > :last_seen_id  -- Parameter from web app
ORDER BY log_id ASC
LIMIT 50;

-- 8. STRING COMPARISON - Head-to-Head
-- Compare performance between different practice sessions
WITH recent_strings AS (
    SELECT 
        date(event_time) as session_date,
        string_total_time,
        ROW_NUMBER() OVER (PARTITION BY date(event_time) ORDER BY string_total_time) as rank_in_session
    FROM shot_log_simple 
    WHERE event_type = 'STOP' 
        AND string_total_time IS NOT NULL
        AND date(event_time) >= date('now', '-7 days')
)
SELECT 
    session_date,
    COUNT(*) as strings_fired,
    MIN(string_total_time) as best_time,
    AVG(string_total_time) as avg_time,
    string_total_time as median_time
FROM recent_strings r1
WHERE rank_in_session = (
    SELECT ROUND(COUNT(*) / 2.0) 
    FROM recent_strings r2 
    WHERE r2.session_date = r1.session_date
)
GROUP BY session_date, string_total_time
ORDER BY session_date DESC;

-- 9. COACHING INSIGHTS - Problem Shots
-- Identifies consistently slow shots for training focus
SELECT 
    shot_number,
    COUNT(*) as occurrences,
    AVG(shot_time) as avg_time,
    COUNT(CASE WHEN shot_time > 0.50 THEN 1 END) as slow_shots,
    ROUND(100.0 * COUNT(CASE WHEN shot_time > 0.50 THEN 1 END) / COUNT(*), 1) as slow_percentage,
    'Focus on shot #' || shot_number || ' - ' || 
    ROUND(100.0 * COUNT(CASE WHEN shot_time > 0.50 THEN 1 END) / COUNT(*), 1) || 
    '% over 0.5s' as coaching_note
FROM shot_log_simple 
WHERE event_type = 'SHOT' 
    AND shot_time > 0
    AND date(event_time) >= date('now', '-14 days')
GROUP BY shot_number
HAVING COUNT(*) >= 5  -- Only shots with enough data
ORDER BY slow_percentage DESC;

-- 10. SESSION SUMMARY - For Match Directors
-- Complete session overview for match management
SELECT 
    date(event_time) as session_date,
    timer_device,
    MIN(event_time) as session_start,
    MAX(event_time) as session_end,
    ROUND((julianday(MAX(event_time)) - julianday(MIN(event_time))) * 24 * 60, 1) as duration_minutes,
    COUNT(CASE WHEN event_type = 'START' THEN 1 END) as strings_started,
    COUNT(CASE WHEN event_type = 'STOP' THEN 1 END) as strings_completed,
    COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) as total_shots,
    MIN(string_total_time) as fastest_string,
    AVG(string_total_time) as avg_string_time,
    ROUND(COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) * 1.0 / 
          NULLIF(COUNT(CASE WHEN event_type = 'STOP' THEN 1 END), 0), 1) as avg_shots_per_string
FROM shot_log_simple 
WHERE date(event_time) = date('now')  -- Today's session
GROUP BY date(event_time), timer_device
ORDER BY session_start DESC;