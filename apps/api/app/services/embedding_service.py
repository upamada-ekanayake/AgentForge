from functools import lru_cache

from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_VECTOR_SIZE = 384


class EmbeddingError(RuntimeError):
    """Raised when embeddings cannot be generated."""


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_text(text: str) -> list[float]:
    embeddings = embed_texts([text])
    return embeddings[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    clean_texts = [text.strip() for text in texts if text.strip()]
    if not clean_texts:
        raise EmbeddingError("No text provided for embedding.")

    try:
        model = get_embedding_model()
        vectors = model.encode(
            clean_texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
    except Exception as exc:
        raise EmbeddingError("Could not generate embeddings.") from exc

    return [vector.astype(float).tolist() for vector in vectors]
