from functools import lru_cache
from app.db.database import get_cosmos_database
from app.services.stevens_service import StevensService
from app.services.canvas_service import CanvasService
from app.services.voice_service import AzureVoiceService  # ✅ Add this import
from typing import AsyncGenerator


@lru_cache()
def get_services(cosmos_db):
    """Create singleton instances of services with injected dependencies"""
    return {
        "stevens_service": StevensService(cosmos_db),  # Existing
        "canvas_service": CanvasService(),             # Existing
        "voice_service": AzureVoiceService(),          # ✅ New Voice Service
    }


async def get_service_context() -> AsyncGenerator[dict, None]:
    """Dependency that provides service instances"""
    cosmos_db = await get_cosmos_database()
    services = get_services(cosmos_db)
    yield services
