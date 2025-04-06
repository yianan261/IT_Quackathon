from typing import List, Dict, Optional, Any
import logging
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel
from azure.ai.projects.models import FunctionTool, ToolSet
from app.services.user_functions import user_functions
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(), 
            conn_str=settings.CONN_STR
        )
        self.agent = self.project_client.agents.get_agent(settings.AGENT_ID)
        self.toolset = ToolSet()
        self.toolset.add(FunctionTool(user_functions))

    async def get_completion(self,
                           messages: List[Dict[str, str]],
                           functions: Optional[List[Dict]] = None,
                           function_call: str = "auto",
                           temperature: float = 0.7) -> Dict[str, Any]:
        """获取 AI 回复"""
        try:
            thread = self.project_client.agents.create_thread()
            for message in messages:
                self.project_client.agents.create_message(
                    thread_id=thread.id,
                    role=message["role"],
                    content=message["content"]
                )
            
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=self.agent.id,
                toolset=self.toolset
            )
            
            
            messages = self.project_client.agents.list_messages(thread_id=thread.id)
            latest_message = next(
                (m for m in reversed(messages.data) if m.role == "assistant"),
                None
            )
            
            content = (latest_message.content[0].text.value
                      if latest_message and latest_message.content
                      and latest_message.content[0].text
                      and latest_message.content[0].text.value else "")
            
            return {"content": content, "function_call": None}
            
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}")
            raise