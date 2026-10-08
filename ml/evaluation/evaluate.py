"""
ml/evaluation/evaluate.py

Comprehensive system evaluation suite.
Evaluates:
1. Text Classification Model on held-out SMS test set.
2. Lexical URL Model on held-out PhiUSIIL test set.
3. Multimodal Fusion Model on 100% Organic SMS-URL Pairs.
4. Predefined Test Cases (Organic Positive, Organic Negative, Adversarial Mismatches).

Outputs summary report to ml/experiments/results/evaluation_summary.json.
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent           # ml/
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.fraud_service import FraudService
from ml.evaluation.comparison import generate_benchmark_comparison

RESULTS_DIR = BASE_DIR / "experiments" / "results"
TEST_CASES_DIR = PROJECT_ROOT / "data" / "test_cases"
OUTPUT_REPORT = RESULTS_DIR / "evaluation_summary.json"


def evaluate_test_cases(service: FraudService) -> dict:
    test_case_files = [
        ("organic_positive", TEST_CASES_DIR / "organic_positive.json"),
        ("organic_negative", TEST_CASES_DIR / "organic_negative.json"),
        ("adversarial_mismatch", TEST_CASES_DIR / "adversarial_mismatch.json"),
    ]

    all_case_results = []
    category_summary = {}

    for cat_name, file_path in test_case_files:
        if not file_path.exists():
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        correct_count = 0
        cat_cases = []

        for case in cases:
            text = case.get("text", "")
            url = case.get("url")
            expected_label = case.get("ground_truth", "fraud").lower()

            res = service.analyze_message(text=text, url=url)
            risk_score = res["risk_score"]
            predicted_fraud = risk_score >= 50.0
            is_correct = (predicted_fraud and expected_label == "fraud") or (not predicted_fraud and expected_label == "legitimate")

            if is_correct:
                correct_count += 1

            cat_cases.append({
                "id": case.get("id"),
                "description": case.get("description"),
                "expected": expected_label,
                "predicted_risk": risk_score,
                "risk_tier": res["risk_tier"],
                "contradiction_detected": res["contradiction_analysis"].get("is_contradiction_detected", False),
                "brand_mismatch": res["contradiction_analysis"].get("brand_mismatch_detected", False),
                "is_correct": is_correct
            })

        all_case_results.extend(cat_cases)
        category_summary[cat_name] = {
            "total_cases": len(cases),
            "correct": correct_count,
            "accuracy": round(correct_count / max(1, len(cases)), 4)
        }

    return {
        "summary_by_category": category_summary,
        "details": all_case_results
    }


def run_full_evaluation():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Running End-to-End System Evaluation ===")

    print("[evaluate] Initializing master fraud service...")
    service = FraudService()

    print("[evaluate] Evaluating curated test cases...")
    test_case_eval = evaluate_test_cases(service)

    print("[evaluate] Generating benchmark and ablation comparison...")
    benchmark_data = generate_benchmark_comparison()

    # Load component metrics
    text_metrics_path = RESULTS_DIR / "text_metrics.json"
    url_metrics_path = RESULTS_DIR / "url_metrics.json"
    fusion_metrics_path = RESULTS_DIR / "fusion_metrics.json"

    text_m = json.load(open(text_metrics_path)) if text_metrics_path.exists() else {}
    url_m = json.load(open(url_metrics_path)) if url_metrics_path.exists() else {}
    fusion_m = json.load(open(fusion_metrics_path)) if fusion_metrics_path.exists() else {}

    summary = {
        "status": "SUCCESS",
        "system_version": "1.0.0",
        "models": {
            "text_model": text_m,
            "url_model": url_m,
            "fusion_model": fusion_m
        },
        "curated_test_cases_evaluation": test_case_eval,
        "ablation_benchmark": benchmark_data
    }

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[evaluate] Comprehensive evaluation report saved to {OUTPUT_REPORT}")
    print("\n--- Curated Test Cases Results ---")
    for cat, stats in test_case_eval["summary_by_category"].items():
        print(f"  {cat:22s}: {stats['correct']}/{stats['total_cases']} correct ({stats['accuracy']*100:.1f}%)")
    print("-----------------------------------\n")

    return summary


if __name__ == "__main__":
    run_full_evaluation()
