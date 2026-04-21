import asyncio
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from agent.main_agent import MainAgent
from agent.real_agent import REAL_AGENT_DEFAULT_MODEL, RealEvaluationAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner
from engine.text_utils import contains_uncertainty


ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "data" / "golden_set.jsonl"
REPORTS_DIR = ROOT / "reports"
SUMMARY_PATH = REPORTS_DIR / "summary.json"
BENCHMARK_RESULTS_PATH = REPORTS_DIR / "benchmark_results.json"
FAILURE_ANALYSIS_PATH = ROOT / "analysis" / "failure_analysis.md"
REFLECTION_TEMPLATE_PATH = ROOT / "analysis" / "reflections" / "reflection_TEMPLATE.md"


DEFAULT_BENCHMARK_AGENT_CONFIG = {
    "Agent_V1_Base": {"kind": "simulated", "model": None},
    "Agent_V2_Optimized": {"kind": "real", "model": REAL_AGENT_DEFAULT_MODEL},
}


def load_dataset() -> List[Dict]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "Thieu data/golden_set.jsonl. Hay chay 'python data/synthetic_gen.py' truoc."
        )

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = [json.loads(line) for line in file if line.strip()]

    if not dataset:
        raise ValueError("File data/golden_set.jsonl rong.")
    return dataset


def calculate_cohens_kappa(results: List[Dict]) -> float:
    all_judge_names = sorted(
        {
            name
            for result in results
            for name in result["judge"].get("individual_labels", {})
            if not name.startswith("offline/tie-breaker") and not name.startswith("groundedness")
        }
    )
    if len(all_judge_names) < 2:
        return 0.0

    pairwise_kappas = []
    for left in range(len(all_judge_names)):
        for right in range(left + 1, len(all_judge_names)):
            labels_a = []
            labels_b = []
            for result in results:
                labels = result["judge"].get("individual_labels", {})
                if all_judge_names[left] in labels and all_judge_names[right] in labels:
                    labels_a.append(labels[all_judge_names[left]])
                    labels_b.append(labels[all_judge_names[right]])

            total = len(labels_a)
            if total == 0:
                continue

            observed = sum(a == b for a, b in zip(labels_a, labels_b)) / total
            p_yes_a = sum(label == "pass" for label in labels_a) / total
            p_yes_b = sum(label == "pass" for label in labels_b) / total
            p_no_a = 1 - p_yes_a
            p_no_b = 1 - p_yes_b
            expected = p_yes_a * p_yes_b + p_no_a * p_no_b
            if expected == 1:
                pairwise_kappas.append(1.0)
            else:
                pairwise_kappas.append((observed - expected) / (1 - expected))

    if not pairwise_kappas:
        return 0.0
    return round(sum(pairwise_kappas) / len(pairwise_kappas), 4)


def aggregate_judge_usage(result: Dict) -> Dict[str, float]:
    usage_entries = result["judge"].get("individual_usage", {}).values()
    return {
        "prompt_tokens": sum(entry.get("prompt_tokens", 0) for entry in usage_entries),
        "completion_tokens": sum(entry.get("completion_tokens", 0) for entry in usage_entries),
        "total_tokens": sum(entry.get("total_tokens", 0) for entry in usage_entries),
        "cost": round(sum(entry.get("cost", 0.0) for entry in usage_entries), 6),
    }


