"""Tests for data export functionality."""

import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Import without pytest dependency check
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from impact_bridge.data_export import DataExporter, EXPORT_SCHEMA_VERSION


def create_temp_export_dir():
    """Create temporary directory for exports."""
    return tempfile.mkdtemp()


def create_sample_log_files(temp_export_dir):
    """Create sample log files for testing."""
    log_dir = Path(temp_export_dir) / "logs"
    log_dir.mkdir()
    
    # Create sample JSONL log file
    jsonl_file = log_dir / "test_events.jsonl"
    with open(jsonl_file, 'w') as f:
        # Timer start event
        event1 = {
            "timestamp_iso": "2025-09-14T10:00:00Z",
            "type": "Status",
            "device": "Timer",
            "device_id": "60:09:C3:1F:DC:1A", 
            "details": "Timer Start Button pressed, Random countdown: 2.25s",
            "seq": 1
        }
        json.dump(event1, f)
        f.write('\n')
        
        # Shot detected event
        event2 = {
            "timestamp_iso": "2025-09-14T10:00:10Z",
            "type": "String",
            "device": "Timer",
            "device_id": "60:09:C3:1F:DC:1A",
            "details": "Shot detected",
            "seq": 2
        }
        json.dump(event2, f)
        f.write('\n')
        
        # Impact detected event
        event3 = {
            "timestamp_iso": "2025-09-14T10:00:11Z",
            "type": "String", 
            "device": "Sensor",
            "device_id": "F8:FE:92:31:12:E3",
            "details": "Sensor Impact detected",
            "seq": 3
        }
        json.dump(event3, f)
        f.write('\n')
        
        # String summary event
        event4 = {
            "timestamp_iso": "2025-09-14T10:00:30Z",
            "type": "StringSummary",
            "device": "Bridge",
            "device_id": "MCU1",
            "details": "String Time: 30.00s; Shots Detected: 1; Impacts Detected: 1",
            "seq": 4
        }
        json.dump(event4, f)
        f.write('\n')
    
    return [jsonl_file]


def test_data_exporter_initialization(temp_export_dir):
    """Test DataExporter initialization."""
    exporter = DataExporter(export_dir=str(temp_export_dir))
    
    assert exporter.export_dir == Path(temp_export_dir)
    assert exporter.enable_parquet is True
    assert exporter.compression == "gzip"
    
    # Check that subdirectories were created
    assert (Path(temp_export_dir) / "csv").exists()
    assert (Path(temp_export_dir) / "ndjson").exists()
    assert (Path(temp_export_dir) / "parquet").exists()
    assert (Path(temp_export_dir) / "archives").exists()


def test_csv_export(temp_export_dir, sample_log_files):
    """Test CSV export functionality."""
    exporter = DataExporter(export_dir=str(temp_export_dir))
    
    csv_path = exporter.export_run_data_csv(sample_log_files, "test_runs.csv")
    
    assert csv_path.exists()
    assert csv_path.name == "test_runs.csv"
    
    # Read and verify CSV content
    with open(csv_path, 'r') as f:
        content = f.read()
        assert "run_id,start_time,end_time" in content
        assert "shots_detected,impacts_detected" in content


def test_ndjson_export(temp_export_dir, sample_log_files):
    """Test NDJSON export functionality."""
    exporter = DataExporter(export_dir=str(temp_export_dir))
    
    ndjson_path = exporter.export_ndjson(sample_log_files, "test_raw.jsonl")
    
    assert ndjson_path.exists()
    assert ndjson_path.name == "test_raw.jsonl"
    
    # Read and verify NDJSON content
    with open(ndjson_path, 'r') as f:
        lines = f.readlines()
        
        # First line should be schema
        schema_line = json.loads(lines[0])
        assert schema_line["_type"] == "schema"
        assert schema_line["_version"] == EXPORT_SCHEMA_VERSION
        
        # Subsequent lines should be data records
        assert len(lines) > 1
        data_line = json.loads(lines[1])
        assert "_schema_version" in data_line
        assert "_exported_at" in data_line
        assert "_source_file" in data_line


def test_parquet_export(temp_export_dir, sample_log_files):
    """Test Parquet export functionality."""
    exporter = DataExporter(export_dir=str(temp_export_dir))
    
    parquet_path = exporter.export_parquet(sample_log_files, "test_analytics.parquet")
    
    assert parquet_path.exists()
    assert parquet_path.name == "test_analytics.parquet"
    assert parquet_path.suffix == ".parquet"


