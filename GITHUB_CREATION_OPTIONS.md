# GitHub Issues Creation Guide

You have **two options** for creating the GitHub issues from our comprehensive project organization:

## Option 1: Manual Creation (Recommended for Learning)

### Step 1: Create Labels
Go to `https://github.com/J2WFFDev/LeadVille/labels` and create these labels:

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

### Step 3: Create Issues
Use the content from `ISSUES_TO_CREATE.md` - copy/paste each issue template into GitHub's new issue form.

## Option 2: Automated Creation (Faster)

### Prerequisites
1. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo` (full control)
   - Copy the token

### Run the Script
```powershell
# Set your GitHub token
$env:GITHUB_TOKEN = "your_token_here"

# Install required Python packages
pip install requests

# Run the creation script
python scripts/create_github_issues.py
```

The script will:
- ✅ Create all labels with proper colors
- ✅ Create all 4 milestones
- ✅ Create the first 5 critical issues with full templates

## What You'll Get

After either method, you'll have:
- **Complete label system** for organizing issues
- **4 project milestones** matching our development phases  
- **Detailed issues** with acceptance criteria and technical requirements
- **Proper cross-references** between related issues
- **Ready-to-use project board** for tracking progress

## Next Steps After Creation

1. **Set up Project Board**: Create a new project board and link it to your repository
2. **Prioritize Issues**: Review and adjust issue priorities based on current needs
3. **Assign Team Members**: If working with others, assign issues appropriately
4. **Start Development**: Begin with Phase 1 critical issues (Pi setup, database foundation)

## Recommendation

I suggest starting with **Option 1 (Manual)** for the first few issues so you understand the GitHub workflow, then using **Option 2 (Automated)** if you want to create all 21 issues quickly.

The manual approach helps you:
- Learn GitHub's project management features
- Customize issue content as needed
- Better understand the project structure
- Make adjustments during creation