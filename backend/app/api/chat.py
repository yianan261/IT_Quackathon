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
from app.services.workday_service import WorkdayService
from app.services.user_service import UserService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


def get_canvas_service():
    return CanvasService()


def get_stevens_service():
    return StevensService()


def get_model_service():
    return ModelService()


def get_workday_service():
    return WorkdayService(headless=False, mock_for_testing=False)


def get_user_service():
    return UserService()


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


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    model_service: ModelService = Depends(get_model_service)
) -> ChatResponse:
    try:
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
