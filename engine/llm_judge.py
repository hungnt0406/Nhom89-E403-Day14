import asyncio
import json
import os
import re
from typing import Any, Dict, List, Tuple
from urllib import error, request

from dotenv import load_dotenv

from engine.text_utils import contains_uncertainty, safe_div, token_f1, tokenize


load_dotenv()


def _to_five_point(score_0_to_1: float) -> float:
    return round(1 + max(0.0, min(1.0, score_0_to_1)) * 4, 2)


class LLMJudge:
    def __init__(self) -> None:
        self.judge_mode = os.getenv("JUDGE_MODE", "auto").strip().lower()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_base_url = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).rstrip("/")
        self.openrouter_title = os.getenv(
            "OPENROUTER_APP_TITLE", "Lab14-AI-Evaluation-Benchmarking"
        )
        self.openrouter_referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
        self.request_timeout_sec = float(os.getenv("OPENROUTER_TIMEOUT_SEC", "45"))
        self.default_models = {
            "gpt": os.getenv("OPENROUTER_GPT_MODEL", "openai/gpt-4.1-mini"),
            "claude": os.getenv(
                "OPENROUTER_CLAUDE_MODEL", "anthropic/claude-3.5-haiku"
            ),
            "gemini": os.getenv("OPENROUTER_GEMINI_MODEL", "google/gemini-2.5-flash"),
        }
        self.tie_breaker = "groundedness-auditor-sim"

    def _extract_context_tokens(self, contexts: List[str]) -> set:
        context_tokens = set()
        for context in contexts:
            context_tokens.update(tokenize(context))
        return context_tokens

    def _judge_semantic_match(
        self, question: str, answer: str, ground_truth: str, contexts: List[str]
    ) -> Dict[str, Any]:
        expected_unknown = contains_uncertainty(ground_truth)
        answer_truth_f1 = token_f1(answer, ground_truth)
        question_alignment = token_f1(answer, question)
        if expected_unknown:
            normalized = 1.0 if contains_uncertainty(answer) else 0.15
        else:
            normalized = 0.75 * answer_truth_f1 + 0.25 * question_alignment

        score = _to_five_point(normalized)
        label = "pass" if score >= 3.5 else "fail"
        return {
            "score": score,
            "label": label,
            "reason": (
                "Offline judge uu tien semantic overlap giua answer va ground truth, co can "
                "nhac muc do bam sat cau hoi."
            ),
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
            },
        }

    def _judge_groundedness(
        self, answer: str, ground_truth: str, contexts: List[str]
    ) -> Dict[str, Any]:
        expected_unknown = contains_uncertainty(ground_truth)
        context_tokens = self._extract_context_tokens(contexts)
        answer_tokens = set(tokenize(answer))
        grounded_ratio = safe_div(len(answer_tokens & context_tokens), len(answer_tokens))
        coverage = token_f1(answer, ground_truth)

        if expected_unknown:
            normalized = 1.0 if contains_uncertainty(answer) else 0.1
        else:
            normalized = 0.6 * grounded_ratio + 0.4 * coverage

        score = _to_five_point(normalized)
        label = "pass" if score >= 3.5 else "fail"
        return {
            "score": score,
            "label": label,
            "reason": (
                "Offline judge uu tien groundedness trong context va phat hien answer khong duoc "
                "ho tro boi tai lieu retrieve."
            ),
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
            },
        }

    def _run_tie_breaker(
        self, answer: str, ground_truth: str, contexts: List[str]
    ) -> Dict[str, Any]:
        context_tokens = self._extract_context_tokens(contexts)
        answer_tokens = set(tokenize(answer))
        expected_tokens = set(tokenize(ground_truth))
        supported = safe_div(len(answer_tokens & context_tokens), len(answer_tokens))
        target_coverage = safe_div(len(answer_tokens & expected_tokens), len(expected_tokens))
        normalized = min(1.0, 0.5 * supported + 0.5 * target_coverage)
        score = _to_five_point(normalized)
        return {
            "score": score,
            "label": "pass" if score >= 3.5 else "fail",
            "reason": "Tie-breaker offline chon cach danh gia bao thu dua tren supported facts.",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
            },
        }

    def _should_use_openrouter(self) -> bool:
        if self.judge_mode == "offline":
            return False
        if self.judge_mode == "openrouter":
            if not self.openrouter_api_key:
                raise RuntimeError(
                    "JUDGE_MODE=openrouter nhung chua co OPENROUTER_API_KEY trong environment."
                )
            return True
        return bool(self.openrouter_api_key)

    def _compact_contexts(self, contexts: List[str], limit: int = 2, size: int = 320) -> str:
        trimmed = []
        for context in contexts[:limit]:
            compact = " ".join(context.split())
            trimmed.append(compact[:size])
        return "\n".join(f"- {item}" for item in trimmed)

    def _build_messages(
        self, question: str, answer: str, ground_truth: str, contexts: List[str]
    ) -> List[Dict[str, str]]:
        system_prompt = (
            "You are a strict benchmark judge for a RAG agent. Evaluate only against the supplied "
            "ground truth and retrieved context. Return JSON only with keys: score, label, reason. "
            "score must be a number from 1.0 to 5.0. label must be pass or fail. "
            "Use pass only when the answer is materially correct, grounded, and safe."
        )
        user_prompt = "\n".join(
            [
                f"Question:\n{question}",
                f"Candidate answer:\n{answer}",
                f"Ground truth:\n{ground_truth}",
                "Retrieved context:",
                self._compact_contexts(contexts) or "- No context provided",
                "",
                "Scoring rubric:",
                "- 5: correct, grounded, concise, no risky speculation.",
                "- 4: mostly correct with minor omissions.",
                "- 3: partially correct or somewhat ungrounded.",
                "- 2: mostly wrong, unsafe, or unsupported.",
                "- 1: clearly wrong or hallucinated.",
                "",
                'Return only compact JSON, for example: {"score": 4.2, "label": "pass", "reason": "..."}.',
            ]
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _extract_message_content(self, payload: Dict[str, Any]) -> str:
        choices = payload.get("choices", [])
        if not choices:
            raise ValueError("OpenRouter response khong co choices.")
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            return "\n".join(parts)
        raise ValueError("Khong doc duoc content tu OpenRouter response.")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _call_openrouter_model(
        self,
        model_id: str,
        question: str,
        answer: str,
        ground_truth: str,
        contexts: List[str],
    ) -> Dict[str, Any]:
        url = f"{self.openrouter_base_url}/chat/completions"
        payload = {
            "model": model_id,
            "messages": self._build_messages(question, answer, ground_truth, contexts),
            "temperature": 0,
            "max_tokens": 220,
        }
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "X-Title": self.openrouter_title,
        }
        if self.openrouter_referer:
            headers["HTTP-Referer"] = self.openrouter_referer

        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.request_timeout_sec) as response:
                raw_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:  # pragma: no cover - network path
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{model_id} HTTP {exc.code}: {body}") from exc
        except error.URLError as exc:  # pragma: no cover - network path
            raise RuntimeError(f"{model_id} network error: {exc.reason}") from exc

        parsed = self._extract_json(self._extract_message_content(raw_payload))
        raw_score = float(parsed.get("score", 1.0))
        score = round(max(1.0, min(5.0, raw_score)), 2)
        label = str(parsed.get("label", "fail")).strip().lower()
        if label not in {"pass", "fail"}:
            label = "pass" if score >= 3.5 else "fail"
        reason = str(parsed.get("reason", "No rationale returned.")).strip()
        usage = raw_payload.get("usage", {}) or {}

        return {
            "score": score,
            "label": label,
            "reason": reason,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost": round(float(usage.get("cost", 0.0) or 0.0), 6),
            },
            "response_model": raw_payload.get("model", model_id),
        }

    async def _evaluate_openrouter(
        self, question: str, answer: str, ground_truth: str, contexts: List[str]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        tasks = [
            asyncio.to_thread(
                self._call_openrouter_model,
                model_id,
                question,
                answer,
                ground_truth,
                contexts,
            )
            for model_id in self.default_models.values()
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        judges: List[Tuple[str, Dict[str, Any]]] = []
        for model_id, result in zip(self.default_models.values(), responses):
            if isinstance(result, Exception):
                raise RuntimeError(f"Judge {model_id} failed: {result}") from result
            judges.append((model_id, result))
        return judges

    def _pairwise_agreement(self, scores: List[float]) -> float:
        if len(scores) < 2:
            return 0.0
        pair_values = []
        for left in range(len(scores)):
            for right in range(left + 1, len(scores)):
                pair_values.append(max(0.0, 1 - abs(scores[left] - scores[right]) / 4))
        return round(sum(pair_values) / len(pair_values), 4)

    def _format_result(
        self,
        judges: List[Tuple[str, Dict[str, Any]]],
        backend: str,
        use_tie_breaker: bool = False,
        tie_break: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        scores = [judge["score"] for _, judge in judges]
        individual_scores = {name: judge["score"] for name, judge in judges}
        individual_labels = {name: judge["label"] for name, judge in judges}
        individual_reasons = {name: judge["reason"] for name, judge in judges}
        individual_usage = {
            name: {
                **judge.get("usage", {}),
                "response_model": judge.get("response_model", name),
            }
            for name, judge in judges
        }

        conflict_detected = (max(scores) - min(scores)) > 1.0 if scores else False
        agreement_rate = self._pairwise_agreement(scores)

        if use_tie_breaker and tie_break:
            final_score = round(sorted(scores + [tie_break["score"]])[1], 2)
            resolution_strategy = "median_of_three_plus_offline_tiebreaker"
            individual_scores[self.tie_breaker] = tie_break["score"]
            individual_labels[self.tie_breaker] = tie_break["label"]
            individual_reasons[self.tie_breaker] = tie_break["reason"]
            individual_usage[self.tie_breaker] = {
                **tie_break.get("usage", {}),
                "response_model": self.tie_breaker,
            }
        else:
            final_score = round(sorted(scores)[len(scores) // 2], 2)
            resolution_strategy = "median_of_three_models" if len(scores) >= 3 else "mean_of_two_judges"
            if len(scores) == 2:
                final_score = round(sum(scores) / 2, 2)

        return {
            "backend": backend,
            "final_score": final_score,
            "agreement_rate": agreement_rate,
            "conflict_detected": conflict_detected,
            "resolution_strategy": resolution_strategy,
            "individual_scores": individual_scores,
            "individual_labels": individual_labels,
            "individual_reasons": individual_reasons,
            "individual_usage": individual_usage,
            "pass_votes": sum(1 for label in individual_labels.values() if label == "pass"),
        }

    async def evaluate_multi_judge(
        self,
        question: str,
        answer: str,
        ground_truth: str,
        contexts: List[str] | None = None,
    ) -> Dict[str, Any]:
        contexts = contexts or []

        if self._should_use_openrouter():
            try:
                openrouter_judges = await self._evaluate_openrouter(
                    question, answer, ground_truth, contexts
                )
                return self._format_result(openrouter_judges, backend="openrouter")
            except Exception:
                if self.judge_mode == "openrouter":
                    raise

        offline_a = self._judge_semantic_match(question, answer, ground_truth, contexts)
        offline_b = self._judge_groundedness(answer, ground_truth, contexts)
        offline_c = self._run_tie_breaker(answer, ground_truth, contexts)

        return self._format_result(
            [
                ("offline/semantic", offline_a),
                ("offline/groundedness", offline_b),
                ("offline/tie-breaker", offline_c),
            ],
            backend="offline",
        )

    async def check_position_bias(self, response_a: str, response_b: str) -> Dict[str, float]:
        tokens_a = len(tokenize(response_a))
        tokens_b = len(tokenize(response_b))
        if tokens_a + tokens_b == 0:
            return {"position_bias": 0.0}
        return {"position_bias": round(abs(tokens_a - tokens_b) / (tokens_a + tokens_b), 4)}
