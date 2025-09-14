#!/usr/bin/env python3
"""
LeadVille Installation Validation Script
Comprehensive testing and validation of LeadVille installation
"""

import sys
import subprocess
import importlib.util
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def log_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def log_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def log_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== {msg} ==={Colors.END}")

class ValidationResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results: List[Dict[str, Any]] = []
    
    def add_result(self, category: str, test: str, status: str, message: str, details: Optional[str] = None):
        self.results.append({
            'category': category,
            'test': test,
            'status': status,
            'message': message,
            'details': details
        })
        
        if status == 'PASS':
            self.passed += 1
        elif status == 'FAIL':
            self.failed += 1
        elif status == 'WARN':
            self.warnings += 1

class LeadVilleValidator:
    def __init__(self, leadville_dir: Path = Path("/opt/leadville")):
        self.leadville_dir = leadville_dir
        self.results = ValidationResult()
    
    def run_command(self, cmd: str, shell: bool = True) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd, shell=shell, capture_output=True, text=True, timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def validate_system_requirements(self):
        """Validate basic system requirements."""
        log_header("System Requirements")
        
        # Check if running on Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo:
                    log_success("Running on Raspberry Pi")
                    self.results.add_result("System", "Platform", "PASS", "Raspberry Pi detected")
                else:
                    log_warning("Not running on Raspberry Pi")
                    self.results.add_result("System", "Platform", "WARN", "Not a Raspberry Pi", cpuinfo[:200])
        except FileNotFoundError:
            log_error("Cannot detect system type")
            self.results.add_result("System", "Platform", "FAIL", "Cannot read /proc/cpuinfo")
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 7):
            log_success(f"Python version: {python_version.major}.{python_version.minor}")
            self.results.add_result("System", "Python", "PASS", f"Python {python_version.major}.{python_version.minor}")
        else:
            log_error(f"Python version too old: {python_version.major}.{python_version.minor}")
            self.results.add_result("System", "Python", "FAIL", "Python version < 3.7")
        
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage(self.leadville_dir.parent)
        free_gb = free // (1024**3)
        if free_gb >= 1:
            log_success(f"Free disk space: {free_gb}GB")
            self.results.add_result("System", "Disk Space", "PASS", f"{free_gb}GB available")
        else:
            log_error(f"Low disk space: {free_gb}GB")
            self.results.add_result("System", "Disk Space", "FAIL", f"Only {free_gb}GB available")
    
    def validate_directory_structure(self):
        """Validate LeadVille directory structure."""
        log_header("Directory Structure")
        
        required_dirs = [
            self.leadville_dir,
            self.leadville_dir / "src",
            self.leadville_dir / "config",
            self.leadville_dir / "logs",
            self.leadville_dir / "venv",
        ]
        
        for dir_path in required_dirs:
            if dir_path.exists() and dir_path.is_dir():
                log_success(f"Directory exists: {dir_path}")
                self.results.add_result("Directories", str(dir_path), "PASS", "Directory exists")
            else:
                log_error(f"Missing directory: {dir_path}")
                self.results.add_result("Directories", str(dir_path), "FAIL", "Directory missing")
        
        # Check file ownership
        import pwd
        try:
            leadville_uid = pwd.getpwnam('leadville').pw_uid
            current_owner = self.leadville_dir.stat().st_uid
            
            if current_owner == leadville_uid:
                log_success("Directory ownership correct")
                self.results.add_result("Directories", "Ownership", "PASS", "Owned by leadville user")
            else:
                log_error("Directory ownership incorrect")
                self.results.add_result("Directories", "Ownership", "FAIL", "Not owned by leadville user")
        except KeyError:
            log_error("leadville user does not exist")
            self.results.add_result("Directories", "User", "FAIL", "leadville user missing")
    
    def validate_python_environment(self):
        """Validate Python virtual environment."""
        log_header("Python Environment")
        
        venv_python = self.leadville_dir / "venv" / "bin" / "python"
        
        if venv_python.exists():
            log_success("Virtual environment Python exists")
            self.results.add_result("Python", "VirtualEnv", "PASS", "Virtual environment found")
            
            # Test virtual environment
            code, stdout, stderr = self.run_command(f"{venv_python} --version")
            if code == 0:
                log_success(f"Virtual environment Python: {stdout.strip()}")
                self.results.add_result("Python", "VirtualEnv Version", "PASS", stdout.strip())
            else:
                log_error(f"Virtual environment Python error: {stderr}")
                self.results.add_result("Python", "VirtualEnv Version", "FAIL", stderr)
        else:
            log_error("Virtual environment Python not found")
            self.results.add_result("Python", "VirtualEnv", "FAIL", "venv/bin/python missing")
    
    def validate_python_dependencies(self):
        """Validate Python package dependencies."""
        log_header("Python Dependencies")
        
        venv_python = self.leadville_dir / "venv" / "bin" / "python"
        
        required_packages = [
            'bleak',
            'numpy',
            'asyncio',
        ]
        
        # Test FastAPI packages if available
        api_packages = [
            'fastapi',
            'uvicorn',
            'pydantic',
        ]
        
        for package in required_packages:
            code, stdout, stderr = self.run_command(
                f"cd {self.leadville_dir} && {venv_python} -c 'import {package}; print(f\"{package} OK\")'"
            )
            if code == 0:
                log_success(f"Package available: {package}")
                self.results.add_result("Dependencies", package, "PASS", "Import successful")
            else:
                log_error(f"Package missing/broken: {package}")
                self.results.add_result("Dependencies", package, "FAIL", f"Import failed: {stderr}")
        
        # Test API packages (optional)
        for package in api_packages:
            code, stdout, stderr = self.run_command(
                f"cd {self.leadville_dir} && {venv_python} -c 'import {package}'"
            )
            if code == 0:
                log_success(f"API package available: {package}")
                self.results.add_result("Dependencies", f"API-{package}", "PASS", "API package available")
            else:
                log_warning(f"API package missing: {package}")
                self.results.add_result("Dependencies", f"API-{package}", "WARN", "API package not available")
    
    def validate_leadville_modules(self):
        """Validate LeadVille module imports."""
        log_header("LeadVille Modules")
        
        venv_python = self.leadville_dir / "venv" / "bin" / "python"
        
        modules_to_test = [
            'impact_bridge',
            'impact_bridge.wtvb_parse',
            'impact_bridge.shot_detector',
        ]
        
        for module in modules_to_test:
            code, stdout, stderr = self.run_command(
                f"cd {self.leadville_dir} && PYTHONPATH=src {venv_python} -c 'import {module}; print(f\"{module} OK\")'"
            )
            if code == 0:
                log_success(f"Module importable: {module}")
                self.results.add_result("Modules", module, "PASS", "Import successful")
            else:
                log_error(f"Module import failed: {module}")
                self.results.add_result("Modules", module, "FAIL", f"Import error: {stderr}")
    
    def validate_configuration(self):
        """Validate configuration files."""
        log_header("Configuration")
        
        config_file = self.leadville_dir / "config" / "dev_config.json"
        
        if config_file.exists():
            log_success("Configuration file exists")
            self.results.add_result("Config", "File Exists", "PASS", "dev_config.json found")
            
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                log_success("Configuration JSON is valid")
                self.results.add_result("Config", "JSON Valid", "PASS", "Valid JSON format")
                
                # Check for required sections
                required_sections = ['enhanced_impact', 'timing', 'sensor']
                for section in required_sections:
                    if section in config:
                        log_success(f"Configuration section exists: {section}")
                        self.results.add_result("Config", f"Section-{section}", "PASS", "Section present")
                    else:
                        log_warning(f"Configuration section missing: {section}")
                        self.results.add_result("Config", f"Section-{section}", "WARN", "Section missing")
                
            except json.JSONDecodeError as e:
                log_error(f"Configuration JSON invalid: {e}")
                self.results.add_result("Config", "JSON Valid", "FAIL", f"JSON error: {e}")
        else:
            log_error("Configuration file missing")
            self.results.add_result("Config", "File Exists", "FAIL", "dev_config.json missing")
    
    def validate_bluetooth(self):
        """Validate Bluetooth functionality."""
        log_header("Bluetooth")
        
        # Check if hciconfig is available
        code, stdout, stderr = self.run_command("which hciconfig")
        if code != 0:
            log_error("hciconfig command not available")
            self.results.add_result("Bluetooth", "hciconfig", "FAIL", "Command not found")
            return
        
        # Check Bluetooth adapter
        code, stdout, stderr = self.run_command("hciconfig hci0")
        if code == 0:
            log_success("Bluetooth adapter detected")
            self.results.add_result("Bluetooth", "Adapter", "PASS", "hci0 adapter found")
            
            # Check if adapter is up
            if "UP RUNNING" in stdout:
                log_success("Bluetooth adapter is active")
                self.results.add_result("Bluetooth", "Status", "PASS", "Adapter is UP RUNNING")
            else:
                log_warning("Bluetooth adapter not active")
                self.results.add_result("Bluetooth", "Status", "WARN", "Adapter not UP RUNNING")
        else:
            log_error("No Bluetooth adapter found")
            self.results.add_result("Bluetooth", "Adapter", "FAIL", "No hci0 adapter")
        
        # Test BLE scanning (short duration)
        code, stdout, stderr = self.run_command("timeout 5 hcitool lescan")
        if code == 0 or code == 124:  # 124 = timeout (expected)
            log_success("BLE scanning functional")
            self.results.add_result("Bluetooth", "BLE Scan", "PASS", "Scan command works")
        else:
            log_error(f"BLE scanning failed: {stderr}")
            self.results.add_result("Bluetooth", "BLE Scan", "FAIL", f"Scan error: {stderr}")
    
    def validate_systemd_services(self):
        """Validate systemd service installation."""
        log_header("SystemD Services")
        
        services = [
            'leadville-bridge',
            'leadville-api',
            'leadville-network',
        ]
        
        for service in services:
            # Check if service file exists
            service_file = Path(f"/etc/systemd/system/{service}.service")
            if service_file.exists():
                log_success(f"Service file exists: {service}")
                self.results.add_result("Services", f"{service}-file", "PASS", "Service file exists")
            else:
                log_error(f"Service file missing: {service}")
                self.results.add_result("Services", f"{service}-file", "FAIL", "Service file missing")
                continue
            
            # Check service status
            code, stdout, stderr = self.run_command(f"systemctl is-enabled {service}")
            if code == 0 and stdout.strip() == "enabled":
                log_success(f"Service enabled: {service}")
                self.results.add_result("Services", f"{service}-enabled", "PASS", "Service is enabled")
            else:
                log_warning(f"Service not enabled: {service}")
                self.results.add_result("Services", f"{service}-enabled", "WARN", "Service not enabled")
            
            # Check if service is running
            code, stdout, stderr = self.run_command(f"systemctl is-active {service}")
            if code == 0 and stdout.strip() == "active":
                log_success(f"Service running: {service}")
                self.results.add_result("Services", f"{service}-active", "PASS", "Service is active")
            else:
                log_info(f"Service not running: {service}")
                self.results.add_result("Services", f"{service}-active", "INFO", "Service not running")
    
    def validate_application_startup(self):
        """Test basic application startup."""
        log_header("Application Startup")
        
        venv_python = self.leadville_dir / "venv" / "bin" / "python"
        
        # Test main application import
        code, stdout, stderr = self.run_command(
            f"cd {self.leadville_dir} && timeout 10 PYTHONPATH=src {venv_python} -c '"
            f"import sys; "
            f"print(\"Testing application import...\"); "
            f"try: "
            f"    with open(\"leadville_bridge.py\") as f: "
            f"        content = f.read(); "
            f"    print(\"Main script found\"); "
            f"except Exception as e: "
            f"    print(f\"Main script error: {{e}}\"); "
            f"    sys.exit(1)"
            f"'"
        )
        
        if code == 0:
            log_success("Main application script accessible")
            self.results.add_result("Application", "Main Script", "PASS", "leadville_bridge.py found")
        else:
            log_error(f"Main application script issues: {stderr}")
            self.results.add_result("Application", "Main Script", "FAIL", f"Script error: {stderr}")
    
    def run_full_validation(self) -> bool:
        """Run complete validation suite."""
        log_info(f"Starting LeadVille installation validation...")
        log_info(f"LeadVille directory: {self.leadville_dir}")
        
        self.validate_system_requirements()
        self.validate_directory_structure()
        self.validate_python_environment()
        self.validate_python_dependencies()
        self.validate_leadville_modules()
        self.validate_configuration()
        self.validate_bluetooth()
        self.validate_systemd_services()
        self.validate_application_startup()
        
        return self.results.failed == 0
    
    def print_summary(self):
        """Print validation summary."""
        log_header("Validation Summary")
        
        print(f"Tests Run: {len(self.results.results)}")
        print(f"✅ Passed: {Colors.GREEN}{self.results.passed}{Colors.END}")
        print(f"❌ Failed: {Colors.RED}{self.results.failed}{Colors.END}")
        print(f"⚠️  Warnings: {Colors.YELLOW}{self.results.warnings}{Colors.END}")
        
        if self.results.failed > 0:
            print(f"\n{Colors.RED}❌ VALIDATION FAILED{Colors.END}")
            print("The following tests failed:")
            
            for result in self.results.results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['category']}/{result['test']}: {result['message']}")
            
            print(f"\nReview the detailed output above and fix the failing tests.")
            return False
        elif self.results.warnings > 0:
            print(f"\n{Colors.YELLOW}⚠️  VALIDATION PASSED WITH WARNINGS{Colors.END}")
            print("Some optional components have issues:")
            
            for result in self.results.results:
                if result['status'] == 'WARN':
                    print(f"  • {result['category']}/{result['test']}: {result['message']}")
            
            print(f"\nThe system should work, but consider addressing the warnings.")
            return True
        else:
            print(f"\n{Colors.GREEN}✅ ALL TESTS PASSED{Colors.END}")
            print("LeadVille installation validation successful!")
            return True
    
    def save_report(self, output_file: Path):
        """Save detailed validation report."""
        report = {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'summary': {
                'passed': self.results.passed,
                'failed': self.results.failed,
                'warnings': self.results.warnings,
                'total': len(self.results.results)
            },
            'results': self.results.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        log_success(f"Detailed report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Validate LeadVille installation")
    parser.add_argument(
        "--leadville-dir", "-d",
        type=Path,
        default=Path("/opt/leadville"),
        help="LeadVille installation directory (default: /opt/leadville)"
    )
    parser.add_argument(
        "--report", "-r",
        type=Path,
        help="Save detailed report to file"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation (skip some tests)"
    )
    
    args = parser.parse_args()
    
    validator = LeadVilleValidator(args.leadville_dir)
    
    try:
        success = validator.run_full_validation()
        validator.print_summary()
        
        if args.report:
            validator.save_report(args.report)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        log_warning("Validation interrupted by user")
        return 1
    except Exception as e:
        log_error(f"Validation failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())