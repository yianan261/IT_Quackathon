from typing import List, Dict, Optional, Any
import logging
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tracers import ConsoleCallbackHandler
from pydantic import BaseModel
from app.services.user_functions import all_tools
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str
    content: str


class ModelService:

    def __init__(self):
        # Initialize OpenAI chat model
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL or "gpt-4-turbo-preview",
            temperature=0.7,
            max_tokens=settings.MAX_TOKENS or 1000,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Available LangChain tools
        self.tools = all_tools
        
        # Create the agent prompt using the standard format
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant for Stevens Institute of Technology students. 
You have access to various tools to help students with their academic needs including:
- Getting current courses and assignments
- Checking grades and announcements  
- Navigating Workday for registration and financial information
- Getting academic calendar events and program requirements

CRITICAL RESPONSE FORMATTING RULES:
1. When a tool returns structured JSON data with "response_type" field, you MUST return that exact JSON structure without any modification.
2. Do NOT reformat structured JSON responses into natural language or markdown.
3. Do NOT add explanatory text before or after structured JSON responses.
4. If the tool response contains "response_type", return the complete JSON as-is.
5. Only provide natural language responses for tools that return plain text or when no structured data is involved.

STRUCTURED RESPONSE DETECTION:
- If tool response contains "response_type": "assignments" → Return the complete JSON exactly as provided

- If tool response is plain text or doesn't contain "response_type" → Respond naturally with emojis and encouragement

Use the available tools when needed to provide accurate and helpful information."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        
        # Configure agent executor with LangSmith tracing
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True,
            return_intermediate_steps=True,  # Enable step tracking
            max_iterations=5,  # Prevent infinite loops
            early_stopping_method="generate"  # Stop when final answer is generated
        )

    async def get_completion(self,
                             messages: List[Dict[str, str]],
                             functions: Optional[List[Dict]] = None,
                             function_call: str = "auto",
                             temperature: float = 0.7) -> Dict[str, Any]:
        """
        Get completion using LangChain agent with tools
        """
        try:
            # Convert messages to LangChain format
            chat_history = []
            user_input = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    # System messages are handled in the prompt template
                    continue
                elif msg["role"] == "user":
                    user_input = msg["content"]  # Use the last user message as input
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))
            
            # Remove the last user message from history since it's used as input
            if chat_history and isinstance(chat_history[-1], HumanMessage):
                chat_history = chat_history[:-1]
            
            # Debug: Print what we're passing to the agent
            agent_input = {
                "input": user_input,
                "chat_history": chat_history
            }
            logger.info(f"[DEBUG] Passing to agent: input='{user_input}', chat_history={len(chat_history)} messages")
            
            # Run the agent with metadata for LangSmith tracing
            result = await self.agent_executor.ainvoke(
                agent_input,
                config={
                    "tags": ["stevens-ai-assistant", "chat-endpoint"],
                    "metadata": {
                        "user_input_length": len(user_input),
                        "chat_history_length": len(chat_history),
                        "session_type": "chat"
                    }
                }
            )
            
            return {
                "content": result["output"],
                "function_call": None  # LangChain handles this internally
            }

        except Exception as e:
            logger.error(f"Error getting completion from LangChain agent: {str(e)}")
            raise

    def generate_response(self,
                          messages: List[ChatMessage],
                          function_result: Optional[str] = None,
                          current_function: Optional[str] = None) -> str:
        """
        Generate a response using LangChain agent (sync version)
        """
        try:
            # Convert ChatMessage objects to dictionaries
            message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            # If we have function result, add it as context
            if function_result:
                system_message = {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant for Stevens Institute of Technology students. "
                        "Use the following context to answer the question naturally and conversationally. "
                        f"\n\nContext: {function_result}\n\n"
                        "Please summarize it for the user in a clear and concise manner. Use some emojis to make it more engaging. "
                        "Also include some words of encouragement and motivation to the user (keep it short), who is a student at Stevens Institute of Technology."
                    )
                }
                message_dicts.insert(0, system_message)

            # Use the sync version for compatibility
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, create a new thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.get_completion(message_dicts))
                        result = future.result()
                else:
                    result = loop.run_until_complete(self.get_completion(message_dicts))
            except RuntimeError:
                # No event loop, create one
                result = asyncio.run(self.get_completion(message_dicts))
            
            return result.get("content", "")

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error generating a response."

    def chat_with_tools(self, user_input: str, chat_history: Optional[List] = None) -> str:
        """
        Simple chat interface with tools (sync version)
        """
        try:
            messages = []
            if chat_history:
                messages.extend(chat_history)
            messages.append({"role": "user", "content": user_input})
            
            result = self.generate_response([ChatMessage(role=msg["role"], content=msg["content"]) for msg in messages])
            return result
        except Exception as e:
            logger.error(f"Error in chat_with_tools: {str(e)}")
            return "I apologize, but I encountered an error processing your request."
