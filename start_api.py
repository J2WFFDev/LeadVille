#!/usr/bin/env python3
"""
Simple script to start the LeadVille Impact Bridge FastAPI server.

Usage:
    python start_api.py
    python start_api.py --host 0.0.0.0 --port 8080 --debug

This provides a convenient way to start the API server with different configurations.
"""

import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Start LeadVille Impact Bridge FastAPI server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind to (default: 8000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log-level", default="INFO", help="Log level (default: INFO)")
    
    args = parser.parse_args()
    
    # Set environment variables for the API configuration
    os.environ["API_HOST"] = args.host
    os.environ["API_PORT"] = str(args.port)
    os.environ["API_DEBUG"] = "true" if args.debug else "false"
    os.environ["LOG_LEVEL"] = args.log_level.upper()
    
    print("🚀 Starting LeadVille Impact Bridge FastAPI Server...")
    print(f"📡 Server: http://{args.host}:{args.port}")
    print(f"📚 API Docs: http://{args.host}:{args.port}/v1/docs")
    print(f"❤️  Health Check: http://{args.host}:{args.port}/v1/health")
    print(f"📊 Metrics: http://{args.host}:{args.port}/v1/metrics")
    print()
    
    # Import and run the main function
    from src.impact_bridge.api.main import main as api_main
    api_main()

if __name__ == "__main__":
    main()