import os
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Union
import logging
import json
import re
from app.core.config import settings
from openai import OpenAI
from tzlocal import get_localzone
from zoneinfo import ZoneInfo

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CanvasService:

    def __init__(self):
        self.base_url = settings.CANVAS_API_URL
        self.headers = {"Authorization": f"Bearer {settings.CANVAS_API_KEY}"}
        self.client = OpenAI()

    def get_current_courses(self) -> List[Dict]:
        """Get list of current courses"""
        try:
            url = f"{self.base_url}/courses"
            logger.info(f"Fetching courses from: {url}")
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
            all_courses = self.get_current_courses()
            course_infos = [{
                "id": course["id"],
                "name": course["name"]
            } for course in all_courses]
            assignments = self.get_assignments_for_course(course_infos)
            return assignments[
                "courses"] if "courses" in assignments else assignments

        except Exception as e:
            logger.error(f"Error getting upcoming assignments: {str(e)}")
            return []

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

    def get_assignments_for_course(
            self, course: Union[str, int, List[Dict]]) -> Dict:
        """Get assignments for a specific course or courses"""
        logger.info(f"=====Getting assignments for course: {course}====")
        try:
            course_infos = []
            # the course could be string, int, or list of course dicts
            if isinstance(course, str):
                course_infos = self._extract_course_identifier(course)
                logger.info(f"======Course info: {course_infos}=======")
                if not course_infos:
                    logger.warning(
                        f"No course ID found for identifier: {course}")
                    return {"courses": []}
            elif isinstance(course, list):
                course_infos = course
            else:
                course_id = course
                courses = self.get_current_courses()
                course_info = next(
                    (c for c in courses if c["id"] == course_id), None)
                if course_info:
                    course_infos = [{
                        "id": course_id,
                        "name": course_info["name"]
                    }]

            local_tz = get_localzone()

            all_courses_assignments = []
            for course_info in course_infos:
                course_id = course_info["id"]
                logger.info(
                    f"======Processing assignments for course {course_info['name']} with ID {course_id}===="
                )
                url = f"{self.base_url}/courses/{course_id}/assignments"
                logger.info(f"Fetching assignments from: {url}")

                response = requests.get(url,
                                        headers=self.headers,
                                        params={"include[]": ["submission"]})

                if response.status_code != 200:
                    logger.error(
                        f"Error response for assignments: {response.text}")
                    continue

                assignments = response.json()
                logger.info(f"Retrieved {len(assignments)} total assignments")

                now = datetime.now(timezone.utc)
                # get assignments due in the next 2 weeks
                two_weeks_from_now = now + timedelta(weeks=2)

                upcoming_assignments = []
                for assignment in assignments:
                    due_at = assignment.get('due_at')
                    if due_at:
                        try:
                            due_date_utc = datetime.fromisoformat(
                                due_at.replace('Z', '+00:00'))
                            # Convert to local timezone
                            due_date_local = due_date_utc.astimezone(local_tz)

                            if now <= due_date_utc <= two_weeks_from_now:
                                assignment_info = {
                                    'name':
                                    assignment.get('name'),
                                    'due_at':
                                    due_date_local.isoformat(),
                                    'points_possible':
                                    assignment.get('points_possible'),
                                    'html_url':
                                    assignment.get('html_url'),
                                    'description':
                                    assignment.get('description')
                                }
                                logger.info(
                                    f"Found upcoming assignment: {assignment_info['name']} due at {due_date_local}"
                                )
                                upcoming_assignments.append(assignment_info)
                        except ValueError as e:
                            logger.error(
                                f"Error parsing date {due_at}: {str(e)}")

                upcoming_assignments.sort(key=lambda x: x['due_at'])

                all_courses_assignments.append({
                    "course_name":
                    course_info["name"],
                    "assignments":
                    upcoming_assignments
                })

            logger.info(
                f"Retrieved assignments for {len(all_courses_assignments)} courses"
            )
            return {"courses": all_courses_assignments}

        except Exception as e:
            logger.error(
                f"Error fetching assignments for course {course}: {str(e)}")
            return {"courses": []}

    def format_assignments_response(self, assignments_data: Dict) -> str:
        """Format assignments response with error handling"""
        try:
            if not assignments_data:
                return "No assignment information available."
            logger.info(f"*****Assignments data: {assignments_data}*****")
            all_courses = assignments_data.get("courses", [])
            if not all_courses:
                return "No upcoming assignments found for any of the specified courses."

            response_parts = []
            logger.info(f"*****All courses: {all_courses}*****")
            for course_data in all_courses:
                course_name = course_data.get("course_name", "Unknown Course")
                assignments = course_data.get("assignments", [])

                if not assignments:
                    continue

                response_parts.append(f"\n📚 {course_name}")

                # Sort assignments by due date
                assignments = sorted(
                    [a for a in assignments if a.get("due_at")],
                    key=lambda x: x.get("due_at"))
                logger.info(f"*****Sorted assignments: {assignments}*****")
                for assignment in assignments:
                    try:
                        name = assignment.get("name", "Unnamed Assignment")
                        due_at = assignment.get("due_at")
                        points = assignment.get("points_possible")
                        url = assignment.get("html_url")

                        if due_at:
                            due_date = datetime.fromisoformat(
                                due_at.replace('Z', '+00:00'))
                            local_tz = get_localzone()
                            due_date = due_date.astimezone(local_tz)

                            assignment_parts = [
                                f"  📝 {name}",
                                f"     Due: {due_date.strftime('%B %d, %Y at %I:%M %p %Z')}"
                            ]

                            if points is not None:
                                assignment_parts.append(
                                    f"     Points: {points}")
                            if url:
                                assignment_parts.append(f"     Link: {url}")

                            response_parts.append("\n".join(assignment_parts))

                    except Exception as e:
                        logger.error(f"Error formatting assignment: {str(e)}")
                        continue

            if not response_parts:
                return "No upcoming assignments are currently listed for your courses. 📚✨"

            return "\n\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error formatting assignments response: {str(e)}")
            return "Error retrieving assignment information."

    def _extract_course_identifier(self, query: str) -> List[Dict[str, Any]]:
        """Extract course IDs from query using available courses"""
        try:
            courses = self.get_current_courses()
            if not courses:
                logger.warning("No courses found")
                return []

            course_context = "\n".join([
                f"Course ID: {course['id']}, Name: {course['name']}, Code: {course.get('course_code', '')}"
                for course in courses
            ])
            logger.info(f"Course context for LLM: {course_context}")

            prompt = f"""
            Given the following list of courses:
            {course_context}

            And the user query:
            "{query}"

            Find ALL courses that match the query. Return a JSON array of objects with exact numerical course IDs and full course names.
            The course IDs must be the complete numerical IDs from the course listing.

            Example format for matches: [
                {{"id": 78280, "name": "2025S EE 553-A"}},
                {{"id": 78275, "name": "2025S CS 505-WS/EE 605-WS"}}
            ]
            Example format for no matches: []

            Rules:
            1. Match on course name, code, or subject matter (e.g., "C++" should match "Engineering Programming: C++")
            2. The IDs must be the full numerical IDs from the course listing
            3. Return ONLY the JSON array, no other text
            4. If multiple courses are mentioned (e.g., "C++ and probability"), return all matching courses
            IMPORTANT: You MUST return ALL courses that match any part of the user query.
            """

            messages = [{
                "role":
                "system",
                "content":
                "You are a course matching assistant. Return ONLY the JSON array."
            }, {
                "role": "user",
                "content": prompt
            }]

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", messages=messages,
                temperature=0.3).choices[0].message.content

            try:
                response = response.strip()
                course_list = json.loads(response)

                if not isinstance(course_list, list):
                    raise ValueError("Invalid response format")

                if not course_list:
                    logger.info("No matching courses found")
                    return []

                validated_courses = [{
                    "id": int(course["id"]),
                    "name": course["name"]
                } for course in course_list if any(
                    c["id"] == int(course["id"]) for c in courses)]

                logger.info(
                    f"****Successfully matched courses: {validated_courses}****"
                )
                return validated_courses

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Error parsing course info: {str(e)}")
                return []

        except Exception as e:
            logger.error(f"Error extracting course identifier: {str(e)}")
            return []