def test_match_archive(temp_export_dir, sample_log_files):
    """Test match archive creation."""
    exporter = DataExporter(export_dir=str(temp_export_dir))
    
    archive_path = exporter.create_match_archive(
        match_id="TEST_MATCH",
        log_files=sample_log_files,
        include_all_formats=True
    )
    
    assert archive_path.exists()
    assert archive_path.suffix == ".zip"
    assert "TEST_MATCH" in archive_path.name
    
    # Verify archive contents
    with zipfile.ZipFile(archive_path, 'r') as archive:
        file_list = archive.namelist()
        
        # Should contain original logs
        assert any("logs/" in f for f in file_list)
        
        # Should contain exports
        assert any("exports/" in f for f in file_list)
        
        # Should contain metadata
        assert "metadata.json" in file_list
        
        # Verify metadata content
        metadata_content = archive.read("metadata.json")
        metadata = json.loads(metadata_content)
        assert metadata["match_id"] == "TEST_MATCH"
        assert metadata["schema_version"] == EXPORT_SCHEMA_VERSION


def test_data_offload(temp_export_dir):
    """Test data offload functionality."""
    # Create some old test files
    source_dir = Path(temp_export_dir) / "source"
    source_dir.mkdir()
    
    old_file = source_dir / "old_data.txt"
    old_file.write_text("old data")
    
    # Set modification time to make it appear old
    import time
    old_time = time.time() - (40 * 24 * 60 * 60)  # 40 days ago
    os.utime(old_file, (old_time, old_time))
    
    exporter = DataExporter(export_dir=str(temp_export_dir))
    
    # Offload data older than 30 days
    from datetime import timedelta
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    archive_path = exporter.offload_data(
        source_dir=source_dir,
        cutoff_date=cutoff_date,
        archive_name="test_offload.zip",
        delete_source=False
    )
    
    assert archive_path.exists()
    assert archive_path.name == "test_offload.zip"
    
    # Verify archive contains the old file
    with zipfile.ZipFile(archive_path, 'r') as archive:
        file_list = archive.namelist()
        assert "old_data.txt" in file_list
        assert "offload_metadata.json" in file_list


def test_export_filters(temp_export_dir, sample_log_files):
    """Test export with event filtering."""
    exporter = DataExporter(export_dir=str(temp_export_dir))
    
    # Export only "String" events
    ndjson_path = exporter.export_ndjson(
        sample_log_files, 
        "filtered_events.jsonl",
        filter_events=["String"]
    )
    
    # Count the exported events (excluding schema line)
    with open(ndjson_path, 'r') as f:
        lines = f.readlines()
        data_lines = [line for line in lines[1:] if line.strip()]
        
        # Should have 2 String events (shot + impact)
        assert len(data_lines) == 2
        
        for line in data_lines:
            record = json.loads(line)
            assert record.get("type") == "String" or record.get("event_type") == "String"


def test_empty_logs_handling(temp_export_dir):
    """Test handling of empty or missing log files."""
    exporter = DataExporter(export_dir=str(temp_export_dir))
    
    # Test with empty file list
    csv_path = exporter.export_run_data_csv([], "empty_test.csv")
    assert csv_path.exists()
    
    # Verify it has headers but no data
    with open(csv_path, 'r') as f:
        content = f.read()
        lines = content.strip().split('\n')
        assert len(lines) == 1  # Only header line
        assert "run_id,start_time" in lines[0]


if __name__ == "__main__":
    # Simple test runner without pytest
    import traceback
    import shutil
    
    def run_test(test_func, temp_dir, sample_files=None):
        try:
            if sample_files is not None:
                test_func(temp_dir, sample_files)
            else:
                test_func(temp_dir)
            print(f"✓ {test_func.__name__}")
            return True
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            traceback.print_exc()
            return False
    
    # Create temporary directory for testing
    temp_dir = create_temp_export_dir()
    
    try:
        print(f"Running data export tests in {temp_dir}...")
        
        # Create sample log files
        sample_files = create_sample_log_files(temp_dir)
        
        # Run tests
        passed = 0
        total = 0
        
        tests = [
            (test_data_exporter_initialization, False),
            (test_csv_export, True),
            (test_ndjson_export, True),
            (test_parquet_export, True),
            (test_match_archive, True),
            (test_data_offload, False),
            (test_export_filters, True),
            (test_empty_logs_handling, False),
        ]
        
        for test_func, needs_samples in tests:
            total += 1
            if needs_samples:
                if run_test(test_func, temp_dir, sample_files):
                    passed += 1
            else:
                if run_test(test_func, temp_dir):
                    passed += 1
        
        print(f"\nTest Results: {passed}/{total} passed")
        
        if passed == total:
            print("All tests passed! ✓")
        else:
            print(f"{total - passed} tests failed! ✗")
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)