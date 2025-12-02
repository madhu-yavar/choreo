#!/usr/bin/env python3
"""
Script to run the PII service directly with FastAPI/uvicorn without Docker.
This mimics the setup in the Dockerfile but runs locally.
"""

import os
import sys
from pathlib import Path

# Add the pii_service directory to Python path
project_root = Path(__file__).parent.parent
pii_service_path = project_root / "pii_service"
sys.path.insert(0, str(pii_service_path))

# Set environment variables that would normally be set in Docker
os.environ.setdefault("PYTHONPATH", str(project_root))
os.environ.setdefault("GLINER_LOCAL_DIR", str(project_root / "models" / "pii" / "gliner_small-v2.1"))

# Import and run the app
if __name__ == "__main__":
    # Change to the pii_service directory
    os.chdir(pii_service_path)
    
    # Run with uvicorn using subprocess to ensure correct environment
    import subprocess
    import sys
    
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
    
    subprocess.run(cmd)