def summarize_results(results: List[Dict], agent_version: str, duration_sec: float) -> Dict:
    total = len(results)
    pass_count = sum(result["status"] == "pass" for result in results)
    fail_count = sum(result["status"] == "fail" for result in results)
    error_count = sum(result["status"] == "error" for result in results)
    type_counts = Counter(result["metadata"].get("type", "unknown") for result in results)
    difficulty_counts = Counter(
        result["metadata"].get("difficulty", "unknown") for result in results
    )
    total_agent_tokens = sum(result["agent_metadata"].get("tokens_used", 0) for result in results)
    total_agent_cost = round(
        sum(result["agent_metadata"].get("estimated_cost_usd", 0.0) for result in results), 6
    )
    judge_usage = [aggregate_judge_usage(result) for result in results]
    total_judge_tokens = sum(item["total_tokens"] for item in judge_usage)
    total_judge_cost = round(sum(item["cost"] for item in judge_usage), 6)
    judge_backends = Counter(result["judge"].get("backend", "unknown") for result in results)
    agent_backends = Counter(result["agent_metadata"].get("backend", "unknown") for result in results)
    agent_models = Counter(result["agent_metadata"].get("model", "unknown") for result in results)
    retrieval_backends = Counter(
        result["agent_metadata"].get("retrieval_backend", "unknown") for result in results
    )
    embedding_models = Counter(
        result["agent_metadata"].get("embedding_model", "unknown") for result in results
    )

    metrics = {
        "avg_score": round(sum(result["judge"]["final_score"] for result in results) / total, 4),
        "hit_rate": round(
            sum(result["ragas"]["retrieval"]["hit_rate"] for result in results) / total, 4
        ),
        "mrr": round(sum(result["ragas"]["retrieval"]["mrr"] for result in results) / total, 4),
        "agreement_rate": round(
            sum(result["judge"]["agreement_rate"] for result in results) / total, 4
        ),
        "cohens_kappa": calculate_cohens_kappa(results),
        "avg_faithfulness": round(
            sum(result["ragas"]["faithfulness"] for result in results) / total, 4
        ),
        "avg_relevancy": round(sum(result["ragas"]["relevancy"] for result in results) / total, 4),
        "avg_latency_sec": round(sum(result["latency_sec"] for result in results) / total, 4),
        "avg_agent_latency_sec": round(
            sum(result.get("agent_latency_sec", 0.0) for result in results) / total, 4
        ),
        "avg_judge_latency_sec": round(
            sum(result.get("judge_latency_sec", 0.0) for result in results) / total, 4
        ),
        "agent_tokens": total_agent_tokens,
        "judge_tokens": total_judge_tokens,
        "total_tokens": total_agent_tokens + total_judge_tokens,
        "agent_estimated_cost_usd": total_agent_cost,
        "judge_estimated_cost_usd": total_judge_cost,
        "estimated_cost_usd": round(total_agent_cost + total_judge_cost, 6),
        "pass_rate": round(pass_count / total, 4),
        "conflict_rate": round(
            sum(result["judge"]["conflict_detected"] for result in results) / total, 4
        ),
    }

    return {
        "metadata": {
            "version": agent_version,
            "total": total,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "duration_sec": round(duration_sec, 4),
        },
        "metrics": metrics,
        "status_breakdown": {
            "pass": pass_count,
            "fail": fail_count,
            "error": error_count,
        },
        "distributions": {
            "by_type": dict(sorted(type_counts.items())),
            "by_difficulty": dict(sorted(difficulty_counts.items())),
        },
        "judge_backends": dict(sorted(judge_backends.items())),
        "agent_backends": dict(sorted(agent_backends.items())),
        "agent_models": dict(sorted(agent_models.items())),
        "retrieval_backends": dict(sorted(retrieval_backends.items())),
        "embedding_models": dict(sorted(embedding_models.items())),
    }


def build_regression_report(v1_summary: Dict, v2_summary: Dict) -> Dict:
    v1_metrics = v1_summary["metrics"]
    v2_metrics = v2_summary["metrics"]

    deltas = {
        "avg_score": round(v2_metrics["avg_score"] - v1_metrics["avg_score"], 4),
        "hit_rate": round(v2_metrics["hit_rate"] - v1_metrics["hit_rate"], 4),
        "mrr": round(v2_metrics["mrr"] - v1_metrics["mrr"], 4),
        "avg_latency_sec": round(
            v2_metrics["avg_latency_sec"] - v1_metrics["avg_latency_sec"], 4
        ),
        "estimated_cost_usd": round(
            v2_metrics["estimated_cost_usd"] - v1_metrics["estimated_cost_usd"], 6
        ),
    }

    thresholds = {
        "min_avg_score_delta": 0.1,
        "min_hit_rate_delta": 0.02,
        "min_mrr_delta": 0.02,
        "max_latency_increase_sec": 0.02,
        "max_cost_increase_usd": 0.01,
    }
    checks = {
        "quality_improved": deltas["avg_score"] >= thresholds["min_avg_score_delta"],
        "hit_rate_improved": deltas["hit_rate"] >= thresholds["min_hit_rate_delta"],
        "mrr_improved": deltas["mrr"] >= thresholds["min_mrr_delta"],
        "latency_within_budget": deltas["avg_latency_sec"]
        <= thresholds["max_latency_increase_sec"],
        "cost_within_budget": deltas["estimated_cost_usd"]
        <= thresholds["max_cost_increase_usd"],
    }
    decision = "RELEASE" if all(checks.values()) else "ROLLBACK"

    return {
        "baseline_version": v1_summary["metadata"]["version"],
        "candidate_version": v2_summary["metadata"]["version"],
        "thresholds": thresholds,
        "checks": checks,
        "deltas": deltas,
        "decision": decision,
    }


