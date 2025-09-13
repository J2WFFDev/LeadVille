# GitHub Issues Creation Guide

You have **two options** for creating the comprehensive GitHub project setup for LeadVille Impact Bridge:

## Option 1: Automated Creation (Recommended) 🚀

### Quick Setup
```bash
# 1. Get your GitHub token
# Go to https://github.com/settings/tokens
# Create token with 'repo' scope

# 2. Set environment variable
export GITHUB_TOKEN="your_token_here"

# 3. Run the automation script
python scripts/create_github_issues.py
```

### What Gets Created Automatically
- ✅ **16 Labels** with proper colors and descriptions
- ✅ **4 Phase Milestones** matching project organization
- ✅ **21+ Comprehensive Issues** with full templates
- ✅ **Smart Duplicate Detection** (skips existing issues)
- ✅ **Complete Cross-references** between related issues

### Comprehensive Issue Set
The automation creates all issues from the PROJECT_ORGANIZATION.md plan:

#### Phase 1: Core Infrastructure (3 new + 2 existing)
- [x] Raspberry Pi Base System Setup (new - appears missing)
- [x] Database Foundation (existing #4)
- [x] FastAPI Backend Foundation (existing #5) 
- [ ] MQTT Internal Message Bus (new)
- [ ] Networking Modes (Online/Offline) (new)

#### Phase 2: BLE Integration (3 new + 2 existing)
- [x] WTVB01-BT50 Sensor Integration (existing #6)
- [x] AMG Labs Commander Timer Integration (existing #7)
- [ ] Pluggable Timer Driver Architecture (new)
- [ ] Device Pairing and Management (new)
- [ ] Time Synchronization System (new)

#### Phase 3: Web UI & Roles (7 new issues)
- [ ] Frontend Foundation (React + Vite + Tailwind)
- [ ] Authentication & Role-Based Access
- [ ] Admin Dashboard & System Monitoring
- [ ] Range Officer (RO) View
- [ ] Scorekeeper Interface
- [ ] Spectator & Coach Views
- [ ] WebSocket Real-time Updates

#### Phase 4: Production Ready (5 new issues)
- [ ] Boot Status Screen (Kiosk Mode)
- [ ] Simulation Mode & Testing Framework
- [ ] Data Export & Analytics
- [ ] Installation & Deployment System
- [ ] Monitoring & Observability

### Features
- **Duplicate Detection**: Won't create issues that already exist
- **Complete Templates**: Each issue has detailed acceptance criteria
- **Proper Labels**: Type, priority, component, and phase labels
- **Milestone Assignment**: All issues properly assigned to phases
- **Cross-references**: Issues reference related/blocking issues
- **Error Handling**: Robust error handling and progress reporting

## Option 2: Manual Creation

### Step 1: Create Labels
Go to `https://github.com/J2WFFDev/LeadVille/labels` and create:

**Type Labels:**
- `epic` (Red) - Large multi-issue features
- `feature` (Blue) - New functionality  
- `enhancement` (Light Blue) - Improvements
- `bug` (Orange) - Something isn't working
- `documentation` (Dark Blue) - Documentation updates

**Priority Labels:**
- `critical` (Red) - Blocks other work
- `high` (Orange) - Important for milestone
- `medium` (Yellow) - Standard priority
- `low` (Green) - Nice to have

**Component Labels:**
- `backend` (Purple) - FastAPI, database, APIs
- `frontend` (Blue) - React UI components
- `ble` (Light Green) - Bluetooth device integration
- `infrastructure` (Light Orange) - System setup, networking
- `database` (Light Yellow) - SQLite, migrations

**Phase Labels:**
- `phase-1` (Light Red) - Core Infrastructure
- `phase-2` (Light Orange) - BLE Integration  
- `phase-3` (Light Yellow) - Web UI & Roles
- `phase-4` (Light Green) - Production Features

### Step 2: Create Milestones
Go to `https://github.com/J2WFFDev/LeadVille/milestones` and create:

1. **Phase 1: Core Infrastructure** - Foundation systems: Pi setup, database, FastAPI, MQTT, networking
2. **Phase 2: BLE Integration** - Device connectivity: WTVB01-BT50 sensors, AMG Commander timer
3. **Phase 3: Web UI & Roles** - User interfaces: React frontend, authentication, dashboards
4. **Phase 4: Production Ready** - Production features: kiosk mode, simulation, exports

### Step 3: Create Issues Manually
Use the templates from `.github/ISSUES_TO_CREATE.md` for the first 5 issues, then refer to the comprehensive descriptions in `scripts/create_github_issues.py` for all Phase 3 and Phase 4 issues.

## Validation & Testing

Before running the automation, you can validate it:

```bash
# Test the script configuration
python scripts/test_issues_creation.py
```

This validates:
- Label configuration
- Milestone setup
- Issue template structure
- Cross-reference validity
- Phase distribution

## What You'll Get

After either method, you'll have:
- **Complete project structure** with proper organization
- **Comprehensive issue set** covering all development phases
- **Professional labeling system** for easy filtering and organization
- **Milestone tracking** for sprint and release planning
- **Ready-to-use project board** structure

## Next Steps After Creation

1. **Create Project Board**: Set up GitHub Projects for sprint planning
2. **Prioritize Issues**: Review and adjust issue priorities
3. **Assign Team Members**: Distribute work appropriately  
4. **Start Development**: Begin with Phase 1 critical issues

## Recommended Workflow

**Sprint Planning (2-week sprints):**
- Sprint 1-2: Phase 1 foundation issues
- Sprint 3-4: Phase 2 BLE integration
- Sprint 5-7: Phase 3 UI development
- Sprint 8-9: Phase 4 production features

## Troubleshooting

See `scripts/README.md` for detailed troubleshooting guide covering:
- GitHub token issues
- Network connectivity problems
- Permission errors
- Validation failures

## Why Choose Automated Creation?

The automated approach ensures:
- ✅ **Consistency** - All issues follow the same high-quality template
- ✅ **Completeness** - Nothing is missed from the comprehensive plan
- ✅ **Accuracy** - Proper cross-references and milestone assignments
- ✅ **Speed** - Create 20+ issues in under a minute
- ✅ **Maintenance** - Easy to update and re-run as project evolves

The manual approach is better for:
- Learning GitHub project management features
- Customizing individual issue content
- Working without API access
- Small, incremental issue creation