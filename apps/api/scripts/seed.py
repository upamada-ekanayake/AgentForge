import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, close_database_connection
from app.models import import_all_models
from app.models.enums import WorkspaceRole
from app.modules.internships.models import InternshipPost
from app.modules.users.models import User
from app.modules.workspaces.models import Workspace, WorkspaceMember

import_all_models()


DEMO_EMAIL = "demo@agentforge.local"
DEMO_WORKSPACE_NAME = "AgentForge Demo Workspace"


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                full_name="Demo User",
                hashed_password=None,
            )
            session.add(user)
            await session.flush()

        workspace = await session.scalar(
            select(Workspace).where(
                Workspace.name == DEMO_WORKSPACE_NAME,
                Workspace.owner_id == user.id,
            ),
        )
        if workspace is None:
            workspace = Workspace(name=DEMO_WORKSPACE_NAME, owner_id=user.id)
            session.add(workspace)
            await session.flush()

        membership = await session.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.user_id == user.id,
            ),
        )
        if membership is None:
            session.add(
                WorkspaceMember(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    role=WorkspaceRole.OWNER,
                ),
            )

        demo_posts = [
            {
                "title": "AI Product Intern",
                "company_name": "Northstar Labs",
                "location": "Remote",
                "description": "Support AI product discovery, workflow analysis, and prototype evaluation.",
                "requirements": "Python basics, strong writing, product thinking, and interest in AI tools.",
                "source_url": "https://example.com/internships/ai-product-intern",
            },
            {
                "title": "Backend Engineering Intern",
                "company_name": "Harbor Systems",
                "location": "Hybrid",
                "description": "Build API services, database models, and internal tooling for operations teams.",
                "requirements": "FastAPI or Django exposure, SQL fundamentals, and Git workflow familiarity.",
                "source_url": "https://example.com/internships/backend-engineering-intern",
            },
        ]

        for post_data in demo_posts:
            existing_post = await session.scalar(
                select(InternshipPost).where(
                    InternshipPost.workspace_id == workspace.id,
                    InternshipPost.title == post_data["title"],
                    InternshipPost.company_name == post_data["company_name"],
                ),
            )
            if existing_post is None:
                session.add(
                    InternshipPost(
                        workspace_id=workspace.id,
                        created_by_id=user.id,
                        **post_data,
                    ),
                )

        await session.commit()
        print("Seed data ready.")
        print(f"Demo user: {user.id} ({user.email})")
        print(f"Demo workspace: {workspace.id} ({workspace.name})")


async def main() -> None:
    try:
        await seed()
    finally:
        await close_database_connection()


if __name__ == "__main__":
    asyncio.run(main())
