# ai_code_review

4개 레이어로 분리한 AI 코드 리뷰 시스템 초기 스캐폴딩입니다.

## Architecture

### 1. Frontend
- GitHub public repo URL 입력
- 질문 입력
- 리뷰 결과 JSON 표시

### 2. Backend (FastAPI)
- API 진입점
- `/api/index`: RAG 서비스에 인덱싱 요청 전달
- `/api/review`: LangGraph 서비스에 리뷰 요청 전달

### 3. LangGraph Layer
- 질문 분석
- retrieval 품질 판단
- query rewrite
- 재검색
- 코드 리뷰 생성
- 개선안 생성
- 최종 report 생성
- Self-RAG 재시도는 최대 1회
- `langgraph` 라이브러리의 `StateGraph` 기반으로 조건 분기 수행
- 독립 서비스로 배포되며 RAG 서비스의 retrieval API를 호출

### 4. RAG Layer
- GitHub public Python repo clone
- `.py` 파일 AST 파싱
- 함수 단위 청킹
- 임베딩 후 Qdrant 저장
- 리뷰 시 Qdrant 기반 retrieval 수행
- 독립 서비스로 배포되며 `/index`, `/retrieve` API 제공

## Response Schema

최종 응답은 구조화된 JSON입니다.

```json
{
  "summary": "string",
  "findings": [
    {
      "severity": "low|medium|high|critical",
      "title": "string",
      "file_path": "string",
      "line": 10,
      "rationale": "string",
      "recommendation": "string"
    }
  ],
  "improved_code": [
    {
      "file_path": "string",
      "symbol": "string",
      "code": "string",
      "explanation": "string"
    }
  ]
}
```

## Project Layout

```text
backend/
  app/
    api/
    models/
    services/
langgraph_layer/
rag_layer/
frontend/
```

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

## Docker

실행용 컨테이너는 `frontend`, `backend`, `langgraph`, `rag`, `qdrant` 로 나눴습니다.

- `frontend`: 사용자 UI
- `backend`: 메인 API 진입점
- `langgraph`: 리뷰 오케스트레이션 서비스
- `rag`: 인덱싱/검색 서비스
- `qdrant`: 벡터 DB

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- LangGraph service: `http://localhost:8002`
- RAG service: `http://localhost:8001`
- Qdrant: `http://localhost:6333`

## Environment

`.env` 에 최소한 아래 값을 넣어야 합니다.

```env
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=code_chunks
QDRANT_VECTOR_SIZE=1536
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4.1-mini
RAG_SERVICE_URL=http://localhost:8001
LANGGRAPH_SERVICE_URL=http://localhost:8002
```

## Notes

- Qdrant만 사용하며 별도 DB는 두지 않습니다.
- 임베딩은 OpenAI Embeddings API를 사용하도록 연결했습니다.
- 로컬 Qdrant는 `QDRANT_API_KEY` 없이 사용할 수 있고, Qdrant Cloud는 `QDRANT_URL` 과 `QDRANT_API_KEY` 를 함께 넣으면 됩니다.
- Docker Compose에서는 서비스 간 통신 주소를 각 컨테이너 이름으로 자동 오버라이드합니다.
- 환경설정은 `.env` 파일 하나만 사용합니다. `.env` 는 `.gitignore` 에 포함되어 있어 로컬에서만 관리합니다.
- 리뷰 생성 노드는 아직 placeholder이므로 실제 운영용 LLM 호출은 별도로 연결해야 합니다.
