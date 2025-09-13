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

def get_existing_issues():
    """Get existing issues to avoid duplicates"""
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    existing_titles = set()
    page = 1
    while True:
        response = requests.get(
            f'{BASE_URL}/issues',
            headers=headers,
            params={'page': page, 'per_page': 100, 'state': 'all'}
        )
        if response.status_code == 200:
            issues = response.json()
            if not issues:  # No more issues
                break
            for issue in issues:
                existing_titles.add(issue['title'])
            page += 1
        else:
            print(f"Warning: Failed to fetch existing issues: {response.status_code}")
            break
    
    return existing_titles

def create_issues(milestone_numbers: Dict[str, int]):
    """Create all GitHub issues from PROJECT_ORGANIZATION.md"""
    
    # Get existing issues to avoid duplicates
    print("Checking existing issues...")
    existing_titles = get_existing_issues()
    print(f"Found {len(existing_titles)} existing issues")
    
    all_issues = []
    
    # Phase 1: Core Infrastructure Issues
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
- Include watchdog configuration for reliability

## Related Issues
- Blocks all Phase 1 issues
- Foundation for Issues #2-5

## Phase/Milestone
- [x] Phase 1: Core Infrastructure''',
            'labels': ['feature', 'critical', 'infrastructure', 'phase-1'],
            'milestone': milestone_numbers.get('Phase 1: Core Infrastructure')
        },
        {
            'title': '[FEATURE] MQTT Internal Message Bus',
            'body': '''## Feature Description
Set up internal MQTT message bus with mosquitto broker for real-time communication between LeadVille system components.

## User Story
As a Developer, I want a reliable message bus system so that sensor data, timer events, and system status can be communicated between services in real-time.

## Acceptance Criteria
- [ ] Mosquitto MQTT broker installed and configured
- [ ] MQTT topics designed and documented:
  - [ ] `bridge/status` - System status updates
  - [ ] `sensor/{id}/telemetry` - Sensor data streams
  - [ ] `timer/events` - Timer event notifications
  - [ ] `run/{id}/events` - Run-specific events
- [ ] Python MQTT client wrapper implemented
- [ ] MQTT service monitoring and health checks
- [ ] Message persistence configuration
- [ ] Security configuration (authentication/authorization)

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5

### System Integration
- [ ] Mosquitto broker systemd service
- [ ] Python paho-mqtt client integration
- [ ] Message schema validation
- [ ] Error handling and reconnection logic
- [ ] Monitoring and logging

## Implementation Notes
- Use mosquitto for lightweight, reliable messaging
- Implement QoS levels appropriate for message types
- Add message retention for critical status updates
- Design for future clustering/HA if needed

## Related Issues
- Depends on: #1 (Pi Base System)
- Blocks: #6 (WTVB01-BT50), #7 (AMG Timer)
- Related to: All real-time communication

## Phase/Milestone
- [x] Phase 1: Core Infrastructure''',
            'labels': ['feature', 'critical', 'backend', 'infrastructure', 'phase-1'],
            'milestone': milestone_numbers.get('Phase 1: Core Infrastructure')
        },
        {
            'title': '[FEATURE] Networking Modes (Online/Offline)',
            'body': '''## Feature Description
Implement dual networking modes with AP mode (offline) and client mode (online) switching capabilities.

## User Story
As a Range Officer, I want the system to work both with existing Wi-Fi networks and as a standalone access point so that LeadVille can operate in any network environment.

## Acceptance Criteria
- [ ] Hostapd + dnsmasq configured for AP mode
- [ ] Captive portal redirecting to `bridge.local`
- [ ] Network mode switching API endpoint
- [ ] Nginx reverse proxy configuration
- [ ] Network status monitoring
- [ ] Automatic fallback to AP mode if client connection fails

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5 with Wi-Fi capability

### System Integration
- [ ] hostapd access point configuration
- [ ] dnsmasq DHCP/DNS server
- [ ] nginx reverse proxy setup
- [ ] NetworkManager integration
- [ ] Captive portal web interface

## Implementation Notes
- Default to AP mode on first boot
- Provide web interface for network configuration
- Implement network health monitoring
- Add LED indicators for network status

## Related Issues
- Depends on: #3 (FastAPI Backend)
- Enables: Remote access and local operation
- Related to: All web interface development

