#!/usr/bin/env python3
"""
OpenAPI Specification Generator for LeadVille Impact Bridge API
Generates OpenAPI 3.0 specification from FastAPI application
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
import argparse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from impact_bridge.api.main import create_app
    from impact_bridge.api.config import api_config
except ImportError as e:
    print(f"❌ Failed to import LeadVille API modules: {e}")
    print("   Make sure you're running this from the LeadVille root directory")
    print("   and that all dependencies are installed.")
    sys.exit(1)


def generate_openapi_spec(output_format: str = "json", output_file: str = None) -> Dict[str, Any]:
    """Generate OpenAPI specification from FastAPI app.
    
    Args:
        output_format: Format for output ('json' or 'yaml')
        output_file: Optional output file path
        
    Returns:
        OpenAPI specification as dictionary
    """
    print("🚀 Generating OpenAPI specification...")
    
    # Create FastAPI application
    app = create_app()
    
    # Generate OpenAPI specification
    openapi_spec = app.openapi()
    
    # Add additional metadata
    openapi_spec.update({
        "info": {
            **openapi_spec.get("info", {}),
            "title": "LeadVille Impact Bridge API",
            "description": """
# LeadVille Impact Bridge API

Production BLE-based impact sensor system for shooting sports with real-time shot detection and impact correlation.

## Features

- **🔒 Secure Authentication** - JWT-based authentication with role-based access control
- **📊 Real-time Metrics** - System performance and sensor data monitoring
- **❤️ Health Monitoring** - Component health checks and diagnostics
- **🔧 Device Management** - BLE device configuration and control
- **📝 Structured Logging** - NDJSON format logging with request tracking

## Authentication

This API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Rate Limiting

API requests are rate-limited to prevent abuse. Current limits:
- 100 requests per minute per client
- Higher limits available for authenticated users

## Error Handling

All errors follow a consistent format:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable error message",
        "details": {...}
    },
    "request_id": "unique-request-identifier"
}
```
            """.strip(),
            "version": "2.0.0",
            "contact": {
                "name": "LeadVille Development Team",
                "email": "team@leadville.example.com",
                "url": "https://github.com/J2WFFDev/LeadVille"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": f"http://localhost:{api_config.port}",
                "description": "Development server"
            },
            {
                "url": f"http://raspberrypi.local:{api_config.port}",
                "description": "Raspberry Pi deployment"
            }
        ],
        "tags": [
            {
                "name": "Health",
                "description": "System health and status monitoring"
            },
            {
                "name": "Metrics", 
                "description": "Performance metrics and system statistics"
            },
            {
                "name": "Authentication",
                "description": "User authentication and authorization"
            },
            {
                "name": "Device Management",
                "description": "BLE device configuration and control"
            }
        ]
    })
    
    # Output specification
    if output_format.lower() == "yaml":
        try:
            import yaml
            spec_content = yaml.dump(openapi_spec, default_flow_style=False, sort_keys=False)
        except ImportError:
            print("⚠️  YAML output requires PyYAML. Install with: pip install pyyaml")
            print("   Falling back to JSON output")
            output_format = "json"
            spec_content = json.dumps(openapi_spec, indent=2)
    else:
        spec_content = json.dumps(openapi_spec, indent=2)
    
    # Write to file or stdout
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(spec_content)
        
        print(f"✅ OpenAPI specification written to: {output_path}")
        print(f"   Format: {output_format.upper()}")
        print(f"   Size: {len(spec_content):,} characters")
        
        # Display some key stats
        paths_count = len(openapi_spec.get("paths", {}))
        components_count = len(openapi_spec.get("components", {}).get("schemas", {}))
        
        print(f"   Endpoints: {paths_count}")
        print(f"   Models: {components_count}")
        
    else:
        print(spec_content)
    
    return openapi_spec


def main():
    """Main entry point for OpenAPI generation."""
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI specification for LeadVille Impact Bridge API"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the generated specification"
    )
    
    args = parser.parse_args()
    
    try:
        # Generate specification
        spec = generate_openapi_spec(
            output_format=args.format,
            output_file=args.output
        )
        
        # Validate if requested
        if args.validate:
            print("\n🔍 Validating OpenAPI specification...")
            
            # Basic validation
            required_fields = ["openapi", "info", "paths"]
            missing_fields = [field for field in required_fields if field not in spec]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return 1
            
            # Check OpenAPI version
            if not spec["openapi"].startswith("3."):
                print(f"⚠️  OpenAPI version {spec['openapi']} may not be fully supported")
            
            print("✅ OpenAPI specification is valid")
        
        print("\n🎯 OpenAPI generation complete!")
        
        if args.output:
            print("\n📋 Usage examples:")
            print(f"   View in Swagger UI: https://editor.swagger.io (upload {args.output})")
            print(f"   Generate client:    openapi-generator-cli generate -i {args.output} -g python")
        
    except Exception as e:
        print(f"❌ Failed to generate OpenAPI specification: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())