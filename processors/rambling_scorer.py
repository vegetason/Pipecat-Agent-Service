"""
processors/rambling_scorer.py
------------------------------
Pure scoring functions for rambling detection.
No Pipecat, no I/O — easy to unit test in isolation.

Two signals combined:
  1. Token count     — is the answer just too long?
  2. Semantic similarity — is the candidate repeating themselves?
"""

from config import config
from utils.logger import get_logger

log = get_logger(__name__)


def count_tokens(text: str) -> int:
    """Approximate token count — 1 token ≈ 4 characters."""
    return len(text) // 4


def is_over_token_limit(text: str) -> bool:
    return count_tokens(text) >= config.rambling.token_count_threshold


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x ** 2 for x in a) ** 0.5
    mag_b = sum(x ** 2 for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def embed_sentence(sentence: str) -> list[float]:
    """
    Lightweight sentence embedding using character n-gram frequencies.
    Replace with sentence-transformers for production accuracy:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model.encode(sentence).tolist()
    """
    ngrams: dict[str, int] = {}
    s = sentence.lower()
    for i in range(len(s) - 2):
        ng = s[i:i+3]
        ngrams[ng] = ngrams.get(ng, 0) + 1
    total = sum(ngrams.values()) or 1
    return [v / total for v in list(ngrams.values())[:64]]


def is_repeating(sentences: list[str]) -> bool:
    """
    Check if any two sentences in the sliding window are semantically similar
    above the configured threshold.
    """
    window = sentences[-config.rambling.window_size:]
    if len(window) < 2:
        return False
    embeddings = [embed_sentence(s) for s in window]
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= config.rambling.similarity_threshold:
                log.debug("Repetition detected", similarity=round(sim, 3))
                return True
    return False


def is_rambling(full_text: str, sentences: list[str]) -> bool:
    """
    Combined check — rambling if BOTH token limit exceeded AND repetition found.
    Requiring both reduces false positives on long but varied answers.
    """
    return is_over_token_limit(full_text) and is_repeating(sentences)