## Phase/Milestone
- [x] Phase 1: Core Infrastructure''',
            'labels': ['feature', 'critical', 'infrastructure', 'phase-1'],
            'milestone': milestone_numbers.get('Phase 1: Core Infrastructure')
        }
    ]

    # Phase 2: BLE Integration Issues (additional ones beyond existing #6, #7)
    phase2_issues = [
        {
            'title': '[FEATURE] Pluggable Timer Driver Architecture',
            'body': '''## Feature Description
Create abstract timer driver interface supporting multiple timer vendors with AMG Labs Commander as reference implementation.

## User Story
As a Developer, I want a flexible timer driver system so that LeadVille can support multiple timer brands and models without core system changes.

## Acceptance Criteria
- [ ] Abstract timer driver interface created
- [ ] AMG Labs Commander driver implemented
- [ ] SpecialPie timer driver placeholder created
- [ ] Timer vendor selection in Admin UI
- [ ] Driver registration and discovery system
- [ ] Common timer event schema
- [ ] Driver configuration management

## Technical Requirements
### Hardware Dependencies
- [x] Various BLE shot timers (AMG, SpecialPie, etc.)
- [x] Raspberry Pi 4/5 with BLE capability

### System Integration
- [ ] Abstract base class for timer drivers
- [ ] Plugin discovery mechanism
- [ ] Configuration schema validation
- [ ] Event normalization layer
- [ ] Health monitoring interface

## Implementation Notes
- Use factory pattern for driver instantiation
- Implement common BLE connection handling
- Add driver simulation capabilities for testing
- Design for hot-swapping timer types

## Related Issues
- Depends on: #7 (AMG Commander Timer)
- Enables: Multi-vendor timer support
- Related to: Admin UI timer selection

## Phase/Milestone
- [x] Phase 2: BLE Integration''',
            'labels': ['feature', 'high', 'ble', 'backend', 'phase-2'],
            'milestone': milestone_numbers.get('Phase 2: BLE Integration')
        },
        {
            'title': '[FEATURE] Device Pairing and Management',
            'body': '''## Feature Description
Implement BLE device discovery, pairing, assignment to targets/stages, and comprehensive device management.

## User Story
As a Range Officer, I want to easily pair and assign sensors and timers to specific targets and stages so that the system knows which device corresponds to which target.

## Acceptance Criteria
- [ ] BLE device discovery and scanning
- [ ] Device pairing and authentication
- [ ] Device assignment to targets/stages
- [ ] Device configuration APIs (`/api/admin/devices`)
- [ ] Device health monitoring and alerts
- [ ] Battery level tracking and warnings
- [ ] Signal quality monitoring (RSSI)
- [ ] Device firmware version tracking

## Technical Requirements
### Hardware Dependencies
- [x] WTVB01-BT50 sensors
- [x] AMG Labs Commander timer
- [x] Raspberry Pi 4/5 with BLE capability

### System Integration
- [ ] Device discovery service
- [ ] Database device registry
- [ ] FastAPI device management endpoints
- [ ] WebSocket device status updates
- [ ] Device assignment validation

## Implementation Notes
- Implement device fingerprinting for auto-recognition
- Add device testing and calibration workflows
- Include device replacement procedures
- Design for multi-stage match configurations

## Related Issues
- Depends on: #6 (WTVB01-BT50), #7 (AMG Timer)
- Enables: Match setup and configuration
- Related to: Admin UI device management

## Phase/Milestone
- [x] Phase 2: BLE Integration''',
            'labels': ['feature', 'high', 'ble', 'backend', 'phase-2'],
            'milestone': milestone_numbers.get('Phase 2: BLE Integration')
        },
        {
            'title': '[FEATURE] Time Synchronization System',
            'body': '''## Feature Description
Implement time synchronization protocol for sensors and timers with drift monitoring and correction.

## User Story
As a Range Officer, I want all devices synchronized to a common time reference so that shot detection and timer events can be accurately correlated.

## Acceptance Criteria
- [ ] Time sync protocol for sensors and timers
- [ ] Drift monitoring and detection
- [ ] Periodic resync (configurable interval, ±20ms drift detection)
- [ ] NTP client for Pi time synchronization
- [ ] Clock offset calculation and correction
- [ ] Time sync status monitoring
- [ ] Drift metrics in Admin UI

## Technical Requirements
### Hardware Dependencies
- [x] WTVB01-BT50 sensors
- [x] AMG Labs Commander timer
- [x] Raspberry Pi 4/5 with network/BLE

