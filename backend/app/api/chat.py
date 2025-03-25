from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
from app.services.model_service import ModelService
from app.context import get_service_context
import re
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
model_service = ModelService()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    response: str
    sources: List[dict] = []


def extract_course_reference(message: str) -> str:
    """Extract potential course name from message"""
    patterns = [
        r"(?:in|for|my|the)\s+([a-zA-Z\s]+(?:class|course))",
        r"(?:in|for|my|the)\s+([a-zA-Z\s]+)\s+(?:class|course)",
        r"([a-zA-Z\s]+(?:class|course))",
        r"([a-zA-Z\s]+)\s+assignments"
    ]
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            return match.group(1).strip()
    return ""


@router.post("/")
async def chat(request: ChatRequest, services: dict = Depends(get_service_context)):
    """Chat endpoint that allows the model to invoke services functions"""
    try:
        user_message = request.messages[-1].content
        logger.info(f"\n=== New Chat Request ===\nReceived message: {user_message}")

        canvas_service = services["canvas_service"]
        stevens_service = services["stevens_service"]

        conversation_history = request.messages.copy()
        # Initial call: no current_function provided
        model_response = model_service.generate_response(request.messages)

        if not isinstance(model_response, dict):
            logger.error(f"Unexpected model response type: {type(model_response)}. Response: {model_response}")
            return ChatResponse(response="Unexpected response from model.")

        logger.info(f"\nInitial LLM response: {json.dumps(model_response, indent=2)}")

        attempts = 0
        max_attempts = 5
        while isinstance(model_response, dict) and "function" in model_response and attempts < max_attempts:
            attempts += 1
            logger.info(f"Processing function call attempt {attempts}")

            function_name = model_response["function"]
            try:
                arguments = model_response["arguments"]
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing arguments: {str(e)}. Arguments: {model_response['arguments']}")
                return ChatResponse(response="Invalid arguments.")

            logger.info(f"Function call: {function_name} with arguments: {arguments}")

            function_result = None

            if function_name == "get_course_assignments":
                course_identifier = arguments["course_identifier"]
                logger.info(f"Getting assignments for course: {course_identifier}")
                assignments = canvas_service.get_assignments_for_course(course_identifier)
                logger.info(f"Got assignments response: {assignments}")
                if assignments:
                    function_result = canvas_service.format_assignments_response(assignments)
                    logger.info(f"Formatted assignments: {function_result}")
                else:
                    function_result = f"No assignments found for {course_identifier}."
                    logger.info("No assignments found")

            elif function_name == "get_upcoming_courses_assignments":
                all_assignments = []
                try:
                    all_assignments = canvas_service.get_upcoming_assignments()
                    if all_assignments:
                        function_result = canvas_service.format_assignments_response(all_assignments)
                        logger.info(f"Formatted assignments: {function_result}")
                    else:
                        function_result = "No assignments found."
                        logger.info("No assignments found")
                except Exception as e:
                    logger.error(f"Error getting upcoming assignments: {str(e)}")
                if all_assignments:
                    try:
                        function_result = canvas_service.format_assignments_response({"courses": all_assignments})
                        logger.info(f"Formatted all assignments: {function_result}")
                    except Exception as e:
                        logger.error(f"Error formatting assignments: {str(e)}")
                        function_result = "Error formatting assignments."
                else:
                    function_result = "No upcoming assignments found in any courses."
                    logger.info("No assignments found in any courses")

            elif function_name == "get_academic_calendar_event":
                function_result = await stevens_service.get_calendar_event(arguments.get("event_type", ""))

            elif function_name == "get_program_requirements":
                program_name = arguments["program"]
                function_result = await stevens_service.get_program_requirements(program_name)

            elif function_name == "get_announcements_for_all_courses":
                logger.info("Getting announcements for all courses")
                announcements = canvas_service.get_announcements_for_all_courses()
                logger.info(f"Got announcements response: {announcements}")
                if announcements:
                    formatted_announcements = canvas_service.format_announcements_response(announcements)
                    function_result = formatted_announcements
                    logger.info(f"Formatted announcements: {function_result}")
                else:
                    function_result = "No announcements found for your courses."

            elif function_name == "get_announcements_for_specific_courses":
                course_identifier = arguments["course_identifier"]
                logger.info(f"Getting announcements for course: {course_identifier}")
                announcements = canvas_service.get_announcements_for_course(course_identifier)
                logger.info(f"Got announcements response: {announcements}")
                if announcements:
                    formatted_announcements = canvas_service.format_announcements_response(announcements)
                    function_result = formatted_announcements
                    logger.info(f"Formatted announcements: {function_result}")
                else:
                    function_result = f"No announcements found for {course_identifier}."
                    logger.info("No announcements found")

            # Add function result to conversation history
            function_result_str = json.dumps(function_result) if isinstance(function_result, (dict, list)) else function_result

            conversation_history.append(ChatMessage(role="assistant", content=function_result_str))

            # Pass the current function name along with function_result to generate_response
            model_response = model_service.generate_response(conversation_history, function_result_str, current_function=function_name)
            logger.info(f"Next LLM response: {model_response}")

        if isinstance(model_response, dict):
            return ChatResponse(response=f"Error: Unable to process request after {max_attempts} attempts")
        return ChatResponse(response=model_response)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
