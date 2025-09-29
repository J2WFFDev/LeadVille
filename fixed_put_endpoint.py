@app.put("/api/admin/bridge/config")
async def update_bridge_config(request: dict):
    """Update bridge config with MINIMAL schema - just MAC addresses for BLE connection"""
    try:
        import json
        from pathlib import Path
        
        # Validate request structure
        timer_address = request.get("timer")
        sensor_addresses = request.get("sensors", [])
        
        if not isinstance(sensor_addresses, list):
            return JSONResponse(
                content={"error": "sensors must be a list"},
                status_code=400
            )
        
        # MINIMAL SCHEMA - Bridge only needs MAC addresses for BLE
        bridge_config = {
            "timer": timer_address,      # Just MAC address string
            "sensors": sensor_addresses  # Just array of MAC address strings
        }
        
        # Write MINIMAL config for bridge
        config_file = Path("bridge_device_config.json")
        with open(config_file, 'w') as f:
            json.dump(bridge_config, f, indent=2)
        
        # Update DATABASE with full assignment info for stage/target tracking
        try:
            from src.impact_bridge.device_manager import device_manager
            
            # Update database with stage/target assignments
            for sensor_addr in sensor_addresses:
                # Update device_pool table with assignment info
                device_manager.update_device_assignment(sensor_addr, "assigned", "sensor")
            
            if timer_address:
                device_manager.update_device_assignment(timer_address, "assigned", "timer")
                
        except Exception as db_error:
            logger.warning(f"Database update failed (bridge config saved): {db_error}")
        
        # Return enriched response for API consumers
        paired_devices = device_manager.get_paired_devices()
        device_lookup = {device['address']: device for device in paired_devices}
        
        enriched_response = {
            "timer": {
                "address": timer_address,
                "status": "configured" if timer_address else "not_configured",
                "device_info": device_lookup.get(timer_address) if timer_address else None
            },
            "sensors": [
                {
                    "address": addr,
                    "device_info": device_lookup.get(addr),
                    "status": "paired" if device_lookup.get(addr) else "not_paired"
                }
                for addr in sensor_addresses
            ],
            "summary": {
                "timer_configured": bool(timer_address),
                "sensors_count": len(sensor_addresses),
                "sensors_paired": len([s for s in sensor_addresses if device_lookup.get(s)])
            }
        }
        
        logger.info(f"Bridge config updated: timer={timer_address}, sensors={len(sensor_addresses)} devices")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Bridge configuration updated",
            "config": enriched_response
        })
        
    except Exception as e:
        logger.error(f"Failed to update bridge config: {e}")
        return JSONResponse(
            content={"error": f"Failed to update bridge config: {str(e)}"},
            status_code=500
        )