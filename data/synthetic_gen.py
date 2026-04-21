import asyncio
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.knowledge_base import iter_fact_records


def build_golden_dataset() -> List[Dict]:
    cases: List[Dict] = []

    for fact_index, fact in enumerate(iter_fact_records(), start=1):
        for variant_index, prompt in enumerate(fact["prompts"], start=1):
            difficulty = fact["difficulty"]
            if variant_index == len(fact["prompts"]) and difficulty == "easy":
                difficulty = "medium"

            case_id = f"case_{fact_index:02d}_{variant_index:02d}"
            cases.append(
                {
                    "case_id": case_id,
                    "question": prompt,
                    "expected_answer": fact["answer"],
                    "expected_retrieval_ids": [fact["document_id"]],
                    "context": fact["document_content"],
                    "metadata": {
                        "difficulty": difficulty,
                        "type": fact["type"],
                        "source_doc_id": fact["document_id"],
                        "source_doc_title": fact["document_title"],
                        "fact_id": fact["id"],
                        "variant": variant_index,
                        "red_team": fact["type"] in {"hard-case", "safety"},
                    },
                }
            )

    return cases


async def generate_qa_from_text(text: str = "", num_pairs: int = 54) -> List[Dict]:
    dataset = build_golden_dataset()
    return dataset[: max(num_pairs, 54)]


def save_dataset(cases: List[Dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for case in cases:
            file.write(json.dumps(case, ensure_ascii=False) + "\n")


def print_summary(cases: List[Dict]) -> None:
    by_type = Counter(case["metadata"]["type"] for case in cases)
    by_difficulty = Counter(case["metadata"]["difficulty"] for case in cases)
    red_team = sum(1 for case in cases if case["metadata"]["red_team"])

    print(f"Generated {len(cases)} cases")
    print(f"Red-team cases: {red_team}")
    print("By type:")
    for label, total in sorted(by_type.items()):
        print(f"  - {label}: {total}")
    print("By difficulty:")
    for label, total in sorted(by_difficulty.items()):
        print(f"  - {label}: {total}")


async def main() -> None:
    output_path = ROOT / "data" / "golden_set.jsonl"
    cases = await generate_qa_from_text()
    save_dataset(cases, output_path)
    print_summary(cases)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
