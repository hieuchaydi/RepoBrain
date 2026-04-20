from __future__ import annotations

import hashlib

from repobrain.engine.provider_base import tokenize


class LocalHashEmbeddingProvider:
    name = "local-hash"

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            tokens = tokenize(text)
            if not tokens:
                vectors.append(vector)
                continue
            for token in tokens:
                slot = self._stable_slot(token)
                vector[slot] += 1.0
            total = sum(vector) or 1.0
            vectors.append([item / total for item in vector])
        return vectors

    def _stable_slot(self, token: str) -> int:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.dimensions


class LocalLexicalReranker:
    name = "local-lexical"

    def score(self, query: str, candidate_text: str) -> float:
        query_tokens = set(tokenize(query))
        candidate_tokens = tokenize(candidate_text)
        if not query_tokens or not candidate_tokens:
            return 0.0
        overlap = sum(1 for token in candidate_tokens if token in query_tokens)
        coverage = overlap / max(len(query_tokens), 1)
        density = overlap / max(len(candidate_tokens), 1)
        return round((coverage * 0.75) + (density * 8.0), 6)
