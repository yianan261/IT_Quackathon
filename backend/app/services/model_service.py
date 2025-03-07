from typing import List, Optional, Dict, Union
import logging
import traceback
from openai import OpenAI
from pydantic import BaseModel
import json

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str
    content: str


#TODO: add more external function calls for other services if required
class ModelService:

    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-3.5-turbo"

        self.functions = [{
            "name": "get_course_assignments",
            "description": "Get upcoming assignments for a specific course",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_identifier": {
                        "type":
                        "string",
                        "description":
                        "Course code or name (e.g., 'EE 553', 'C++', 'Programming')"
                    }
                }
            }
        }, {
            "name": "get_upcoming_courses_assignments",
            "description": "Get upcoming assignments for all enrolled courses",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }, {
            "name": "get_academic_calendar_event",
            "description":
            "Get information about academic calendar events (like spring break, semester start/end dates, etc)",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_type": {
                        "type":
                        "string",
                        "description":
                        "Type of academic calendar event (e.g., 'spring break', 'finals week', 'semester start')"
                    }
                }
            }
        }, {
            "name": "get_program_requirements",
            "description":
            "Get course requirements for a specific degree program",
            "parameters": {
                "type": "object",
                "properties": {
                    "program": {
                        "type":
                        "string",
                        "description":
                        "Degree program name (e.g., 'AAI masters', 'Computer Science PhD')"
                    }
                }
            }
        }]

    def generate_response(
        self,
        messages: List[ChatMessage],
        function_result: Optional[Union[str,
                                        Dict]] = None) -> Union[str, dict]:
        """Generate a response using the OpenAI API with function calling and structured responses"""
        try:
            formatted_messages = [{
                "role": msg.role,
                "content": msg.content
            } for msg in messages]

            if function_result:
                formatted_context = json.dumps(
                    function_result, indent=2) if isinstance(
                        function_result, dict) else function_result
                readable_context = (
                    "You are a helpful assistant with access to Stevens Institute of Technology information. "
                    "Use the following context to answer the question, but respond naturally and conversationally. "
                    f"\n\nContext: {formatted_context}\n\n"
                    "Please summarize it for the user in a clear and concise manner. Please use some emojis to make it more engaging.\
                        Also include some words of encouragement and motivation to the user (keep it short), who is a student at Stevens Institute of Technology."
                )

                formatted_messages.append({
                    "role": "system",
                    "content": readable_context
                })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                functions=self.functions,
                function_call="auto",
                temperature=0.7,
                max_tokens=500)

            response_message = response.choices[0].message
            if hasattr(response_message,
                       "function_call") and response_message.function_call:
                return {
                    "function": response_message.function_call.name,
                    "arguments": response_message.function_call.arguments
                }
            # if no function call, return the response content (string)
            return response_message.content

        except Exception as e:
            logger.error(
                f"Error generating response: {str(e)}\n{traceback.format_exc()}"
            )
            return "I apologize, but I encountered an error generating a response."
