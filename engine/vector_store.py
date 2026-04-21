import hashlib
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib import error, request

import chromadb
from dotenv import load_dotenv

from data.knowledge_base import KNOWLEDGE_BASE
from engine.text_utils import token_set, tokenize


load_dotenv()


ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = ROOT / ".chroma"
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
).rstrip("/")
OPENROUTER_APP_TITLE = os.getenv(
    "OPENROUTER_APP_TITLE", "Lab14-AI-Evaluation-Benchmarking"
)
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
OPENROUTER_TIMEOUT_SEC = float(os.getenv("OPENROUTER_TIMEOUT_SEC", "45"))
OPENROUTER_EMBEDDING_MODEL = os.getenv("OPENROUTER_EMBEDDING_MODEL", "baai/bge-m3")


QUERY_EXPANSIONS = {
    "hit rate": ["retrieval", "top-k", "ground truth"],
    "mrr": ["retrieval", "rank", "ground truth"],
    "judge": ["consensus", "agreement", "kappa"],
    "rollback": ["release gate", "cost", "latency"],
    "hallucination": ["groundedness", "retrieval miss", "context"],
    "prompt injection": ["safety", "out of context", "goal hijacking"],
    "chunking": ["semantic chunking", "reranking"],
    "failure analysis": ["5 whys", "root cause", "clustering"],
}


class OpenRouterEmbeddingClient:
    def __init__(
        self,
        model: str = OPENROUTER_EMBEDDING_MODEL,
        api_key: Optional[str] = None,
    ) -> None:
        self.model = model
        self.api_key = (api_key or os.getenv("OPENROUTER_API_KEY", "")).strip()
        self.base_url = OPENROUTER_BASE_URL
        self.timeout_sec = OPENROUTER_TIMEOUT_SEC

    def available(self) -> bool:
        return bool(self.api_key)

    def embed_texts(self, texts: List[str], input_type: str = "search_document") -> Dict:
        if not self.api_key:
            raise RuntimeError("Chua co OPENROUTER_API_KEY de tao embeddings.")
        if not texts:
            return {
                "embeddings": [],
                "usage": {
                    "prompt_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0.0,
                },
            }

        payload = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
            "input_type": input_type,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": OPENROUTER_APP_TITLE,
        }
        if OPENROUTER_HTTP_REFERER:
            headers["HTTP-Referer"] = OPENROUTER_HTTP_REFERER

        req = request.Request(
            url=f"{self.base_url}/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_sec) as response:
                raw_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} khi goi OpenRouter embeddings: {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Loi mang khi goi OpenRouter embeddings: {exc.reason}") from exc

        data = raw_payload.get("data", [])
        embeddings = [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]
        usage = raw_payload.get("usage", {}) or {}
        return {
            "embeddings": embeddings,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost": round(float(usage.get("cost", 0.0) or 0.0), 6),
            },
        }