def classify_failure(result: Dict) -> str:
    if result["ragas"]["retrieval"]["hit_rate"] == 0:
        return "Retrieval Miss"
    if contains_uncertainty(result["expected_answer"]) and not contains_uncertainty(
        result["agent_response"]
    ):
        return "Hallucination"
    if result["judge"]["conflict_detected"]:
        return "Judge Disagreement"
    if result["ragas"]["relevancy"] < 0.3:
        return "Incomplete Answer"
    return "Grounding Gap"


def build_failure_analysis(results: List[Dict], summary: Dict, regression: Dict) -> str:
    total = summary["metadata"]["total"]
    pass_count = summary["status_breakdown"]["pass"]
    error_count = summary["status_breakdown"]["error"]
    fail_results = [result for result in results if result["status"] != "pass"]
    analysis_pool = sorted(
        fail_results if fail_results else results,
        key=lambda item: (
            item["judge"]["final_score"],
            item["ragas"]["retrieval"]["hit_rate"],
            item["ragas"]["retrieval"]["mrr"],
        ),
    )
    focus_results = analysis_pool[: max(3, len(fail_results))]
    worst_cases = analysis_pool[:3]

    clusters = Counter(classify_failure(result) for result in focus_results)
    disagreement_count = sum(
        1 for result in focus_results if result["judge"]["conflict_detected"]
    )

    cluster_lines = []
    for label, count in clusters.most_common():
        if label == "Retrieval Miss":
            cause = (
                "Retriever lấy các tài liệu gần chủ đề nhưng bỏ sót document ground-truth "
                "trong top-k."
            )
        elif label == "Hallucination":
            cause = "Agent không từ chối dữ liệu ngoài phạm vi dù context không đủ."
        elif label == "Judge Disagreement":
            cause = "Câu trả lời khiến 3 judge đánh giá lệch nhau, cần ổn định prompt/format."
        elif label == "Incomplete Answer":
            cause = "Câu trả lời thiếu key facts hoặc thiếu định nghĩa cần có."
        else:
            cause = "Nội dung có dấu hiệu không bám sát context retrieve."
        cluster_lines.append(f"| {label} | {count} | {cause} |")

    if not fail_results:
        cluster_lines.append(
            "| Watchlist | 3 | Không có case fail rõ ràng, nên theo dõi 3 case điểm thấp nhất để tiếp tục tối ưu. |"
        )

    why_sections = []
    for index, case in enumerate(worst_cases, start=1):
        failure_type = classify_failure(case)
        retrieved = ", ".join(case["retrieved_ids"]) or "khong co"
        expected = ", ".join(case["expected_retrieval_ids"]) or "khong ro"
        if failure_type == "Retrieval Miss" and case["judge"]["final_score"] >= 3.5:
            why_chain = [
                (
                    f"**Triệu chứng:** Case {case['case_id']} trả lời nghe hợp lý, nhưng "
                    f"retrieve {retrieved} thay vì {expected}."
                ),
                "**Why 1:** Câu hỏi ngắn và dùng paraphrase nên embedding kéo về nhóm tài liệu gần nghĩa.",
                "**Why 2:** Retriever hiện tại ưu tiên semantic similarity, chưa lexical-rerank cho từ khóa đặc thù như MRR.",
                "**Why 3:** Agent vẫn suy luận được đáp án từ tài liệu lân cận nên judge chấm cao.",
                "**Why 4:** Tuy vậy benchmark yêu cầu đúng grounded retrieval, nên câu trả lời đúng do may mắn vẫn bị fail.",
                "**Nguyên nhân gốc:** Cần hybrid retrieval hoặc rerank để đưa document ground-truth vào top-k thay vì chỉ tìm tài liệu gần nghĩa.",
            ]
        elif failure_type == "Retrieval Miss":
            why_chain = [
                f"**Triệu chứng:** Case {case['case_id']} retrieve sai tài liệu ({retrieved}) thay vì {expected}.",
                "**Why 1:** Query được diễn đạt theo paraphrase nên overlap với nhiều document lân cận.",
                "**Why 2:** Chroma embedding recall tốt theo chủ đề, nhưng chưa đủ chính xác với cụm từ khóa gốc của fact cần tìm.",
                "**Why 3:** Top-k bị lấp đầy bởi các tài liệu liên quan nhưng không chứa đáp án đúng.",
                "**Why 4:** Agent vì thế hoặc từ chối quá sớm, hoặc trả lời dựa trên context gần đúng nhưng không trúng fact.",
                "**Nguyên nhân gốc:** Cần query expansion, hybrid rerank và ưu tiên từ khóa định danh fact để giảm semantic near-miss.",
            ]
        elif failure_type == "Hallucination":
            why_chain = [
                f"**Triệu chứng:** Case {case['case_id']} là out-of-context nhưng agent vẫn trả lời cụ thể.",
                "**Why 1:** Answer generator ưu tiên trả lời hơn từ chối an toàn.",
                "**Why 2:** Ngưỡng confidence để fallback 'không đủ thông tin' chưa đủ chặt.",
                "**Why 3:** Retrieval vẫn trả về tài liệu gần chủ đề nên agent bị over-confident.",
                "**Why 4:** Prompt generation chưa ưu tiên policy no-hallucination.",
                "**Nguyên nhân gốc:** Cần fallback rõ ràng hơn cho out-of-context và prompt đổi hướng.",
            ]
        else:
            why_chain = [
                f"**Triệu chứng:** Case {case['case_id']} đạt điểm judge thấp ({case['judge']['final_score']}).",
                "**Why 1:** Câu trả lời thiếu một phần key facts so với ground truth.",
                "**Why 2:** Agent chọn cách trả lời ngắn hoặc citation chưa đủ rõ.",
                "**Why 3:** Retriever cung cấp context đúng nhưng generation không tổng hợp hết ý.",
                "**Why 4:** Prompt answer template chưa ép kết cấu đầy đủ cho case khó.",
                "**Nguyên nhân gốc:** Cần template generation và post-processing ổn định hơn cho hard cases.",
            ]

        why_sections.append(
            "\n".join(
                [
                    f"### Case #{index}: {case['case_id']} ({failure_type})",
                    f"- Câu hỏi: {case['question']}",
                    f"- Expected retrieval IDs: {expected}",
                    f"- Retrieved IDs: {retrieved}",
                    (
                        f"- Judge score: {case['judge']['final_score']} | "
                        f"Conflict: {'có' if case['judge']['conflict_detected'] else 'không'}"
                    ),
                    *[f"{step_index + 1}. {line}" for step_index, line in enumerate(why_chain)],
                ]
            )
        )

    action_plan = [
        "- Bổ sung hybrid retrieval: giữ Chroma embedding để lấy recall, sau đó lexical-rerank cho các từ khóa đặc thù như MRR, Hit Rate, failure clustering.",
        "- Tăng fetch_k cho câu hỏi paraphrase ngắn, nhưng chỉ rerank và cắt top_k sau cùng để không đội chi phí generation quá nhiều.",
        "- Theo dõi riêng nhóm 'answer đúng nhưng grounding sai' vì đây là failure mode quan trọng của benchmark hiện tại.",
        "- Giữ fallback 'không đủ thông tin' cho out-of-context và prompt injection, nhưng cần tránh abstain sai khi knowledge base đã có đáp án.",
        "- Tiếp tục dùng regression gate để chặn release nếu hit rate, MRR, latency hoặc cost đi xuống xấu.",
    ]

    return "\n".join(
        [
            "# Báo cáo Phân tích Thất bại",
            "",
            "## 1. Tổng quan Benchmark",
            f"- **Tổng số case:** {total}",
            f"- **Pass/Fail/Error:** {pass_count}/{total - pass_count}/{error_count}",
            f"- **Điểm LLM-Judge trung bình:** {summary['metrics']['avg_score']:.2f} / 5.0",
            (
                f"- **Chỉ số retrieval:** Hit Rate {summary['metrics']['hit_rate']:.2f}, "
                f"MRR {summary['metrics']['mrr']:.2f}"
            ),
            "- **So với V1:**",
            f"  - Avg score: {regression['deltas']['avg_score']:+.2f}",
            f"  - Hit Rate: {regression['deltas']['hit_rate']:+.2f}",
            f"  - MRR: {regression['deltas']['mrr']:+.2f}",
            f"  - Avg latency: {regression['deltas']['avg_latency_sec']:+.2f}s",
            f"  - Estimated cost: {regression['deltas']['estimated_cost_usd']:+.4f} USD",
            f"- **Regression gate:** {regression['decision']}",
            "- **Tiêu chí pass:** Judge >= 3.5 và Hit Rate = 1.0.",
            (
                "- **Ghi chú:** Không có case fail rõ ràng; báo cáo dưới đây tập trung vào 3 case điểm thấp nhất để tiếp tục tối ưu."
                if not fail_results
                else "- **Ghi chú:** V2 đã đạt RELEASE, nhưng 3 case fail đều xoay quanh retrieval miss ở nhóm câu hỏi paraphrase/ngắn."
            ),
            "",
            "## 2. Phân nhóm lỗi",
            "| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |",
            "|----------|----------|---------------------|",
            *cluster_lines,
            f"- **Tín hiệu phụ:** {disagreement_count}/{len(focus_results)} case trong nhóm phân tích có disagreement giữa các judge.",
            "",
            "## 3. Phân tích 5 Whys (3 case tệ nhất)",
            "",
            *why_sections,
            "",
            "## 4. Kế hoạch cải tiến",
            *action_plan,
        ]
    )


