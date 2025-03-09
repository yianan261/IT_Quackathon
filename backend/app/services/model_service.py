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


class ModelService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-3.5-turbo"

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_course_assignments",
                    "description": "Get upcoming assignments for a specific course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_identifier": {
                                "type": "string",
                                "description": "Course code or name (e.g., 'EE 553', 'C++', 'Programming')",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_upcoming_courses_assignments",
                    "description": "Get upcoming assignments for all enrolled courses",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_academic_calendar_event",
                    "description": "Get information about academic calendar events (like spring break, semester start/end dates, etc)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_type": {
                                "type": "string",
                                "description": "Type of academic calendar event (e.g., 'spring break', 'finals week', 'semester start')",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_program_requirements",
                    "description": "Get course requirements for a specific degree program",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "program": {
                                "type": "string",
                                "description": "Degree program name (e.g., 'AAI masters', 'Computer Science PhD')",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_announcements_for_all_courses",
                    "description": "Get announcements for all enrolled courses, generally if you do not get course ids or name, you would call this function",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_announcements_for_specific_courses",
                    "description": "Get announcements for specific courses",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_identifier": {
                                "type": "string",
                                "description": "Course code or name (e.g., 'EE 553', 'C++', 'Programming'), could be a list of courses",
                            }
                        },
                    },
                },
            },
        ]

    def generate_response(
        self,
        messages: List[ChatMessage],
        function_result: Optional[Union[str, Dict]] = None,
        current_function: Optional[str] = None
    ) -> Union[str, dict]:
        """
        Generate a response using the OpenAI API with function calling and structured responses.

        :param messages: Chat history messages.
        :param function_result: The result returned by an external function (optional).
        :param current_function: The name of the function that was just called (optional).
        :return: If the model decides to call a function, returns {"function": ..., "arguments": ...}; otherwise returns a text reply.
        """
        try:
            # 1. Format the chat messages as expected by the API
            formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

            # 2. If there is function_result, add a system message with context.
            if function_result:
                formatted_context = (
                    json.dumps(function_result, indent=2)
                    if isinstance(function_result, dict)
                    else function_result
                )
                readable_context = (
                    "You are a helpful assistant with access to Stevens Institute of Technology information. "
                    "Use the following context to answer the question, but respond naturally and conversationally. "
                    f"\n\nContext: {formatted_context}\n\n"
                    "Please summarize it for the user in a clear and concise manner. Please use some emojis to make it more engaging. "
                    "Also include some words of encouragement and motivation to the user (keep it short), who is a student at Stevens Institute of Technology. "
                )
                # Append additional details based on which function was called
                if current_function:
                   
                    if current_function == "get_announcements_for_specific_courses":
                        readable_context += "when you deal with annoucements querying, please include the annoucement link that you get from external function for each course in your response "
                    elif current_function == "get_announcements_for_all_courses":
                        readable_context += "when you deal with annoucements querying, please include the annoucement link that you get from external function for each course in your response  "
                    

                formatted_messages.append({"role": "system", "content": readable_context})

            # 3. If current_function is provided, add a system message indicating which function was just called.
            if current_function:
                system_message = f"(Function Called: {current_function})"
                formatted_messages.append({"role": "system", "content": system_message})
                logger.info(f"(Function Called: {current_function})")

            # 4. Call the OpenAI API to generate a response.
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=500,
            )

            response_message = response.choices[0].message
            if hasattr(response_message, "tool_calls") and response_message.tool_calls:
                return {
                    "function": response_message.tool_calls[0].function.name,
                    "arguments": response_message.tool_calls[0].function.arguments,
                }

            return response_message.content

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}\n{traceback.format_exc()}")
            return "I apologize, but I encountered an error generating a response."
