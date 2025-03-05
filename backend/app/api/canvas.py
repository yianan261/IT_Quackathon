# from fastapi import APIRouter, HTTPException
# from app.services.canvas_service import CanvasService
# from typing import List, Dict, Optional
# import logging

# logger = logging.getLogger(__name__)
# router = APIRouter()
# canvas_service = CanvasService()

# # TODO: probably don't need these endpoints, will get rid later

# @router.get("/test")
# async def test_endpoint():
#     """Test endpoint to verify router is working"""
#     return {"message": "Canvas router is working"}

# @router.get("/assignments/upcoming", response_model=List[Dict])
# async def get_upcoming_assignments():
#     """Get all upcoming assignments from all courses"""
#     try:
#         return canvas_service.get_upcoming_assignments()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/courses/{course_id}/assignments", response_model=List[Dict])
# async def get_course_assignments(course_id: str):
#     """Get assignments for a specific course"""
#     try:
#         assignments = canvas_service.get_course_assignments(course_id)
#         if not assignments:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"No assignments found for course {course_id}")
#         return assignments
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/courses", response_model=List[Dict])
# async def get_current_courses():
#     try:
#         courses = canvas_service.get_current_courses()
#         return [{
#             "id": course.id,
#             "name": course.name,
#             "code": course.course_code
#         } for course in courses]
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/courses/identify")
# async def identify_course(query: str):
#     """Identify course from natural language query"""
#     logger.debug(f"Received query: {query}")

#     try:
#         result = canvas_service.extract_course_identifier(query.get("query"))
#         logger.debug(f"Result from service: {result}")
#         return {"identified_course": result}
#         # return canvas_service.extract_course_identifier(query)
#     except Exception as e:
#         logger.error(f"Error in identify_course: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# __all__ = ['router']
