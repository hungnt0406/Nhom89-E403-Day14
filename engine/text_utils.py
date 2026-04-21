import re
from typing import Iterable, List, Set


STOPWORDS = {
    "a",
    "an",
    "and",
    "bao",
    "bang",
    "bi",
    "bo",
    "cach",
    "cac",
    "can",
    "cho",
    "co",
    "con",
    "cua",
    "da",
    "de",
    "den",
    "do",
    "duoc",
    "gi",
    "gioi",
    "hay",
    "hon",
    "khac",
    "khi",
    "khong",
    "la",
    "lam",
    "len",
    "mot",
    "neu",
    "nhu",
    "nhung",
    "o",
    "ra",
    "roi",
    "se",
    "so",
    "tai",
    "the",
    "thi",
    "theo",
    "thi",
    "toi",
    "tren",
    "trong",
    "tu",
    "va",
    "vi",
    "voi",
}


TOKEN_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def tokenize(text: str) -> List[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text or "")]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def token_set(text: str) -> Set[str]:
    return set(tokenize(text))


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def jaccard_similarity(a: Iterable[str], b: Iterable[str]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a and not set_b:
        return 1.0
    return safe_div(len(set_a & set_b), len(set_a | set_b))


def token_f1(a: str, b: str) -> float:
    tokens_a = tokenize(a)
    tokens_b = tokenize(b)
    if not tokens_a and not tokens_b:
        return 1.0
    overlap = len(set(tokens_a) & set(tokens_b))
    precision = safe_div(overlap, len(set(tokens_a)))
    recall = safe_div(overlap, len(set(tokens_b)))
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def contains_uncertainty(answer: str) -> bool:
    normalized = " ".join(tokenize(answer))
    markers = {
        "khong du thong tin",
        "khong co thong tin",
        "khong tim thay",
        "khong de cap",
        "chua thay",
    }
    return any(marker in normalized for marker in markers)
