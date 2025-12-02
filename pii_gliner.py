import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from gliner import GLiNER

class GlinerDetector:
    def __init__(self):
        base = Path(__file__).parent
        local_dir = os.getenv("GLINER_LOCAL_DIR")
        if local_dir and not os.path.isabs(local_dir):
            local_dir = str((base / local_dir).resolve())

        model_id  = os.getenv("GLINER_MODEL", "urchade/gliner_small-v2.1")
        offline = os.getenv("HF_HUB_OFFLINE", "0").lower() in ("1","true","yes")

        self.model = None
        self.labels = []
        self.threshold = 0.60
        self.model_path = None
        self.error = None

        try:
            print(f"[GLiNER] Initializing with model_id={model_id}, local_dir={local_dir}, offline={offline}")

            # Try to load from local directory first
            if local_dir and Path(local_dir).is_dir():
                print(f"[GLiNER] Loading from local directory: {local_dir}")
                # Check for model files
                model_files = ["pytorch_model.bin", "model.safetensors", "config.json"]
                existing_files = []
                for f in model_files:
                    if Path(local_dir).joinpath(f).exists():
                        existing_files.append(f)

                if not existing_files:
                    raise RuntimeError(f"No model files found in {local_dir}. Expected: {model_files}")

                print(f"[GLiNER] Found model files: {existing_files}")
                self.model = GLiNER.from_pretrained(local_dir)
                self.model_path = local_dir
            else:
                # Download from HuggingFace
                if offline:
                    raise RuntimeError(
                        "HF_HUB_OFFLINE=1 but GLINER_LOCAL_DIR is invalid. "
                        "Set GLINER_LOCAL_DIR to a downloaded model directory."
                    )
                print(f"[GLiNER] Downloading from HuggingFace: {model_id}")
                self.model = GLiNER.from_pretrained(model_id)
                self.model_path = model_id

            # Initialize labels and threshold - OPTIMIZED FOR REDUCED NOISE
            labels = os.getenv("GLINER_LABELS", "person,location")  # Removed organization to reduce false positives
            self.labels = [s.strip().lower() for s in labels.split(",") if s.strip()]
            self.threshold = float(os.getenv("GLINER_THRESHOLD", "0.80"))  # Increased from 0.60 to reduce noise

            print(f"[GLiNER] Successfully initialized")
            print(f"[GLiNER] Model: {self.model_path}")
            print(f"[GLiNER] Labels: {self.labels}")
            print(f"[GLiNER] Threshold: {self.threshold}")

        except Exception as e:
            self.error = str(e)
            print(f"[GLiNER] ERROR: Failed to initialize: {e}")
            print(f"[GLiNER] This means PERSON/LOCATION detection will not work!")
            # Don't raise the exception - allow the service to continue without GLiNER

    def detect(self, text: str, labels: Optional[List[str]] = None, threshold: Optional[float]=None) -> List[Dict[str, Any]]:
        if self.model is None:
            print(f"[GLiNER] WARNING: Model not loaded, cannot detect entities. Error: {self.error}")
            return []

        lbls = labels or self.labels
        thr  = threshold if threshold is not None else self.threshold
        if not lbls or not text.strip():
            return []

        try:
            # returns [{start, end, label, score}]
            entities = self.model.predict_entities(text, labels=lbls, threshold=thr)
            print(f"[GLiNER] Detected {len(entities)} entities in text: {text[:50]}...")
            return entities
        except Exception as e:
            print(f"[GLiNER] ERROR: Failed to detect entities: {e}")
            return []
