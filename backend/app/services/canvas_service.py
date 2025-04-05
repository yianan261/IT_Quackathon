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
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
            course_infos = [
                {"id": course["id"], "name": course["name"]} for course in all_courses
            ]
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
            logger.error(
                f"Error fetching raw assignments for course {course_id}: {str(e)}"
            )
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
                logger.info(
                    f"======Processing assignments for course {course_info['name']} with ID {course_id}===="
                )
                url = f"{self.base_url}/courses/{course_id}/assignments"
                logger.info(f"Fetching assignments from: {url}")
                response = requests.get(
                    url, headers=self.headers, params={"include[]": ["submission"]}
                )
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
                            due_date_utc = datetime.fromisoformat(
                                due_at.replace("Z", "+00:00")
                            )
                            # Convert to local timezone
                            due_date_local = due_date_utc.astimezone(local_tz)
                            if now <= due_date_utc <= two_weeks_from_now:
                                assignment_info = {
                                    "name": assignment.get("name"),
                                    "due_at": due_date_local.isoformat(),
                                    "points_possible": assignment.get(
                                        "points_possible"
                                    ),
                                    "html_url": assignment.get("html_url"),
                                    "description": assignment.get("description"),
                                }
                                logger.info(
                                    f"Found upcoming assignment: {assignment_info['name']} due at {due_date_local}"
                                )
                                upcoming_assignments.append(assignment_info)
                        except ValueError as e:
                            logger.error(f"Error parsing date {due_at}: {str(e)}")
                upcoming_assignments.sort(key=lambda x: x["due_at"])
                all_courses_assignments.append(
                    {
                        "course_name": course_info["name"],
                        "assignments": upcoming_assignments,
                    }
                )
            logger.info(
                f"Retrieved assignments for {len(all_courses_assignments)} courses"
            )
            return {"courses": all_courses_assignments}
        except Exception as e:
            logger.error(f"Error fetching assignments for course {course}: {str(e)}")
            return {"courses": []}

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
                return {"id": course["id"], "name": course["name"]}
        return None

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
                logger.info(
                    f"Extracted course info from query '{course}': {course_infos}"
                )
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
            now = datetime.now(timezone.utc)
            one_week_ago = now - timedelta(days=7)
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
                response = requests.get(url, headers=self.headers, params=params)
                if response.status_code != 200:
                    logger.error(
                        f"Error response for announcements (course {course_id}): {response.text}"
                    )
                    continue
                announcements = response.json()
                ann_list = []
                for ann in announcements:
                    posted_at = ann.get("posted_at")
                    # Filter for future announcements (if posted_at is in the future)
                    if posted_at:
                        try:
                            posted_date_utc = datetime.fromisoformat(
                                posted_at.replace("Z", "+00:00")
                            )
                            # Only include announcements from past week onwards
                            if posted_date_utc >= one_week_ago:
                                ann_list.append(
                                    {
                                        "title": ann.get("title", ""),
                                        "author": {
                                            "display_name": ann.get("author", {}).get(
                                                "display_name", ""
                                            ),
                                            "avatar_image_url": ann.get(
                                                "author", {}
                                            ).get("avatar_image_url", ""),
                                            "pronouns": ann.get("author", {}).get(
                                                "pronouns", ""
                                            ),
                                        },
                                        "posted_at": ann.get("posted_at", ""),
                                        "message": ann.get("message", ""),
                                    }
                                )
                                logger.info(
                                    f"Found future announcement: {ann.get('title')} posted at {posted_date_utc}"
                                )
                        except ValueError as e:
                            logger.error(f"Error parsing date {posted_at}: {str(e)}")

                # Sort announcements chronologically (nearest future date first)
                ann_list.sort(key=lambda x: x["posted_at"])

                results.append(
                    {
                        "course_name": course_name,
                        "course_announcements_link": f"https://sit.instructure.com/courses/{course_id}/announcements",
                        "announcements": ann_list,
                    }
                )
            return {"courses": results}
        except Exception as e:
            logger.error(
                f"Error fetching announcements for course {course}: {str(e)}",
                exc_info=True,
            )
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
            course_infos = [
                {"id": course["id"], "name": course["name"]} for course in all_courses
            ]
            announcements = self.get_announcements_for_course(course_infos)
            return announcements
        except Exception as e:
            logger.error(f"Error fetching announcements for all courses: {str(e)}")
            return {"courses": []}

    def get_grades_for_course(self, course: Union[int, str, List[Dict]]) -> Dict:
        """
        Get grades for a specific course or courses.

        Parameters:
            course (Union[int, str, List[Dict]]):
                - If an integer, represents a single course ID;
                - If a string, represents a course name or keyword (will be parsed via _extract_course_identifier);
                - If a list, it should be a list of course dictionaries (each must contain at least "id" and "name").

        Returns:
            Dict: In the format {"courses": [ { "course_name": ..., "grades": {...} }, ... ] }
        """
        try:
            # Determine the course list based on the input parameter type
            course_infos = []
            if isinstance(course, str):
                course_infos = self._extract_course_identifier(course)
                logger.info(
                    f"Extracted course info from query '{course}': {course_infos}"
                )
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
            # Iterate over each course and get grades
            for course_info in course_infos:
                course_id = course_info["id"]
                course_name = course_info["name"]

                # First get all assignments for the course
                assignments_url = f"{self.base_url}/courses/{course_id}/assignments"
                logger.info(
                    f"Fetching assignments for course {course_name} (ID: {course_id}) from: {assignments_url}"
                )
                assignments_response = requests.get(
                    assignments_url, headers=self.headers
                )

                if assignments_response.status_code != 200:
                    logger.error(
                        f"Error response for assignments (course {course_id}): {assignments_response.text}"
                    )
                    continue

                assignments = assignments_response.json()

                # Now get the submissions for these assignments
                submissions_url = (
                    f"{self.base_url}/courses/{course_id}/students/submissions"
                )
                params = {
                    "student_ids[]": "self",  # get submissions for the current user
                    "include[]": [
                        "assignment",
                        "submission_comments",
                        "rubric_assessment",
                        "score",
                        "user",
                    ],
                }

                logger.info(
                    f"Fetching submissions for course {course_name} (ID: {course_id}) from: {submissions_url}"
                )
                submissions_response = requests.get(
                    submissions_url, headers=self.headers, params=params
                )

                if submissions_response.status_code != 200:
                    logger.error(
                        f"Error response for submissions (course {course_id}): {submissions_response.text}"
                    )
                    continue

                submissions = submissions_response.json()

                # Get course total grade
                enrollment_url = f"{self.base_url}/courses/{course_id}/enrollments"
                params = {"user_id": "self"}

                logger.info(
                    f"Fetching enrollment/grade data for course {course_name} (ID: {course_id}) from: {enrollment_url}"
                )
                enrollment_response = requests.get(
                    enrollment_url, headers=self.headers, params=params
                )

                course_grade = None
                if enrollment_response.status_code == 200:
                    enrollments = enrollment_response.json()
                    if enrollments and len(enrollments) > 0:
                        for enrollment in enrollments:
                            if enrollment.get("type") == "StudentEnrollment":
                                course_grade = {
                                    "current_grade": enrollment.get("grades", {}).get(
                                        "current_grade"
                                    ),
                                    "current_score": enrollment.get("grades", {}).get(
                                        "current_score"
                                    ),
                                    "final_grade": enrollment.get("grades", {}).get(
                                        "final_grade"
                                    ),
                                    "final_score": enrollment.get("grades", {}).get(
                                        "final_score"
                                    ),
                                }
                                break

                # Process submissions data
                processed_submissions = []
                for submission in submissions:
                    assignment_id = submission.get("assignment_id")
                    assignment = next(
                        (a for a in assignments if a["id"] == assignment_id), None
                    )

                    if assignment:
                        processed_submissions.append(
                            {
                                "assignment_name": assignment.get(
                                    "name", "Unknown Assignment"
                                ),
                                "assignment_id": assignment_id,
                                "score": submission.get("score"),
                                "grade": submission.get("grade"),
                                "points_possible": assignment.get("points_possible"),
                                "submitted_at": submission.get("submitted_at"),
                                "late": submission.get("late", False),
                                "missing": submission.get("missing", False),
                                "submission_type": submission.get("submission_type"),
                                "submission_url": submission.get("html_url"),
                                "assignment_url": assignment.get("html_url"),
                            }
                        )

                results.append(
                    {
                        "course_name": course_name,
                        "course_id": course_id,
                        "course_grade": course_grade,
                        "grades_url": f"https://sit.instructure.com/courses/{course_id}/grades",
                        "submissions": processed_submissions,
                    }
                )

            return {"courses": results}
        except Exception as e:
            logger.error(
                f"Error fetching grades for course {course}: {str(e)}", exc_info=True
            )
            return {"courses": []}

    def get_grades_for_all_courses(self) -> Dict:
        """
        Get grades for all current courses.

        This function retrieves all current courses via get_current_courses,
        then calls get_grades_for_course with the list of courses to get
        grades for each course.

        Returns:
            Dict: In the format {"courses": [ { "course_name": ..., "grades": {...} }, ... ] }
        """
        try:
            all_courses = self.get_current_courses()
            course_infos = [
                {"id": course["id"], "name": course["name"]} for course in all_courses
            ]
            grades = self.get_grades_for_course(course_infos)
            return grades
        except Exception as e:
            logger.error(f"Error fetching grades for all courses: {str(e)}")
            return {"courses": []}

    def get_formatted_grades_for_all_courses(self) -> Dict:
        """Get formatted grades for all courses"""
        try:
            raw_grades = self.get_grades_for_all_courses()
            formatted_courses = []

            for course in raw_grades.get("courses", []):
                course_name = course.get("course_name")
                current_grade = course.get("course_grade", {})
                submissions = course.get("submissions", [])

                formatted_assignments = []
                for submission in submissions:
                    name = submission.get("assignment_name", "")
                    points_possible = submission.get("points_possible", 0)
                    score = submission.get("score")

                    formatted_assignment = {
                        "name": name,
                        "score": (
                            f"{score}/{points_possible}"
                            if score is not None
                            else "Not graded yet"
                        ),
                        "percentage": (
                            f"{(score/points_possible*100):.1f}%"
                            if score is not None and points_possible
                            else "Not graded yet"
                        ),
                    }
                    formatted_assignments.append(formatted_assignment)

                formatted_course = {
                    "course_name": course_name,
                    "current_grade": {
                        "letter_grade": current_grade.get(
                            "current_grade", "Not available"
                        ),
                        "percentage": (
                            f"{current_grade.get('current_score', 0):.1f}%"
                            if current_grade.get("current_score") is not None
                            else "Not available"
                        ),
                    },
                    "assignments": formatted_assignments,
                }

                formatted_courses.append(formatted_course)

            return {"courses": formatted_courses}

        except Exception as e:
            logger.error(f"Error getting formatted grades: {str(e)}")
            return {"courses": []}
        
    def get_formatted_grades_for_all_courses(self) -> Dict:
        """Get formatted grades for all courses"""
        try:
            raw_grades = self.get_grades_for_all_courses()
            formatted_courses = []
        
            for course in raw_grades.get("courses", []):
                course_name = course.get("course_name")
                current_grade = course.get("course_grade", {})
                submissions = course.get("submissions", [])
            
            
                formatted_assignments = []
                for submission in submissions:
                    name = submission.get("assignment_name", "")
                    points_possible = submission.get("points_possible", 0)
                    score = submission.get("score")
                
                    formatted_assignment = {
                        "name": name,
                        "score": f"{score}/{points_possible}" if score is not None else "Not graded yet",
                        "percentage": f"{(score/points_possible*100):.1f}%" if score is not None and points_possible else "Not graded yet"
                    }
                    formatted_assignments.append(formatted_assignment)
            
                formatted_course = {
                    "course_name": course_name,
                    "current_grade": {
                        "letter_grade": current_grade.get("current_grade", "Not available"),
                        "percentage": f"{current_grade.get('current_score', 0):.1f}%" if current_grade.get('current_score') is not None else "Not available"
                    },
                    "assignments": formatted_assignments
                }
            
                formatted_courses.append(formatted_course)
        
            return {"courses": formatted_courses}
        
        except Exception as e:
            logger.error(f"Error getting formatted grades: {str(e)}")
            return {"courses": []}
        
    async def get_formatted_grades_for_course(self, course_id: int) -> dict:
        """Get formatted grades for a specific course"""
        try:
            # Get course grades
            raw_grades = self.get_grades_for_course(course_id)
            if not raw_grades or not raw_grades.get("courses"):
                return {"courses": []}
                
            course_data = raw_grades["courses"][0]  # Get data for the first course
            
            # Format the course data
            formatted_course = {
                "course_name": course_data.get("course_name", "Unknown Course"),
                "current_grade": {
                    "letter_grade": course_data.get("course_grade", {}).get("current_grade"),
                    "percentage": (
                        f"{course_data.get('course_grade', {}).get('current_score', 0):.1f}%"
                        if course_data.get('course_grade', {}).get('current_score') is not None
                        else "Not available"
                    )
                },
                "assignments": []
            }
            
            # Format assignments
            for submission in course_data.get("submissions", []):
                score = submission.get("score")
                points_possible = submission.get("points_possible")
                
                formatted_assignment = {
                    "name": submission.get("assignment_name", "Unknown Assignment"),
                    "score": (
                        f"{score:.1f}/{points_possible:.1f}"
                        if score is not None and points_possible is not None
                        else "Not graded yet"
                    ),
                    "percentage": (
                        f"{(score / points_possible * 100):.1f}%"
                        if score is not None and points_possible and points_possible > 0
                        else "Not graded yet"
                    )
                }
                formatted_course["assignments"].append(formatted_assignment)
            
            return {"courses": [formatted_course]}  # Return as a list with one course
            
        except Exception as e:
            logger.error(f"Error formatting grades: {str(e)}")
            return {"courses": []}