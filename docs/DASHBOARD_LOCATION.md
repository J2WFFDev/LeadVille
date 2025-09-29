# Dashboard File Locations

## Active Dashboard

**Current Location (served by nginx):**
```
frontend/public/docs/dashboard/system_status_dashboard.html
```

**URL:** `http://192.168.1.125:5173/docs/dashboard/system_status_dashboard.html`

## Important Notes

- The main working dashboard is served from `frontend/public/docs/dashboard/` 
- This file connects to the API on port **8001**
- Any dashboard updates must be made to this location
- The `docs/dashboard/` directory contains backup/archive files only

## Deployment

To deploy dashboard changes:

```bash
# Copy to the correct location on Pi
scp system_status_dashboard.html jrwest@192.168.1.125:/home/jrwest/projects/LeadVille/frontend/public/docs/dashboard/

# Restart nginx if caching issues occur
ssh jrwest@192.168.1.125 "sudo systemctl restart nginx"
```

## Cleanup Completed

- ❌ Removed: `system_status_dashboard.html` (root directory duplicate)
- ❌ Removed: `docs/dashboard/system_status_dashboard.html` (unused Pi copy)
- ✅ Active: `frontend/public/docs/dashboard/system_status_dashboard.html` (production)