### System Integration
- [ ] NTP client configuration
- [ ] BLE time sync protocol
- [ ] Drift calculation algorithms
- [ ] Database time offset storage
- [ ] Real-time sync monitoring

## Implementation Notes
- Use NTP for Pi system time accuracy
- Implement device-specific sync protocols
- Add visual indicators for sync status
- Include manual sync triggers for troubleshooting

## Related Issues
- Depends on: #6 (WTVB01-BT50), #7 (AMG Timer)
- Critical for: Shot-to-impact correlation
- Related to: System monitoring dashboard

## Phase/Milestone
- [x] Phase 2: BLE Integration''',
            'labels': ['feature', 'high', 'ble', 'backend', 'phase-2'],
            'milestone': milestone_numbers.get('Phase 2: BLE Integration')
        }
    ]

    # Phase 3: Web UI & Role Management Issues
    phase3_issues = [
        {
            'title': '[FEATURE] Frontend Foundation (React + Vite + Tailwind)',
            'body': '''## Feature Description
Set up modern React frontend with Vite build system and Tailwind CSS for responsive, kiosk-friendly user interfaces.

## User Story
As a Developer, I want a modern, fast frontend development environment so that I can build responsive user interfaces efficiently for all LeadVille roles.

## Acceptance Criteria
- [ ] React + Vite + TypeScript setup
- [ ] Tailwind CSS configured for responsive design
- [ ] Kiosk-friendly design patterns
- [ ] Routing and layout components
- [ ] WebSocket client for real-time updates
- [ ] Build and deployment pipeline
- [ ] Hot module replacement for development

## Technical Requirements
### Hardware Dependencies
- [x] Any modern browser (Chromium-based recommended)

### System Integration
- [ ] Vite build configuration
- [ ] TypeScript configuration
- [ ] Tailwind CSS setup
- [ ] React Router for navigation
- [ ] WebSocket client library
- [ ] Production build optimization

## Implementation Notes
- Design for touch-friendly interactions
- Implement responsive breakpoints for various screen sizes
- Add dark/light theme support
- Optimize for kiosk display permanence

## Related Issues
- Enables: All Phase 3 UI development
- Foundation for: RO, Admin, Scorekeeper UIs
- Related to: WebSocket real-time updates

## Phase/Milestone
- [x] Phase 3: Web UI & Roles''',
            'labels': ['feature', 'critical', 'frontend', 'phase-3'],
            'milestone': milestone_numbers.get('Phase 3: Web UI & Roles')
        },
        {
            'title': '[FEATURE] Authentication & Role-Based Access',
            'body': '''## Feature Description
Implement JWT authentication with refresh tokens and comprehensive role-based access control system.

## User Story
As a System Administrator, I want secure role-based access so that different users (admin, RO, scorekeeper, etc.) can only access appropriate system functions.

## Acceptance Criteria
- [ ] JWT authentication with refresh tokens
- [ ] Role system: `admin`, `ro`, `scorekeeper`, `viewer`, `coach`
- [ ] Login/logout flows with secure session management
- [ ] CSRF protection for unsafe methods
- [ ] Role-based route protection
- [ ] Permission middleware for API endpoints
- [ ] Session timeout and renewal

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5 web server

### System Integration
- [ ] JWT token generation and validation
- [ ] Secure session storage
- [ ] Role-based middleware
- [ ] Frontend route guards
- [ ] API endpoint protection
- [ ] CSRF token handling

## Implementation Notes
- Use secure HTTP-only cookies for tokens
- Implement automatic token refresh
- Add role inheritance (admin > ro > scorekeeper > viewer)
- Design for future LDAP/SSO integration

## Related Issues
- Depends on: Previous phase infrastructure
- Blocks: All role-specific UI development
- Related to: All secure API endpoints

## Phase/Milestone
- [x] Phase 3: Web UI & Roles''',
            'labels': ['feature', 'critical', 'frontend', 'backend', 'phase-3'],
            'milestone': milestone_numbers.get('Phase 3: Web UI & Roles')
        },
        {
            'title': '[FEATURE] Admin Dashboard & System Monitoring',
            'body': '''## Feature Description
Create comprehensive Admin dashboard for node management, network configuration, and system monitoring.

## User Story
As a System Administrator, I want a comprehensive admin dashboard so that I can monitor system health, configure settings, and troubleshoot issues.

