import os
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Union
import logging
import json
import re
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CanvasService:

    def __init__(self):
        self.base_url = settings.CANVAS_API_URL
        self.headers = {"Authorization": f"Bearer {settings.CANVAS_API_KEY}"}
        logger.info(f"CanvasService initialized with URL: {self.base_url!r}"
                    )  # !r shows quotes
        logger.info(f"Using API key: {settings.CANVAS_API_KEY[:5]}..."
                    )  # Show first 5 chars
        logger.info(f"Headers configured: {self.headers}")

    def get_current_courses(self) -> List[Dict]:
        """Get list of current courses"""
        try:
            url = f"{self.base_url}/courses"
            logger.info(f"Fetching courses from: {url}")
            logger.info(f"Using headers: {self.headers}")
            response = requests.get(f"{self.base_url}/courses",
                                    headers=self.headers,
                                    params={"enrollment_state": "active"})
            logger.info(f"Courses API Response Status: {response.status_code}")
            logger.info(f"Courses API Response: {response.text}")
            response.raise_for_status()
            courses = response.json()
            logger.info(f"Retrieved courses: {courses}")
            return courses
        except Exception as e:
            logger.error(f"Error getting courses: {str(e)}", exc_info=True)
            return []

    def get_upcoming_assignments(self) -> List[Dict]:
        """Get upcoming assignments for all courses"""
        try:
            response = requests.get(
                f"{self.base_url}/users/self/upcoming_assignments",
                headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting upcoming assignments: {str(e)}")
            return []

    def extract_course_identifier(self, query: str) -> Optional[int]:
        """
        Use LLM to understand which course the user is referring to in their query
        Gets the course ID, which is used to get the assignments for the course
        Returns the course identifier (ID) or None if no course is mentioned
        """
        courses = self.get_current_courses()
        if not courses:
            logger.error("No courses retrieved from Canvas API")
            return None
        logger.info(f"Available courses for matching: {courses}")
        course_context = "\n".join([
            f"{course['name']} ({course.get('course_code', '')})"
            for course in courses
        ])
        logger.info(f"Course context for LLM: {course_context}")

        # Prepare prompt for LLM
        prompt = f"""
        Given the following list of courses:
        {course_context}

        And the user query:
        "{query}"

        Which course code (if any) is the user referring to? Return ONLY the corresponding course id `id` and course name `name` if found
        in json format, or "None" if no such course is found.
        Do not include any other text in your response.
        """

        from app.services.model_service import ModelService
        model = ModelService()
        response = model.get_completion(prompt)

        try:
            response = response.strip()
            if response.lower() == "none":
                return None
            course_info = json.loads(response)
            logger.info(f"Course info: {course_info}")
            return {"id": int(course_info["id"]), "name": course_info["name"]}
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error parsing course info: {str(e)}")
            return None

    def find_course_by_name(self, search_term: str) -> Dict:
        """find a course by partial name match"""
        logger.info(f"Searching for course with term: '{search_term}'")

        course_id = self.extract_course_identifier(search_term)
        if course_id:
            search_term = course_id

        logger.debug(f"Using search term: '{search_term}'")
        courses = self.get_current_courses()

        if not courses:
            logger.warning("No courses retrieved to search through")
            return None

        search_term = search_term.lower()

        for course in courses:
            course_code = course.get('course_code', '').lower()
            course_name = course.get('name', '').lower()

            if (search_term in course_code or search_term in course_name
                    or search_term in course.get('name', '').lower()):
                logger.info(f"Found matching course: {course.get('name')}")
                return course

        logger.warning(f"No course found matching: '{search_term}'")
        return None

    def get_raw_assignments(self, course_id: int) -> List[Dict]:
        """Gets raw assignments for specific course (include metadata from Canvas)"""
        try:
            url = f"{self.base_url}/courses/{course_id}/assignments"
            logger.info(f"Fetching raw assignments from: {url}")

            response = requests.get(
                url,
                headers=self.headers,
                params={"include[]": ["submission"]}  # Include submission data
            )

            logger.info(
                f"Raw assignment request status: {response.status_code}")

            if response.status_code != 200:
                logger.error(
                    f"Error response for assignments: {response.text}")
                return []

            assignments = response.json()
            logger.info(f"Retrieved {len(assignments)} raw assignments")
            return assignments

        except Exception as e:
            logger.error(
                f"Error fetching raw assignments for course {course_id}: {str(e)}"
            )
            return []

    def get_assignments_for_course(self, course: Union[str,
                                                       int]) -> List[Dict]:
        """Get assignments for a specific course
        Identifies course by course identifier string or course ID
        """
        course_id = None  # Initialize course_id at the start
        try:
            course_info = None
            if isinstance(course, str):
                course_info = self.extract_course_identifier(course)
                if not course_info:
                    logger.warning(
                        f"No course ID found for identifier: {course}")
                    return []
                course_id = course_info["id"]
            else:
                course_id = course
                # Get course info for the ID
                courses = self.get_current_courses()
                course_info = next(
                    (c for c in courses if c["id"] == course_id), None)
                if course_info:
                    course_info = {
                        "id": course_id,
                        "name": course_info["name"]
                    }

            response = requests.get(
                f"{self.base_url}/courses/{course_id}/assignments",
                headers=self.headers)

            response.raise_for_status()

            url = f"{self.base_url}/courses/{course_id}/assignments"
            logger.info(f"Fetching assignments from: {url}")

            response = requests.get(url, headers=self.headers)

            logger.info(f"Assignment request status: {response.status_code}")

            if response.status_code != 200:
                logger.error(
                    f"Error response for assignments: {response.text}")
                return []

            assignments = response.json()
            logger.info(f"Retrieved {len(assignments)} total assignments")

            now = datetime.now(timezone.utc)

            # filter for upcoming assignments
            upcoming_assignments = []
            for assignment in assignments:
                name = assignment.get('name', None)
                due_at = assignment.get('due_at', None)
                unlock_at = assignment.get('unlock_at')
                points_possible = assignment.get('points_possible', None)
                has_submitted = assignment.get('has_submitted_submissions',
                                               False)

                is_unlocked = unlock_at is None or datetime.fromisoformat(
                    unlock_at.replace('Z', '+00:00')) <= now

                if due_at and is_unlocked and not assignment.get(
                        'locked_for_user', False):
                    try:
                        due_date = datetime.fromisoformat(
                            due_at.replace('Z', '+00:00'))

                        #  include if due date is in the future
                        if due_date > now:
                            logger.info(
                                f"Found upcoming assignment: {assignment.get('name')} due at {due_at}"
                            )
                            upcoming_assignments.append(assignment)
                    except ValueError as e:
                        logger.error(f"Error parsing date {due_at}: {str(e)}")

            upcoming_assignments.sort(key=lambda x: x['due_at'])

            logger.info(
                f"Filtered to {len(upcoming_assignments)} upcoming assignments"
            )
            return {
                "course name":
                course_info["name"] if course_info else f"Course {course_id}",
                "assignments": upcoming_assignments
            }

        except Exception as e:
            logger.error(
                f"Error fetching assignments for course {course}: {str(e)}")
            return []

    def format_assignments_response(self, assignments: List[Dict],
                                    course_name: str) -> str:
        logger.info(
            f"Formatting {len(assignments)} assignments for {course_name}")
        if not assignments:
            return f"No upcoming assignments found for {course_name}."

        response = f"Upcoming assignments for {course_name}:\n\n"
        for assignment in assignments:
            due_at = datetime.fromisoformat(assignment['due_at'].replace(
                'Z', '+00:00'))

            response += f"📝 {assignment['name']}\n"
            response += f"   Due: {due_at.strftime('%B %d, %Y at %I:%M %p')}\n"
            if assignment.get('points_possible'):
                response += f"   Points: {assignment['points_possible']}\n"
            if assignment.get('html_url'):
                response += f"   Link: {assignment['html_url']}\n"
            response += "\n"

        logger.debug(f"Formatted response: {response}")
        return response
