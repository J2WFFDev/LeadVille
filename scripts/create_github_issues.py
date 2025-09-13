#!/usr/bin/env python3
"""
GitHub Issues Creator for LeadVille Impact Bridge
Creates all issues from PROJECT_ORGANIZATION.md via GitHub API
"""

import requests
import json
import os
from typing import List, Dict

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Set this as environment variable
REPO_OWNER = 'J2WFFDev'
REPO_NAME = 'LeadVille'
BASE_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}'

def create_labels():
    """Create all necessary labels for the project"""
    labels = [
        # Type Labels
        {'name': 'epic', 'color': 'B60205', 'description': 'Large multi-issue features'},
        {'name': 'feature', 'color': '0052CC', 'description': 'New functionality'},
        {'name': 'enhancement', 'color': 'A2EEEF', 'description': 'Improvements to existing features'},
        {'name': 'bug', 'color': 'D93F0B', 'description': 'Something isn\'t working'},
        {'name': 'documentation', 'color': '0075CA', 'description': 'Documentation updates'},
        
        # Priority Labels
        {'name': 'critical', 'color': 'B60205', 'description': 'Blocks other work or system unusable'},
        {'name': 'high', 'color': 'D93F0B', 'description': 'Important for milestone completion'},
        {'name': 'medium', 'color': 'FBCA04', 'description': 'Standard priority'},
        {'name': 'low', 'color': '0E8A16', 'description': 'Nice to have, future consideration'},
        
        # Component Labels
        {'name': 'backend', 'color': '5319E7', 'description': 'FastAPI, database, APIs'},
        {'name': 'frontend', 'color': '1D76DB', 'description': 'React UI components'},
        {'name': 'ble', 'color': 'C2E0C6', 'description': 'Bluetooth device integration'},
        {'name': 'infrastructure', 'color': 'F9D0C4', 'description': 'System setup, networking, services'},
        {'name': 'database', 'color': 'FEF2C0', 'description': 'SQLite, migrations, data models'},
        
        # Phase Labels
        {'name': 'phase-1', 'color': 'E99695', 'description': 'Core Infrastructure'},
        {'name': 'phase-2', 'color': 'F9D0C4', 'description': 'BLE Integration'},
        {'name': 'phase-3', 'color': 'FEF2C0', 'description': 'Web UI & Roles'},
        {'name': 'phase-4', 'color': 'C2E0C6', 'description': 'Production Features'}
    ]
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    for label in labels:
        response = requests.post(
            f'{BASE_URL}/labels',
            headers=headers,
            json=label
        )
        if response.status_code == 201:
            print(f"✓ Created label: {label['name']}")
        elif response.status_code == 422:
            print(f"- Label already exists: {label['name']}")
        else:
            print(f"✗ Failed to create label {label['name']}: {response.status_code}")

def create_milestones():
    """Create project milestones"""
    milestones = [
        {
            'title': 'Phase 1: Core Infrastructure',
            'description': 'Foundation systems: Pi setup, database, FastAPI, MQTT, networking',
            'state': 'open'
        },
        {
            'title': 'Phase 2: BLE Integration', 
            'description': 'Device connectivity: WTVB01-BT50 sensors, AMG Commander timer, multi-vendor support',
            'state': 'open'
        },
        {
            'title': 'Phase 3: Web UI & Roles',
            'description': 'User interfaces: React frontend, authentication, role-based dashboards', 
            'state': 'open'
        },
        {
            'title': 'Phase 4: Production Ready',
            'description': 'Production features: kiosk mode, simulation, exports, deployment',
            'state': 'open'
        }
    ]
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    milestone_numbers = {}
    for milestone in milestones:
        response = requests.post(
            f'{BASE_URL}/milestones',
            headers=headers,
            json=milestone
        )
        if response.status_code == 201:
            milestone_data = response.json()
            milestone_numbers[milestone['title']] = milestone_data['number']
            print(f"✓ Created milestone: {milestone['title']}")
        else:
            print(f"✗ Failed to create milestone {milestone['title']}: {response.status_code}")
    
    return milestone_numbers

