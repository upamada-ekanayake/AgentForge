from app.modules.agents.schemas import (
    RetrievedChunk,
    RetrievedInternshipPost,
    RetrieverOutput,
)
from app.modules.internships.models import InternshipPost


def build_retriever_output(
    cv_chunks: list[dict[str, object]],
    internship_post: InternshipPost,
) -> RetrieverOutput:
    return RetrieverOutput(
        cv_chunks=[RetrievedChunk.model_validate(chunk) for chunk in cv_chunks],
        internship_post=RetrievedInternshipPost.model_validate(internship_post),
    )
