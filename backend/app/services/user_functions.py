from typing import Any, Set, Callable, Dict, List
import json
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
from app.services.mcp_service import MCPService

# Create singleton instances
_canvas_service = CanvasService()
_stevens_service = StevensService()

# Initialize services
mcp_service = MCPService()


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
    assignments = _canvas_service.get_upcoming_assignments()
    return json.dumps({"courses": assignments})


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
    all_courses = _canvas_service.get_current_courses()
    course_infos = [{
        "id": course["id"],
        "name": course["name"]
    } for course in all_courses]
    announcements = _canvas_service.get_announcements_for_course(course_infos)
    return json.dumps(announcements)


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
    Get context data for the user from multiple sources via the Model Context Provider.
    
    Args:
        context_types: List of context types to retrieve (e.g., "courses", "assignments", "announcements")
    
    Returns:
        JSON string containing all requested context data
    """
    context = mcp_service.get_user_context(context_types)
    return json.dumps(context)


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
                "List of context types to retrieve (e.g., courses, assignments, announcements)",
                "items": {
                    "type":
                    "string",
                    "enum":
                    ["courses", "assignments", "announcements"]
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
}]
