import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, close_database_connection
from app.models import import_all_models
from app.models.enums import DocumentStatus
from app.modules.users.models import User
from app.modules.workspaces.models import Workspace
from app.modules.documents.models import Document, DocumentChunk
from app.services.text_chunker import chunk_text
from app.services.embedding_service import embed_texts
from app.services.qdrant_service import upsert_chunk_vectors

import_all_models()

MOCK_CV = """
Upamada Ekanayake
Email: upamada@agentforge.local
Skills: Python, FastAPI, PostgreSQL, Git, Docker, REST APIs, SQL, Agile.

Experience:
- Software Engineering Intern at TechLabs (FastAPI, PostgreSQL API development)
- Backend developer on high-scale Python services. Built database models with SQLAlchemy and migrations with Alembic.
- Managed local deployments with Docker Compose and set up CI/CD workflows using GitHub Actions.
"""

async def seed_cv() -> None:
    async with AsyncSessionLocal() as session:
        # Find demo user
        user = await session.scalar(select(User).where(User.email == "demo@agentforge.local"))
        if user is None:
            print("Demo user not found. Please run seed.py first.")
            return

        # Find workspace
        workspace = await session.scalar(
            select(Workspace).where(Workspace.owner_id == user.id)
        )
        if workspace is None:
            print("Demo workspace not found. Please run seed.py first.")
            return

        # Project root
        project_root = Path(__file__).resolve().parents[2]
        storage_dir = project_root / "storage" / "documents"
        storage_dir.mkdir(parents=True, exist_ok=True)
        cv_path = storage_dir / "demo-cv.txt"
        cv_path.write_text(MOCK_CV, encoding="utf-8")

        # Create Document in DB
        doc = await session.scalar(
            select(Document).where(
                Document.workspace_id == workspace.id,
                Document.filename == "demo-cv.txt"
            )
        )
        if doc is None:
            doc = Document(
                workspace_id=workspace.id,
                user_id=user.id,
                filename="demo-cv.txt",
                content_type="text/plain",
                storage_path=str(cv_path.relative_to(project_root)),
                size_bytes=len(MOCK_CV),
                status=DocumentStatus.UPLOADED
            )
            session.add(doc)
            await session.flush()
        else:
            print("Demo CV document already exists in database.")
            # Clean up existing chunks first
            chunks_stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            chunks = await session.scalars(chunks_stmt)
            for chunk in chunks:
                await session.delete(chunk)
            await session.flush()

        # Chunk text
        chunks = chunk_text(MOCK_CV)
        db_chunks = []
        for index, text in enumerate(chunks):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=index,
                content=text,
            )
            session.add(db_chunk)
            db_chunks.append(db_chunk)
        
        doc.status = DocumentStatus.READY
        await session.flush()

        # Try to index in Qdrant
        print("Indexing CV chunks in Qdrant...")
        try:
            vectors = embed_texts([c.content for c in db_chunks])
            points = []
            for chunk, vector in zip(db_chunks, vectors, strict=True):
                point_id = str(chunk.id)
                points.append({
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "document_id": str(doc.id),
                        "chunk_id": str(chunk.id),
                        "workspace_id": str(workspace.id),
                        "user_id": str(user.id),
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                    }
                })
                chunk.qdrant_point_id = point_id
            
            upsert_chunk_vectors(points)
            print("Successfully indexed chunks in Qdrant.")
        except Exception as e:
            print(f"Warning: Qdrant indexing failed: {e}")
            print("The document will still be available for database matching.")

        await session.commit()
        print(f"Demo CV seeded successfully. ID: {doc.id}")

async def main() -> None:
    try:
        await seed_cv()
    finally:
        await close_database_connection()

if __name__ == "__main__":
    asyncio.run(main())
