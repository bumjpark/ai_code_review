from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ai-code-review"
    api_prefix: str = "/api"
    rag_service_url: str = "http://localhost:8001"
    langgraph_service_url: str = "http://localhost:8002"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "code_chunks"
    qdrant_vector_size: int = 1536
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4.1-mini"
    openai_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
