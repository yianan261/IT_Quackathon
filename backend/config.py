import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
# dummy URL, need to add db later
DATABASE_URL: str = "sqlite:///./dummy.db"

# CosmosDB Settings
COSMOSDB_URI: Optional[str] = None
COSMOSDB_KEY: Optional[str] = None
COSMOSDB_DATABASE: str = "stevens-ai"


class Config:
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    CANVAS_API_URL = os.getenv('CANVAS_API_URL')
    CANVAS_API_KEY = os.getenv('CANVAS_API_KEY')
    MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')