def create_issues(milestone_numbers: Dict[str, int]):
    """Create all GitHub issues"""
    # Phase 1 Issues
    phase1_issues = [
        {
            'title': '[FEATURE] Raspberry Pi Base System Setup',
            'body': '''## Feature Description
Set up the foundational Raspberry Pi system with all required packages, systemd services framework, and auto-startup configuration for LeadVille Impact Bridge.

## User Story
As a System Administrator, I want the Raspberry Pi to automatically boot and run LeadVille services so that the impact sensor system is ready for use without manual intervention.

## Acceptance Criteria
- [ ] Raspberry Pi OS configured with required packages (Python 3.11, pip, git, etc.)
- [ ] Systemd service framework created for LeadVille components
- [ ] Auto-startup configuration working (services start on boot)
- [ ] Basic system logging configured (journald integration)
- [ ] System health monitoring basics in place
- [ ] Documentation for Pi setup process

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5
- [ ] SD card (32GB+ recommended)
- [ ] Network connectivity (Wi-Fi/Ethernet)

### System Integration
- [ ] systemd service units
- [ ] Python virtual environment setup
- [ ] Log rotation configuration
- [ ] Basic security hardening

## Implementation Notes
- Use Raspberry Pi OS (Debian-based)
- Create dedicated user for LeadVille services
- Set up proper file permissions and service isolation
- Include watchdog configuration for reliability''',
            'labels': ['feature', 'critical', 'infrastructure', 'phase-1'],
            'milestone': milestone_numbers.get('Phase 1: Core Infrastructure')
        },
        {
            'title': '[FEATURE] Database Foundation with SQLite and SQLAlchemy ORM',
            'body': '''## Feature Description
Implement the core database system using SQLite with WAL mode, SQLAlchemy ORM, and Alembic migrations to support all LeadVille data storage requirements.

## User Story
As a Developer, I want a robust, zero-maintenance database system so that sensor data, timer events, and match information are reliably stored and easily accessible.

## Acceptance Criteria
- [ ] SQLite database configured with WAL (Write-Ahead Logging) mode
- [ ] SQLAlchemy ORM models created for all entities
- [ ] Alembic migration system configured
- [ ] Database connection pooling and optimization
- [ ] Basic CRUD operations tested
- [ ] Data integrity constraints implemented

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5 (sufficient storage on SD card)

### System Integration
- [ ] SQLAlchemy Core and ORM setup
- [ ] Alembic migrations configured
- [ ] Connection string management
- [ ] Transaction handling patterns
- [ ] Error handling and logging''',
            'labels': ['feature', 'critical', 'database', 'backend', 'phase-1'],
            'milestone': milestone_numbers.get('Phase 1: Core Infrastructure')
        }
        # Add more issues as needed...
    ]
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    for issue in phase1_issues:
        response = requests.post(
            f'{BASE_URL}/issues',
            headers=headers,
            json=issue
        )
        if response.status_code == 201:
            issue_data = response.json()
            print(f"✓ Created issue #{issue_data['number']}: {issue['title']}")
        else:
            print(f"✗ Failed to create issue {issue['title']}: {response.status_code}")

def main():
    """Main execution function"""
    if not GITHUB_TOKEN:
        print("❌ Please set GITHUB_TOKEN environment variable")
        print("   Create a personal access token at: https://github.com/settings/tokens")
        print("   Required scopes: repo, issues")
        return
    
    print("🚀 Creating LeadVille GitHub Issues...")
    print("=" * 50)
    
    print("\n📋 Creating Labels...")
    create_labels()
    
    print("\n🎯 Creating Milestones...")
    milestone_numbers = create_milestones()
    
    print("\n📝 Creating Issues...")
    create_issues(milestone_numbers)
    
    print("\n✅ GitHub setup complete!")
    print(f"   Visit: https://github.com/{REPO_OWNER}/{REPO_NAME}/issues")

if __name__ == '__main__':
    main()