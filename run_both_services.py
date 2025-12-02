#!/usr/bin/env python3
"""
Script to run both PII and Toxicity services simultaneously with FastAPI/uvicorn without Docker.
This mimics the setup in the Docker Compose but runs locally.
"""

import subprocess
import os
import signal
import sys
from pathlib import Path

def run_pii_service():
    """Run the PII service"""
    project_root = Path(__file__).parent.parent
    pii_service_path = project_root / "pii_service"
    
    # Path to the new virtual environment
    venv_path = project_root / "format_service" / "new_env"
    python_path = venv_path / "bin" / "python"
    
    cmd = [
        str(python_path),
        "-m", "uvicorn",
        "app:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ]
    
    # Change to the pii_service directory
    os.chdir(pii_service_path)
    
    return subprocess.Popen(cmd)

def run_tox_service():
    """Run the Toxicity service"""
    project_root = Path(__file__).parent.parent
    tox_service_path = project_root / "tox_service"
    
    # Path to the new virtual environment
    venv_path = project_root / "format_service" / "new_env"
    python_path = venv_path / "bin" / "python"
    
    cmd = [
        str(python_path),
        "-m", "uvicorn",
        "app:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--log-level", "info"
    ]
    
    # Change to the tox_service directory
    os.chdir(tox_service_path)
    
    return subprocess.Popen(cmd)

def main():
    """Run both services concurrently"""
    print("Starting both PII service (port 8000) and Toxicity service (port 8001)...")
    print("Press Ctrl+C to stop both services")
    
    # Start both services
    pii_process = run_pii_service()
    tox_process = run_tox_service()
    
    try:
        # Wait for both processes
        pii_process.wait()
        tox_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down services...")
        # Terminate both processes
        pii_process.terminate()
        tox_process.terminate()
        
        # Wait for processes to complete termination
        pii_process.wait()
        tox_process.wait()
        print("Services stopped.")

if __name__ == "__main__":
    main()