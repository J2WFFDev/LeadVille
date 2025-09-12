"""
WitMotion BT50 Sensor Data Parser

This module handles parsing of WitMotion 5561 protocol frames from BT50 sensors.
Corrected to use 1mg scale factor for proper acceleration values.
"""

import struct
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

def parse_5561(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Parse WitMotion 5561 protocol frames with corrected 1mg scale factor
    
    Args:
        data: Raw bytes from BT50 sensor
        
    Returns:
        Dictionary with parsed samples or None if parsing fails
    """
    try:
        if len(data) < 44:
            logger.debug(f"Frame too short: {len(data)} bytes")
            return None
            
        # Check for 5561 frame header
        if data[0] != 0x55 or data[1] != 0x61:
            logger.debug(f"Invalid header: {data[0]:02x} {data[1]:02x}")
            return None
            
        samples = []
        
        # Parse acceleration data (3 axes * 2 bytes each = 6 bytes per sample)
        # Frame contains multiple samples
        for i in range(2, min(len(data) - 5, 42), 6):  # Leave room for checksum
            if i + 6 <= len(data):
                # Parse 16-bit signed integers (little-endian)
                ax_raw = struct.unpack('<h', data[i:i+2])[0]
                ay_raw = struct.unpack('<h', data[i+2:i+4])[0] 
                az_raw = struct.unpack('<h', data[i+4:i+6])[0]
                
                # Convert to mg (1mg scale factor - corrected from previous 0.061mg)
                # Raw values are already in mg units
                ax_mg = ax_raw * 1.0  # 1mg per count
                ay_mg = ay_raw * 1.0
                az_mg = az_raw * 1.0
                
                # Convert to g units (divide by 1000)
                ax_g = ax_mg / 1000.0
                ay_g = ay_mg / 1000.0
                az_g = az_mg / 1000.0
                
                sample = {
                    'vx_raw': ax_raw,
                    'vy_raw': ay_raw, 
                    'vz_raw': az_raw,
                    'vx_mg': ax_mg,
                    'vy_mg': ay_mg,
                    'vz_mg': az_mg,
                    'vx_g': ax_g,
                    'vy_g': ay_g,
                    'vz_g': az_g,
                }
                samples.append(sample)
        
        if not samples:
            logger.debug("No samples parsed from frame")
            return None
            
        return {
            'frame_type': '5561',
            'samples': samples,
            'sample_count': len(samples)
        }
        
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return None


def calculate_magnitude(vx_raw: int, vy_raw: int, vz_raw: int) -> float:
    """Calculate 3D magnitude from raw acceleration values"""
    return (vx_raw**2 + vy_raw**2 + vz_raw**2)**0.5


def detect_impact_simple(samples: List[Dict], threshold: float = 150.0) -> bool:
    """Simple impact detection based on raw value changes"""
    if not samples:
        return False
        
    # Check if any sample exceeds threshold from baseline
    for sample in samples:
        magnitude = calculate_magnitude(
            sample['vx_raw'], 
            sample['vy_raw'], 
            sample['vz_raw']
        )
        if magnitude > threshold:
            return True
            
    return False