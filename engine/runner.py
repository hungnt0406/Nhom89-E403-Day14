import asyncio
import time
from typing import Dict, List


class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge, max_concurrency: int = 8):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def run_single_test(self, test_case: Dict) -> Dict:
        async with self.semaphore:
            start_time = time.perf_counter()
            try:
                agent_start_time = time.perf_counter()
                response = await self.agent.query(test_case["question"])
                agent_latency = time.perf_counter() - agent_start_time

                ragas_scores = await self.evaluator.score(test_case, response)
                judge_start_time = time.perf_counter()
                judge_result = await self.judge.evaluate_multi_judge(
                    question=test_case["question"],
                    answer=response["answer"],
                    ground_truth=test_case["expected_answer"],
                    contexts=response.get("contexts", []),
                )
                judge_latency = time.perf_counter() - judge_start_time
                total_latency = time.perf_counter() - start_time

                status = (
                    "pass"
                    if judge_result["final_score"] >= 3.5
                    and ragas_scores["retrieval"]["hit_rate"] == 1.0
                    else "fail"
                )

                return {
                    "case_id": test_case["case_id"],
                    "question": test_case["question"],
                    "expected_answer": test_case["expected_answer"],
                    "expected_retrieval_ids": test_case.get("expected_retrieval_ids", []),
                    "metadata": test_case.get("metadata", {}),
                    "agent_response": response["answer"],
                    "contexts": response.get("contexts", []),
                    "retrieved_ids": response.get("retrieved_ids", []),
                    "agent_metadata": response.get("metadata", {}),
                    "agent_latency_sec": round(agent_latency, 4),
                    "judge_latency_sec": round(judge_latency, 4),
                    "latency_sec": round(total_latency, 4),
                    "ragas": ragas_scores,
                    "judge": judge_result,
                    "status": status,
                }
            except Exception as exc:  # pragma: no cover - defensive path for benchmark stability
                latency = time.perf_counter() - start_time
                return {
                    "case_id": test_case.get("case_id", "unknown"),
                    "question": test_case.get("question", ""),
                    "expected_answer": test_case.get("expected_answer", ""),
                    "expected_retrieval_ids": test_case.get("expected_retrieval_ids", []),
                    "metadata": test_case.get("metadata", {}),
                    "agent_response": "",
                    "contexts": [],
                    "retrieved_ids": [],
                    "agent_metadata": {},
                    "agent_latency_sec": 0.0,
                    "judge_latency_sec": 0.0,
                    "latency_sec": round(latency, 4),
                    "ragas": {
                        "faithfulness": 0.0,
                        "relevancy": 0.0,
                        "retrieval": {"hit_rate": 0.0, "mrr": 0.0},
                    },
                    "judge": {
                        "final_score": 1.0,
                        "agreement_rate": 0.0,
                        "conflict_detected": False,
                        "resolution_strategy": "error",
                        "individual_scores": {},
                        "individual_labels": {},
                        "individual_reasons": {"error": str(exc)},
                        "individual_usage": {},
                        "backend": "error",
                        "pass_votes": 0,
                    },
                    "status": "error",
                }

    async def run_all(self, dataset: List[Dict]) -> List[Dict]:
        tasks = [self.run_single_test(case) for case in dataset]
        results = await asyncio.gather(*tasks)
        return sorted(results, key=lambda item: item["case_id"])
