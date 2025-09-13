# LeadVille GitHub Issues Automation

This directory contains automation scripts for setting up the complete LeadVille GitHub project with all issues, labels, and milestones from the PROJECT_ORGANIZATION.md plan.

## Quick Start

### Prerequisites
1. **GitHub Personal Access Token**: 
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo` (full control of private repositories)
   - Copy the generated token

2. **Python Environment**:
   ```bash
   pip install requests
   ```

### Automated Creation (Recommended)

```bash
# Set your GitHub token
export GITHUB_TOKEN="your_token_here"

# Run the comprehensive creation script
python scripts/create_github_issues.py
```

This will automatically create:
- ✅ **16 Labels** (type, priority, component, phase)
- ✅ **4 Milestones** (Phase 1-4)
- ✅ **18+ Issues** with full templates and cross-references

## What Gets Created

### Labels
- **Type**: `epic`, `feature`, `enhancement`, `bug`, `documentation`
- **Priority**: `critical`, `high`, `medium`, `low`  
- **Component**: `backend`, `frontend`, `ble`, `infrastructure`, `database`
- **Phase**: `phase-1`, `phase-2`, `phase-3`, `phase-4`

### Milestones
1. **Phase 1: Core Infrastructure** - Pi setup, database, FastAPI, MQTT, networking
2. **Phase 2: BLE Integration** - WTVB01-BT50 sensors, AMG Commander timer, device management
3. **Phase 3: Web UI & Roles** - React frontend, authentication, role-based dashboards
4. **Phase 4: Production Ready** - Kiosk mode, simulation, exports, deployment tools

### Issues by Phase

#### Phase 1: Core Infrastructure (6 issues)
- Raspberry Pi Base System Setup
- Database Foundation (SQLite + SQLAlchemy)
- FastAPI Backend Foundation
- MQTT Internal Message Bus
- Networking Modes (Online/Offline)

#### Phase 2: BLE Integration (5 issues)
- WTVB01-BT50 Sensor Integration *(already exists)*
- AMG Labs Commander Timer Integration *(already exists)*
- Pluggable Timer Driver Architecture
- Device Pairing and Management
- Time Synchronization System

#### Phase 3: Web UI & Roles (7 issues)
- Frontend Foundation (React + Vite + Tailwind)
- Authentication & Role-Based Access
- Admin Dashboard & System Monitoring
- Range Officer (RO) View
- Scorekeeper Interface
- Spectator & Coach Views
- WebSocket Real-time Updates

#### Phase 4: Production Ready (5 issues)
- Boot Status Screen (Kiosk Mode)
- Simulation Mode & Testing Framework
- Data Export & Analytics
- Installation & Deployment System
- Monitoring & Observability

## Script Features

### Smart Duplicate Detection
- ✅ Checks existing issues to avoid duplicates
- ✅ Skips issues that already exist
- ✅ Reports creation summary

### Complete Templates
- ✅ Full issue descriptions with acceptance criteria
- ✅ Technical requirements and implementation notes
- ✅ Proper cross-references between related issues
- ✅ Phase assignments and milestone linking

### Error Handling
- ✅ Network error recovery
- ✅ Token validation
- ✅ Detailed error reporting
- ✅ Progress tracking

## Manual Alternative

If you prefer to create issues manually:

1. **Create Labels**: Use the GitHub UI to create all labels listed above
2. **Create Milestones**: Add the 4 phase milestones 
3. **Create Issues**: Copy templates from `ISSUES_TO_CREATE.md` and the enhanced descriptions in this script

## Troubleshooting

### Common Issues

**"403 Forbidden" Error**:
- Verify your GitHub token has `repo` scope
- Check that you have write access to the repository

**"422 Unprocessable Entity"**:
- Usually means label/milestone already exists (this is normal)
- Check issue body formatting if it fails on issue creation

**Network Errors**:
- Check internet connection
- Verify GitHub API is accessible from your network

### Validation

After running the script, verify:
1. Visit https://github.com/J2WFFDev/LeadVille/issues
2. Check that all phases have appropriate issue counts
3. Verify labels and milestones are properly assigned
4. Review cross-references between issues

## Next Steps

After creating issues:

1. **Create Project Board**: Set up GitHub Projects for sprint planning
2. **Prioritize Issues**: Review and adjust priorities based on current needs
3. **Assign Team Members**: Distribute work across the team
4. **Start Development**: Begin with Phase 1 critical infrastructure issues

## Development Workflow

Recommended 2-week sprint structure:
- **Sprint 1-2**: Phase 1 foundation (Issues #1-5)
- **Sprint 3-4**: Phase 2 BLE integration
- **Sprint 5-7**: Phase 3 UI development  
- **Sprint 8-9**: Phase 4 production features

Each issue includes detailed acceptance criteria and implementation notes to guide development.