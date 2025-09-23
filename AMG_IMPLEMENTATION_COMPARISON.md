# AMG Implementation Comparison Analysis

## Current Implementation (leadville_bridge.py)

### Architecture
- **Location**: `src/impact_bridge/leadville_bridge.py` lines 413-498
- **Connection**: Direct `BleakClient` usage
- **Parsing**: Hardcoded byte pattern matching in `amg_notification_handler()`

### Parsing Logic
```python
# Only handles 3 specific patterns:
if frame_header == 0x01 and frame_type == 0x05:    # START (0x0105)
elif frame_header == 0x01 and frame_type == 0x03:  # SHOT (0x0103) 
elif frame_header == 0x01 and frame_type == 0x08:  # STOP (0x0108)
```

### Data Extraction
- **START**: String number from `data[13]`
- **SHOT**: Timer data from bytes 4-9 (time_cs, split_cs, first_cs)
- **STOP**: String number and total time

### Database Storage
- **Table**: `timer_events`
- **Method**: `_persist_timer_event()`
- **Schema**:
  ```sql
  CREATE TABLE timer_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts_ns INTEGER,
      device_id TEXT,
      event_type TEXT,     -- 'START', 'SHOT', 'STOP'
      split_seconds REAL,
      split_cs INTEGER,
      raw_hex TEXT
  )
  ```

### Pros
✅ **Working** - Currently integrated and functional  
✅ **Simple** - Direct database insertion  
✅ **Tested** - In production use  
✅ **Handles core events** - START/SHOT/STOP detection  

### Cons
❌ **Limited parsing** - Only 3 frame types  
❌ **Hardcoded logic** - No extensibility  
❌ **Missing data** - Doesn't extract rich timer information  
❌ **No structured data** - Raw bytes only  

---

## New Implementation (amg.py + amg_parse.py)

### Architecture
- **Location**: `src/impact_bridge/ble/amg.py` + `amg_parse.py`
- **Connection**: Modern `AmgClient` class with callbacks
- **Parsing**: Sophisticated `parse_amg_timer_data()` function

### Parsing Logic
```python
# Handles multiple frame types and states:
- ShotState.START (5), ACTIVE (3), STOPPED (8)  
- Type IDs: 1 (shot detection), 10-26 (sequences)
- Rich data extraction from 14-byte frames
```

### Data Extraction
```python
# Extracts comprehensive data:
{
    'type_id': int,           # Frame type identifier
    'shot_state': str,        # 'START', 'ACTIVE', 'STOPPED'  
    'shot_state_raw': int,    # Raw state value
    'current_shot': int,      # Shot number
    'total_shots': int,       # Total shots in sequence
    'current_time': float,    # Current time in seconds
    'split_time': float,      # Split time
    'first_shot_time': float, # First shot time
    'second_shot_time': float,# Second shot time
    'current_round': int,     # Round/series number
    'event_type': str,        # Always "String" for timer
    'event_detail': str,      # Human-readable description
    'raw_hex': str           # Original hex data
}
```

### Database Storage
- **Status**: ❌ **NOT CONNECTED** - No database integration
- **Missing**: No equivalent to `_persist_timer_event()`

### Pros
✅ **Rich data** - Extracts all timer information  
✅ **Extensible** - Handles multiple frame types  
✅ **Modern architecture** - Callback-based design  
✅ **Better error handling** - Graceful parsing failures  
✅ **Structured output** - Dictionary format for easy processing  
✅ **Based on research** - References AMG protocol documentation  

### Cons
❌ **Not integrated** - No database connection  
❌ **Unused** - Not called by main bridge  
❌ **Untested** - No production validation  
❌ **Over-engineered** - May be more complex than needed  

---

## Key Differences Summary

| Aspect | Current (Working) | New (Unused) |
|--------|------------------|--------------|
| **Integration** | ✅ Full | ❌ None |
| **Database** | ✅ timer_events | ❌ No storage |
| **Frame Types** | 3 patterns | Multiple types |
| **Data Richness** | Basic | Comprehensive |
| **Architecture** | Simple handler | Modern client |
| **Error Handling** | Basic | Robust |
| **Extensibility** | Limited | High |
| **Production Ready** | ✅ Yes | ❌ No |

---

## Recommendations

### Option A: Test Current (What you requested)
1. **Check Pi database** - Use commands in `PI_AMG_TEST_COMMANDS.md`
2. **Verify functionality** - Look for timer_events with START/SHOT/STOP
3. **Check logs** - Confirm AMG notifications are being processed

### Option B: Integrate New Parser (Next step)
1. **Keep current database flow** - Use existing `_persist_timer_event()`
2. **Replace parsing logic** - Use `parse_amg_timer_data()` for rich extraction
3. **Add structured data** - Store parsed fields in new columns
4. **Maintain compatibility** - Keep existing event_type/split_seconds

### Option C: Hybrid Approach (Recommended)
1. **Enhance current handler** - Use new parser but keep database schema
2. **Add rich logging** - Log structured data to separate file
3. **Gradual migration** - Test new parser alongside current logic