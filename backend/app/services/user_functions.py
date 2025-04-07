from typing import Any, Set, Callable, Optional
import json
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
from playwright.async_api import async_playwright
from app.services.workday_service import WorkdayService
import asyncio
import os
from threading import Thread

# Create singleton instances
_canvas_service = CanvasService()
_stevens_service = StevensService()

_workday_service: Optional[WorkdayService] = None


async def get_workday_service() -> WorkdayService:
    global _workday_service
    if _workday_service is None:
        playwright = await async_playwright().start()
        _workday_service = WorkdayService(playwright)

        await _workday_service.start()
    return _workday_service


async def navigate_to_workday_registration(mock_mode: bool = False,
                                           stay_open: bool = False) -> str:
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
        result = await service.navigate_to_workday_registration(stay_open)

        print(
            f"***************Navigated to Workday registration page: {result}")

        
        final_result = {
            "success":
            result["success"],
            "message":
            result["message"],
            "screenshot":
            result.get("screenshot"),
            "human_message":
            ("✅ I've redirected you to the Workday course registration page.\n\n"
             "ℹ️ Here's more information on how you can register for courses: "
             "https://support.stevens.edu/support/solutions/articles/19000082229"
             ) if result["success"] else
            "❌ I couldn't navigate to the registration page."
        }
        if not stay_open:
            await service.close()

        print("[DEBUG] Tool result returned to agent:",
              json.dumps(final_result))

        return json.dumps(final_result)

    except Exception as e:
        return json.dumps({
            "success":
            False,
            "error":
            f"Error navigating to registration: {str(e)}",
            "human_message":
            "❌ I couldn't navigate to the registration page. Try logging in manually at https://stevens.okta.com/"
        })


async def navigate_to_workday_financial_account(mock_mode: bool = False,
                                                stay_open: bool = False
                                                ) -> str:
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
        result = await service.navigate_to_workday_financial_account(stay_open)

        if not stay_open:
            await service.close()

        return json.dumps({
            "success":
            result["success"],
            "message":
            result["message"],
            "screenshot":
            result.get("screenshot"),
            "human_message":
            ("✅ I've redirected you to the Workday financial account page.\n\n"
             ) if result["success"] else
            "❌ I couldn't navigate to the financial account page."
        })

    except Exception as e:
        return json.dumps({
            "success":
            False,
            "error":
            f"Error navigating to financial account: {str(e)}"
        })


async def shutdown_workday_browser() -> str:
    try:
        if _workday_service:
            await _workday_service.close()
            return json.dumps({
                "success": True,
                "message": "Browser closed successfully."
            })
        return json.dumps({
            "success": False,
            "message": "WorkdayService is not active."
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def shutdown_workday_browser_sync() -> str:
    return run_async_tool(shutdown_workday_browser())


_background_loop = asyncio.new_event_loop()


def _start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


# Start the background thread
t = Thread(target=_start_background_loop,
           args=(_background_loop, ),
           daemon=True)
t.start()


def run_async_tool(tool_coro):
    print("[DEBUG] run_async_tool: scheduling on background loop")
    try:
        future = asyncio.run_coroutine_threadsafe(tool_coro, _background_loop)
        result = future.result()  # This blocks but safely waits for the result
        print("[DEBUG] run_async_tool: coroutine finished")
        return result
    except Exception as e:
        print(f"[ERROR] Exception in run_async_tool: {e}")
        return json.dumps({
            "success": False,
            "error": f"Exception during async tool run: {str(e)}"
        })


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
    navigate_to_workday_registration_sync,
    navigate_to_workday_financial_account_sync,
    # navigate_to_workday_registration,
    # navigate_to_workday_financial_account
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
    "name": "navigate_to_workday_registration_sync",
    "description":
    "Navigate to the course registration page in Workday. This will open a browser and prompt you to enter your credentials if not already logged in.",
    "parameters": {
        "type": "object",
        "properties": {
            "mock_mode": {
                "type": "boolean",
                "description": "Use mock mode for testing without Playwright"
            },
            "stay_open": {
                "type":
                "boolean",
                "description":
                "Stay open the browser after navigating to the registration page, set to true"
            }
        }
    }
}, {
    "name": "navigate_to_workday_financial_account_sync",
    "description":
    "Navigate to the financial account page in Workday. This will open a browser and prompt you to enter your credentials if not already logged in.",
    "parameters": {
        "type": "object",
        "properties": {
            "mock_mode": {
                "type": "boolean",
                "description": "Use mock mode for testing without Playwright"
            },
            "stay_open": {
                "type":
                "boolean",
                "description":
                "Stay open the browser after navigating to the financial account page, set to true"
            }
        }
    }
}]
