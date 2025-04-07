from typing import Any, Set, Callable, Optional
import json
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
# from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from app.services.workday_service import WorkdayService
import asyncio
# from app.services.workday_service2 import WorkdayService
import os

# Create singleton instances
_canvas_service = CanvasService()
_stevens_service = StevensService()

# with sync_playwright() as playwright:
#     _workday_service = WorkdayService(
#         playwright,
#         current_academic_year="2025-2026 Semester Academic Calendar",
#         current_academic_semester="2025 Fall Semester(09/02/2025-12/22/2025)",
#         graduate_level="Graduate")

# def navigate_to_workday_registration_sync(mock_mode: bool = False) -> str:
#     try:
#         result = _workday_service.navigate_to_workday_registration(
#             mock_mode=mock_mode)

#         human_message = (
#             "I've redirected you to the Workday course registration page. "
#             "Here's more information on how you can register for courses: "
#             "https://support.stevens.edu/support/solutions/articles/19000082229"
#         ) if result.get("success") else None

#         return json.dumps({
#             "success": result["success"],
#             "message": result["message"],
#             "screenshot": result["screenshot"],
#             "human_message": human_message
#         })
#     except Exception as e:
#         return json.dumps({
#             "success":
#             False,
#             "error":
#             f"Error navigating to registration: {str(e)}"
#         })

_workday_service: Optional[WorkdayService] = None


async def get_workday_service() -> WorkdayService:
    global _workday_service
    if _workday_service is None:
        _workday_service = WorkdayService()
        await _workday_service.start()
    return _workday_service


async def navigate_to_workday_registration(mock_mode: bool = False) -> str:
    """
    Navigate to the course registration page in Workday.
    This will open a browser and prompt you to enter your credentials if not already logged in.

    Args:
        mock_mode: Use mock mode for testing without Playwright installed

    Returns:
        JSON string with navigation results
    """
    try:
        service = await get_workday_service()
        result = await service.navigate_to_workday_registration()

        human_message = (
            "I've redirected you to the Workday course registration page. "
            "Here's more information on how you can register for courses: "
            "https://support.stevens.edu/support/solutions/articles/19000082229"
        ) if result.get("success") else None

        return json.dumps({
            "success": result["success"],
            "message": result["message"],
            "screenshot": result["screenshot"],
            "human_message": human_message
        })
    except Exception as e:
        return json.dumps({
            "success":
            False,
            "error":
            f"Error navigating to registration: {str(e)}"
        })


async def navigate_to_workday_financial_account(
        mock_mode: bool = False) -> str:
    """
    Navigate to the financial account page in Workday.
    This will open a browser and prompt you to enter your credentials if not already logged in.

    Args:
        mock_mode: Use mock mode for testing without Playwright installed

    Returns:
        JSON string with navigation results
    """
    try:
        service = await get_workday_service()
        result = await service.navigate_to_workday_financial_account()
        human_message = (
            "I've redirected you to the Workday financial account page. "
        ) if result.get("success") else None

        return json.dumps({
            "success": result["success"],
            "message": result["message"],
            "screenshot": result["screenshot"],
            "human_message": human_message
        })

    except Exception as e:
        return json.dumps({
            "success":
            False,
            "error":
            f"Error navigating to financial account: {str(e)}"
        })