## Acceptance Criteria
- [ ] Node management interface (`/api/admin/node`)
- [ ] Network configuration (Online/Offline switching)
- [ ] System monitoring: CPU/temp/disk usage
- [ ] Service health indicators (BLE, MQTT, DB)
- [ ] Real-time log tail viewer (last 200 lines, autoscroll)
- [ ] Device management and pairing interface
- [ ] Configuration management UI

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5 admin access

### System Integration
- [ ] System metrics collection
- [ ] Log streaming endpoints
- [ ] Configuration API endpoints
- [ ] Real-time monitoring dashboard
- [ ] Network management integration
- [ ] Service control interfaces

## Implementation Notes
- Use WebSocket for real-time metrics
- Implement log filtering and search
- Add system backup/restore features
- Include diagnostic tools and health checks

## Related Issues
- Depends on: Authentication & Frontend Foundation
- Enables: Complete system administration
- Related to: All system monitoring needs

## Phase/Milestone
- [x] Phase 3: Web UI & Roles''',
            'labels': ['feature', 'critical', 'frontend', 'backend', 'phase-3'],
            'milestone': milestone_numbers.get('Phase 3: Web UI & Roles')
        },
        {
            'title': '[FEATURE] Range Officer (RO) View',
            'body': '''## Feature Description
Create visual Range Officer interface with stage layout, target status, live hit markers, and match management.

## User Story
As a Range Officer, I want a visual dashboard showing target status and live impacts so that I can monitor match progress and quickly identify any issues.

## Acceptance Criteria
- [ ] Visual stage layout with SVG/Canvas
- [ ] Per-target status badges (OK/Degraded/Offline)
- [ ] Live hit markers and impact visualization
- [ ] Last-string summary panel with timestamps
- [ ] History sidebar for prior strings review
- [ ] Match control buttons (start/stop/pause)
- [ ] Alert notifications for system issues

## Technical Requirements
### Hardware Dependencies
- [x] Touch-capable display (recommended)

### System Integration
- [ ] Stage layout configuration
- [ ] Real-time sensor event display
- [ ] Timer event integration
- [ ] Match state management
- [ ] WebSocket event streaming
- [ ] Alert system integration

## Implementation Notes
- Design for rapid visual assessment
- Use color coding for status indicators
- Implement touch-friendly controls
- Add audio alerts for critical events

## Related Issues
- Depends on: Authentication & Frontend Foundation
- Requires: Phase 2 BLE integration
- Critical for: Match operations

## Phase/Milestone
- [x] Phase 3: Web UI & Roles''',
            'labels': ['feature', 'critical', 'frontend', 'phase-3'],
            'milestone': milestone_numbers.get('Phase 3: Web UI & Roles')
        },
        {
            'title': '[FEATURE] Scorekeeper Interface',
            'body': '''## Feature Description
Build tabular scorekeeper interface with runs management, timer alignment validation, and audit trail.

## User Story
As a Scorekeeper, I want a detailed interface for managing run data so that I can validate timing, make corrections, and maintain accurate match records.

## Acceptance Criteria
- [ ] Tabular runs view with filtering (stage/squad)
- [ ] Timer alignment validation with bounded edits
- [ ] Audit trail for data corrections
- [ ] Export functionality (CSV, NDJSON)
- [ ] Run annotation and notes system
- [ ] Batch operations for common tasks
- [ ] Data validation and error highlighting

## Technical Requirements
### Hardware Dependencies
- [x] Keyboard/mouse interface preferred

### System Integration
- [ ] Runs database queries and filtering
- [ ] Timer event correlation display
- [ ] Audit logging system
- [ ] Data export endpoints
- [ ] Validation rule engine
- [ ] Batch operation APIs

## Implementation Notes
- Implement spreadsheet-like interface for efficiency
- Add keyboard shortcuts for common operations
- Include data validation rules and warnings
- Design for rapid data entry and correction

## Related Issues
- Depends on: Authentication & Frontend Foundation
- Requires: Complete data model (Phase 1)
- Critical for: Match data accuracy

## Phase/Milestone
- [x] Phase 3: Web UI & Roles''',
            'labels': ['feature', 'high', 'frontend', 'phase-3'],
            'milestone': milestone_numbers.get('Phase 3: Web UI & Roles')
        },
        {
            'title': '[FEATURE] Spectator & Coach Views',
            'body': '''## Feature Description
