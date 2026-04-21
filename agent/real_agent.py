import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib import error, request

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.text_utils import safe_div, token_set, tokenize
from engine.vector_store import (
    OPENROUTER_BASE_URL,
    OPENROUTER_EMBEDDING_MODEL,
    OPENROUTER_HTTP_REFERER,
    OPENROUTER_TIMEOUT_SEC,
    ChromaKnowledgeBase,
)


load_dotenv()


REAL_AGENT_DEFAULT_MODEL = os.getenv(
    "OPENROUTER_AGENT_MODEL", "google/gemini-2.5-flash"
)
OPENROUTER_APP_TITLE = os.getenv(
    "OPENROUTER_APP_TITLE", "Lab14-AI-Evaluation-Benchmarking"
)


class RealEvaluationAgent:
    """Real lab-related RAG agent backed by ChromaDB + OpenRouter."""

    def __init__(
        self,
        model: str = REAL_AGENT_DEFAULT_MODEL,
        top_k: int = 4,
        min_fact_score: int = 2,
        embedding_model: str = OPENROUTER_EMBEDDING_MODEL,
        retrieval_mode: str = "normal",
        fetch_k: Optional[int] = None,
        extra_delay_sec: float = 0.0,
    ) -> None:
        self.model = model
        self.top_k = top_k
        self.min_fact_score = min_fact_score
        self.retrieval_mode = retrieval_mode
        self.fetch_k = fetch_k or top_k
        self.extra_delay_sec = extra_delay_sec
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.base_url = OPENROUTER_BASE_URL
        self.timeout_sec = OPENROUTER_TIMEOUT_SEC
        self.retriever = ChromaKnowledgeBase(embedding_model=embedding_model)

    async def query(self, question: str, history: Optional[List[Dict[str, str]]] = None) -> Dict:
        history = history or []
        if self.extra_delay_sec > 0:
            await asyncio.sleep(self.extra_delay_sec)

        retrieval = self.retriever.query(question, top_k=self.fetch_k)
        retrieved_docs = self._materialize_documents(retrieval["documents"])
        ranked_facts = self._rank_facts(question, retrieved_docs)

        if not self.api_key:
            return self._offline_answer(question, retrieved_docs, ranked_facts, retrieval)

        try:
            answer_payload = await asyncio.to_thread(
                self._generate_answer,
                question,
                retrieved_docs,
                ranked_facts,
                history,
            )
        except Exception as exc:
            fallback = self._offline_answer(question, retrieved_docs, ranked_facts, retrieval)
            fallback["metadata"]["backend"] = "offline-fallback"
            fallback["metadata"]["model"] = self.model
            fallback["metadata"]["generation_error"] = str(exc)
            return fallback

        generation_usage = answer_payload.get("usage", {})
        retrieval_usage = retrieval["usage"]
        return {
            "answer": answer_payload["answer"],
            "contexts": [self._format_context(doc) for doc in retrieved_docs],
            "retrieved_ids": [doc["id"] for doc in retrieved_docs],
            "metadata": {
                "backend": "openrouter",
                "model": answer_payload.get("response_model", self.model),
                "tokens_used": generation_usage.get("total_tokens", 0)
                + retrieval_usage.get("total_tokens", 0),
                "estimated_cost_usd": round(
                    float(generation_usage.get("cost", 0.0) or 0.0)
                    + float(retrieval_usage.get("cost", 0.0) or 0.0),
                    6,
                ),
                "sources": [doc["title"] for doc in retrieved_docs],
                "retrieval_scores": [
                    {"document_id": doc["id"], "score": round(doc["score"], 4)}
                    for doc in retrieved_docs
                ],
                "supporting_facts": [
                    {
                        "fact_id": fact["id"],
                        "document_id": fact["document_id"],
                        "score": fact["score"],
                    }
                    for fact in ranked_facts[:3]
                ],
                "retrieval_backend": retrieval["backend"],
                "embedding_model": self.retriever.embedding_model,
                "retrieval_mode": self.retrieval_mode,
                "embedding_tokens": retrieval_usage.get("total_tokens", 0),
                "embedding_cost_usd": retrieval_usage.get("cost", 0.0),
                "generation_tokens": generation_usage.get("total_tokens", 0),
                "generation_cost_usd": generation_usage.get("cost", 0.0),
            },
        }

    def _materialize_documents(self, candidates: List[Dict]) -> List[Dict]:
        documents = []
        for candidate in candidates:
            source = self.retriever.get_document(candidate["id"])
            if source:
                documents.append({**source, "score": candidate["score"]})

        if self.retrieval_mode == "degraded":
            if len(documents) > self.top_k:
                documents = documents[1 : self.top_k + 1]
            else:
                documents = list(reversed(documents))[: self.top_k]
        else:
            documents = documents[: self.top_k]
        return documents

    def _rank_facts(self, question: str, documents: List[Dict]) -> List[Dict]:
        query_tokens = token_set(question)
        ranked_facts = []
        for document in documents:
            for fact in document["facts"]:
                fact_text = " ".join(
                    [fact["answer"], " ".join(fact["keywords"]), " ".join(fact["prompts"])]
                )
                fact_tokens = token_set(fact_text)
                overlap = len(query_tokens & fact_tokens)
                coverage = safe_div(overlap, len(query_tokens))
                score = round(overlap + coverage, 4)
                ranked_facts.append(
                    {
                        **fact,
                        "document_id": document["id"],
                        "document_title": document["title"],
                        "score": score,
                    }
                )

        ranked_facts.sort(key=lambda item: (item["score"], item["id"]), reverse=True)
        return ranked_facts

    def _system_prompt(self) -> str:
        return (
            "Ban la mot AI Evaluation Engineering Assistant cho bai lab benchmarking agent. "
            "Chi duoc tra loi dua tren retrieved context. Neu context khong du, phai noi ro "
            "'Khong du thong tin trong tai lieu da retrieve'. Tra loi bang tieng Viet, ngan gon "
            "nhung ky thuat, va neu co the thi ket thuc bang dong 'Nguon: ...' gom document id."
        )

    def _messages(
        self,
        question: str,
        retrieved_docs: List[Dict],
        ranked_facts: List[Dict],
        history: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        contexts = "\n\n".join(self._format_context(doc, limit=460) for doc in retrieved_docs)
        facts = "\n".join(
            f"- {fact['answer']} [{fact['document_id']}]"
            for fact in ranked_facts[:3]
            if fact["score"] >= self.min_fact_score
        )
        messages = [{"role": "system", "content": self._system_prompt()}]
        messages.extend(history[-6:])
        messages.append(
            {
                "role": "user",
                "content": "\n".join(
                    [
                        f"Câu hỏi: {question}",
                        "",
                        "Retrieved context:",
                        contexts or "Không có context phù hợp.",
                        "",
                        "Supporting facts:",
                        facts or "- Không có supporting fact đủ mạnh.",
                        "",
                        "Yêu cầu trả lời:",
                        "- Bám sát context.",
                        "- Nếu thiếu thông tin thì nói rõ là không đủ thông tin.",
                        "- Ưu tiên giải thích theo logic evaluation engineering.",
                        "- Trích dẫn nguồn bằng document id ở cuối câu trả lời.",
                    ]
                ),
            }
        )
        return messages

    def _generate_answer(
        self,
        question: str,
        retrieved_docs: List[Dict],
        ranked_facts: List[Dict],
        history: List[Dict[str, str]],
    ) -> Dict:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self._messages(question, retrieved_docs, ranked_facts, history),
            "temperature": 0.2,
            "max_tokens": 350,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": OPENROUTER_APP_TITLE,
        }
        if OPENROUTER_HTTP_REFERER:
            headers["HTTP-Referer"] = OPENROUTER_HTTP_REFERER

        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_sec) as response:
                raw_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} khi goi OpenRouter: {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Loi mang khi goi OpenRouter: {exc.reason}") from exc

        content = self._extract_content(raw_payload)
        usage = raw_payload.get("usage", {}) or {}
        return {
            "answer": content.strip(),
            "response_model": raw_payload.get("model", self.model),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost": round(float(usage.get("cost", 0.0) or 0.0), 6),
            },
        }

    def _extract_content(self, raw_payload: Dict) -> str:
        choices = raw_payload.get("choices", [])
        if not choices:
            raise ValueError("OpenRouter response khong co choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )
        raise ValueError("Khong doc duoc noi dung tra loi tu OpenRouter.")

    def _offline_answer(
        self,
        question: str,
        retrieved_docs: List[Dict],
        ranked_facts: List[Dict],
        retrieval: Dict,
    ) -> Dict:
        best_fact = ranked_facts[0] if ranked_facts else None
        if not best_fact or best_fact["score"] < self.min_fact_score:
            answer = (
                "Khong du thong tin trong tai lieu da retrieve de tra loi chac chan. "
                f"Nguon da xem: {', '.join(doc['id'] for doc in retrieved_docs)}."
            )
        else:
            answer = (
                f"{best_fact['answer']} "
                f"Nguon: {best_fact['document_title']} [{best_fact['document_id']}]."
            )

        retrieval_usage = retrieval["usage"]
        generation_tokens = (
            len(tokenize(question))
            + len(tokenize(answer))
            + sum(len(tokenize(doc["content"])) for doc in retrieved_docs)
        )
        return {
            "answer": answer,
            "contexts": [self._format_context(doc) for doc in retrieved_docs],
            "retrieved_ids": [doc["id"] for doc in retrieved_docs],
            "metadata": {
                "backend": "offline",
                "model": "offline-rag-agent",
                "tokens_used": generation_tokens + retrieval_usage.get("total_tokens", 0),
                "estimated_cost_usd": round(retrieval_usage.get("cost", 0.0), 6),
                "sources": [doc["title"] for doc in retrieved_docs],
                "retrieval_scores": [
                    {"document_id": doc["id"], "score": round(doc["score"], 4)}
                    for doc in retrieved_docs
                ],
                "supporting_facts": [
                    {
                        "fact_id": fact["id"],
                        "document_id": fact["document_id"],
                        "score": fact["score"],
                    }
                    for fact in ranked_facts[:3]
                ],
                "retrieval_backend": retrieval["backend"],
                "embedding_model": self.retriever.embedding_model,
                "retrieval_mode": self.retrieval_mode,
                "embedding_tokens": retrieval_usage.get("total_tokens", 0),
                "embedding_cost_usd": retrieval_usage.get("cost", 0.0),
            },
        }

    def _format_context(self, document: Dict, limit: int = 9999) -> str:
        content = " ".join(document["content"].split())
        return f"{document['title']} ({document['id']}): {content[:limit]}"


async def run_single_question(question: str, model: str) -> None:
    agent = RealEvaluationAgent(model=model)
    response = await agent.query(question)
    print(json.dumps(response, ensure_ascii=False, indent=2))


async def repl(model: str) -> None:
    agent = RealEvaluationAgent(model=model)
    history: List[Dict[str, str]] = []
    print(f"RealEvaluationAgent đang chạy với model: {model}")
    print("Gõ 'exit' để thoát.")
    while True:
        try:
            question = input("\nBạn: ").strip()
        except EOFError:
            print()
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break

        response = await agent.query(question, history=history)
        print(f"\nAgent: {response['answer']}")
        print(f"Sources: {', '.join(response['retrieved_ids'])}")
        print(
            "Backend/Model: "
            f"{response['metadata'].get('backend')} / {response['metadata'].get('model')}"
        )
        print(
            "Retrieval: "
            f"{response['metadata'].get('retrieval_backend')} / "
            f"{response['metadata'].get('embedding_model')}"
        )
        history.extend(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": response["answer"]},
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the real AI evaluation lab agent.")
    parser.add_argument("--question", help="Ask a single question and exit.")
    parser.add_argument(
        "--model",
        default=REAL_AGENT_DEFAULT_MODEL,
        help="OpenRouter model id for the real agent.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.question:
        asyncio.run(run_single_question(args.question, args.model))
    else:
        asyncio.run(repl(args.model))
