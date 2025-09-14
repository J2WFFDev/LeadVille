# LeadVille Data Export & Analytics

This document describes the comprehensive data export and analytics features implemented in LeadVille Impact Bridge.

## Overview

The data export system provides multiple formats and capabilities for exporting, archiving, and analyzing sensor data:

- **CSV Export**: One row per run with comprehensive data aggregation
- **NDJSON Export**: Raw event data with schema versioning for analysis
- **Parquet Export**: Optimized columnar format for analytics (optional)
- **Match Archives**: Complete match packages with all data formats
- **Data Offload**: Automated archival of old data

## Export Formats

### CSV Export
Creates a tabular export with one row per shooting run, containing:
- Run metadata (ID, start/end times, duration)
- Shot and impact counts
- Correlation statistics
- Device information

Example CSV structure:
```csv
run_id,start_time,end_time,duration_seconds,shots_detected,impacts_detected,correlation_success_rate
run_1,2025-09-14T10:00:00Z,2025-09-14T10:00:30Z,30.0,5,4,0.8
```

### NDJSON Export
Exports raw event data in newline-delimited JSON format with:
- Schema versioning for compatibility
- Full event data preservation
- Export metadata and timestamps
- Optional filtering by event types

Each file starts with a schema record:
```json
{"_type":"schema","_version":"1.0.0","_description":"LeadVille Impact Bridge export data"}
```

Followed by event records:
```json
{"_schema_version":"1.0.0","timestamp_iso":"2025-09-14T10:00:00Z","event_type":"shot_detected","device":"Timer"}
```

### Parquet Export
Optimized columnar format for analytics:
- High compression efficiency
- Fast query performance
- Optional partitioning by date/session
- Support for multiple compression algorithms (gzip, brotli, lz4, zstd)

## Configuration

Data export is configured in `config/dev_config.json`:

```json
{
  "data_export": {
    "enabled": true,
    "export_dir": "exports",
    "auto_export": {
      "enabled": false,
      "interval_hours": 24,
      "formats": ["csv", "ndjson"]
    },
    "formats": {
      "csv": {
        "enabled": true,
        "include_debug": false
      },
      "ndjson": {
        "enabled": true,
        "schema_version": "1.0.0",
        "include_raw_data": true
      },
      "parquet": {
        "enabled": true,
        "compression": "gzip",
        "partition_by": null
      }
    },
    "offload": {
      "auto_offload": false,
      "retention_days": 30,
      "delete_after_offload": false
    }
  }
}
```

## Command Line Interface

The `scripts/export_data.py` script provides a comprehensive CLI for data export operations:

### Basic Export
```bash
# Export all formats
python scripts/export_data.py export --format all

# Export specific format
python scripts/export_data.py export --format csv
python scripts/export_data.py export --format ndjson
python scripts/export_data.py export --format parquet

# Export with filtering
python scripts/export_data.py export --format ndjson --filter-events "shot_detected,impact_detected"
```

### Match Archives
```bash
# Create complete match archive
python scripts/export_data.py archive --match-id "Match_2024_Championship"

# Archive with custom database
python scripts/export_data.py archive --match-id "Match_001" --db-path "custom.db"

# Archive logs only (no exports)
python scripts/export_data.py archive --match-id "Match_001" --logs-only
```

### Data Offload
```bash
# Offload data older than 30 days
python scripts/export_data.py offload --days-old 30

# Offload with source deletion
python scripts/export_data.py offload --days-old 60 --delete-source --yes

# Custom source directory
python scripts/export_data.py offload --source-dir /path/to/logs --days-old 90
```

### List Exports
```bash
# List all existing exports
python scripts/export_data.py list
```

## Programmatic Usage

The `DataExporter` class can be used programmatically:

