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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
            course_infos = [{"id": course["id"], "name": course["name"]} for course in all_courses]
            assignments = self.get_assignments_for_course(course_infos)
            return assignments["courses"] if "courses" in assignments else assignments
        except Exception as e:
            logger.error(f"Error getting upcoming assignments: {str(e)}")
            return []

    def find_course_by_name(self, search_term: str) -> Dict:
        """Find a course by partial name match"""
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
            course_code = course.get("course_code", "").lower()
            course_name = course.get("name", "").lower()
            if (
                search_term in course_code
                or search_term in course_name
                or search_term in course.get("name", "").lower()
            ):
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
                params={"include[]": ["submission"]},  # Include submission data
            )
            logger.info(f"Raw assignment request status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Error response for assignments: {response.text}")
                return []
            assignments = response.json()
            logger.info(f"Retrieved {len(assignments)} raw assignments")
            return assignments
        except Exception as e:
            logger.error(f"Error fetching raw assignments for course {course_id}: {str(e)}")
            return []

    def get_assignments_for_course(self, course: Union[str, int, List[Dict]]) -> Dict:
        """Get assignments for a specific course or courses"""
        logger.info(f"=====Getting assignments for course: {course}====")
        try:
            course_infos = []
            # The course parameter can be a string, int, or a list of course dicts
            if isinstance(course, str):
                course_infos = self.extract_course_identifier(course)
                logger.info(f"======Course info: {course_infos}=======")
                if not course_infos:
                    logger.warning(f"No course ID found for identifier: {course}")
                    return {"courses": []}
            elif isinstance(course, list):
                course_infos = course
            else:
                course_id = course
                courses = self.get_current_courses()
                course_info = next((c for c in courses if c["id"] == course_id), None)
                if course_info:
                    course_infos = [{"id": course_id, "name": course_info["name"]}]
            local_tz = get_localzone()
            all_courses_assignments = []
            for course_info in course_infos:
                course_id = course_info["id"]
                logger.info(f"======Processing assignments for course {course_info['name']} with ID {course_id}====")
                url = f"{self.base_url}/courses/{course_id}/assignments"
                logger.info(f"Fetching assignments from: {url}")
                response = requests.get(url, headers=self.headers, params={"include[]": ["submission"]})
                if response.status_code != 200:
                    logger.error(f"Error response for assignments: {response.text}")
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
                            due_date_utc = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                            # Convert to local timezone
                            due_date_local = due_date_utc.astimezone(local_tz)
                            if now <= due_date_utc <= two_weeks_from_now:
                                assignment_info = {
                                    "name": assignment.get("name"),
                                    "due_at": due_date_local.isoformat(),
                                    "points_possible": assignment.get("points_possible"),
                                    "html_url": assignment.get("html_url"),
                                    "description": assignment.get("description"),
                                }
                                logger.info(f"Found upcoming assignment: {assignment_info['name']} due at {due_date_local}")
                                upcoming_assignments.append(assignment_info)
                        except ValueError as e:
                            logger.error(f"Error parsing date {due_at}: {str(e)}")
                upcoming_assignments.sort(key=lambda x: x["due_at"])
                all_courses_assignments.append({
                    "course_name": course_info["name"],
                    "assignments": upcoming_assignments,
                })
            logger.info(f"Retrieved assignments for {len(all_courses_assignments)} courses")
            return {"courses": all_courses_assignments}
        except Exception as e:
            logger.error(f"Error fetching assignments for course {course}: {str(e)}")
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
                assignments = sorted([a for a in assignments if a.get("due_at")], key=lambda x: x.get("due_at"))
                logger.info(f"*****Sorted assignments: {assignments}*****")
                for assignment in assignments:
                    try:
                        name = assignment.get("name", "Unnamed Assignment")
                        due_at = assignment.get("due_at")
                        points = assignment.get("points_possible")
                        url = assignment.get("html_url")
                        if due_at:
                            due_date = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                            local_tz = get_localzone()
                            due_date = due_date.astimezone(local_tz)
                            assignment_parts = [
                                f"  📝 {name}",
                                f"     Due: {due_date.strftime('%B %d, %Y at %I:%M %p %Z')}",
                            ]
                            if points is not None:
                                assignment_parts.append(f"     Points: {points}")
                            if url:
                                assignment_parts.append(f"     Link: {url}")
                            response_parts.append("\n".join(assignment_parts))
                    except Exception as e:
                        logger.error(f"Error formatting assignment: {str(e)}")
                        continue
            if not response_parts:
                return "No upcoming assignments are curren tly listed for your courses. 📚✨"
            return "\n\n".join(response_parts)
        except Exception as e:
            logger.error(f"Error formatting assignments response: {str(e)}")
            return "Error retrieving assignment information."

    def extract_course_identifier(self, query: str) -> Dict:
        """
        This functionality will now be handled by the Azure agent
        We'll keep this method as a wrapper for compatibility
        """
        try:
            # The Azure agent will handle the course matching logic
            return self.get_course_info(query)
        except Exception as e:
            logger.error(f"Error extracting course identifier: {str(e)}")
            return None

    def get_course_info(self, query: str) -> Dict:
        """Get course information from the Azure agent"""
        # This would be handled by your Azure agent's course matching logic
        # For now, return the course data directly from Canvas
        courses = self.get_current_courses()
        # Basic matching logic - in production this would be handled by the Azure agent
        for course in courses:
            if query.lower() in course["name"].lower():
                return {
                    "id": course["id"],
                    "name": course["name"]
                }
        return None

    def format_announcements_response(self, announcements_data: Dict) -> str:
        """Format announcements response with error handling, keeping latest 3 announcements per course"""
        try:
            if not announcements_data:
                return "No announcement information available."

            all_courses = announcements_data.get("courses", [])
            if not all_courses:
                return "No announcements found for any of the specified courses."

            response_parts = []
            
            for course_data in all_courses:
                course_name = course_data.get("course_name", "Unknown Course")
                announcements = course_data.get("announcements", [])
                course_link = course_data.get("course_announcements_link", "")

                if not announcements:
                    continue

                response_parts.append(f"\n📚 {course_name}")
                if course_link:
                    response_parts.append(f"   View all announcements: {course_link}")

                # Sort announcements by posted_at date and keep latest 3
                sorted_announcements = sorted(
                    [a for a in announcements if a.get("posted_at")],
                    key=lambda x: x.get("posted_at"),
                    reverse=True
                )[:3]

                for announcement in sorted_announcements:
                    try:
                        title = announcement.get("title", "Untitled Announcement")
                        posted_at = announcement.get("posted_at")
                        author = announcement.get("author", {})
                        author_name = author.get("display_name", "Unknown Author")
                        author_pronouns = author.get("pronouns", "")

                        if posted_at:
                            posted_date = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                            local_tz = get_localzone()
                            posted_date = posted_date.astimezone(local_tz)
                            
                            announcement_parts = [
                                f"  📢 {title}",
                                f"     Posted: {posted_date.strftime('%B %d, %Y at %I:%M %p %Z')}",
                                f"     By: {author_name}{f' ({author_pronouns})' if author_pronouns else ''}"
                            ]
                            response_parts.append("\n".join(announcement_parts))
                    except Exception as e:
                        logger.error(f"Error formatting announcement: {str(e)}")
                        continue

            if not response_parts:
                return "No announcements are currently available for your courses. 📚✨"

            return "\n\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error formatting announcements response: {str(e)}")
            return "Error retrieving announcement information."

    def get_announcements_for_course(self, course: Union[int, str, List[Dict]]) -> Dict:
        """
        Get announcements for specified course(s).

        Parameters:
            course (Union[int, str, List[Dict]]):
                - If an integer, represents a single course ID;
                - If a string, represents a course name or keyword (will be parsed via _extract_course_identifier);
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
                logger.info(f"Extracted course info from query '{course}': {course_infos}")
                if not course_infos:
                    logger.warning(f"No course ID found for identifier: {course}")
                    return {"courses": []}
            elif isinstance(course, list):
                course_infos = course
            else:  # assume integer course id
                courses = self.get_current_courses()
                course_info = next((c for c in courses if c["id"] == course), None)
                if course_info:
                    course_infos = [{"id": course, "name": course_info["name"]}]
                else:
                    logger.warning(f"No course found with ID: {course}")
                    return {"courses": []}

            results = []
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
                logger.info(f"Fetching announcements for course {course_name} (ID: {course_id}) from: {url} with params: {params}")
                response = requests.get(url, headers=self.headers, params=params)
                if response.status_code != 200:
                    logger.error(f"Error response for announcements (course {course_id}): {response.text}")
                    continue
                announcements = response.json()
                ann_list = []
                for ann in announcements:
                    ann_list.append({
                        "title": ann.get("title", ""),
                        "author": {
                            "display_name": ann.get("author", {}).get("display_name", ""),
                            "avatar_image_url": ann.get("author", {}).get("avatar_image_url", ""),
                            "pronouns": ann.get("author", {}).get("pronouns", ""),
                        },
                        "posted_at": ann.get("posted_at", ""),
                        "message": ann.get("message", "")
                    })
                results.append({
                    "course_name": course_name,
                    "course_announcements_link": f"https://sit.instructure.com/courses/{course_id}/announcements",
                    "announcements": ann_list
                })
            return {"courses": results}
        except Exception as e:
            logger.error(f"Error fetching announcements for course {course}: {str(e)}", exc_info=True)
            return {"courses": []}

    def get_announcements_for_all_courses(self) -> Dict:
        """
        Get announcements for all current courses.

        This function retrieves all current courses via get_current_courses,
        then calls get_announcements_for_course with the list of courses to get
        announcements for each course.

        Returns:
            Dict: In the format {"courses": [ { "course_name": ..., "announcements": [ {...}, ... ] }, ... ] }.
        """
        try:
            all_courses = self.get_current_courses()
            course_infos = [{"id": course["id"], "name": course["name"]} for course in all_courses]
            announcements = self.get_announcements_for_course(course_infos)
            return announcements
        except Exception as e:
            logger.error(f"Error fetching announcements for all courses: {str(e)}")
            return {"courses": []}

 