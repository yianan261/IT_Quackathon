from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
from app.services.model_service import ModelService
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
import re

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
model_service = ModelService()


def get_canvas_service():
    return CanvasService()


def get_stevens_service():
    return StevensService()


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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint that communicates with the Azure AI Agent and handles responses.
    
    This endpoint now utilizes the Model Context Provider (MCP) pattern,
    where the agent can request multiple types of context data in a single call.
    """
    try:
        # Convert Pydantic models to dictionaries for Azure service
        messages = [{
            "role": msg.role,
            "content": msg.content
        } for msg in request.messages]

        # Get response from the model service
        response = await model_service.get_completion(messages=messages)

        # Return the response content
        return ChatResponse(response=response["content"])

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Error processing request: {str(e)}")
