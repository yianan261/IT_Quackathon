from dotenv import load_dotenv
import os
import logging
from app.context import get_service_context
from fastapi import Depends
import time

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

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


@app.get("/test/canvas/grades")
async def test_canvas_grades():
    """
    Test endpoint for Canvas grades API.
    Retrieves grades for all active courses.
    """
    grades = canvas.get_grades_for_all_courses()
    return {
        "grades": grades
    }


@app.get("/test/canvas/grades/{course_id}")
async def test_canvas_grades_for_course(course_id: int):
    """
    Test endpoint for Canvas grades API.
    Retrieves grades for a specific course.
    """
    grades = canvas.get_grades_for_course(course_id)
    return {
        "course_id": course_id,
        "grades": grades
    }


@app.get("/test/automation")
async def test_automation():
    """
    提供自动化指令的测试端点，用于Browser Automation。
    指令包含：
    1. 导航到指定URL
    2. 根据选择器点击元素
    3. 等待页面加载后点击 Academics 按钮
    """
    automation_instruction = {
        "action": "multi_step_navigation",
        "target_url": "https://login.stevens.edu/app/UserHome",
        "steps": [
            {
                "action": "click",
                "description": "Workday card",
                "selector": "div.app-button img[alt='Workday']",  # 最精确的选择器
                "fallback_selectors": [
                    # 基于图像的选择器
                    "img[alt='Workday']",
                    "img[src*='workday']",
                    
                    # 基于文本的选择器
                    ".app-button-name:contains('Workday')",
                    "div:contains('Workday')",
                    
                    # 特定元素结构选择器
                    "a[aria-label*='Workday']",
                    "div[title='Workday']",
                    ".app-button[href*='workday']",
                ],
                "timeout": 10000,  # 10秒超时
                "critical": True   # 标记为关键操作
            },
            {
                "action": "click",
                "description": "Academics button in Workday",
                "selector": "button[data-automation-id*='academics' i], button[aria-label*='Academics' i]",  # 更精确的选择器，使用不区分大小写的匹配
                "fallback_selectors": [
                    # 更丰富的基于文本的选择器
                    "button:has(span:contains('Academics'))",
                    "button:contains('Academics')",
                    "div[role='button']:contains('Academics')",
                    
                    # 更宽松的基于属性的选择器
                    "div[aria-label*='academics' i]",
                    "a[aria-label*='academics' i]",
                    "div[class*='academics' i]",
                    
                    # 基于图像或图标的选择器
                    "img[alt*='academics' i]",
                    
                    # 通用容器选择器
                    "[role='menuitem']:contains('Academics')",
                    ".gwt-Label:contains('Academics')",
                    "#workdayApplications a:contains('Academics')",
                    
                    # Workday 特有的选择器
                    "[data-automation-widget-type='BUTTON']:contains('Academics')"
                ],
                "wait_before_click": 4000,  # 增加等待时间至7秒，确保Workday页面完全加载
                "timeout": 20000,  # 增加超时时间至20秒
                "critical": True   # 标记为关键操作
            }
        ],
        "session_id": f"test-session-{int(time.time())}"  # 使用时间戳确保每次ID不同
    }
    
    return {
        "status": "success",
        "message": "Multi-step automation instruction ready",
        "instruction": automation_instruction
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
