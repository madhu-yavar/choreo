#!/usr/bin/env python3
"""
Script to download the GLiNER model files
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download

# Set the model directory
model_dir = Path("../pii_service/models/gliner_small-v2.1").resolve()
model_dir.mkdir(parents=True, exist_ok=True)

print(f"Downloading GLiNER model to {model_dir}")

# Download the model files
snapshot_download(
    repo_id="urchade/gliner_small-v2.1",
    local_dir=model_dir,
    local_dir_use_symlinks=False
)

print("Model download complete!")