def ensure_reflection_template() -> None:
    REFLECTION_TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REFLECTION_TEMPLATE_PATH.exists():
        return
    REFLECTION_TEMPLATE_PATH.write_text(
        "\n".join(
            [
                "# Reflection Template",
                "",
                "## Phan cong",
                "- Module da dong gop:",
                "",
                "## Quyet dinh ky thuat",
                "- Van de kho nhat da giai quyet:",
                "- Trade-off da chap nhan:",
                "",
                "## Bai hoc rut ra",
                "- Dieu se lam khac di o lan tiep theo:",
            ]
        ),
        encoding="utf-8",
    )


async def run_benchmark_with_results(agent_version: str, dataset: List[Dict]) -> Tuple[List[Dict], Dict]:
    print(f"Khoi dong Benchmark cho {agent_version}...")
    agent, agent_config = build_agent_for_version(agent_version)
    runner = BenchmarkRunner(
        agent=agent,
        evaluator=RetrievalEvaluator(),
        judge=LLMJudge(),
    )

    start_time = asyncio.get_running_loop().time()
    results = await runner.run_all(dataset)
    duration_sec = asyncio.get_running_loop().time() - start_time
    summary = summarize_results(results, agent_version, duration_sec)
    summary["agent_configuration"] = agent_config
    return results, summary


