from typing import List, Dict, Optional, Any
import logging
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel
from azure.ai.projects.models import FunctionTool, ToolSet, ConnectionType
from app.services.user_functions import user_functions
from app.core.config import settings
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str
    content: str


class ModelService:

    def __init__(self):
        # Initialize Azure AI Project client with connection string
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(), conn_str=settings.CONN_STR)
        # Get the existing agent
        self.agent = self.project_client.agents.get_agent(settings.AGENT_ID)

        # Initialize embeddings client for generating vector embeddings
        self.embeddings = self.project_client.inference.get_embeddings_client()

        # Get Azure AI Search connection
        try:
            # Get the default search connection from project client
            self.search_connection = self.project_client.connections.get_default(
                connection_type=ConnectionType.AZURE_AI_SEARCH,
                include_credentials=True)

            # Create search client for RAG
            self.search_client = SearchClient(
                index_name=settings.AISEARCH_INDEX_NAME,
                endpoint=self.search_connection.endpoint_url,
                credential=AzureKeyCredential(key=self.search_connection.key),
            )
            self.rag_enabled = True
            logger.info("RAG enabled with Azure AI Search")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure AI Search: {str(e)}")
            self.rag_enabled = False

        self.toolset = ToolSet()
        self.toolset.add(FunctionTool(user_functions))

    async def retrieve_relevant_documents(self,
                                          query: str,
                                          top: int = 5) -> List[Dict]:
        """
        Retrieve relevant documents from Azure AI Search
        """
        if not self.rag_enabled:
            logger.warning("RAG is not enabled, skipping document retrieval")
            return []

        try:
            # Generate vector embedding for query
            embedding_model = settings.EMBEDDINGS_MODEL or "text-embedding-ada-002"
            embedding = self.embeddings.embed(model=embedding_model,
                                              input=query)
            search_vector = embedding.data[0].embedding

            # Create vector query
            vector_query = VectorizedQuery(vector=search_vector,
                                           k_nearest_neighbors=top,
                                           fields="contentVector")

            # Search for relevant documents
            search_results = self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                select=["id", "content", "filepath", "title", "url"])

            # Process search results
            documents = [{
                "id": result["id"],
                "content": result["content"],
                "filepath": result.get("filepath", ""),
                "title": result.get("title", ""),
                "url": result.get("url", "")
            } for result in search_results]

            logger.debug(
                f"Retrieved {len(documents)} documents for query: {query}")
            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []

    async def get_completion(self,
                             messages: List[Dict[str, str]],
                             functions: Optional[List[Dict]] = None,
                             function_call: str = "auto",
                             temperature: float = 0.7) -> Dict[str, Any]:
        """
        Get completion from Azure AI Foundry agent with RAG enhancement
        """
        try:
            # Create a new thread for this conversation
            thread = self.project_client.agents.create_thread()

            # Get the user's query from the last user message
            user_query = next(
                (m["content"]
                 for m in reversed(messages) if m["role"] == "user"), "")

            # Retrieve relevant documents using RAG if enabled
            relevant_docs = []
            if self.rag_enabled and user_query:
                relevant_docs = await self.retrieve_relevant_documents(
                    user_query)

            # Prepare context from relevant documents
            context = ""
            if relevant_docs:
                logger.info("????????? Relevant documents found: ",
                            relevant_docs)
                context = "Here is some relevant information that might help answer the question:\n\n"
                for i, doc in enumerate(relevant_docs, 1):
                    context += f"Document {i}:\n"
                    context += f"Title: {doc.get('title', 'No title')}\n"
                    context += f"Content: {doc['content']}\n\n"

            # Add system message with RAG context if available
            if context:
                system_message = {
                    "role":
                    "assistant",
                    "content":
                    "You are a helpful assistant with access to Stevens Institute of Technology information. "
                    "Use the following context to answer the question, but respond naturally and conversationally. "
                    f"\n\n{context}\n\n"
                    "Provide a clear and concise answer. Use emojis to make it engaging. "
                    "Include a short encouraging message for the student."
                }
                self.project_client.agents.create_message(
                    thread_id=thread.id,
                    role=system_message["role"],
                    content=system_message["content"])

            # Add all user messages to the thread
            for message in messages:
                self.project_client.agents.create_message(
                    thread_id=thread.id,
                    role=message["role"],
                    content=message["content"])

            # Process the conversation with the agent
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=self.agent.id,
                toolset=self.toolset)
            print("[DEBUG] Run status:", run.status)

            # Get the agent's response
            messages = self.project_client.agents.list_messages(
                thread_id=thread.id)
            print("&&&&&&&&&&& MESSAGES: ", messages, "&&&&&&&&&&&")
            # Debug: Print out all text messages
            for m in messages.data:
                if m.content and m.content[0].text:
                    print(f"[DEBUG] Agent Message (role={m.role}):",
                          m.content[0].text.value)

            # Handle empty case
            if not messages.data:
                logger.warning("No text messages returned from agent.")
                return {
                    "content": "[Error] Agent did not return any messages.",
                    "function_call": None
                }

            # Find the last assistant message that doesn't contain the system prompt
            # This ensures we get the actual response, not just the RAG context
            latest_message = None
            for m in reversed(messages.data):
                if m.role == "assistant":
                    # Skip if this is the system message we added with RAG context
                    if context and m.content and m.content[
                            0].text and context in m.content[0].text.value:
                        continue
                    latest_message = m
                    break

            if not latest_message:
                # Try again without context filtering
                latest_message = next((m for m in reversed(messages.data)
                                       if m.role == "assistant"), None)

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
                    role="assistant",
                    content=context_message)
            else:
                # Try to get RAG context for the last user message
                try:
                    user_query = next(
                        (msg.content
                         for msg in reversed(messages) if msg.role == "user"),
                        "")
                    if user_query and self.rag_enabled:
                        # Convert messages to the format expected by retrieve_relevant_documents
                        relevant_docs = self.retrieve_relevant_documents(
                            user_query)

                        if relevant_docs:
                            context = "Here is some relevant information that might help answer the question:\n\n"
                            for i, doc in enumerate(relevant_docs, 1):
                                context += f"Document {i}:\n"
                                context += f"Title: {doc.get('title', 'No title')}\n"
                                context += f"Content: {doc['content']}\n\n"

                            context_message = (
                                "You are a helpful assistant with access to Stevens Institute of Technology information. "
                                "Use the following context to answer the question, but respond naturally and conversationally. "
                                f"\n\nContext: {context}\n\n"
                                "Please summarize it for the user in a clear and concise manner. Please use some emojis to make it more engaging. "
                                "Also include some words of encouragement and motivation to the user (keep it short), who is a student at Stevens Institute of Technology. "
                            )
                            self.project_client.agents.create_message(
                                thread_id=thread.id,
                                role="assistant",
                                content=context_message)
                except Exception as e:
                    logger.warning(f"Failed to add RAG context: {str(e)}")

            # Process with the agent
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id, agent_id=self.agent.id)

            # Get the response
            messages = self.project_client.agents.list_messages(
                thread_id=thread.id)
            return messages.data[
                -1].text if messages.data and messages.data[-1].text else ""

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error generating a response."
