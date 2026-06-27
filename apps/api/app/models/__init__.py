"""Shared model metadata helpers."""

from app.core.database import Base


def import_all_models() -> None:
    import app.modules.agents.models  # noqa: F401
    import app.modules.applications.models  # noqa: F401
    import app.modules.documents.models  # noqa: F401
    import app.modules.internships.models  # noqa: F401
    import app.modules.logs.models  # noqa: F401
    import app.modules.users.models  # noqa: F401
    import app.modules.workspaces.models  # noqa: F401


__all__ = ["Base", "import_all_models"]
