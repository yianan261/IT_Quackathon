from typing import Any, Set, Callable
import json
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
from app.services.cosmos_service import CosmosService

# Create singleton instances
_canvas_service = CanvasService()
_stevens_service = StevensService()
_cosmos_service = CosmosService()

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
        announcements = _canvas_service.get_announcements_for_course(course['id'])
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
    announcements = _canvas_service.get_announcements_for_course(course_identifier)
    return json.dumps(announcements)

def get_grades() -> str:
    """
    Get grades for all courses.

    :return: JSON string containing grades for all courses
    """
    try:
        grades = _canvas_service.get_formatted_grades_for_all_courses()
        return json.dumps(grades)
    except Exception as e:
        logger.error(f"Error getting grades: {str(e)}")
        return json.dumps({"error": str(e)})

def get_course_grades(course_id: str) -> str:
    """
    Get grades for a specific course.

    :param course_id: Course ID
    :return: JSON string containing grades for the specified course
    """
    try:
        grades = _canvas_service.get_formatted_grades_for_course(course_id)
        return json.dumps(grades)
    except Exception as e:
        logger.error(f"Error getting course grades: {str(e)}")
        return json.dumps({"error": str(e)})

async def get_student_info(student_id: str = None) -> str:
    """
    Get student information from the database.
    
    Args:
        student_id (str, optional): Specific student ID to query. 
                                  If None, returns all students.
    
    Returns:
        str: Formatted student information
    """
    try:
        context = await _cosmos_service.get_student_context(student_id)
        return json.dumps(context)  # 确保返回的是字符串
    except Exception as e:
        logger.error(f"Error getting student info: {str(e)}")
        return json.dumps({"error": f"Error retrieving student information: {str(e)}"})
# Register all functions
user_functions: Set[Callable[..., Any]] = {
    get_course_assignments,
    get_current_courses,
    get_upcoming_courses_assignments,
    get_academic_calendar_event,
    get_program_requirements,
    get_announcements_for_all_courses,
    get_announcements_for_specific_courses,
    get_grades,           # Add this
    get_course_grades,  
    get_student_info
} 