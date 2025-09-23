#!/usr/bin/env python3
"""
Enhanced AMG Handler Integration
Combines the working AMG event detection with the sophisticated new parser
"""

# This shows the enhanced AMG notification handler that should replace the current one
# in leadville_bridge.py

async def enhanced_amg_notification_handler(self, characteristic, data):
    """Enhanced AMG timer notifications with rich parsing"""
    hex_data = data.hex()
    self.logger.debug(f"AMG notification: {hex_data}")
    
    # Use the new sophisticated parser
    try:
        from impact_bridge.ble.amg_parse import parse_amg_timer_data, format_amg_event
        parsed_data = parse_amg_timer_data(data)
        
        if parsed_data:
            # Log the rich parsed information
            formatted_event = format_amg_event(parsed_data)
            self.logger.info(f"📝 AMG Event: {formatted_event}")
            
            # Extract event details for compatibility with existing logic
            shot_state = parsed_data.get('shot_state', 'UNKNOWN')
            current_time = parsed_data.get('current_time', 0.0)
            current_shot = parsed_data.get('current_shot', 0)
            split_time = parsed_data.get('split_time', 0.0)
            
            # Handle different event types (maintaining existing behavior)
            if shot_state == 'START':
                self.start_beep_time = datetime.now()
                string_number = parsed_data.get('current_round', self.current_string_number)
                self.current_string_number = string_number
                self.logger.info(f"📝 Status: Timer DC:1A - -------Start Beep ------- String #{string_number} at {self.start_beep_time.strftime('%H:%M:%S.%f')[:-3]}")
                
                # Persist with rich data
                self._persist_enhanced_timer_event(
                    event_type='START', 
                    raw_hex=hex_data,
                    parsed_data=parsed_data
                )
                
            elif shot_state == 'ACTIVE' and parsed_data.get('type_id') == 1:
                # Shot detection event
                shot_time = datetime.now()
                self.shot_counter += 1
                
                # Calculate split time from previous shot
                shot_split_seconds = 0.0
                if hasattr(self, 'previous_shot_time') and self.previous_shot_time:
                    shot_split_seconds = (shot_time - self.previous_shot_time).total_seconds()
                
                self.logger.info(f"🔫 String {self.current_string_number}, Shot #{self.shot_counter} - Time {current_time:.2f}s, Split {shot_split_seconds:.2f}s, First {parsed_data.get('first_shot_time', 0):.2f}s")
                
                self.previous_shot_time = shot_time
                
                # Record shot for timing correlation
                if self.timing_calibrator:
                    self.timing_calibrator.record_shot(shot_time, self.shot_counter, self.current_string_number)
                
                # Persist with rich data
                self._persist_enhanced_timer_event(
                    event_type='SHOT', 
                    raw_hex=hex_data,
                    parsed_data=parsed_data,
                    split_seconds=current_time
                )
                    
            elif shot_state == 'STOPPED':
                reception_timestamp = datetime.now()
                string_number = parsed_data.get('current_round', self.current_string_number)
                
                # Calculate total info
                total_info = ""
                if self.start_beep_time:
                    total_ms = (reception_timestamp - self.start_beep_time).total_seconds() * 1000
                    total_info = f" (total: {current_time:.2f}s)"
                    
                self.logger.info(f"📝 Status: Timer DC:1A - Stop Beep for String #{string_number} at {reception_timestamp.strftime('%H:%M:%S.%f')[:-3]}{total_info}")
                
                # Reset for next string  
                self.start_beep_time = None
                self.impact_counter = 0
                self.shot_counter = 0
                self.previous_shot_time = None
                
                # Persist with rich data
                self._persist_enhanced_timer_event(
                    event_type='STOP', 
                    raw_hex=hex_data,
                    parsed_data=parsed_data,
                    split_seconds=current_time
                )
            else:
                # Unknown or other event types
                self.logger.debug(f"AMG Other Event: {shot_state} - {formatted_event}")
                
                # Still persist for analysis
                self._persist_enhanced_timer_event(
                    event_type=shot_state, 
                    raw_hex=hex_data,
                    parsed_data=parsed_data
                )
                
    except ImportError:
        # Fallback to old parsing if new parser not available
        self.logger.warning("New AMG parser not available, using fallback")
        await self.amg_notification_handler_fallback(characteristic, data)
    except Exception as e:
        self.logger.error(f"Enhanced AMG parsing failed: {e}")
        # Fallback to old parsing
        await self.amg_notification_handler_fallback(characteristic, data)