Create read-only spectator dashboard and coach interface with notes, bookmarks, and privacy controls.

## User Story
As a Coach, I want to view match progress and add private notes so that I can analyze performance and provide feedback without interfering with match operations.

## Acceptance Criteria
- [ ] Read-only spectator dashboard with privacy toggle
- [ ] Coach notes interface with per-run annotations
- [ ] Bookmark functionality for key moments
- [ ] Coach notes export and sharing
- [ ] Spectator-friendly live display
- [ ] Privacy controls for sensitive data
- [ ] Historical match review capabilities

## Technical Requirements
### Hardware Dependencies
- [x] Any device with modern browser

### System Integration
- [ ] Read-only data access layers
- [ ] Notes database schema
- [ ] Privacy filtering system
- [ ] Export and sharing endpoints
- [ ] Live match data streaming
- [ ] Historical data queries

## Implementation Notes
- Design for minimal system impact
- Implement granular privacy controls
- Add note sharing and collaboration features
- Optimize for mobile viewing

## Related Issues
- Depends on: Authentication & Frontend Foundation
- Enables: Spectator and coaching functionality
- Related to: Match data display systems

## Phase/Milestone
- [x] Phase 3: Web UI & Roles''',
            'labels': ['feature', 'medium', 'frontend', 'phase-3'],
            'milestone': milestone_numbers.get('Phase 3: Web UI & Roles')
        },
        {
            'title': '[FEATURE] WebSocket Real-time Updates',
            'body': '''## Feature Description
Implement WebSocket endpoint for real-time updates with <150ms end-to-end latency for live match monitoring.

## User Story
As any User, I want real-time updates in the web interface so that I can see live match progress without manual refresh.

## Acceptance Criteria
- [ ] WebSocket endpoint (`/ws/live`) implementation
- [ ] Real-time event types: `status`, `sensor_event`, `timer_event`, `run_update`
- [ ] Client-side WebSocket reconnection handling
- [ ] <150ms end-to-end UI update latency
- [ ] Event filtering by user role and permissions
- [ ] Connection health monitoring
- [ ] Graceful degradation for connection issues

## Technical Requirements
### Hardware Dependencies
- [x] Stable network connection

### System Integration
- [ ] FastAPI WebSocket support
- [ ] MQTT to WebSocket bridge
- [ ] Event filtering and routing
- [ ] Client connection management
- [ ] Performance monitoring
- [ ] Error handling and recovery

## Implementation Notes
- Use WebSocket for bi-directional communication
- Implement client-side retry logic with exponential backoff
- Add connection quality indicators
- Optimize message payload sizes for performance

## Related Issues
- Depends on: Frontend Foundation & MQTT Message Bus
- Critical for: All real-time UI functionality
- Related to: All role-based interfaces

## Phase/Milestone
- [x] Phase 3: Web UI & Roles''',
            'labels': ['feature', 'critical', 'frontend', 'backend', 'phase-3'],
            'milestone': milestone_numbers.get('Phase 3: Web UI & Roles')
        }
    ]

    # Phase 4: Production Features
    phase4_issues = [
        {
            'title': '[FEATURE] Boot Status Screen (Kiosk Mode)',
            'body': '''## Feature Description
Create fullscreen boot status display with system information, service status, and auto-refresh for kiosk deployment.

## User Story
As a Range Officer, I want to see system status immediately on boot so that I can verify all services are running before starting a match.

## Acceptance Criteria
- [ ] Fullscreen on-boot status display
- [ ] Node name, network mode, SSID, IPs (v4/v6)
- [ ] Service status LEDs (green/yellow/red)
- [ ] Last 20 log lines display
- [ ] 2-second auto-refresh without login prompt
- [ ] Touch/click to enter full interface
- [ ] Boot progress indicator

## Technical Requirements
### Hardware Dependencies
- [x] Display capable of fullscreen (touchscreen preferred)

### System Integration
- [ ] Boot-time service startup
- [ ] System information gathering
- [ ] Service health monitoring
- [ ] Log tail display
- [ ] Kiosk mode browser setup
- [ ] Auto-refresh mechanism

## Implementation Notes
- Launch automatically after system services
- Use large, readable fonts for distance viewing
- Implement timeout to full interface
- Add emergency admin access methods

## Related Issues
- Depends on: All Phase 1-3 infrastructure
- Enables: Production kiosk deployment
- Related to: System monitoring

