from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Stevens AI Assistant"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    MAX_TOKENS: int = 1000

    # LangSmith Configuration
    LANGCHAIN_TRACING_V2: str = "true"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "stevens-ai-assistant"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    VECTOR_DB_PATH: str = "vector_db"

    CANVAS_API_URL: Optional[str] = "https://stevens.instructure.com/api/v1"
    CANVAS_API_KEY: Optional[str] = "1030~2PcFfvh6H9WGCQZyYBRzHCkHG2RFMNXVU4kFzNv2WDVENeMtMwkHuhhFPhfKkVZQ"

    # Azure-specific settings (deprecated, no longer used)
    # CONN_STR: str
    # AGENT_ID: str

    DATABASE_URL: str = "sqlite:///./dummy.db"

    COSMOSDB_URI: Optional[str] = None
    COSMOSDB_KEY: Optional[str] = None
    COSMOSDB_DATABASE: str = "stevens-ai"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