def _persist_enhanced_timer_event(self, event_type: str, raw_hex: str = None, parsed_data: dict = None, split_seconds: float = None):
    """Enhanced timer event persistence with rich AMG data and fixed database handling"""
    try:
        # Fix database path - use the actual path found on Pi
        db_path = Path(__file__).parent.parent.parent / 'logs' / 'bt50_samples.db'
        
        # Alternative paths based on Pi findings
        possible_paths = [
            Path(__file__).parent.parent.parent / 'logs' / 'bt50_samples.db',  # /home/jrwest/logs/
            Path(__file__).parent.parent / 'logs' / 'bt50_samples.db',        # project/logs/
            Path('/home/jrwest/logs/bt50_samples.db'),                        # absolute path
        ]
        
        # Find the existing database or use the first path
        db_path = None
        for path in possible_paths:
            if path.exists():
                db_path = path
                break
        if not db_path:
            db_path = possible_paths[0]  # Use first as default
            
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        
        # Enhanced table schema with rich AMG data
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS timer_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_ns INTEGER,
                device_id TEXT,
                event_type TEXT,
                split_seconds REAL,
                split_cs INTEGER,
                raw_hex TEXT,
                -- New columns for rich AMG data
                shot_state TEXT,
                type_id INTEGER,
                current_shot INTEGER,
                total_shots INTEGER,
                current_time REAL,
                split_time REAL,
                first_shot_time REAL,
                second_shot_time REAL,
                current_round INTEGER,
                event_detail TEXT,
                parsed_json TEXT
            )
            """
        )
        
        ts_ns = int(time.time() * 1e9)
        
        # Extract rich data if available
        if parsed_data:
            import json
            values = (
                ts_ns, 
                "AMG_TIMER",  # Fixed device_id instead of trying to get from amg_client
                event_type,
                split_seconds or parsed_data.get('current_time', 0),
                int((split_seconds or parsed_data.get('current_time', 0)) * 100),  # split_cs
                raw_hex,
                # Rich data
                parsed_data.get('shot_state'),
                parsed_data.get('type_id'),
                parsed_data.get('current_shot'),
                parsed_data.get('total_shots'),
                parsed_data.get('current_time'),
                parsed_data.get('split_time'),
                parsed_data.get('first_shot_time'),
                parsed_data.get('second_shot_time'),
                parsed_data.get('current_round'),
                parsed_data.get('event_detail'),
                json.dumps(parsed_data)
            )
            
            cur.execute(
                """INSERT INTO timer_events (
                    ts_ns, device_id, event_type, split_seconds, split_cs, raw_hex,
                    shot_state, type_id, current_shot, total_shots, current_time, 
                    split_time, first_shot_time, second_shot_time, current_round, 
                    event_detail, parsed_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                values
            )
        else:
            # Fallback to basic data
            cur.execute(
                "INSERT INTO timer_events (ts_ns, device_id, event_type, split_seconds, split_cs, raw_hex) VALUES (?,?,?,?,?,?)",
                (ts_ns, "AMG_TIMER", event_type, split_seconds, int((split_seconds or 0) * 100), raw_hex),
            )
        
        con.commit()
        con.close()
        
        # Log successful persistence
        print(f"✅ Persisted AMG event: {event_type} to {db_path}")
        
    except Exception as e:
        # Log the error but don't crash the bridge
        print(f"⚠️ AMG database persistence failed: {e}")
        # Don't raise - this is best-effort logging

# Fallback to original handler if needed
async def amg_notification_handler_fallback(self, characteristic, data):
    """Original AMG handler as fallback"""
    # This would be the existing handler code as backup
    pass