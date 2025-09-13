"""
AMG Frame Validation with Checksum Verification
Enhanced validation for AMG timer frames including integrity checks
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Frame validation results"""
    VALID = "valid"
    INVALID_LENGTH = "invalid_length"
    INVALID_CHECKSUM = "invalid_checksum"
    INVALID_FRAME_TYPE = "invalid_frame_type"
    INVALID_DATA_RANGE = "invalid_data_range"
    CORRUPTED_DATA = "corrupted_data"


class AMGFrameValidator:
    """Enhanced frame validation for AMG timer data"""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._validation_stats = {
            "total_frames": 0,
            "valid_frames": 0,
            "invalid_frames": 0,
            "error_counts": {}
        }
        
    def validate_frame(self, data: bytes, enable_checksum: bool = False) -> Dict[str, Any]:
        """
        Comprehensive frame validation
        
        Args:
            data: Raw frame bytes
            enable_checksum: Enable checksum validation (if AMG supports it)
            
        Returns:
            Dict with validation results and details
        """
        self._validation_stats["total_frames"] += 1
        
        validation_result = {
            "valid": False,
            "result": ValidationResult.CORRUPTED_DATA,
            "errors": [],
            "warnings": [],
            "frame_size": len(data),
            "hex_data": data.hex().upper()
        }
        
        try:
            # 1. Length validation
            if not self._validate_length(data, validation_result):
                return validation_result
                
            # 2. Frame structure validation
            if not self._validate_frame_structure(data, validation_result):
                return validation_result
                
            # 3. Data range validation
            if not self._validate_data_ranges(data, validation_result):
                return validation_result
                
            # 4. Checksum validation (if enabled)
            if enable_checksum and not self._validate_checksum(data, validation_result):
                return validation_result
                
            # 5. Sequence validation (detect corrupted sequences)
            self._validate_sequence_integrity(data, validation_result)
            
            # Frame is valid
            validation_result["valid"] = True
            validation_result["result"] = ValidationResult.VALID
            self._validation_stats["valid_frames"] += 1
            
            logger.debug(f"Frame validation passed: {data.hex()}")
            
        except Exception as e:
            validation_result["errors"].append(f"Validation exception: {e}")
            self._update_stats(ValidationResult.CORRUPTED_DATA)
            logger.error(f"Frame validation exception: {e}")
            
        return validation_result
        
    def _validate_length(self, data: bytes, result: Dict[str, Any]) -> bool:
        """Validate frame length"""
        expected_length = 14
        
        if len(data) != expected_length:
            result["errors"].append(f"Invalid frame length: {len(data)}, expected {expected_length}")
            result["result"] = ValidationResult.INVALID_LENGTH
            self._update_stats(ValidationResult.INVALID_LENGTH)
            return False
            
        return True
        
    def _validate_frame_structure(self, data: bytes, result: Dict[str, Any]) -> bool:
        """Validate frame structure and type"""
        if len(data) < 2:
            result["errors"].append("Frame too short for structure validation")
            return False
            
        type_id = data[0]
        shot_state = data[1]
        
        # Validate type_id (commonly 1-30 based on AMG protocol)
        if not (1 <= type_id <= 30):
            if self.strict_mode:
                result["errors"].append(f"Invalid type_id: {type_id}, expected 1-30")
                return False
            else:
                result["warnings"].append(f"Unusual type_id: {type_id}")
                
        # Validate shot_state (3=ACTIVE, 5=START, 8=STOP)
        valid_states = [3, 5, 8]
        if shot_state not in valid_states:
            result["warnings"].append(f"Unusual shot_state: {shot_state}, expected one of {valid_states}")
            # Don't fail for unknown states in non-strict mode, as AMG might have other states
                
        return True
        
    def _validate_data_ranges(self, data: bytes, result: Dict[str, Any]) -> bool:
        """Validate data field ranges"""
        if len(data) < 14:
            return False
            
        current_shot = data[2]
        total_shots = data[3]
        
        # Validate shot numbers
        if current_shot > total_shots and total_shots > 0:
            result["errors"].append(f"Current shot ({current_shot}) > total shots ({total_shots})")
            return False
            
        # Validate shot counts are reasonable
        if total_shots > 100:  # Reasonable limit
            if self.strict_mode:
                result["errors"].append(f"Unreasonable total_shots: {total_shots}")
                return False
            else:
                result["warnings"].append(f"High total_shots: {total_shots}")
                
        # Validate time values (bytes 4-5, 6-7, 8-9, 10-11)
        time_fields = [
            ("current_time", (data[4] << 8) | data[5]),
            ("split_time", (data[6] << 8) | data[7]),
            ("first_shot_time", (data[8] << 8) | data[9]),
            ("second_shot_time", (data[10] << 8) | data[11])
        ]
        
        for field_name, time_value in time_fields:
            # Convert to seconds (AMG uses centiseconds)
            time_seconds = time_value / 100.0
            
            # Validate reasonable time ranges (0 to 1 hour)
            if time_seconds < 0 or time_seconds > 3600:
                result["warnings"].append(f"Unusual {field_name}: {time_seconds:.2f}s")
                
        return True
        
    def _validate_checksum(self, data: bytes, result: Dict[str, Any]) -> bool:
        """
        Validate frame checksum (if AMG protocol includes one)
        
        Note: This is a placeholder implementation. Real AMG protocol 
        analysis would be needed to determine actual checksum algorithm.
        """
        # Placeholder checksum validation
        # Real implementation would depend on AMG protocol specification
        
        if len(data) < 14:
            return False
            
        # Simple XOR checksum example (not necessarily AMG's actual method)
        calculated_checksum = 0
        for byte in data[:-1]:  # All bytes except last
            calculated_checksum ^= byte
            
        frame_checksum = data[-1]  # Assume last byte is checksum
        
        if calculated_checksum != frame_checksum:
            result["errors"].append(f"Checksum mismatch: calculated {calculated_checksum:02X}, frame {frame_checksum:02X}")
            return False
            
        return True
        
    def _validate_sequence_integrity(self, data: bytes, result: Dict[str, Any]):
        """Validate sequence integrity and detect corruption patterns"""
        # Check for common corruption patterns
        
        # 1. All zeros (likely transmission error)
        if all(byte == 0 for byte in data):
            result["warnings"].append("Frame contains all zeros - possible transmission error")
            
        # 2. All same value (likely corruption)
        if len(set(data)) == 1 and data[0] != 0:
            result["warnings"].append(f"Frame contains all same value ({data[0]:02X}) - possible corruption")
            
        # 3. Check for bit patterns that suggest corruption
        if self._detect_bit_corruption(data):
            result["warnings"].append("Detected potential bit-level corruption patterns")
            
    def _detect_bit_corruption(self, data: bytes) -> bool:
        """Detect potential bit-level corruption patterns"""
        # Look for patterns that suggest bit flips or corruption
        
        # Check for excessive alternating bit patterns (0xAA, 0x55)
        alternating_count = 0
        for byte in data:
            if byte in [0xAA, 0x55]:
                alternating_count += 1
                
        if alternating_count > len(data) // 3:  # More than 1/3 alternating
            return True
            
        # Check for excessive high bits (0xFF patterns)
        high_byte_count = sum(1 for byte in data if byte == 0xFF)
        if high_byte_count > len(data) // 2:
            return True
            
        return False
        
    def _update_stats(self, result: ValidationResult):
        """Update validation statistics"""
        self._validation_stats["invalid_frames"] += 1
        
        error_type = result.value
        if error_type not in self._validation_stats["error_counts"]:
            self._validation_stats["error_counts"][error_type] = 0
        self._validation_stats["error_counts"][error_type] += 1
        
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        stats = self._validation_stats.copy()
        
        if stats["total_frames"] > 0:
            stats["success_rate"] = stats["valid_frames"] / stats["total_frames"]
            stats["error_rate"] = stats["invalid_frames"] / stats["total_frames"]
        else:
            stats["success_rate"] = 0.0
            stats["error_rate"] = 0.0
            
        return stats
        
    def reset_stats(self):
        """Reset validation statistics"""
        self._validation_stats = {
            "total_frames": 0,
            "valid_frames": 0,
            "invalid_frames": 0,
            "error_counts": {}
        }