## Phase/Milestone
- [x] Phase 4: Production Ready''',
            'labels': ['feature', 'high', 'frontend', 'infrastructure', 'phase-4'],
            'milestone': milestone_numbers.get('Phase 4: Production Ready')
        },
        {
            'title': '[FEATURE] Simulation Mode & Testing Framework',
            'body': '''## Feature Description
Create comprehensive simulation mode with demo data and complete testing framework for development and demonstration.

## User Story
As a Developer, I want realistic simulation mode so that I can develop and test LeadVille without requiring physical hardware.

## Acceptance Criteria
- [ ] Demo match with fake WTVB01-BT50 sensors and AMG timer
- [ ] Realistic impact patterns and timer sequences
- [ ] Simulation controls (speed, scenarios, errors)
- [ ] PyTest unit test suite
- [ ] Playwright end-to-end tests
- [ ] CI/CD integration ready
- [ ] Performance benchmarking tools

## Technical Requirements
### Hardware Dependencies
- [x] Development environment (any platform)

### System Integration
- [ ] Mock device drivers
- [ ] Realistic data generators
- [ ] Test data fixtures
- [ ] Automated test suite
- [ ] Performance monitoring
- [ ] CI/CD pipeline configuration

## Implementation Notes
- Create multiple match scenarios (precision, action, etc.)
- Generate statistically realistic sensor data
- Include error conditions and edge cases
- Design for automated testing and validation

## Related Issues
- Depends on: Core system implementation
- Enables: Development without hardware
- Critical for: Quality assurance

## Phase/Milestone
- [x] Phase 4: Production Ready''',
            'labels': ['feature', 'high', 'backend', 'phase-4'],
            'milestone': milestone_numbers.get('Phase 4: Production Ready')
        },
        {
            'title': '[FEATURE] Data Export & Analytics',
            'body': '''## Feature Description
Implement comprehensive data export with CSV, NDJSON, and optional Parquet formats for analysis and archiving.

## User Story
As a Match Director, I want to export match data in multiple formats so that I can perform analysis, create reports, and archive match records.

## Acceptance Criteria
- [ ] CSV export (one row per run with all data)
- [ ] NDJSON export for raw analysis with schema versioning
- [ ] Optional Parquet batch export for analytics
- [ ] "Data offload" feature for match archives
- [ ] Export filtering and customization
- [ ] Automated export scheduling
- [ ] Data validation and integrity checks

## Technical Requirements
### Hardware Dependencies
- [x] Sufficient storage for export files

### System Integration
- [ ] Export API endpoints
- [ ] Data transformation pipelines
- [ ] File generation and management
- [ ] Schema versioning system
- [ ] Compression and optimization
- [ ] Transfer and backup integration

## Implementation Notes
- Support incremental and full exports
- Include metadata and schema documentation
- Implement export progress tracking
- Add data anonymization options for privacy

## Related Issues
- Depends on: Complete data model
- Enables: External analysis and reporting
- Related to: Data management workflows

## Phase/Milestone
- [x] Phase 4: Production Ready''',
            'labels': ['feature', 'medium', 'backend', 'phase-4'],
            'milestone': milestone_numbers.get('Phase 4: Production Ready')
        },
        {
            'title': '[FEATURE] Installation & Deployment System',
            'body': '''## Feature Description
Create automated installation system with comprehensive setup documentation and deployment tools.

## User Story
As a System Administrator, I want automated Pi setup so that I can deploy LeadVille quickly and reliably without manual configuration steps.

## Acceptance Criteria
- [ ] `install_pi.sh` script for one-click Pi setup
- [ ] Comprehensive setup documentation (Online/Offline modes)
- [ ] OpenAPI specification generation
- [ ] Systemd unit files for all services
- [ ] Configuration management tools
- [ ] Backup and restore procedures
- [ ] Update and upgrade mechanisms

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5 with fresh OS

### System Integration
- [ ] Automated package installation
- [ ] Service configuration and setup
- [ ] Database initialization and migration
- [ ] Security configuration
- [ ] Network setup automation
- [ ] Validation and testing scripts

## Implementation Notes
- Support both fresh install and upgrade scenarios
- Include rollback capabilities for failed updates
- Add configuration validation and testing
- Design for minimal user intervention

## Related Issues
- Depends on: All system components
- Enables: Easy deployment and maintenance
- Critical for: Production adoption

