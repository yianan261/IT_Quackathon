from typing import Any, Set, Callable, Dict, List, Optional
import json
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
from app.services.workday_service import WorkdayService
from app.services.user_service import UserService
import os

# Create singleton instances
_canvas_service = CanvasService()
_stevens_service = StevensService()
_user_service = UserService()
_workday_service = WorkdayService(headless=False, mock_for_testing=False)


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


def get_user_context(context_types: List[str]) -> str:
    """
    Get comprehensive user context including profile and other requested information.
    
    Args:
        context_types: List of context types to retrieve
                      (e.g., "profile", "assignments", "announcements", "professors")
                      
    Returns:
        JSON string with the requested user context information
    """
    # Start with basic result structure and metadata
    result = {
        "context_meta": {
            "retrieved_at": _user_service._get_current_timestamp(),
            "requested_types": context_types,
            "source_systems": ["User Service (Mock)"]
        }
    }

    # Get profile data from UserService if requested
    if "profile" in context_types:
        result["profile"] = _user_service.get_user_info()

    # Get courses directly from Canvas API if requested
    if "courses" in context_types:
        courses = _canvas_service.get_current_courses()
        result["courses"] = {"success": True, "data": courses, "error": None}
        if "Canvas API" not in result["context_meta"]["source_systems"]:
            result["context_meta"]["source_systems"].append("Canvas API")

    # Integrate data from Canvas API if requested
    if "assignments" in context_types:
        # Get all courses
        courses = _canvas_service.get_current_courses()
        all_assignments = []

        for course in courses:
            assignments = _canvas_service.get_assignments_for_course(
                course['id'])
            if assignments:
                all_assignments.append({
                    "course_name": course["name"],
                    "assignments": assignments
                })

        result["assignments"] = {
            "success": True,
            "data": {
                "course_assignments":
                all_assignments,
                "all_assignments": [
                    assignment for course_assignments in all_assignments
                    for assignment in course_assignments.get(
                        "assignments", [])
                ]
            },
            "error": None
        }

        if "Canvas API" not in result["context_meta"]["source_systems"]:
            result["context_meta"]["source_systems"].append("Canvas API")

    if "announcements" in context_types:
        # Get announcements from Canvas
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

        result["announcements"] = {
            "success": True,
            "data": {
                "course_announcements":
                all_announcements,
                "all_announcements": [
                    announcement for course_announcements in all_announcements
                    for announcement in course_announcements.get(
                        "announcements", [])
                ]
            },
            "error": None
        }

        if "Canvas API" not in result["context_meta"]["source_systems"]:
            result["context_meta"]["source_systems"].append("Canvas API")

    # Update integration status
    source_systems = result["context_meta"]["source_systems"]
    if len(source_systems) > 1:
        result["context_meta"][
            "integration_status"] = f"Data integrated from: {', '.join(source_systems)}"
    else:
        result["context_meta"][
            "integration_status"] = f"Only using data from {source_systems[0]}"

    return json.dumps(result)


# Add workday-related functions


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
        if result["success"]:
            # Don't include the full HTML in the response
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result.pop("html", None)
        return json.dumps(result)
    finally:
        # Don't close the service since it's a singleton
        pass


