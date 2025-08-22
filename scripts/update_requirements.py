#!/usr/bin/env python3
"""
Script to update and manage Python dependencies for GemStrategy.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    
    return result


def update_pip():
    """Update pip to the latest version."""
    print("Updating pip...")
    run_command("python -m pip install --upgrade pip")


def install_requirements():
    """Install requirements from requirements.txt."""
    print("Installing requirements...")
    run_command("pip install -r requirements.txt")


def update_requirements():
    """Update all packages to their latest versions."""
    print("Updating all packages to latest versions...")
    
    # Get list of installed packages
    result = run_command("pip list --format=freeze")
    packages = [line.split('==')[0] for line in result.stdout.strip().split('\n') if '==' in line]
    
    # Update each package
    for package in packages:
        if package not in ['pip', 'setuptools', 'wheel']:
            print(f"Updating {package}...")
            try:
                run_command(f"pip install --upgrade {package}", check=False)
            except Exception as e:
                print(f"Failed to update {package}: {e}")


def generate_requirements():
    """Generate a new requirements.txt with current versions."""
    print("Generating new requirements.txt...")
    run_command("pip freeze > requirements.txt")
    print("New requirements.txt generated!")


def check_security():
    """Check for security vulnerabilities in dependencies."""
    print("Checking for security vulnerabilities...")
    try:
        run_command("pip install safety", check=False)
        run_command("safety check", check=False)
    except Exception as e:
        print(f"Security check failed: {e}")


def main():
    """Main function."""
    print("GemStrategy Dependency Management Script")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage: python update_requirements.py [command]")
        print("Commands:")
        print("  install     - Install requirements")
        print("  update      - Update all packages")
        print("  generate    - Generate new requirements.txt")
        print("  security    - Check for security vulnerabilities")
        print("  all         - Run all commands")
        return
    
    command = sys.argv[1]
    
    if command == "install":
        update_pip()
        install_requirements()
    elif command == "update":
        update_pip()
        update_requirements()
    elif command == "generate":
        generate_requirements()
    elif command == "security":
        check_security()
    elif command == "all":
        update_pip()
        install_requirements()
        update_requirements()
        generate_requirements()
        check_security()
    else:
        print(f"Unknown command: {command}")
        return
    
    print("Operation completed successfully!")


if __name__ == "__main__":
    main()
