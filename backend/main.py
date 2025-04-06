from dotenv import load_dotenv
import os
import logging
from app.context import get_service_context
from fastapi import Depends
import time
import pathlib

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
    return {"announcements": announcements}


@app.get("/test/automation")
async def test_automation():
    """
    提供自动化指令的测试端点，用于Browser Automation。
    指令包含：
    1. 导航到指定URL
    2. 根据选择器点击元素
    3. 等待页面加载后点击 Academics 按钮
    4. 点击 Find Course Sections 并验证对话框
    """
    # 生成唯一会话ID，防止重复执行
    session_id = f"test-session-{int(time.time())}"

    automation_instruction = {
        "action":
        "multi_step_navigation",
        "target_url":
        "https://login.stevens.edu/app/UserHome",
        "steps": [
            # 步骤1: 点击 Workday 卡片
            {
                "action":
                "click",
                "description":
                "Workday card",
                "selector":
                "div.app-button img[alt='Workday']",  # 最精确的选择器
                "fallback_selectors": [
                    # 基于图像的选择器
                    "img[alt='Workday']",
                    "img[src*='workday']",

                    # 基于文本的选择器
                    "div.app-button-name span",
                    "div[title='Workday']",

                    # 特定元素结构选择器
                    "a[aria-label*='Workday']",
                    "div[title='Workday']",
                    ".app-button[href*='workday']",
                ],
                "timeout":
                15000,  # 增加超时时间
                "wait_before_click":
                1000,  # 增加点击前等待时间
                "critical":
                True  # 标记为关键操作
            },
            # 步骤2: 点击 Academics 按钮
            {
                "action":
                "click",
                "description":
                "Academics button in Workday",
                "selector":
                "button[data-automation-id*='academics' i], button[aria-label*='Academics' i]",
                "fallback_selectors": [
                    # 基于标题和文本的选择器
                    "button span[title='Academics']",
                    "button[title*='Academics']",
                    "div[role='button'][title*='Academics']",

                    # 基于内容的选择器
                    "button:has(span:contains(Academics))",
                    "button span[title*='Academics']",
                    "div[aria-label*='academics' i]",
                    "a[aria-label*='academics' i]",
                    "div[class*='academics' i]",
                    "img[alt*='academics' i]",

                    # Workday 特有的选择器
                    "[role='menuitem'][title*='Academics']",
                    "[data-automation-widget-type='BUTTON'][title*='Academics']",

                    # 通用选择器 - 任何包含Academics文本的可交互元素
                    "[tabindex='0']:has(div:contains(Academics))"
                ],
                "wait_before_click":
                3000,  # 增加等待时间，确保页面完全加载
                "timeout":
                25000,  # 增加超时时间
                "critical":
                True  # 标记为关键操作
            },
            # 步骤3: 点击 Find Course Sections 选项
            {
                "action":
                "click",
                "description":
                "Find Course Sections option",
                "selector":
                "div[title='Find Course Sections']",  # 主选择器，基于title属性
                "fallback_selectors": [
                    # 基于类和文本内容的选择器
                    ".WG-C[title='Find Course Sections']",
                    "div.gwt-Label[title='Find Course Sections']",

                    # 基于文本内容的选择器
                    "div[title*='Find Course Sections']",
                    "div[aria-label*='Find Course Sections']",

                    # 基于父子关系的选择器
                    "div.WG-C",

                    # Workday特有的选择器
                    "[data-automation-id*='menuItem'][title*='Find Course Sections']",
                    "[role='menuitem'][title*='Find Course Sections']",

                    # 更通用的选择器作为最后的回退
                    "div[role='button']",
                    "[tabindex='0']"
                ],
                "wait_before_click":
                4000,  # 增加等待时间，确保元素完全加载和可点击
                "timeout":
                25000,  # 增加超时时间
                "critical":
                True  # 标记为关键操作
            },
            # 步骤4: 验证 Find Course Sections 对话框是否出现
            {
                "action":
                "verify_dialog",
                "description":
                "Find Course Sections dialog",
                "selector":
                "[data-automation-id='editPopup'][aria-modal='true']",  # 主选择器，基于自动化ID和modal属性
                "fallback_selectors": [
                    # 基于role和其他属性的选择器
                    "div[role='dialog'][aria-modal='true']",
                    "div.WCU[data-popup-version]",

                    # 基于类的选择器
                    "div.WNT.WHFH",
                    ".wd-popup[aria-modal='true']",

                    # 更通用的选择器作为最后兜底方案
                    "[aria-modal='true']",
                    "div.WCU.wd-popup",
                    "[data-automation-activepopup='true']"
                ],
                "timeout":
                20000,  # 增加超时时间
                "wait_after_verify":
                1000,  # 验证后等待时间，避免过快进行下一步
                "critical":
                True  # 标记为关键操作
            },
            # 步骤5: 点击 "Start Date within" 输入框
            {
                "action":
                "click",
                "description":
                "Start Date within input field",
                "selector":
                "input[placeholder='Search']",  # 简化为已知工作的选择器
                "fallback_selectors": [
                    # 基于自动化ID和类型的选择器
                    "[data-automation-id*='startDate'] input",
                    "[data-uxi-widget-type='selectinput']",

                    # 基于属性的选择器 (避免使用不正确的:contains选择器)
                    "input[aria-labelledby*='startDate']",
                    "input[type='text'][tabindex='0']",

                    # Workday特有的选择器
                    "input[tabindex='0'][aria-invalid='false']",

                    # 直接选择对话框中的搜索输入框
                    "[aria-modal='true'] input[type='text']",
                    "[data-automation-activepopup='true'] input"
                ],
                "wait_before_click":
                1000,  # 点击前等待时间
                "timeout":
                15000,  # 超时时间
                "critical":
                True  # 标记为关键操作
            },
            # 增加一个等待步骤，确保下拉菜单有足够时间显示
            {
                "action": "wait",
                "description": "Wait for dropdown to appear",
                "duration": 2000  # 等待2秒
            },
            # 步骤6: 选择 "Semester Academic Calendar" 选项
            {
                "action":
                "click",
                "description":
                "Semester Academic Calendar option",
                "selector":
                "div[title='Semester Academic Calendar'], [role='option']",  # 修改主选择器
                "fallback_selectors": [
                    # 基于标准属性的选择器 (避免使用:contains)
                    "[role='option']",
                    "[data-automation-label='Semester Academic Calendar']",

                    # 下拉菜单选项通用选择器
                    "[role='listbox'] [role='option']",
                    ".dropdown-list li",
                    ".dropdown-option",

                    # Workday特有的选择器
                    "[data-automation-id='promptOption']",
                    "div[data-automation-id*='dropdown'] div[role='option']",

                    # 基于文本搜索的辅助 (JavaScript逻辑会处理文本匹配)
                    "[role='option']",
                    "li",
                    "div[role='listitem']"
                ],
                "wait_before_click":
                2000,  # 增加点击前等待时间
                "timeout":
                15000,  # 超时时间
                "critical":
                True,  # 标记为关键操作
                "text_content":
                "Semester Academic Calendar"  # 添加文本内容以便JavaScript搜索
            }
        ],
        "session_id":
        session_id,  # 使用时间戳确保每次ID不同
        "debug_mode":
        True  # 启用调试模式，显示更多日志
    }

    return {
        "status": "success",
        "message": "Multi-step automation instruction ready",
        "instruction": automation_instruction
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
