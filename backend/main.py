from dotenv import load_dotenv
import os
import logging
from app.context import get_service_context
from fastapi import Depends
import time
import pathlib
from app.api import voice 

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load .env from parent directory
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from app.api import chat, workday
from cache_manager import CacheManager
from app.services.canvas_service import CanvasService

# global cache manager for repeat queries
cache_manager = CacheManager()
canvas = CanvasService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")

    yield

    logger.info("Application is shutting down...")


# initialize app with the lifespan
app = FastAPI(
    title="Stevens AI Assistant API",
    description="Backend API for Stevens AI Assistant Chrome Extension",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])


# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(chat.router, prefix="/api/chat")
app.include_router(workday.router, prefix="/api/workday")


@app.get("/")
async def root():
    return {"message": "Welcome to Stevens AI Assistant API"}


# TODO: add vector search, get cached data from cache manager
@app.get("/search")
async def search_endpoint(query: str):
    pass


@app.get("/test")
async def test_endpoint():
    return {"status": "ok"}


@app.get("/test/canvas")
async def test_canvas():
    """Test endpoint for Canvas API"""
    courses = canvas.get_current_courses()
    return {"courses_count": len(courses), "courses": courses}


@app.get("/test/canvas/assignments/{course_id}")
async def test_canvas_assignments(course_id: int):
    """Test endpoint for Canvas Assignments API"""
    assignments = canvas.get_assignments_for_course(course_id)
    return {
        "course_id": course_id,
        "assignments_count": len(assignments),
        "assignments": assignments,
        "raw_response": canvas.get_raw_assignments(course_id),
    }


# dependency injection for stevens services
# TODO: need to define these functions
@app.get("/calendar_events")
async def get_calendar_events(service: dict = Depends(get_service_context)):
    """Get calendar events"""
    stevens_service = service["stevens_service"]
    events = await stevens_service.get_calendar_event()
    return {"events_count": len(events), "events": events}


# get annoucements
# method : get

@app.get("/test/canvas/annoucements")
async def test_canvas_annoucements():
    """
    Test endpoint for Canvas announcements API.
    Retrieves announcements for the specified course ID.
    """
    announcements = canvas.get_announcements_for_all_courses()
    # announcements = canvas.format_announcements_response(announcements)
    return {
        
        "announcements": announcements
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