## Phase/Milestone
- [x] Phase 4: Production Ready''',
            'labels': ['feature', 'high', 'infrastructure', 'documentation', 'phase-4'],
            'milestone': milestone_numbers.get('Phase 4: Production Ready')
        },
        {
            'title': '[FEATURE] Monitoring & Observability',
            'body': '''## Feature Description
Add comprehensive monitoring, metrics, structured logging, and system health indicators for production operation.

## User Story
As a System Administrator, I want complete system observability so that I can monitor performance, detect issues early, and maintain system reliability.

## Acceptance Criteria
- [ ] Metrics endpoint for system health
- [ ] Structured logging with configurable levels
- [ ] Health LEDs: BLE link, MQTT broker, DB, disk space, NTP drift
- [ ] Performance monitoring and alerting
- [ ] Resource usage tracking (CPU, memory, disk)
- [ ] Network quality monitoring
- [ ] Automated health reports

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5 with adequate resources

### System Integration
- [ ] Prometheus-compatible metrics
- [ ] Structured JSON logging
- [ ] Health check endpoints
- [ ] Alert notification system
- [ ] Performance data collection
- [ ] Dashboard integration ready

## Implementation Notes
- Use industry-standard monitoring formats
- Implement configurable alert thresholds
- Add predictive health indicators
- Design for external monitoring system integration

## Related Issues
- Depends on: All system components
- Enables: Production monitoring and maintenance
- Critical for: System reliability

## Phase/Milestone
- [x] Phase 4: Production Ready''',
            'labels': ['feature', 'high', 'backend', 'infrastructure', 'phase-4'],
            'milestone': milestone_numbers.get('Phase 4: Production Ready')
        }
    ]
    
    # Combine all issues
    all_issues.extend(phase1_issues)
    all_issues.extend(phase2_issues) 
    all_issues.extend(phase3_issues)
    all_issues.extend(phase4_issues)
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    created_count = 0
    skipped_count = 0
    
    for issue in all_issues:
        if issue['title'] in existing_titles:
            print(f"- Skipping existing issue: {issue['title']}")
            skipped_count += 1
            continue
            
        response = requests.post(
            f'{BASE_URL}/issues',
            headers=headers,
            json=issue
        )
        if response.status_code == 201:
            issue_data = response.json()
            print(f"✓ Created issue #{issue_data['number']}: {issue['title']}")
            created_count += 1
        else:
            print(f"✗ Failed to create issue {issue['title']}: {response.status_code}")
            if response.status_code == 422:
                print(f"  Response: {response.text}")
    
    print(f"\n📊 Summary: {created_count} created, {skipped_count} skipped")
    return created_count

def main():
    """Main execution function"""
    if not GITHUB_TOKEN:
        print("❌ Please set GITHUB_TOKEN environment variable")
        print("   Create a personal access token at: https://github.com/settings/tokens")
        print("   Required scopes: repo, issues")
        print("\nUsage:")
        print("   export GITHUB_TOKEN='your_token_here'")
        print("   python scripts/create_github_issues.py")
        return
    
    print("🚀 Creating LeadVille GitHub Issues...")
    print("=" * 60)
    print("This script will create all remaining GitHub issues")
    print("from the comprehensive PROJECT_ORGANIZATION.md plan.")
    print("=" * 60)
    
    try:
        print("\n📋 Step 1: Creating Labels...")
        create_labels()
        
        print("\n🎯 Step 2: Creating Milestones...")
        milestone_numbers = create_milestones()
        
        if not milestone_numbers:
            print("⚠️  Warning: No milestones created. Issues will not have milestones assigned.")
        
        print("\n📝 Step 3: Creating Issues...")
        created_count = create_issues(milestone_numbers)
        
        print("\n" + "=" * 60)
        print("✅ GitHub Issues Creation Complete!")
        print("=" * 60)
        print(f"📊 Total Issues Created: {created_count}")
        print(f"🔗 View Issues: https://github.com/{REPO_OWNER}/{REPO_NAME}/issues")
        print(f"📋 View Project: https://github.com/{REPO_OWNER}/{REPO_NAME}/projects")
        
        print("\n📚 What's Next:")
        print("1. Review and prioritize the created issues")
        print("2. Create a project board to track progress")
        print("3. Assign issues to team members")
        print("4. Start development with Phase 1 critical issues")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        print("   Check your internet connection and GitHub token.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   Please check your GitHub token permissions.")

if __name__ == '__main__':
    main()