class ChromaKnowledgeBase:
    def __init__(
        self,
        embedding_model: str = OPENROUTER_EMBEDDING_MODEL,
        collection_prefix: str = "lab14_eval_kb",
        persist_directory: Optional[Path] = None,
    ) -> None:
        self.embedding_model = embedding_model
        self.collection_prefix = collection_prefix
        self.persist_directory = Path(persist_directory or CHROMA_DIR)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embedding_client = OpenRouterEmbeddingClient(model=embedding_model)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.records = self._build_records()
        self.collection_name = self._make_collection_name()
        self.index_ready = False
        self.collection = self._get_or_create_collection()

    def _make_collection_name(self) -> str:
        suffix = re.sub(r"[^a-z0-9]+", "_", self.embedding_model.lower()).strip("_")
        name = f"{self.collection_prefix}_{suffix}"
        return name[:120]

    def _build_records(self) -> List[Dict]:
        records = []
        for document in KNOWLEDGE_BASE:
            fact_lines = "\n".join(f"- {fact['answer']}" for fact in document["facts"])
            prompt_lines = "\n".join(
                f"- {prompt}" for fact in document["facts"] for prompt in fact["prompts"]
            )
            record_text = "\n".join(
                [
                    f"Title: {document['title']}",
                    f"Document ID: {document['id']}",
                    f"Content: {document['content']}",
                    "Facts:",
                    fact_lines,
                    "Prompt variants:",
                    prompt_lines,
                ]
            )
            records.append(
                {
                    "id": document["id"],
                    "document": record_text,
                    "metadata": {
                        "doc_id": document["id"],
                        "title": document["title"],
                    },
                }
            )
        return records

    def _corpus_hash(self) -> str:
        payload = {
            "embedding_model": self.embedding_model,
            "records": self.records,
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _get_or_create_collection(self):
        corpus_hash = self._corpus_hash()
        existing_collection = None
        try:
            existing_collection = self.client.get_collection(name=self.collection_name)
        except Exception:
            existing_collection = None

        if existing_collection is not None:
            metadata = existing_collection.metadata or {}
            if (
                metadata.get("corpus_hash") == corpus_hash
                and metadata.get("embedding_model") == self.embedding_model
                and existing_collection.count() == len(self.records)
            ):
                self.index_ready = True
                return existing_collection
            self.client.delete_collection(name=self.collection_name)

        collection = self.client.create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": self.embedding_model,
                "corpus_hash": corpus_hash,
            },
        )

        if self.embedding_client.available():
            try:
                document_embeddings = self.embedding_client.embed_texts(
                    [record["document"] for record in self.records],
                    input_type="search_document",
                )["embeddings"]
                collection.add(
                    ids=[record["id"] for record in self.records],
                    documents=[record["document"] for record in self.records],
                    metadatas=[record["metadata"] for record in self.records],
                    embeddings=document_embeddings,
                )
                self.index_ready = True
            except Exception:
                self.index_ready = False
        return collection

    def _expanded_query(self, question: str) -> str:
        expanded = question.lower()
        extras: List[str] = []
        for trigger, synonyms in QUERY_EXPANSIONS.items():
            if trigger in expanded:
                extras.extend(synonyms)
        if extras:
            expanded = f"{expanded} {' '.join(extras)}"
        return expanded

    def _lexical_query(self, question: str, top_k: int) -> Dict:
        query_tokens = token_set(self._expanded_query(question))
        results = []
        for record in self.records:
            document_tokens = token_set(record["document"])
            score = len(query_tokens & document_tokens)
            results.append(
                {
                    "id": record["id"],
                    "title": record["metadata"]["title"],
                    "document": record["document"],
                    "score": float(score),
                }
            )
        results.sort(key=lambda item: (item["score"], item["id"]), reverse=True)
        return {
            "documents": results[:top_k],
            "usage": {
                "prompt_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
            },
            "backend": "lexical-fallback",
        }

    def query(self, question: str, top_k: int = 4) -> Dict:
        if not self.embedding_client.available() or not self.index_ready:
            return self._lexical_query(question, top_k=top_k)

        try:
            query_payload = self.embedding_client.embed_texts(
                [self._expanded_query(question)],
                input_type="search_query",
            )
            result = self.collection.query(
                query_embeddings=query_payload["embeddings"],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            fallback = self._lexical_query(question, top_k=top_k)
            fallback["error"] = str(exc)
            return fallback

        documents = []
        raw_documents = result.get("documents", [[]])[0]
        raw_metadatas = result.get("metadatas", [[]])[0]
        raw_distances = result.get("distances", [[]])[0]
        for document_text, metadata, distance in zip(
            raw_documents, raw_metadatas, raw_distances
        ):
            documents.append(
                {
                    "id": metadata["doc_id"],
                    "title": metadata["title"],
                    "document": document_text,
                    "score": round(1 - float(distance), 4),
                }
            )
        return {
            "documents": documents,
            "usage": query_payload["usage"],
            "backend": "chromadb-openrouter-embeddings",
        }

    def get_document(self, doc_id: str) -> Optional[Dict]:
        for document in KNOWLEDGE_BASE:
            if document["id"] == doc_id:
                return document
        return None
