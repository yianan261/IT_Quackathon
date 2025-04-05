from typing import List, Dict, Optional, Any
import logging
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MCPService:
    """
    Model Context Provider (MCP) service that centralizes access to various data sources.
    This service acts as a single entry point for the agent to retrieve context from
    multiple services without needing to know the implementation details of each.
    """

    def __init__(self):
        self.canvas_service = CanvasService()
        self.stevens_service = StevensService()

    def get_user_context(self, context_types: List[str]) -> Dict[str, Any]:
        """
        Retrieves all requested context types in a single, structured response.
        
        Args:
            context_types: List of context types to retrieve (e.g., "courses", "assignments", "announcements")
            
        Returns:
            A dictionary containing all requested context data with standardized schema
        """
        logger.info(f"MCP retrieving context types: {context_types}")
        context = {}
        errors = []

        try:
            # Add metadata for context tracking
            context["context_meta"] = {
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source_systems": [],
                "requested_types": context_types
            }

            # Process each requested context type
            for context_type in context_types:
                if context_type == "courses":
                    result = self._get_courses_context()
                    context["courses"] = result
                    if result["success"]:
                        if "Canvas" not in context["context_meta"][
                                "source_systems"]:
                            context["context_meta"]["source_systems"].append(
                                "Canvas")
                    else:
                        errors.append(f"Error with courses: {result['error']}")

                elif context_type == "assignments":
                    result = self._get_assignments_context()
                    context["assignments"] = result
                    if result["success"]:
                        if "Canvas" not in context["context_meta"][
                                "source_systems"]:
                            context["context_meta"]["source_systems"].append(
                                "Canvas")
                    else:
                        errors.append(
                            f"Error with assignments: {result['error']}")

                elif context_type == "announcements":
                    result = self._get_announcements_context()
                    context["announcements"] = result
                    if result["success"]:
                        if "Canvas" not in context["context_meta"][
                                "source_systems"]:
                            context["context_meta"]["source_systems"].append(
                                "Canvas")
                    else:
                        errors.append(
                            f"Error with announcements: {result['error']}")

                else:
                    logger.warning(
                        f"Unknown context type requested: {context_type}")

            # Add any errors to metadata
            if errors:
                context["context_meta"]["errors"] = errors

            logger.info(
                f"MCP successfully retrieved {len(context) - 1} context types"
            )  # -1 for context_meta
            return context

        except Exception as e:
            logger.error(f"Error in MCP while retrieving context: {str(e)}")
            return {
                "context_meta": {
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "source_systems": [],
                    "requested_types": context_types,
                    "errors": [f"Global MCP error: {str(e)}"]
                }
            }

    def _get_courses_context(self) -> Dict:
        """Retrieves courses context with standardized response format"""
        try:
            courses = self.canvas_service.get_current_courses()
            # Format and clean the data to ensure standard schema
            formatted_courses = []
            for course in courses:
                formatted_courses.append({
                    "id":
                    course.get("id"),
                    "name":
                    course.get("name", "Unknown Course"),
                    "code":
                    course.get("course_code", ""),
                    "url":
                    course.get("html_url", "")
                })

            return {
                "success":
                True,
                "data":
                formatted_courses,
                "formatted_response":
                self.canvas_service.format_courses_response(courses),
                "error":
                None
            }
        except Exception as e:
            logger.error(f"Error retrieving courses context: {str(e)}")
            return {
                "success": False,
                "data": None,
                "formatted_response": None,
                "error": str(e)
            }

    def _get_assignments_context(self) -> Dict:
        """Retrieves assignments context with standardized response format"""
        try:
            courses = self.canvas_service.get_current_courses()
            course_infos = [{
                "id": course["id"],
                "name": course["name"]
            } for course in courses]
            raw_assignments = self.canvas_service.get_assignments_for_course(
                course_infos)

            # Standardize the data structure
            if "courses" not in raw_assignments:
                return {
                    "success": False,
                    "data": None,
                    "error": "Invalid assignment data structure"
                }

            # Format data in a consistent way
            formatted_assignments = []
            for course in raw_assignments["courses"]:
                course_name = course.get("course_name", "Unknown Course")
                for assignment in course.get("assignments", []):
                    formatted_assignments.append({
                        "name":
                        assignment.get("name", "Unnamed Assignment"),
                        "course_name":
                        course_name,
                        "due_at":
                        assignment.get("due_at"),
                        "points_possible":
                        assignment.get("points_possible"),
                        "url":
                        assignment.get("html_url", "")
                    })

            return {
                "success": True,
                "data": {
                    "course_assignments": raw_assignments["courses"],
                    "all_assignments": formatted_assignments
                },
                "error": None
            }
        except Exception as e:
            logger.error(f"Error retrieving assignments context: {str(e)}")
            return {"success": False, "data": None, "error": str(e)}

    def _get_announcements_context(self) -> Dict:
        """Retrieves announcements context with standardized response format"""
        try:
            all_courses = self.canvas_service.get_current_courses()
            course_infos = [{
                "id": course["id"],
                "name": course["name"]
            } for course in all_courses]
            raw_announcements = self.canvas_service.get_announcements_for_course(
                course_infos)

            if "courses" not in raw_announcements:
                return {
                    "success": False,
                    "data": None,
                    "error": "Invalid announcement data structure"
                }

            # Format data in a consistent way
            formatted_announcements = []
            for course in raw_announcements["courses"]:
                course_name = course.get("course_name", "Unknown Course")
                for announcement in course.get("announcements", []):
                    formatted_announcements.append({
                        "title":
                        announcement.get("title", "Untitled Announcement"),
                        "course_name":
                        course_name,
                        "posted_at":
                        announcement.get("posted_at"),
                        "author":
                        announcement.get("author",
                                         {}).get("display_name",
                                                 "Unknown Author"),
                        "url":
                        course.get("course_announcements_link", "")
                    })

            return {
                "success": True,
                "data": {
                    "course_announcements": raw_announcements["courses"],
                    "all_announcements": formatted_announcements
                },
                "error": None
            }
        except Exception as e:
            logger.error(f"Error retrieving announcements context: {str(e)}")
            return {"success": False, "data": None, "error": str(e)}

