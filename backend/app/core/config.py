from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Stevens AI Assistant"

    OPENAI_API_KEY: Optional[str] = None

    VECTOR_DB_PATH: str = "vector_db"

    CANVAS_API_URL: str
    CANVAS_API_KEY: str

    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str

    # dummy URL, need to add db later
    DATABASE_URL: str = "sqlite:///./dummy.db"

    # CosmosDB Settings
    COSMOSDB_URI: Optional[str] = None
    COSMOSDB_KEY: Optional[str] = None
    COSMOSDB_DATABASE: str = "stevens-ai"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
