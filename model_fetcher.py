import argparse
import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except Exception as e:
    print(f"huggingface_hub not available: {e}", file=sys.stderr)
    sys.exit(1)


def fetch_model(hf_id: str, target: Path, token: str | None = None, allow: list[str] | None = None):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if token:
        kwargs["token"] = token
    if allow:
        kwargs["allow_patterns"] = allow
    # Download full snapshot (weights + tokenizer/config)
    snapshot_download(repo_id=hf_id, local_dir=str(target), local_dir_use_symlinks=False, **kwargs)


def main():
    p = argparse.ArgumentParser(description="Download a Hugging Face model snapshot to target directory")
    p.add_argument("--hf-id", dest="hf_id", help="Hugging Face repo id, e.g. sentence-transformers/all-MiniLM-L6-v2")
    p.add_argument("--target", dest="target", required=True, help="Target directory to place the model contents")
    p.add_argument("--allow", dest="allow", nargs="*", default=None, help="Optional allow patterns (globs)")
    args = p.parse_args()

    hf_id = args.hf_id or os.getenv("HF_MODEL_ID")
    if not hf_id:
        print("No model id provided via --hf-id or HF_MODEL_ID", file=sys.stderr)
        return 2

    token = os.getenv("HF_TOKEN")
    fetch_model(hf_id=hf_id, target=Path(args.target), token=token, allow=args.allow)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