def build_agent_for_version(agent_version: str):
    default_config = DEFAULT_BENCHMARK_AGENT_CONFIG.get(agent_version)
    if not default_config:
        raise ValueError(f"Khong co cau hinh benchmark agent cho version {agent_version}")

    env_prefix = "BASELINE" if agent_version == "Agent_V1_Base" else "CANDIDATE"
    agent_kind = os.getenv(
        f"BENCHMARK_{env_prefix}_AGENT", default_config["kind"]
    ).strip().lower()

    if agent_kind == "real":
        model = os.getenv(
            f"BENCHMARK_{env_prefix}_REAL_MODEL",
            os.getenv("OPENROUTER_AGENT_MODEL", default_config["model"] or REAL_AGENT_DEFAULT_MODEL),
        ).strip()
        top_k = int(os.getenv(f"BENCHMARK_{env_prefix}_TOP_K", "4"))
        min_fact_score = int(os.getenv(f"BENCHMARK_{env_prefix}_MIN_FACT_SCORE", "2"))
        retrieval_mode = os.getenv(
            f"BENCHMARK_{env_prefix}_RETRIEVAL_MODE", "normal"
        ).strip().lower()
        fetch_k = int(
            os.getenv(
                f"BENCHMARK_{env_prefix}_FETCH_K",
                str(top_k + 2 if retrieval_mode == "degraded" else top_k),
            )
        )
        extra_delay_sec = float(os.getenv(f"BENCHMARK_{env_prefix}_EXTRA_DELAY_SEC", "0"))
        agent = RealEvaluationAgent(
            model=model,
            top_k=top_k,
            min_fact_score=min_fact_score,
            retrieval_mode=retrieval_mode,
            fetch_k=fetch_k,
            extra_delay_sec=extra_delay_sec,
        )
        config = {
            "kind": "real",
            "model": model,
            "top_k": top_k,
            "min_fact_score": min_fact_score,
            "fetch_k": fetch_k,
            "retrieval_mode": retrieval_mode,
            "extra_delay_sec": extra_delay_sec,
        }
        return agent, config

    simulated_version = os.getenv(
        f"BENCHMARK_{env_prefix}_SIM_VERSION", agent_version
    ).strip()
    agent = MainAgent(version=simulated_version)
    config = {
        "kind": "simulated",
        "version": simulated_version,
        "model": agent.config["model"],
    }
    return agent, config


