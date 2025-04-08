from typing import Any, Set, Callable, Optional
import json
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
from playwright.sync_api import sync_playwright
from app.services.workday_service import WorkdayService
import asyncio
import os
from threading import Thread

# Create singleton instances
_canvas_service = CanvasService()
_stevens_service = StevensService()
with sync_playwright() as p:
    _workday_service = WorkdayService(p)


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


def login_to_workday(username: Optional[str] = None,
                     password: Optional[str] = None,
                     mock_mode: bool = False) -> str:
    """
    Log in to Stevens Workday system.
    
    Args:
        username: Optional username (will use environment variable if not provided)
        password: Optional password (will use environment variable if not provided)
        mock_mode: Use mock mode for testing without Playwright installed
        
    Returns:
        JSON string with login results
    """
    # Update the global singleton if mock mode is requested
    global _workday_service
    if mock_mode and not _workday_service.using_mock:
        _workday_service = WorkdayService(headless=False,
                                          mock_for_testing=True)

    try:
        result = _workday_service.login(username, password)

        # Check if we need user input for credentials
        if not result["success"] and result.get("needs_user_input", False):
            # Special case: return the message to the user to prompt for credentials
            print("Browser is open for user to enter credentials")

            # Add the screenshot path to make it accessible in the response
            if "screenshot" in result:
                abs_screenshot_path = os.path.abspath(result["screenshot"])
                result["screenshot_abs_path"] = abs_screenshot_path

            # Return the message to be shown to the user
            return json.dumps({
                "success":
                True,  # We mark this as success so the agent doesn't retry
                "message":
                result.get(
                    "message",
                    "Please enter your Stevens login credentials in the browser window"
                ),
                "needs_user_input":
                True,
                "screenshot":
                result.get("screenshot_abs_path", "")
            })

        if result["success"]:
            # Don't include the full HTML in the response
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result.pop("html", None)

            # Add absolute screenshot path
            if "screenshot" in result:
                result["screenshot_abs_path"] = os.path.abspath(
                    result["screenshot"])

        return json.dumps(result)
    finally:
        # Don't close the service since it's a singleton
        pass


def get_grades() -> str:
    """
    Gets grades for all enrolled courses in a simplified format.
    
    This function retrieves grades for all courses the student is enrolled in,
    returning a simplified format with only essential information.
    
    :return: A JSON string of grades information for all courses.
    """
    grades = _canvas_service.get_simplified_grades()
    return json.dumps(grades)

def get_grades_for_course(course_identifier: str) -> str:
    """
    Gets grades for a specific course in a simplified format.
    
    :param course_identifier: The course name, code, or ID (e.g., "CS115", "Machine Learning").
    :return: A JSON string of grades information for the specified course.
    """
    grades = _canvas_service.get_simplified_grades(course_identifier)
    return json.dumps(grades)
def navigate_to_workday_registration(mock_mode: bool = False) -> str:
    """
    Navigate to the course registration page in Workday.
    This will first ensure you are logged in, then navigate to the registration page.
    
    Args:
        mock_mode: Use mock mode for testing without Playwright installed
        
    Returns:
        JSON string with navigation results
    """
    # Update the global singleton if mock mode is requested
    global _workday_service
    if mock_mode and not _workday_service.using_mock:
        _workday_service = WorkdayService(headless=False,
                                          mock_for_testing=True)

    try:
        # Check if we are logged in
        if not _workday_service.logged_in:
            # First attempt login
            login_result = _workday_service.login()
            login_result_json = json.loads(json.dumps(login_result))

            # If login needs user input, forward that message
            if not login_result.get("success", False) and login_result.get(
                    "needs_user_input", False):
                # Add the screenshot path to make it accessible in the response
                if "screenshot" in login_result:
                    abs_screenshot_path = os.path.abspath(
                        login_result["screenshot"])
                    login_result["screenshot_abs_path"] = abs_screenshot_path

                # Return the message to be shown to the user
                return json.dumps({
                    "success":
                    True,  # We mark this as success so the agent doesn't retry
                    "message":
                    login_result.get(
                        "message",
                        "Please enter your Stevens login credentials in the browser window"
                    ),
                    "needs_user_input":
                    True,
                    "screenshot":
                    login_result.get("screenshot_abs_path", "")
                })

            # If login failed for some other reason, return that error
            if not login_result.get("success", False):
                return json.dumps({
                    "success":
                    False,
                    "error":
                    f"Failed to log in: {login_result.get('error', 'Unknown error')}",
                    "message":
                    "Cannot navigate to registration page without logging in first."
                })

        # Now navigate to academics
        academics_result = _workday_service.navigate_to_academics()
        if not academics_result.get("success", False):
            return json.dumps({
                "success":
                False,
                "error":
                f"Failed to navigate to academics: {academics_result.get('error', 'Unknown error')}",
                "message":
                "Cannot access course registration without navigating to academics first."
            })

        # TODO: Add actual navigation to registration page here
        # For now, we'll return success with the academics page
        if "screenshot" in academics_result:
            academics_result["screenshot_abs_path"] = os.path.abspath(
                academics_result["screenshot"])

        return json.dumps({
            "success":
            True,
            "message":
            "Successfully navigated to the academics page. From here, you can access course registration.",
            "screenshot":
            academics_result.get("screenshot_abs_path", "")
        })

    except Exception as e:
        return json.dumps({
            "success":
            False,
            "error":
            f"Error navigating to course registration: {str(e)}"
        })


# Register all functions
user_functions: Set[Callable[..., Any]] = {
    get_course_assignments,
    get_current_courses,
    get_upcoming_courses_assignments,
    get_program_requirements,
    get_announcements_for_all_courses,
    get_announcements_for_specific_courses,
    login_to_workday,
    navigate_to_workday_registration,
    get_grades,
    get_grades_for_course,
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
},
{
    "name": "get_advisors_info_sync",
    "description": "Gets advisor contact information scraped from Workday",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "get_grades",
    "description": "Get grades for all courses the student is enrolled in, in a simplified format with only essential information",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "get_grades_for_course",
    "description": "Get grades for a specific course in a simplified format with only essential information",
    "parameters": {
        "type": "object",
        "properties": {
            "course_identifier": {
                "type": "string",
                "description": "Course name, code, or ID (e.g., 'CS115', 'Machine Learning')"
            }
        },
        "required": ["course_identifier"]
    }
}]
