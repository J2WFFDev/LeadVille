#!/usr/bin/env python3
"""Quick utility to load a bridge YAML config and print parsed sensors.

Usage:
    python scripts/check_sensors_config.py path/to/config.yaml

This helps validate that the runtime config contains the expected `sensors:` entries
and that the `sensor` and `mac` fields are present.
"""
import sys
from pathlib import Path
from src.impact_bridge.config import load_config, validate_config


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_sensors_config.py path/to/config.yaml")
        sys.exit(2)

    config_path = sys.argv[1]
    path = Path(config_path)
    if not path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    try:
        config = load_config(str(path))
        errors = validate_config(config)
        if errors:
            print("Config validation errors:")
            for e in errors:
                print(" -", e)
        else:
            print("Config OK")

        print(f"AMG configured: {bool(config.amg)}")
        print(f"Sensor count: {len(config.sensors)}")
        for i, s in enumerate(config.sensors):
            print(f"[{i}] sensor={s.sensor} mac={s.mac} plate={s.plate} adapter={s.adapter}")

    except Exception as e:
        print(f"Failed to load config: {e}")
        raise


if __name__ == '__main__':
    main()