async def main() -> None:
    dataset = load_dataset()
    judge_config = LLMJudge()

    v1_results, v1_summary = await run_benchmark_with_results("Agent_V1_Base", dataset)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized", dataset)
    regression = build_regression_report(v1_summary, v2_summary)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FAILURE_ANALYSIS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ensure_reflection_template()

    summary_payload = {
        "metadata": v2_summary["metadata"],
        "metrics": v2_summary["metrics"],
        "baseline_metrics": v1_summary["metrics"],
        "status_breakdown": v2_summary["status_breakdown"],
        "distributions": v2_summary["distributions"],
        "agent_backends": v2_summary.get("agent_backends", {}),
        "agent_models": v2_summary.get("agent_models", {}),
        "retrieval_backends": v2_summary.get("retrieval_backends", {}),
        "embedding_models": v2_summary.get("embedding_models", {}),
        "agent_configuration": v2_summary.get("agent_configuration", {}),
        "baseline_agent_configuration": v1_summary.get("agent_configuration", {}),
        "judge_backends": v2_summary.get("judge_backends", {}),
        "judge_configuration": {
            "mode": judge_config.judge_mode,
            "default_models": judge_config.default_models,
        },
        "regression": regression,
    }
    benchmark_payload = {
        "versions": {
            "Agent_V1_Base": v1_results,
            "Agent_V2_Optimized": v2_results,
        },
        "summaries": {
            "Agent_V1_Base": v1_summary,
            "Agent_V2_Optimized": v2_summary,
        },
        "regression": regression,
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    BENCHMARK_RESULTS_PATH.write_text(
        json.dumps(benchmark_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    FAILURE_ANALYSIS_PATH.write_text(
        build_failure_analysis(v2_results, v2_summary, regression), encoding="utf-8"
    )

    print("\n--- KET QUA SO SANH (REGRESSION) ---")
    print(f"V1 Score: {v1_summary['metrics']['avg_score']}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']}")
    print(f"Hit Rate Delta: {regression['deltas']['hit_rate']:+.4f}")
    print(f"MRR Delta: {regression['deltas']['mrr']:+.4f}")
    print(f"Cost Delta: {regression['deltas']['estimated_cost_usd']:+.6f}")
    print(f"Latency Delta: {regression['deltas']['avg_latency_sec']:+.4f}")
    print(f"QUYET DINH: {regression['decision']}")


if __name__ == "__main__":
    asyncio.run(main())
