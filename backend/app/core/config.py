from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Stevens AI Assistant"

    OPENAI_API_KEY: Optional[str] = None

    VECTOR_DB_PATH: str = "vector_db"

    CANVAS_API_URL: str
    CANVAS_API_KEY: str

    CONN_STR: str
    AGENT_ID: str

    DATABASE_URL: str = "sqlite:///./dummy.db"

    COSMOSDB_URI: Optional[str] = None
    COSMOSDB_KEY: Optional[str] = None
    COSMOSDB_DATABASE: str = "stevens-ai"
    
   #for webpage
    COSMOS_ENDPOINT: str
    COSMOS_URI: str | None = None
    COSMOS_KEY: str
    COSMOS_DATABASE: str = "stevens-ai"
    COSMOS_CONTAINER: str = "students"

    class Config:
        env_file = ".env"
        # case_sensitive = True
        # extra = "allow"


settings = Settings()
