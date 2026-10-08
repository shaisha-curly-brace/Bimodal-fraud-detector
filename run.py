"""
run.py

Main launcher for the Multimodal Fraud Detection System (Text + URL).
Usage:
    python run.py                   # Starts FastAPI server on http://localhost:8000
    python run.py --train           # Runs data cleaning and trains all ML models
    python run.py --evaluate        # Runs comprehensive evaluation and benchmark suite
    python run.py --port 8080       # Custom port
"""

import sys
import argparse
from pathlib import Path

# Ensure UTF-8 encoding for standard output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_training():
    print("=== Phase 1: Data Cleaning & Pairing ===")
    from ml.datasets.clean_sms import clean_sms_dataset
    from ml.datasets.clean_url import clean_url_dataset
    from ml.datasets.pairing import build_merged_dataset
    clean_sms_dataset()
    clean_url_dataset()
    build_merged_dataset()

    print("\n=== Phase 2: Training Component Models ===")
    from ml.training.train_text import train_text_model
    from ml.training.train_url import train_url_model
    from ml.training.train_fusion import train_fusion_model

    train_text_model()
    train_url_model()
    train_fusion_model()

    print("\n=== Phase 3: Evaluating System ===")
    from ml.evaluation.evaluate import run_full_evaluation
    run_full_evaluation()
    print("\n[DONE] All models trained and evaluated successfully!")


def run_eval():
    from ml.evaluation.evaluate import run_full_evaluation
    run_full_evaluation()


def start_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    from backend.config import settings

    server_host = host or settings.HOST or "127.0.0.1"
    server_port = port or settings.PORT or 8000

    print("\n" + "=" * 55)
    print("  [+] Multimodal Fraud Detection Server Starting")
    print(f"  [*] Dashboard (Direct IPv4): http://127.0.0.1:{server_port}")
    print(f"  [*] Dashboard (Localhost):   http://localhost:{server_port}")
    print(f"  [*] API Docs:                http://127.0.0.1:{server_port}/docs")
    print("=" * 55 + "\n")

    uvicorn.run("backend.main:app", host=server_host, port=server_port, reload=False)


def main():
    parser = argparse.ArgumentParser(description="Multimodal Fraud Detection CLI (Text + URL)")
    parser.add_argument("--train", action="store_true", help="Train all models from scratch")
    parser.add_argument("--evaluate", action="store_true", help="Run model evaluations and benchmarks")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")

    args = parser.parse_args()

    if args.train:
        run_training()
    elif args.evaluate:
        run_eval()
    else:
        start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
