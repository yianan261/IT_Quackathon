from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
from app.services.model_service import ModelService
from app.context import get_service_context
import re
import logging
import json
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


def get_canvas_service():
    return CanvasService()


def get_stevens_service():
    return StevensService()


def get_model_service():
    return ModelService()


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
        r"([a-zA-Z\s]+(?:class|course))", r"([a-zA-Z\s]+)\s+assignments"
    ]
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            return match.group(1).strip()
    return ""

def needs_student_info(message: str) -> bool:
    """Check if the message indicates need for student information"""
    keywords = [
        'workday', 'register', 'registration', 'enroll', 'enrollment',
        'add course', 'drop course', 'student info', 'student information'
    ]
    message = message.lower()
    return any(keyword in message for keyword in keywords)



@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    canvas_service: CanvasService = Depends(get_canvas_service),
    model_service: ModelService = Depends(get_model_service)
) -> ChatResponse:
    
    try:
        last_message = request.messages[-1].content
        
        if needs_student_info(last_message):
            return ChatResponse(
                response="""To help you better with Workday navigation, I'll need some information about you. 
                Please fill out the student information form at:
                
                http://localhost:8000/form
                
                After submitting the form, I'll be able to provide more personalized assistance with Workday navigation."""
            )
        # Get completion from Azure agent
        response = await model_service.get_completion(
            messages=[{
                "role": msg.role,
                "content": msg.content
            } for msg in request.messages])

        return ChatResponse(response=response["content"])

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
