import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUMMARY_PATH = ROOT / "reports" / "summary.json"
BENCHMARK_RESULTS_PATH = ROOT / "reports" / "benchmark_results.json"
FAILURE_ANALYSIS_PATH = ROOT / "analysis" / "failure_analysis.md"
REFLECTIONS_DIR = ROOT / "analysis" / "reflections"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_lab():
    print("Dang kiem tra dinh dang bai nop...")

    required_files = [SUMMARY_PATH, BENCHMARK_RESULTS_PATH, FAILURE_ANALYSIS_PATH]
    missing = [str(path.relative_to(ROOT)) for path in required_files if not path.exists()]
    if missing:
        for item in missing:
            print(f"Thieu file: {item}")
        raise SystemExit(1)

    summary = _load_json(SUMMARY_PATH)
    benchmark_results = _load_json(BENCHMARK_RESULTS_PATH)
    failure_analysis = FAILURE_ANALYSIS_PATH.read_text(encoding="utf-8")

    if "metrics" not in summary or "metadata" not in summary or "regression" not in summary:
        print("summary.json phai co 'metrics', 'metadata' va 'regression'.")
        raise SystemExit(1)

    metrics = summary["metrics"]
    required_metric_keys = {
        "avg_score",
        "hit_rate",
        "mrr",
        "agreement_rate",
        "cohens_kappa",
        "avg_latency_sec",
        "total_tokens",
        "estimated_cost_usd",
        "pass_rate",
    }
    missing_metric_keys = sorted(required_metric_keys - metrics.keys())
    if missing_metric_keys:
        print(f"summary.json thieu metric: {', '.join(missing_metric_keys)}")
        raise SystemExit(1)

    total_cases = summary["metadata"].get("total", 0)
    if total_cases < 50:
        print(f"Can it nhat 50 cases, hien tai chi co {total_cases}.")
        raise SystemExit(1)

    regression = summary["regression"]
    required_regression_keys = {"baseline_version", "candidate_version", "checks", "deltas", "decision"}
    missing_regression_keys = sorted(required_regression_keys - regression.keys())
    if missing_regression_keys:
        print(f"summary.json thieu regression keys: {', '.join(missing_regression_keys)}")
        raise SystemExit(1)

    versions = benchmark_results.get("versions", {})
    if {"Agent_V1_Base", "Agent_V2_Optimized"} - versions.keys():
        print("benchmark_results.json phai chua ket qua cho Agent_V1_Base va Agent_V2_Optimized.")
        raise SystemExit(1)

    if len(versions["Agent_V2_Optimized"]) != total_cases:
        print("So case trong benchmark_results.json khong khop voi summary metadata.total.")
        raise SystemExit(1)

    placeholders = ["X/Y", "0.XX", "[Mo ta ngan]", "[Mô tả ngắn]"]
    if any(marker in failure_analysis for marker in placeholders):
        print("analysis/failure_analysis.md van con placeholder.")
        raise SystemExit(1)

    reflection_files = []
    if REFLECTIONS_DIR.exists():
        reflection_files = [path for path in REFLECTIONS_DIR.glob("reflection_*.md") if path.is_file()]
    if not reflection_files:
        print("Can co it nhat 1 file reflection_*.md trong analysis/reflections.")
        raise SystemExit(1)

    print("--- Thong ke nhanh ---")
    print(f"Tong so cases: {total_cases}")
    print(f"Diem trung binh: {metrics['avg_score']:.2f}")
    print(f"Hit Rate: {metrics['hit_rate'] * 100:.1f}%")
    print(f"MRR: {metrics['mrr']:.3f}")
    print(f"Agreement Rate: {metrics['agreement_rate'] * 100:.1f}%")
    print(f"Decision: {regression['decision']}")
    print("Bai lab da san sang de nop.")


if __name__ == "__main__":
    validate_lab()
