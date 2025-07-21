from dotenv import load_dotenv
import os
import logging

from fastapi import Depends
import time
import pathlib

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load .env file with multiple fallback paths
def load_environment():
    """Load environment variables from .env file with multiple fallback paths"""
    possible_env_paths = [
        # Current directory (if running from project root)
        pathlib.Path.cwd() / '.env',
        # Parent of backend directory (normal case)
        pathlib.Path(__file__).parent.parent / '.env',
        # Grandparent (if running from deeper nested directory)
        pathlib.Path(__file__).parent.parent.parent / '.env',
        # Explicit project root (when debugging)
        pathlib.Path(__file__).parent.parent / '.env',
    ]
    
    for env_path in possible_env_paths:
        if env_path.exists():
            logger.info(f"📄 Loading .env from: {env_path}")
            load_dotenv(env_path)
            return env_path
    
    logger.warning("⚠️ No .env file found. Using system environment variables only.")
    return None

# Load environment variables
loaded_env_path = load_environment()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Configure LangSmith tracing after settings import
if settings.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
    os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    logger.info("✅ LangSmith tracing enabled")
else:
    logger.info("⚠️ LangSmith API key not found - tracing disabled")
from contextlib import asynccontextmanager
from app.api import chat, workday

from app.services.canvas_service import CanvasService

# global cache manager for repeat queries

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
# @app.get("/calendar_events")
# async def get_calendar_events(service: dict = Depends(get_service_context)):
#     """Get calendar events"""
#     stevens_service = service["stevens_service"]
#     events = await stevens_service.get_calendar_event()
#     return {"events_count": len(events), "events": events}


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
    return {"announcements": announcements}





if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
