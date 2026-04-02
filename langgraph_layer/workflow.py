from typing import Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from backend.app.models.schemas import Finding, ImprovedCode, RetrievalDecision, ReviewContext, ReviewResponse


class ReviewGraphState(TypedDict, total=False):
    question: str
    current_query: str
    retry_count: int
    max_retries: int
    retrieved_chunks: list
    retrieval_decision: RetrievalDecision | None
    report: ReviewResponse | None
    metadata: dict[str, Any]
    github_url: str
    top_k: int
    retriever: Any


class ReviewWorkflow:
    def __init__(self) -> None:
        graph = StateGraph(ReviewGraphState)
        graph.add_node("analyze_question", self.analyze_question)
        graph.add_node("retrieve", self.retrieve)
        graph.add_node("judge_retrieval", self.judge_retrieval)
        graph.add_node("rewrite_query", self.rewrite_query)
        graph.add_node("generate_review", self.generate_review)

        graph.add_edge(START, "analyze_question")
        graph.add_edge("analyze_question", "retrieve")
        graph.add_edge("retrieve", "judge_retrieval")
        graph.add_conditional_edges(
            "judge_retrieval",
            self.route_after_judgement,
            {
                "rewrite_query": "rewrite_query",
                "generate_review": "generate_review",
            },
        )
        graph.add_edge("rewrite_query", "retrieve")
        graph.add_edge("generate_review", END)
        self._graph = graph.compile()

    def analyze_question(self, state: ReviewGraphState) -> dict[str, Any]:
        metadata = dict(state.get("metadata", {}))
        metadata["question_type"] = "code_review"
        return {"metadata": metadata}

    def retrieve(self, state: ReviewGraphState) -> dict[str, Any]:
        retriever = state["retriever"]
        chunks = retriever.retrieve(
            github_url=state["github_url"],
            query=state["current_query"],
            top_k=state["top_k"],
        )
        return {"retrieved_chunks": chunks}

    def judge_retrieval(self, state: ReviewGraphState) -> dict[str, Any]:
        retrieved_chunks = state.get("retrieved_chunks", [])
        sufficient = len(retrieved_chunks) >= 3
        reason = (
            "enough diverse function-level chunks retrieved"
            if sufficient
            else "too little context to generate a reliable review"
        )
        return {
            "retrieval_decision": RetrievalDecision(sufficient=sufficient, reason=reason),
        }

    def route_after_judgement(self, state: ReviewGraphState) -> str:
        decision = state.get("retrieval_decision")
        if decision is None:
            return "generate_review"
        if decision.sufficient:
            return "generate_review"
        if state.get("retry_count", 0) < state.get("max_retries", 1):
            return "rewrite_query"
        return "generate_review"

    def rewrite_query(self, state: ReviewGraphState) -> dict[str, Any]:
        retry_count = state.get("retry_count", 0) + 1
        return {
            "retry_count": retry_count,
            "current_query": f'{state["question"]} python implementation edge cases',
        }

    def generate_review(self, state: ReviewGraphState) -> dict[str, Any]:
        findings: list[Finding] = []
        improved_code: list[ImprovedCode] = []

        for chunk in state.get("retrieved_chunks", [])[:3]:
            findings.append(
                Finding(
                    severity="medium",
                    title=f"리뷰: {chunk.symbol}",
                    file_path=chunk.file_path,
                    line=chunk.start_line,
                    rationale=(
                        "검색된 코드 컨텍스트를 기반으로 생성된 함수 단위의 리뷰 내용입니다. "
                        "실제 LLM 연동 시 이 부분에 분석 모델의 지적 사항이 들어갑니다."
                    ),
                    recommendation="에러 핸들링, 경계값 검사, 변수명 명확성을 검증하세요.",
                )
            )
            improved_code.append(
                ImprovedCode(
                    file_path=chunk.file_path,
                    symbol=chunk.symbol,
                    code=chunk.code,
                    explanation="실제 모델이 생성한 개선된 코드로 대체될 임시(Placeholder) 코드 블록입니다.",
                )
            )

        report = ReviewResponse(
            summary=(
                "검색된 Python 함수 청크 데이터를 바탕으로 구조화된 코드 리뷰가 생성되었습니다. "
                "해당 워크플로우는 LangGraph StateGraph를 사용하여 구성되었습니다."
            ),
            findings=findings,
            improved_code=improved_code,
            retrieval_attempts=state.get("retry_count", 0) + 1,
            used_query=state["current_query"],
            retrieved_context=state.get("retrieved_chunks", []),
        )
        return {"report": report}

    def run(self, context: ReviewContext, github_url: str, retriever, top_k: int) -> ReviewResponse:
        final_state = self._graph.invoke(
            {
                "question": context.question,
                "current_query": context.current_query,
                "retry_count": context.retry_count,
                "max_retries": context.max_retries,
                "retrieved_chunks": context.retrieved_chunks,
                "retrieval_decision": context.retrieval_decision,
                "report": context.report,
                "metadata": context.metadata,
                "github_url": github_url,
                "top_k": top_k,
                "retriever": retriever,
            }
        )
        report = final_state.get("report")
        if report is None:
            raise RuntimeError("Review workflow completed without producing a report.")
        return report