def run_async_tool(tool_coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run_coroutine_threadsafe(tool_coro, loop).result()
        else:
            return loop.run_until_complete(tool_coro)
    except RuntimeError:
        # In case no loop is set
        return asyncio.run(tool_coro)


def navigate_to_workday_registration_sync(mock_mode: bool = False) -> str:
    print("[DEBUG] Called sync wrapper for registration")
    return run_async_tool(navigate_to_workday_registration(mock_mode))


def navigate_to_workday_financial_account_sync(mock_mode: bool = False) -> str:
    print("[DEBUG] Called sync wrapper for financial")
    return run_async_tool(navigate_to_workday_financial_account(mock_mode))


def get_course_assignments(course_identifier: str) -> str:
    """
    Gets upcoming assignments for a specific course.

    :param course_identifier: The course name or ID (e.g., "CS115", "Machine Learning").
    :return: A JSON string of assignment information.
    """
    assignments = _canvas_service.get_assignments_for_course(course_identifier)
    return json.dumps(assignments)


def get_current_courses() -> str:
    """
    Gets all current courses for the student.

    :return: A JSON string of course information.
    """
    courses = _canvas_service.get_current_courses()
    return json.dumps(courses)


def get_upcoming_courses_assignments() -> str:
    """
    Gets upcoming assignments for all enrolled courses.

    :return: A JSON string of assignments for all courses.
    """
    courses = _canvas_service.get_current_courses()
    all_assignments = []

    for course in courses:
        assignments = _canvas_service.get_assignments_for_course(course['id'])
        if assignments:
            all_assignments.append({
                "course_name": course["name"],
                "assignments": assignments
            })

    return json.dumps({"courses": all_assignments})


# TODO: add db, these info will either be stored in db or vector db
def get_academic_calendar_event(event_type: str) -> str:
    """
    Gets information about academic calendar events.

    :param event_type: Type of academic calendar event (e.g., 'spring break', 'finals week').
    :return: A JSON string of calendar event information.
    """
    event = _stevens_service.get_calendar_event(event_type)
    return json.dumps(event)


# TODO: add db, these info will either be stored in db or vector db
def get_program_requirements(program: str) -> str:
    """
    Gets course requirements for a specific degree program.

    :param program: Degree program name (e.g., 'AAI masters', 'Computer Science PhD').
    :return: A JSON string of program requirements.
    """
    requirements = _stevens_service.get_program_requirements(program)
    return json.dumps(requirements)


def get_announcements_for_all_courses() -> str:
    """
    Gets announcements for all enrolled courses.

    :return: A JSON string of announcements for all courses.
    """
    courses = _canvas_service.get_current_courses()
    all_announcements = []

    for course in courses:
        announcements = _canvas_service.get_announcements_for_course(
            course['id'])
        if announcements:
            all_announcements.append({
                "course_name": course["name"],
                "announcements": announcements
            })

    return json.dumps({"courses": all_announcements})


def get_announcements_for_specific_courses(course_identifier: str) -> str:
    """
    Gets announcements for specific courses.

    :param course_identifier: Course code or name (e.g., 'EE 553', 'C++').
    :return: A JSON string of announcements for the specified course.
    """
    announcements = _canvas_service.get_announcements_for_course(
        course_identifier)
    return json.dumps(announcements)


# Register all functions
user_functions: Set[Callable[..., Any]] = {
    get_course_assignments,
    get_current_courses,
    get_upcoming_courses_assignments,
    get_academic_calendar_event,
    get_program_requirements,
    get_announcements_for_all_courses,
    get_announcements_for_specific_courses,
    # navigate_to_workday_registration_sync,
    # navigate_to_workday_financial_account_sync,
    navigate_to_workday_registration,
    navigate_to_workday_financial_account
}

# Define all the available user functions with their schemas
user_functions_schema = [{
    "name": "get_user_context",
    "description":
    "Retrieves context data for the user from multiple sources in a single call. The user profile comes from the User Service, while courses, assignments, and announcements come from Canvas API, and professors data comes from Stevens API. Use this to request several types of data at once. For example, to get profile and assignments information, call get_user_context(context_types=['profile', 'assignments']).",
    "parameters": {
        "type": "object",
        "properties": {
            "context_types": {
                "type": "array",
                "description": "List of context types to retrieve",
                "items": {
                    "type":
                    "string",
                    "enum": [
                        "profile", "courses", "assignments", "announcements",
                        "professors"
                    ]
                }
            }
        },
        "required": ["context_types"]
    }
}, {
    "name": "get_course_assignments",
    "description": "Get assignments for a specific course",
    "parameters": {
        "type": "object",
        "properties": {
            "course_identifier": {
                "type": "string",
                "description": "Course name, code, or ID"
            }
        },
        "required": ["course_identifier"]
    }
}, {
    "name": "navigate_to_workday_registration",
    "description":
    "Navigate to the course registration page in Workday. This will open a browser and prompt you to enter your credentials if not already logged in.",
    "parameters": {
        "type": "object",
        "properties": {
            "mock_mode": {
                "type": "boolean",
                "description": "Use mock mode for testing without Playwright"
            }
        }
    }
}, {
    "name": "navigate_to_workday_financial_account",
    "description":
    "Navigate to the financial account page in Workday. This will open a browser and prompt you to enter your credentials if not already logged in.",
    "parameters": {
        "type": "object",
        "properties": {
            "mock_mode": {
                "type": "boolean",
                "description": "Use mock mode for testing without Playwright"
            }
        }
    }
}]
