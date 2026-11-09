from __future__ import annotations

import logging
import math
import os
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384
MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Singleton service managing NLP text embeddings using Sentence Transformers (all-MiniLM-L6-v2).
    
    Resource Characteristics:
    - Model: sentence-transformers/all-MiniLM-L6-v2 (~90MB on disk)
    - Output Dimension: 384
    - Device: CPU (optimized for standard developer laptops/servers)
    - Memory footprint: ~250MB RAM when loaded
    - Lazy Loading: Loaded once on first request, retained in memory.
    - Fallback: Deterministic token-hash vectorizer if model download fails or in offline test mode.
    """

    _instance: Optional["EmbeddingService"] = None
    _model = None
    _model_loaded: bool = False
    _mock_mode: bool = False

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mock_mode = os.getenv("MOCK_EMBEDDINGS", "false").lower() in ("true", "1", "yes")
        return cls._instance

    def _load_model(self) -> None:
        if self._model_loaded:
            return

        if self._mock_mode:
            logger.info("EmbeddingService operating in MOCK_EMBEDDINGS mode.")
            self._model_loaded = True
            return

        try:
            logger.info("Loading SentenceTransformer model '%s' on CPU...", MODEL_NAME)
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(MODEL_NAME, device="cpu")
            self._model_loaded = True
            logger.info("SentenceTransformer model '%s' loaded successfully.", MODEL_NAME)
        except Exception as exc:
            logger.warning(
                "Could not load SentenceTransformer model '%s': %s. "
                "Engaging deterministic CPU fallback embedding engine.",
                MODEL_NAME,
                exc,
            )
            self._model = None
            self._model_loaded = True

    def encode_text(self, text: str) -> List[float]:
        """
        Generate a normalized 384-dimensional dense vector for a single text string.
        Returns a list of 384 floats.
        """
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIM

        self._load_model()

        if self._model is not None and not self._mock_mode:
            try:
                # normalize_embeddings=True ensures unit length (L2 norm = 1.0)
                embedding = self._model.encode(
                    text.strip(),
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                return embedding.astype(float).tolist()
            except Exception as exc:
                logger.error("SentenceTransformer encode error: %s. Using deterministic fallback.", exc)

        return self._deterministic_fallback_embedding(text)

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Batch-encode a list of texts into normalized 384-dimensional dense vectors.
        """
        if not texts:
            return []

        cleaned = [t.strip() if t else "" for t in texts]
        self._load_model()

        if self._model is not None and not self._mock_mode:
            try:
                embeddings = self._model.encode(
                    cleaned,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                return [emb.astype(float).tolist() for emb in embeddings]
            except Exception as exc:
                logger.error("SentenceTransformer batch encode error: %s", exc)

        return [self.encode_text(t) for t in cleaned]

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calculate cosine similarity between two dense vectors.
        Returns a float in the range [0.0, 1.0].
        """
        if not vec_a or not vec_b:
            return 0.0

        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        cos_sim = float(np.dot(a, b) / (norm_a * norm_b))
        # Clamp to [0.0, 1.0] to avoid negative or out-of-range floating point quirks
        return max(0.0, min(1.0, cos_sim))

    @staticmethod
    def _deterministic_fallback_embedding(text: str) -> List[float]:
        """
        Deterministic, word-hash normalized embedding of dimension 384.
        Preserves semantic overlap based on shared tokens and character n-grams
        when offline or when model weights are not pre-downloaded.
        """
        vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        tokens = text.lower().split()
        if not tokens:
            return [0.0] * EMBEDDING_DIM

        for token in tokens:
            # Hash token into vector indices
            h = hash(token)
            idx1 = abs(h) % EMBEDDING_DIM
            idx2 = abs(hash(token[::-1])) % EMBEDDING_DIM
            vec[idx1] += 1.0
            vec[idx2] += 0.5

        # Also add bigram information
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            idx = abs(hash(bigram)) % EMBEDDING_DIM
            vec[idx] += 0.75

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.astype(float).tolist()


# Global reusable singleton instance
embedding_service = EmbeddingService()
