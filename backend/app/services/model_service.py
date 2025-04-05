from typing import List, Dict, Optional, Any
import logging
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from pydantic import BaseModel
from app.services.user_functions import user_functions
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str
    content: str


class ModelService:

    def __init__(self):
        # Initialize Azure AI Project client with connection string only
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(), conn_str=settings.CONN_STR)

        # Get the existing agent
        self.agent = self.project_client.agents.get_agent(settings.AGENT_ID)

    async def get_completion(self,
                             messages: List[Dict[str, str]],
                             functions: Optional[List[Dict]] = None,
                             function_call: str = "auto",
                             temperature: float = 0.7) -> Dict[str, Any]:
        """
        Get completion from Azure AI Foundry agent
        """
        try:
            # Create a new thread for this conversation
            thread = self.project_client.agents.create_thread()

            # Add all messages to the thread
            for message in messages:
                self.project_client.agents.create_message(
                    thread_id=thread.id,
                    role=message["role"],
                    content=message["content"])

            # Add system message with simplified guidance
            system_message = (
                "You are a helpful assistant with access to Stevens Institute of Technology information. "
                "Use available tools as needed to answer the user's request.")

            self.project_client.agents.create_message(thread_id=thread.id,
                                                      role="system",
                                                      content=system_message)

            # Process the conversation with the agent
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=self.agent.id,
                tools=user_functions)
            logger.info(f"Run status: {run.status}")

            # Get the agent's response
            messages = self.project_client.agents.list_messages(
                thread_id=thread.id)
            logger.debug(f"Messages: {messages}")

            # Debug: Print out all text messages
            for m in messages.data:
                if m.content and m.content[0].text:
                    logger.debug(
                        f"Agent Message (role={m.role}): {m.content[0].text.value}"
                    )

            # Handle empty case
            if not messages.data:
                logger.warning("No text messages returned from agent.")
                return {
                    "content": "[Error] Agent did not return any messages.",
                    "function_call": None
                }

            latest_message = next(
                (m for m in reversed(messages.data) if m.role == "assistant"),
                None)

            if not latest_message:
                logger.warning("No assistant response found.")
                return {
                    "content":
                    "[Error] Agent did not return any assistant message.",
                    "function_call": None
                }

            content = (latest_message.content[0].text.value
                       if latest_message.content
                       and latest_message.content[0].text
                       and latest_message.content[0].text.value else "")

            function_call_info = None

            # # Check if the agent's response includes a function call
            # if latest_message.tool_calls:
            #     tool_call = latest_message.tool_calls[
            #         0]  # Just handling the first tool call for now
            #     function_call_info = {
            #         "name": tool_call.function.name,
            #         "arguments": tool_call.function.arguments
            #     }

            return {"content": content, "function_call": function_call_info}

        except Exception as e:
            logger.error(
                f"Error getting completion from Azure agent: {str(e)}")
            raise

    def generate_response(self,
                          messages: List[ChatMessage],
                          function_result: Optional[str] = None,
                          current_function: Optional[str] = None) -> str:
        """
        Generate a response using the Azure AI Foundry agent
        """
        try:
            # Create a new thread
            thread = self.project_client.agents.create_thread()

            # Add conversation history
            for msg in messages:
                self.project_client.agents.create_message(thread_id=thread.id,
                                                          role=msg.role,
                                                          content=msg.content)

            # Add function result if available
            if function_result:
                context_message = (
                    "You are a helpful assistant with access to Stevens Institute of Technology information. "
                    "Use the following context to answer the question, but respond naturally and conversationally. "
                    f"\n\nContext: {function_result}\n\n"
                    "Please summarize it for the user in a clear and concise manner. Please use some emojis to make it more engaging. "
                    "Also include some words of encouragement and motivation to the user (keep it short), who is a student at Stevens Institute of Technology. "
                )
                self.project_client.agents.create_message(
                    thread_id=thread.id,
                    role="system",
                    content=context_message)

            # Process with the agent
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=self.agent.id,
                tools=user_functions)

            # Get the response
            messages = self.project_client.agents.list_messages(
                thread_id=thread.id)
            latest_message = next(
                (m for m in reversed(messages.data) if m.role == "assistant"),
                None)

            if not latest_message or not latest_message.content:
                return "I apologize, but I encountered an error generating a response."

            content = latest_message.content[
                0].text.value if latest_message.content[0].text else ""
            return content

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error generating a response."
