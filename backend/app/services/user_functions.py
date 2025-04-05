from typing import Any, Set, Callable, Dict, List, Optional
import json
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
from app.services.workday_service import WorkdayService
import os

# Create singleton instances
_canvas_service = CanvasService()
_stevens_service = StevensService()


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
}

# Add workday-related functions


def login_to_workday(username: Optional[str] = None,
                     password: Optional[str] = None) -> str:
    """
    Log in to Stevens Workday system.
    
    Args:
        username: Optional username (will use environment variable if not provided)
        password: Optional password (will use environment variable if not provided)
        
    Returns:
        JSON string with login results
    """
    workday_service = WorkdayService(headless=False)
    try:
        result = workday_service.login(username, password)
        if result["success"]:
            # Don't include the full HTML in the response
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result.pop("html", None)
        return json.dumps(result)
    finally:
        workday_service.close()


def navigate_to_academics() -> str:
    """
    Navigate to the Academics section in Workday.
    Requires being logged in first.
    
    Returns:
        JSON string with navigation results
    """
    workday_service = WorkdayService(headless=False)
    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before navigating to academics",
                    "login_error": login_result.get("error")
                })

        # Now navigate to academics
        result = workday_service.navigate_to_academics()
        if result["success"]:
            # Don't include the full HTML in the response
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result.pop("html", None)
        return json.dumps(result)
    finally:
        workday_service.close()


def search_workday_courses(term: str, subject: Optional[str] = None) -> str:
    """
    Search for courses in Workday.
    
    Args:
        term: Academic term to search for (e.g., "Fall 2023")
        subject: Optional subject filter (e.g., "Computer Science")
        
    Returns:
        JSON string with search results
    """
    workday_service = WorkdayService(headless=False)
    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before searching courses",
                    "login_error": login_result.get("error")
                })

        # Now search courses
        result = workday_service.search_courses(term, subject)
        if result["success"]:
            # Don't include the full HTML in the response
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result.pop("html", None)
        return json.dumps(result)
    finally:
        workday_service.close()


def extract_workday_page(step_name: str, take_screenshot: bool = False) -> str:
    """
    Extract HTML from the current page in Workday with identifying step name.
    
    Args:
        step_name (str): Name to identify this extraction step
        take_screenshot (bool): Whether to take a screenshot (should only be True for final pages)
        
    Returns:
        JSON string with extraction results
    """
    workday_service = WorkdayService(headless=False)
    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before extracting page",
                    "login_error": login_result.get("error")
                })

        # Now extract page
        result = workday_service.extract_current_page(
            step_name, take_screenshot=take_screenshot)
        if result["success"] and result.get("screenshot"):
            # Only include screenshot if it was taken (final pages only)
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result["screenshot_abs_path"] = os.path.abspath(
                result["screenshot"])
            result.pop("html", None)
        else:
            # No screenshot was taken
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result.pop("html", None)

        return json.dumps(result)
    finally:
        workday_service.close()


def validate_registration_page() -> str:
    """
    Take a screenshot of the current page and check if it appears to be a registration page.
    The screenshot can be analyzed by an AI vision model to verify the page contents.
    
    Returns:
        JSON string with screenshot path and validation results
    """
    workday_service = WorkdayService(headless=False)
    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before validating page",
                    "login_error": login_result.get("error")
                })

        # Check if on registration page
        result = workday_service.check_if_on_registration_page()

        # Add absolute path for the screenshot to make it easier to find
        if result["success"] and result.get("screenshot"):
            result["screenshot_abs_path"] = os.path.abspath(
                result["screenshot"])

        return json.dumps(result)
    finally:
        workday_service.close()