def navigate_to_academics(mock_mode: bool = False) -> str:
    """
    Navigate to the Academics section in Workday.
    Requires being logged in first.
    
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

    # Print diagnostic information to debug browser visibility issues
    print(f"WorkdayService using mock mode: {_workday_service.using_mock}")
    print(
        f"WorkdayService headless mode: {getattr(_workday_service.browser, 'headless', 'unknown')}"
    )

    try:
        # Always attempt login if credentials are available
        username = os.environ.get("WORKDAY_USERNAME")
        password = os.environ.get("WORKDAY_PASSWORD")

        if username and password:
            print(
                f"Found credentials in environment. Username: {username[:2]}*** - Attempting login"
            )
            login_result = _workday_service.login(username, password)
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before navigating to academics",
                    "login_error": login_result.get("error")
                })
            print("Login successful. Proceeding to navigate to academics...")
        else:
            print(
                "WARNING: No Workday credentials found in environment variables!"
            )
            print(
                "WORKDAY_USERNAME and WORKDAY_PASSWORD must be set to see the browser"
            )
            if not _workday_service.logged_in:
                return json.dumps({
                    "success": False,
                    "error":
                    "No credentials available and not logged in. Cannot navigate to academics.",
                    "html": None
                })

        # Now navigate to academics
        result = _workday_service.navigate_to_academics()
        if result["success"]:
            # Don't include the full HTML in the response
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result.pop("html", None)
        return json.dumps(result)
    finally:
        # Don't close the service since it's a singleton
        pass


def search_workday_courses(term: str,
                           subject: Optional[str] = None,
                           mock_mode: bool = False) -> str:
    """
    Search for courses in Workday.
    
    Args:
        term: Academic term to search for (e.g., "Fall 2023")
        subject: Optional subject filter (e.g., "Computer Science")
        mock_mode: Use mock mode for testing without Playwright installed
        
    Returns:
        JSON string with search results
    """
    # Update the global singleton if mock mode is requested
    global _workday_service
    if mock_mode and not _workday_service.using_mock:
        _workday_service = WorkdayService(headless=False,
                                          mock_for_testing=True)

    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = _workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before searching courses",
                    "login_error": login_result.get("error")
                })

        # Now search courses
        result = _workday_service.search_courses(term, subject)
        if result["success"]:
            # Don't include the full HTML in the response
            result[
                "html_content"] = "HTML content available in file: " + result.get(
                    "html_file", "Unknown")
            result.pop("html", None)
        return json.dumps(result)
    finally:
        # Don't close the service since it's a singleton
        pass


def extract_workday_page(step_name: str,
                         take_screenshot: bool = False,
                         mock_mode: bool = False) -> str:
    """
    Extract HTML from the current page in Workday with identifying step name.
    
    Args:
        step_name (str): Name to identify this extraction step
        take_screenshot (bool): Whether to take a screenshot (should only be True for final pages)
        mock_mode: Use mock mode for testing without Playwright installed
        
    Returns:
        JSON string with extraction results
    """
    # Update the global singleton if mock mode is requested
    global _workday_service
    if mock_mode and not _workday_service.using_mock:
        _workday_service = WorkdayService(headless=False,
                                          mock_for_testing=True)

    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = _workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before extracting page",
                    "login_error": login_result.get("error")
                })

        # Now extract page
        result = _workday_service.extract_current_page(
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
        # Don't close the service since it's a singleton
        pass


def validate_registration_page(mock_mode: bool = False) -> str:
    """
    Take a screenshot of the current page and check if it appears to be a registration page.
    The screenshot can be analyzed by an AI vision model to verify the page contents.
    
    Args:
        mock_mode: Use mock mode for testing without Playwright installed
    
    Returns:
        JSON string with screenshot path and validation results
    """
    # Update the global singleton if mock mode is requested
    global _workday_service
    if mock_mode and not _workday_service.using_mock:
        _workday_service = WorkdayService(headless=False,
                                          mock_for_testing=True)

    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = _workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before validating page",
                    "login_error": login_result.get("error")
                })

        # Check if on registration page
        result = _workday_service.check_if_on_registration_page()

        # Add absolute path for the screenshot to make it easier to find
        if result["success"] and result.get("screenshot"):
            result["screenshot_abs_path"] = os.path.abspath(
                result["screenshot"])

        return json.dumps(result)
    finally:
        # Don't close the service since it's a singleton
        pass


def automate_course_registration(course_code: str,
                                 mock_mode: bool = False) -> str:
    """
    Automate the course registration process for a specific course.
    
    Args:
        course_code: The code of the course to register for (e.g., "CS 101")
        mock_mode: Use mock mode for testing without Playwright installed
        
    Returns:
        JSON string with registration results and screenshots
    """
    # Update the global singleton if mock mode is requested
    global _workday_service
    if mock_mode and not _workday_service.using_mock:
        _workday_service = WorkdayService(headless=False,
                                          mock_for_testing=True)

    try:
        # First login if credentials are available
        if os.environ.get("WORKDAY_USERNAME") and os.environ.get(
                "WORKDAY_PASSWORD"):
            login_result = _workday_service.login()
            if not login_result["success"]:
                return json.dumps({
                    "success": False,
                    "error": "Failed to log in before registering for course",
                    "login_error": login_result.get("error")
                })

        # Automate course registration
        result = _workday_service.automate_course_registration(course_code)

        # Add absolute paths for screenshots
        if result["success"] and result.get("screenshots"):
            result["screenshot_abs_paths"] = [
                os.path.abspath(s) for s in result["screenshots"] if s
            ]

        return json.dumps(result)
    finally:
        # Don't close the service since it's a singleton
        pass


def open_course_registration(mock_mode: bool = False) -> str:
    """
    Open the course registration page in Workday.
    This function automatically logs in using environment variables and then navigates to the registration page.
    
    Args:
        mock_mode: Use mock mode for testing without Playwright installed
        
    Returns:
        JSON string with results of the operation
    """
    # Update the global singleton if mock mode is requested
    global _workday_service

    # Force non-mock mode and visible browser
    if not mock_mode and _workday_service.using_mock:
        print(
            "Creating a new non-mock WorkdayService instance with visible browser"
        )
        _workday_service = WorkdayService(headless=False,
                                          mock_for_testing=False)

    # Print diagnostic information
    print(f"WorkdayService using mock mode: {_workday_service.using_mock}")
    print(
        f"WorkdayService headless mode: {getattr(_workday_service.browser, 'headless', 'unknown')}"
    )

    # Get credentials from environment
    username = os.environ.get("WORKDAY_USERNAME")
    password = os.environ.get("WORKDAY_PASSWORD")

    if not username or not password:
        print("ERROR: No Workday credentials found in environment variables!")
        return json.dumps({
            "success":
            False,
            "error":
            "No credentials available in environment variables. Please set WORKDAY_USERNAME and WORKDAY_PASSWORD."
        })

    print(f"Found credentials in environment. Username: {username[:2]}***")

    try:
        # Step 1: Login
        print("Attempting to log in...")
        login_result = _workday_service.login(username, password)

        if not login_result["success"]:
            return json.dumps({
                "success": False,
                "error": f"Failed to log in: {login_result.get('error')}",
                "details": login_result
            })

        print("Login successful!")

        # Step 2: Navigate to academics
        print("Navigating to academics section...")
        academics_result = _workday_service.navigate_to_academics()

        if not academics_result["success"]:
            return json.dumps({
                "success": False,
                "error":
                f"Failed to navigate to academics: {academics_result.get('error')}",
                "details": academics_result
            })

        print("Successfully navigated to academics!")

        # Step 3: This would be where we navigate to course registration
        # For now, we'll just return success with the academics page
        return json.dumps({
            "success":
            True,
            "message":
            "Successfully opened academic page. Course registration would be accessed from here.",
            "html_content":
            "HTML content available in academics page",
            "browser_visible":
            not getattr(_workday_service.browser, 'headless', True)
        })

    except Exception as e:
        print(f"Error during course registration process: {str(e)}")
        return json.dumps({
            "success":
            False,
            "error":
            f"Error during course registration process: {str(e)}"
        })

    # Don't close since it's a singleton


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
    automate_course_registration,
    open_course_registration
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
            },
            "mock_mode": {
                "type":
                "boolean",
                "description":
                "Use mock mode for testing without requiring Playwright installation"
            }
        }
    }
}, {
    "name": "navigate_to_academics",
    "description":
    "Navigate to the Academics section in Workday to access course information",
    "parameters": {
        "type": "object",
        "properties": {
            "mock_mode": {
                "type":
                "boolean",
                "description":
                "Use mock mode for testing without requiring Playwright installation"
            }
        }
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
            },
            "mock_mode": {
                "type":
                "boolean",
                "description":
                "Use mock mode for testing without requiring Playwright installation"
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
            },
            "mock_mode": {
                "type":
                "boolean",
                "description":
                "Use mock mode for testing without requiring Playwright installation"
            }
        },
        "required": ["step_name"]
    }
}, {
    "name": "validate_registration_page",
    "description":
    "Take a screenshot of the current page and check if it appears to be a registration page",
    "parameters": {
        "type": "object",
        "properties": {
            "mock_mode": {
                "type":
                "boolean",
                "description":
                "Use mock mode for testing without requiring Playwright installation"
            }
        }
    }
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
            },
            "mock_mode": {
                "type":
                "boolean",
                "description":
                "Use mock mode for testing without requiring Playwright installation"
            }
        },
        "required": ["course_code"]
    }
}, {
    "name": "open_course_registration",
    "description": "Open the course registration page in Workday",
    "parameters": {
        "type": "object",
        "properties": {
            "mock_mode": {
                "type":
                "boolean",
                "description":
                "Use mock mode for testing without requiring Playwright installation"
            }
        }
    }
}]