# Enhanced AMG client with validation
class ValidatedAMGProcessor:
    """AMG data processor with enhanced validation"""
    
    def __init__(self, strict_mode: bool = True, enable_checksum: bool = False):
        self.validator = AMGFrameValidator(strict_mode=strict_mode)
        self.enable_checksum = enable_checksum
        
    def process_amg_frame(self, data: bytes) -> Dict[str, Any]:
        """Process AMG frame with validation"""
        # Validate frame
        validation_result = self.validator.validate_frame(data, self.enable_checksum)
        
        response = {
            "validation": validation_result,
            "parsed_data": None,
            "processing_success": False
        }
        
        if validation_result["valid"]:
            # Parse validated frame
            from .amg_parse import parse_amg_timer_data
            parsed_data = parse_amg_timer_data(data)
            
            if parsed_data:
                response["parsed_data"] = parsed_data
                response["processing_success"] = True
                logger.debug(f"Successfully processed validated AMG frame")
            else:
                response["validation"]["errors"].append("Frame validation passed but parsing failed")
                logger.warning("Frame validation passed but parsing failed")
        else:
            logger.warning(f"Frame validation failed: {validation_result['errors']}")
            
        return response
        
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return self.validator.get_validation_stats()


# Test validation
def test_amg_frame_validation():
    """Test AMG frame validation"""
    validator = AMGFrameValidator(strict_mode=False)  # Use non-strict mode for testing
    
    # Test valid frame (14 bytes = 28 hex characters)
    valid_frame = bytes.fromhex("01030001050200400030002000100000")[:14]  # Truncate to 14 bytes
    result = validator.validate_frame(valid_frame)
    print(f"Valid frame test: {result['valid']} - {result['result'].value}")
    if result['warnings']:
        print(f"  Warnings: {result['warnings']}")
    
    # Test invalid length (12 bytes = 24 hex characters)
    invalid_frame = bytes.fromhex("010300010502004000300020")  # 12 bytes - too short
    result = validator.validate_frame(invalid_frame)
    print(f"Invalid length test: {result['valid']} - {result['result'].value}")
    
    # Test invalid type_id (14 bytes)
    invalid_type = bytes.fromhex("FF030001050200400030002000100000")[:14]  # Invalid type 0xFF
    result = validator.validate_frame(invalid_type)
    print(f"Invalid type test: {result['valid']} - {result['result'].value}")
    if result['warnings']:
        print(f"  Warnings: {result['warnings']}")
    
    # Print stats
    stats = validator.get_validation_stats()
    print(f"Validation stats: {stats}")


if __name__ == "__main__":
    test_amg_frame_validation()