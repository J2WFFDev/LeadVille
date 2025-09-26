# Bridge Configuration Management Endpoints

@app.post("/api/admin/bridge/update_config")
async def update_bridge_config(config: dict):
    """Update the bridge device configuration file"""
    try:
        import json
        from pathlib import Path
        
        # Path to the bridge config file
        config_file = Path("bridge_device_config.json")
        
        # Validate the config structure
        if "timer" not in config or "sensors" not in config:
            return JSONResponse(
                content={"error": "Config must contain 'timer' and 'sensors' keys"},
                status_code=400
            )
        
        # Validate sensors is a list
        if not isinstance(config["sensors"], list):
            return JSONResponse(
                content={"error": "Sensors must be a list"},
                status_code=400
            )
        
        # Write the config file
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logging.info(f"Bridge config updated: timer={config['timer']}, sensors={len(config['sensors'])} devices")
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Bridge config updated with {len(config['sensors'])} sensor(s)",
            "config": config
        })
        
    except Exception as e:
        logging.error(f"Failed to update bridge config: {e}")
        return JSONResponse(
            content={"error": f"Failed to update bridge config: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/bridge/restart")
async def restart_bridge_service():
    """Restart the bridge service to reload configuration"""
    try:
        import subprocess
        
        logging.info("Attempting to restart leadville-bridge service")
        
        # Restart the systemd service
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "leadville-bridge"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logging.info("Bridge service restart initiated successfully")
            return JSONResponse(content={
                "status": "success",
                "message": "Bridge service restart initiated",
                "stdout": result.stdout,
                "stderr": result.stderr
            })
        else:
            logging.error(f"Failed to restart bridge service: {result.stderr}")
            return JSONResponse(
                content={
                    "error": "Failed to restart bridge service",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                },
                status_code=500
            )
        
    except subprocess.TimeoutExpired:
        logging.error("Bridge service restart timed out")
        return JSONResponse(
            content={"error": "Bridge service restart timed out"},
            status_code=500
        )
    except Exception as e:
        logging.error(f"Error restarting bridge service: {e}")
        return JSONResponse(
            content={"error": f"Failed to restart bridge service: {str(e)}"},
            status_code=500
        )

@app.get("/api/admin/bridge/config")
async def get_bridge_config():
    """Get the current bridge device configuration"""
    try:
        import json
        from pathlib import Path
        
        config_file = Path("bridge_device_config.json")
        
        if not config_file.exists():
            # Return default config
            default_config = {
                "timer": "60:09:C3:1F:DC:1A",
                "sensors": ["EA:18:3D:6D:BA:E5", "C2:1B:DB:F0:55:50"]
            }
            return JSONResponse(content={
                "status": "default",
                "config": default_config,
                "message": "Using default configuration (file not found)"
            })
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        return JSONResponse(content={
            "status": "loaded",
            "config": config,
            "message": "Configuration loaded from file"
        })
        
    except Exception as e:
        logging.error(f"Failed to get bridge config: {e}")
        return JSONResponse(
            content={"error": f"Failed to get bridge config: {str(e)}"},
            status_code=500
        )
