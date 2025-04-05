import os
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Union
import logging
import json
import re
from app.core.config import settings
from tzlocal import get_localzone
from zoneinfo import ZoneInfo

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CanvasService:

    def __init__(self):
        self.base_url = "https://sit.instructure.com/api/v1/"
        self.canvas_token = settings.CANVAS_API_KEY
        self.headers = {"Authorization": f"Bearer {self.canvas_token}"}

    def get_current_courses(self) -> List[Dict]:
        """Get list of current courses"""
        try:
            url = f"{self.base_url}/courses"
            logger.info(f"Fetching courses from: {url}")
            response = requests.get(
                f"{self.base_url}/courses",
                headers=self.headers,
                params={"enrollment_state": "active"},
            )
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
        """Find a course by partial name match"""
        logger.info(f"Searching for course with term: '{search_term}'")
        course_ids = self.extract_course_identifier(search_term)
        if course_ids and len(course_ids) > 0:
            # Use the first match
            course_id = course_ids[0]["id"]
            courses = self.get_current_courses()
            course = next((c for c in courses if c["id"] == course_id), None)
            if course:
                logger.info(f"Found matching course: {course.get('name')}")
                return course

        # Fallback to direct search
        logger.debug(f"Using direct search for term: '{search_term}'")
        courses = self.get_current_courses()
        if not courses:
            logger.warning("No courses retrieved to search through")
            return None

        search_term = search_term.lower()
        for course in courses:
            course_code = course.get("course_code", "").lower()
            course_name = course.get("name", "").lower()
            if (search_term in course_code or search_term in course_name
                    or search_term in course.get("name", "").lower()):
                logger.info(f"Found matching course: {course.get('name')}")
                return course
        logger.warning(f"No course found matching: '{search_term}'")
        return None

    def get_raw_assignments(self, course_id: int) -> List[Dict]:
        """Get raw assignments for a specific course (including Canvas metadata)"""
        try:
            url = f"{self.base_url}/courses/{course_id}/assignments"
            logger.info(f"Fetching raw assignments from: {url}")
            response = requests.get(
                url,
                headers=self.headers,
                params={"include[]":
                        ["submission"]},  # Include submission data
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
            # The course parameter can be a string, int, or a list of course dicts
            if isinstance(course, str):
                course_infos = self.extract_course_identifier(course)
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
                # Get assignments due in the next 2 weeks
                two_weeks_from_now = now + timedelta(weeks=2)
                upcoming_assignments = []

                for assignment in assignments:
                    due_at = assignment.get("due_at")
                    if due_at:
                        try:
                            due_date_utc = datetime.fromisoformat(
                                due_at.replace("Z", "+00:00"))
                            # Convert to local timezone
                            due_date_local = due_date_utc.astimezone(local_tz)
                            if now <= due_date_utc <= two_weeks_from_now:
                                assignment_info = {
                                    "name":
                                    assignment.get("name"),
                                    "due_at":
                                    due_date_local.isoformat(),
                                    "points_possible":
                                    assignment.get("points_possible"),
                                    "html_url":
                                    assignment.get("html_url"),
                                    "description":
                                    assignment.get("description"),
                                }
                                logger.info(
                                    f"Found upcoming assignment: {assignment_info['name']} due at {due_date_local}"
                                )
                                upcoming_assignments.append(assignment_info)
                        except ValueError as e:
                            logger.error(
                                f"Error parsing date {due_at}: {str(e)}")

                upcoming_assignments.sort(key=lambda x: x["due_at"])
                all_courses_assignments.append({
                    "course_name":
                    course_info["name"],
                    "assignments":
                    upcoming_assignments,
                })

            logger.info(
                f"Retrieved assignments for {len(all_courses_assignments)} courses"
            )
            return {"courses": all_courses_assignments}
        except Exception as e:
            logger.error(
                f"Error fetching assignments for course {course}: {str(e)}")
            return {"courses": []}

    def format_courses_response(self, courses: List[Dict]) -> str:
        """Format courses response with error handling"""
        try:
            if not courses:
                return "No courses found."
            response_parts = ["📚 Your Current Courses:"]
            for course in courses:
                course_name = course.get("name", "Unknown Course")
                course_code = course.get("course_code", "")
                response_parts.append(f"  • {course_name} ({course_code})")
            return "\n".join(response_parts)
        except Exception as e:
            logger.error(f"Error formatting courses response: {str(e)}")
            return "Error formatting courses information."

    def extract_course_identifier(self, search_term: str) -> List[Dict]:
        """Extract course identifier from search term"""
        logger.info(f"Extracting course identifier from: '{search_term}'")
        try:
            # First try to find an exact match
            courses = self.get_current_courses()
            if not courses:
                logger.warning("No courses available to search through")
                return []

            # Try to find a course by ID if the search term is numeric
            if search_term.isdigit():
                course_id = int(search_term)
                course = next((c for c in courses if c["id"] == course_id),
                              None)
                if course:
                    logger.info(f"Found course by ID: {course['name']}")
                    return [{"id": course["id"], "name": course["name"]}]

            # Try to find a course by name or code
            search_term = search_term.lower()
            matches = []
            for course in courses:
                course_code = course.get("course_code", "").lower()
                course_name = course.get("name", "").lower()
                if (search_term in course_code or search_term in course_name
                        or search_term in course.get("name", "").lower()):
                    logger.info(f"Found matching course: {course.get('name')}")
                    matches.append({
                        "id": course["id"],
                        "name": course["name"]
                    })

            if matches:
                return matches
            logger.warning(f"No course found matching: '{search_term}'")
            return []
        except Exception as e:
            logger.error(f"Error extracting course identifier: {str(e)}")
            return []

    def get_announcements_for_course(
            self, course: Union[int, str, List[Dict]]) -> Dict:
        """
        Get announcements for specified course(s).

        Parameters:
            course (Union[int, str, List[Dict]]):
                - If an integer, represents a single course ID;
                - If a string, represents a course name or keyword (will be parsed via extract_course_identifier);
                - If a list, it should be a list of course dictionaries (each must contain at least "id" and "name").

        Returns:
            Dict: In the format {"courses": [ { "course_name": ..., "announcements": [ {...}, ... ] }, ... ] }.
                  Each announcement contains only the following fields:
                      - title: Announcement title
                      - author: { display_name, avatar_image_url, pronouns }
                      - posted_at: Announcement posted time (string)
                      - message: Announcement content (usually HTML)
        """
        try:
            # Determine the course list based on the input parameter type
            course_infos = []
            if isinstance(course, str):
                course_infos = self.extract_course_identifier(course)
                logger.info(
                    f"Extracted course info from query '{course}': {course_infos}"
                )
                if not course_infos:
                    logger.warning(
                        f"No course ID found for identifier: {course}")
                    return {"courses": []}
            elif isinstance(course, list):
                course_infos = course
            else:  # assume integer course id
                courses = self.get_current_courses()
                course_info = next((c for c in courses if c["id"] == course),
                                   None)
                if course_info:
                    course_infos = [{
                        "id": course,
                        "name": course_info["name"]
                    }]
                else:
                    logger.warning(f"No course found with ID: {course}")
                    return {"courses": []}

            results = []
            now = datetime.now(timezone.utc)
            # One week in the past to capture recent announcements
            one_week_ago = now - timedelta(weeks=1)

            # Iterate over each course and get announcements
            for course_info in course_infos:
                course_id = course_info["id"]
                course_name = course_info["name"]
                url = f"{self.base_url}/courses/{course_id}/discussion_topics"
                params = {
                    "only_announcements": "true",
                    "per_page": 40,
                    "page": 1,
                }
                logger.info(
                    f"Fetching announcements for course {course_name} (ID: {course_id}) from: {url} with params: {params}"
                )
                response = requests.get(url,
                                        headers=self.headers,
                                        params=params)
                if response.status_code != 200:
                    logger.error(
                        f"Error response for announcements (course {course_id}): {response.text}"
                    )
                    continue

                announcements = response.json()
                ann_list = []

                for ann in announcements:
                    posted_at = ann.get("posted_at")
                    # Include only recent or future announcements
                    if posted_at:
                        try:
                            posted_date_utc = datetime.fromisoformat(
                                posted_at.replace("Z", "+00:00"))
                            # Include announcements from the past week or future announcements
                            if posted_date_utc >= one_week_ago:
                                ann_list.append({
                                    "title":
                                    ann.get("title", ""),
                                    "author": {
                                        "display_name":
                                        ann.get("author",
                                                {}).get("display_name", ""),
                                        "avatar_image_url":
                                        ann.get("author", {}).get(
                                            "avatar_image_url", ""),
                                        "pronouns":
                                        ann.get("author",
                                                {}).get("pronouns", ""),
                                    },
                                    "posted_at":
                                    ann.get("posted_at", ""),
                                    "message":
                                    ann.get("message", "")
                                })
                                logger.info(
                                    f"Found announcement: {ann.get('title')} posted at {posted_date_utc}"
                                )
                        except ValueError as e:
                            logger.error(
                                f"Error parsing date {posted_at}: {str(e)}")

                # Sort announcements by date (newest first)
                ann_list.sort(key=lambda x: x["posted_at"], reverse=True)

                results.append({
                    "course_name": course_name,
                    "course_announcements_link":
                    f"https://sit.instructure.com/courses/{course_id}/announcements",
                    "announcements": ann_list
                })

            return {"courses": results}
        except Exception as e:
            logger.error(
                f"Error fetching announcements for course {course}: {str(e)}",
                exc_info=True)
            return {"courses": []}

    def get_announcements_for_all_courses(self) -> Dict:
        """
        Get announcements for all current courses.
        """
        try:
            all_courses = self.get_current_courses()
            course_infos = [{
                "id": course["id"],
                "name": course["name"]
            } for course in all_courses]
            announcements = self.get_announcements_for_course(course_infos)
            return announcements
        except Exception as e:
            logger.error(
                f"Error fetching announcements for all courses: {str(e)}")
            return {"courses": []}