```python
from impact_bridge.data_export import DataExporter
from pathlib import Path

# Initialize exporter
exporter = DataExporter(export_dir="custom_exports")

# Find log files
log_files = list(Path("logs").rglob("*.jsonl"))

# Export to CSV
csv_path = exporter.export_run_data_csv(log_files, "my_runs.csv")

# Export to NDJSON with filtering
ndjson_path = exporter.export_ndjson(
    log_files,
    "filtered_data.jsonl",
    filter_events=["shot_detected", "impact_detected"]
)

# Create match archive
archive_path = exporter.create_match_archive(
    match_id="Championship_2024",
    log_files=log_files,
    include_all_formats=True
)

# Data offload
from datetime import datetime, timedelta, timezone
cutoff = datetime.now(timezone.utc) - timedelta(days=30)
offload_path = exporter.offload_data(
    source_dir=Path("logs"),
    cutoff_date=cutoff,
    delete_source=False
)
```

## File Organization

Exports are organized in the following directory structure:

```
exports/
├── csv/                    # CSV exports
│   ├── run_data_*.csv
│   └── match_*_runs.csv
├── ndjson/                 # NDJSON exports
│   ├── raw_data_*.jsonl
│   └── match_*_raw.jsonl
├── parquet/                # Parquet exports (if enabled)
│   ├── analytics_data_*.parquet
│   └── match_*_analytics.parquet
└── archives/               # Match archives and offloads
    ├── match_*.zip
    └── offload_*.zip
```

## Schema Versioning

NDJSON exports include schema versioning to ensure compatibility across different versions:

- **Version 1.0.0**: Initial schema with basic event structure
- Future versions will maintain backward compatibility
- Schema evolution documented in export metadata

## Integration with Existing Systems

The export system integrates seamlessly with existing LeadVille components:

### Event Logger Integration
- Builds upon existing `StructuredEventLogger`
- Processes existing CSV and NDJSON log formats
- Maintains compatibility with TinTown console output

### Database Integration
- Can export from both log files and SQLite database
- Match archives include database files when available
- Supports both file-based and database-driven workflows

### Configuration System
- Uses existing configuration infrastructure
- Extends `dev_config.json` with export settings
- Maintains configuration consistency

## Performance Considerations

### Large Dataset Handling
- Batch processing for large log files
- Configurable batch size (default: 10,000 records)
- Memory-efficient streaming for JSONL processing

### Compression Options
- Multiple compression algorithms supported
- Gzip (default): Good balance of speed and compression
- Brotli: Higher compression ratio
- LZ4: Faster compression/decompression
- Zstd: Modern algorithm with excellent performance

### Parquet Partitioning
- Optional partitioning by date, session, or custom fields
- Improves query performance for large datasets
- Configurable partition strategy

## Best Practices

### For Regular Operations
1. Use CSV exports for spreadsheet analysis
2. Use NDJSON for programmatic analysis and data pipeline integration
3. Enable Parquet for large-scale analytics
4. Create match archives for important competitions

### For Long-term Storage
1. Use data offload for automated archival
2. Configure appropriate retention periods
3. Consider compression settings for storage efficiency
4. Maintain archive metadata for future reference

### For Analysis Workflows
1. Filter NDJSON exports by relevant event types
2. Use Parquet partitioning for time-series analysis
3. Leverage schema versioning for compatibility
4. Document custom analysis pipelines

## Troubleshooting

### Common Issues

**Empty CSV exports**: Check that log files contain complete run sequences (start button → shots → summary events)

**Large memory usage**: Reduce batch size in DataExporter configuration or process files individually

**Parquet errors**: Ensure pyarrow is installed and compatible with pandas version

**Archive creation fails**: Verify log file permissions and available disk space

### Logging
Export operations are logged at INFO level. Use `--verbose` flag for detailed DEBUG output:

```bash
python scripts/export_data.py --verbose export --format all
```

## Future Enhancements

Planned improvements for future releases:

1. **Automated Scheduling**: Cron-based automatic exports
2. **Cloud Storage**: Direct export to S3, Azure Blob, etc.
3. **Real-time Streaming**: Live data export during matches
4. **Advanced Analytics**: Built-in statistical analysis and reporting
5. **Web Interface**: Browser-based export management
6. **API Endpoints**: RESTful API for remote export control