from typing import Dict, List

from engine.text_utils import contains_uncertainty, safe_div, token_f1, tokenize


class RetrievalEvaluator:
    def calculate_hit_rate(
        self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3
    ) -> float:
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in expected_ids:
                return 1.0 / rank
        return 0.0

    def evaluate_case(self, expected_ids: List[str], retrieved_ids: List[str]) -> Dict:
        return {
            "hit_rate": self.calculate_hit_rate(expected_ids, retrieved_ids, top_k=3),
            "mrr": self.calculate_mrr(expected_ids, retrieved_ids),
            "expected_ids": expected_ids,
            "retrieved_ids": retrieved_ids,
        }

    def _faithfulness(self, answer: str, expected_answer: str, contexts: List[str]) -> float:
        if contains_uncertainty(answer) and contains_uncertainty(expected_answer):
            return 1.0

        context_tokens = set()
        for context in contexts:
            context_tokens.update(tokenize(context))
        answer_tokens = set(tokenize(answer))
        if not answer_tokens:
            return 0.0

        grounded_ratio = safe_div(len(answer_tokens & context_tokens), len(answer_tokens))
        alignment = token_f1(answer, expected_answer)
        return round(min(1.0, 0.55 * grounded_ratio + 0.45 * alignment), 4)

    def _relevancy(self, question: str, answer: str) -> float:
        question_tokens = set(tokenize(question))
        answer_tokens = set(tokenize(answer))
        if not question_tokens or not answer_tokens:
            return 0.0
        return round(safe_div(len(question_tokens & answer_tokens), len(question_tokens)), 4)

    async def score(self, test_case: Dict, response: Dict) -> Dict:
        retrieval = self.evaluate_case(
            test_case.get("expected_retrieval_ids", []), response.get("retrieved_ids", [])
        )
        answer = response.get("answer", "")
        contexts = response.get("contexts", [])
        expected_answer = test_case.get("expected_answer", "")
        question = test_case.get("question", "")

        return {
            "faithfulness": self._faithfulness(answer, expected_answer, contexts),
            "relevancy": self._relevancy(question, answer),
            "retrieval": retrieval,
        }

    async def evaluate_batch(self, dataset: List[Dict], responses: List[Dict]) -> Dict:
        scores = [
            self.evaluate_case(
                case.get("expected_retrieval_ids", []), response.get("retrieved_ids", [])
            )
            for case, response in zip(dataset, responses)
        ]
        total = len(scores)
        return {
            "avg_hit_rate": round(sum(item["hit_rate"] for item in scores) / total, 4),
            "avg_mrr": round(sum(item["mrr"] for item in scores) / total, 4),
        }
