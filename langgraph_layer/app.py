from fastapi import FastAPI

from backend.app.config import settings
from backend.app.models.schemas import ReviewContext, ReviewRequest, ReviewResponse
from langgraph_layer.client import RemoteCodeRetriever
from langgraph_layer.workflow import ReviewWorkflow

app = FastAPI(title="langgraph-service")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/review", response_model=ReviewResponse)
def review(request: ReviewRequest) -> ReviewResponse:
    workflow = ReviewWorkflow()
    retriever = RemoteCodeRetriever(base_url=settings.rag_service_url)
    context = ReviewContext(question=request.question, current_query=request.question)
    return workflow.run(
        context=context,
        github_url=str(request.github_url),
        retriever=retriever,
        top_k=request.top_k,
    )
