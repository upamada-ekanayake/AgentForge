from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings
from app.services.embedding_service import EMBEDDING_VECTOR_SIZE


class QdrantServiceError(RuntimeError):
    """Raised when Qdrant operations fail."""


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def ensure_documents_collection() -> None:
    client = get_qdrant_client()

    try:
        if client.collection_exists(settings.qdrant_collection):
            return

        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(
                size=EMBEDDING_VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )
    except Exception as exc:
        raise QdrantServiceError("Qdrant is unavailable.") from exc


def upsert_chunk_vectors(points: list[dict[str, Any]]) -> None:
    if not points:
        raise QdrantServiceError("No Qdrant points provided for indexing.")

    ensure_documents_collection()
    qdrant_points = [
        models.PointStruct(
            id=point["id"],
            vector=point["vector"],
            payload=point["payload"],
        )
        for point in points
    ]

    try:
        get_qdrant_client().upsert(
            collection_name=settings.qdrant_collection,
            points=qdrant_points,
            wait=True,
        )
    except Exception as exc:
        raise QdrantServiceError("Could not index document chunks in Qdrant.") from exc


def search_document_chunks(
    query_vector: list[float],
    document_id: str,
    limit: int = 5,
) -> list[models.ScoredPoint]:
    ensure_documents_collection()

    try:
        return get_qdrant_client().search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    ),
                ],
            ),
            limit=limit,
            with_payload=True,
        )
    except Exception as exc:
        raise QdrantServiceError("Could not search document chunks in Qdrant.") from exc