def automate_course_registration(course_code: str) -> str:
    """
    Automate the course registration process for a specific course.
    
    Args:
        course_code: The code of the course to register for (e.g., "CS 101")
        
    Returns:
        JSON string with registration results and screenshots
    """
    workday_service = WorkdayService(headless=False)
    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before registering for course",
                    "login_error": login_result.get("error")
                })

        # Automate course registration
        result = workday_service.automate_course_registration(course_code)

        # Add absolute paths for screenshots
        if result["success"] and result.get("screenshots"):
            result["screenshot_abs_paths"] = [
                os.path.abspath(s) for s in result["screenshots"] if s
            ]

        return json.dumps(result)
    finally:
        workday_service.close()


# Register all functions
user_functions: Set[Callable[..., Any]] = {
    get_course_assignments,
    get_current_courses,
    get_upcoming_courses_assignments,
    get_academic_calendar_event,
    get_program_requirements,
    get_announcements_for_all_courses,
    get_announcements_for_specific_courses,
    get_user_context,
    # Add the new Workday functions
    login_to_workday,
    navigate_to_academics,
    search_workday_courses,
    extract_workday_page,
    validate_registration_page,
    automate_course_registration
}

# Define all the available user functions
user_functions = [{
    "name": "get_user_context",
    "description":
    "Retrieves context data for the user from multiple sources in a single call. Instead of making multiple separate function calls, use this to request several types of data at once. For example, to get both course and assignment information, call get_user_context(context_types=['courses', 'assignments']). This is more efficient than calling individual functions.",
    "parameters": {
        "type": "object",
        "properties": {
            "context_types": {
                "type": "array",
                "description":
                "List of context types to retrieve (e.g., courses, assignments, announcements, professors)",
                "items": {
                    "type":
                    "string",
                    "enum":
                    ["courses", "assignments", "announcements", "professors"]
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
    "name": "get_upcoming_courses_assignments",
    "description": "Get upcoming assignments for all courses",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "get_all_courses",
    "description": "Get all courses",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "get_professors",
    "description": "Get information about professors",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "get_announcements_for_all_courses",
    "description": "Get announcements for all courses",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "get_announcements_for_specific_courses",
    "description": "Get announcements for a specific course",
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
    "name": "login_to_workday",
    "description":
    "Log in to Stevens Workday system to access course registration, academic records and more",
    "parameters": {
        "type": "object",
        "properties": {
            "username": {
                "type":
                "string",
                "description":
                "Workday username (optional, will use environment variable if not provided)"
            },
            "password": {
                "type":
                "string",
                "description":
                "Workday password (optional, will use environment variable if not provided)"
            }
        }
    }
}, {
    "name": "navigate_to_academics",
    "description":
    "Navigate to the Academics section in Workday to access course information",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "search_workday_courses",
    "description": "Search for courses in the Workday system",
    "parameters": {
        "type": "object",
        "properties": {
            "term": {
                "type": "string",
                "description":
                "Academic term to search for (e.g., 'Fall 2023')"
            },
            "subject": {
                "type": "string",
                "description":
                "Optional subject filter (e.g., 'Computer Science')"
            }
        },
        "required": ["term"]
    }
}, {
    "name": "extract_workday_page",
    "description": "Extract HTML from the current Workday page for analysis",
    "parameters": {
        "type": "object",
        "properties": {
            "step_name": {
                "type":
                "string",
                "description":
                "Name to identify this extraction step (e.g., 'course_catalog', 'registration_page')"
            },
            "take_screenshot": {
                "type":
                "boolean",
                "description":
                "Whether to take a screenshot (should only be True for final pages)"
            }
        },
        "required": ["step_name"]
    }
}, {
    "name": "validate_registration_page",
    "description":
    "Take a screenshot of the current page and check if it appears to be a registration page",
    "parameters": {}
}, {
    "name": "automate_course_registration",
    "description":
    "Automate the course registration process for a specific course",
    "parameters": {
        "type": "object",
        "properties": {
            "course_code": {
                "type":
                "string",
                "description":
                "The code of the course to register for (e.g., 'CS 101')"
            }
        },
        "required": ["course_code"]
    }
}]
