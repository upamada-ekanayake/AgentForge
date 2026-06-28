import os
import uuid
import pytest
from unittest.mock import patch
from sqlalchemy import select
from app.modules.users.models import User
from app.modules.workspaces.models import Workspace, WorkspaceMember
from app.models.enums import WorkspaceRole, DocumentStatus
from app.modules.internships.models import InternshipPost
from app.models.mixins import TimestampMixin
from app.modules.documents.models import Document, DocumentChunk

pytestmark = pytest.mark.skipif(
    os.getenv("AGENTFORGE_RUN_INTEGRATION") != "1",
    reason="Integration pipeline test requires a running PostgreSQL test database.",
)

@pytest.mark.anyio
async def test_all_pipelines_integration(db_session, client):
    # 1. Create a test user
    user = User(
        email="test_integration@agentforge.local",
        full_name="Integration Test User",
        hashed_password=None,
    )
    db_session.add(user)
    await db_session.flush()

    # 2. Create a workspace
    workspace = Workspace(
        name="Integration Test Workspace",
        owner_id=user.id,
    )
    db_session.add(workspace)
    await db_session.flush()

    # 3. Add workspace membership
    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    db_session.add(membership)

    # 4. Create an internship post
    post = InternshipPost(
        workspace_id=workspace.id,
        created_by_id=user.id,
        title="Software Engineering Intern",
        company_name="Integration Test Corp",
        location="Remote",
        description="Write FastAPI APIs and SQL queries.",
        requirements="FastAPI, SQL, Postgres.",
    )
    db_session.add(post)
    await db_session.flush()

    # 5. Create a document
    document = Document(
        workspace_id=workspace.id,
        user_id=user.id,
        filename="cv.txt",
        content_type="text/plain",
        storage_path="storage/documents/cv-test.txt",
        size_bytes=100,
        status=DocumentStatus.READY,
    )
    db_session.add(document)
    await db_session.flush()

    # 6. Create document chunks
    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content="I have experience with FastAPI, SQL, and Postgres.",
        token_count=10,
    )
    db_session.add(chunk)
    await db_session.commit()

    # 7. Mock search_document (RAG search) to avoid calling actual embeddings and Qdrant
    mocked_chunk = {
        "chunk_id": chunk.id,
        "document_id": document.id,
        "workspace_id": workspace.id,
        "user_id": user.id,
        "chunk_index": 0,
        "content": chunk.content,
        "score": 0.85,
        "qdrant_point_id": "point-0",
    }

    # Patch search_document in the modules where it is imported/used
    with patch("app.modules.agents.service.search_document", return_value=[mocked_chunk]), \
         patch("app.agents.internship_match_graph.search_document", return_value=[mocked_chunk]), \
         patch("app.modules.documents.service.search_document", return_value=[mocked_chunk]):
         
        # --- A. Test Manual Match Pipeline Endpoint ---
        payload = {
            "user_query": "Find FastAPI and SQL match",
            "workspace_id": str(workspace.id),
            "user_id": str(user.id),
            "document_id": str(document.id),
            "internship_post_id": str(post.id),
        }
        
        response = await client.post("/agents/internship-match/run", json=payload)
        assert response.status_code == 201
        data = response.json()
        
        assert "agent_run_id" in data
        assert "pipeline" in data
        pipeline_data = data["pipeline"]
        assert pipeline_data["stopped_reason"] is None
        assert pipeline_data["needs_clarification"] is False
        assert pipeline_data["report"] is not None
        assert pipeline_data["report"]["match_score"] > 0
        
        matched_skills = [item["skill"] for item in pipeline_data["report"]["matched_skills"]]
        assert "fastapi" in matched_skills
        
        manual_run_id = data["agent_run_id"]

        # --- B. Test GET Agent Runs (List & Detail) ---
        runs_response = await client.get(f"/agents/runs?workspace_id={workspace.id}")
        assert runs_response.status_code == 200
        runs_data = runs_response.json()
        assert len(runs_data) > 0
        run_ids = [run["id"] for run in runs_data]
        assert str(manual_run_id) in run_ids

        run_detail_response = await client.get(f"/agents/runs/{manual_run_id}")
        assert run_detail_response.status_code == 200
        run_detail = run_detail_response.json()
        assert run_detail["id"] == str(manual_run_id)
        assert run_detail["status"] == "succeeded"

        # --- C. Test LangGraph Pipeline Endpoint ---
        graph_response = await client.post("/agents/internship-match-graph/run", json=payload)
        assert graph_response.status_code == 201
        graph_data = graph_response.json()
        
        assert "completed_stages" in graph_data
        assert "planner" in graph_data["completed_stages"]
        assert "retriever" in graph_data["completed_stages"]
        assert "evidence_analyzer" in graph_data["completed_stages"]
        assert "context_builder" in graph_data["completed_stages"]
        assert "match_report_generator" in graph_data["completed_stages"]
        
        assert graph_data["deterministic_report"] is not None
        assert graph_data["deterministic_report"]["match_score"] > 0
        assert len(graph_data["errors"]) == 0

        # --- D. Test Internship Ranking Pipeline Endpoint ---
        rank_payload = {
            "query": "FastAPI database developer",
            "workspace_id": str(workspace.id),
            "user_id": str(user.id),
            "document_id": str(document.id),
        }
        rank_response = await client.post("/agents/internship-rank/run", json=rank_payload)
        assert rank_response.status_code == 201
        rank_data = rank_response.json()
        
        assert "agent_run_id" in rank_data
        assert "ranking" in rank_data
        ranking_info = rank_data["ranking"]
        assert ranking_info["total_ranked"] == 1
        assert ranking_info["results"][0]["internship_post_id"] == str(post.id)
        assert ranking_info["results"][0]["match_score"] > 0
