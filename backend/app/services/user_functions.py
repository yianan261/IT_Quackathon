from typing import Any, List, Dict, Optional, Union
import json
import asyncio
from threading import Thread
from langchain_core.tools import tool
from app.services.canvas_service import CanvasService
from app.services.stevens_service import StevensService
from app.services.rag_service import RAGService
from playwright.async_api import async_playwright
from app.services.workday_service import WorkdayService
from app.core.config import settings

# Create singleton instances
_canvas_service = CanvasService()
_stevens_service = StevensService()

# Initialize RAG service if enabled
_rag_service: Optional[RAGService] = None
if settings.RAG_ENABLED:
    try:
        _rag_service = RAGService()
    except Exception as e:
        print(f"[WARNING] Failed to initialize RAG service: {e}")
        _rag_service = None

_workday_service: Optional[WorkdayService] = None


async def get_workday_service() -> WorkdayService:
    global _workday_service
    if _workday_service is None:
        playwright = await async_playwright().start()
        _workday_service = WorkdayService(playwright)
        await _workday_service.start()
    return _workday_service


# Background loop for async operations
_background_loop = asyncio.new_event_loop()


def _start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


# Start the background thread
t = Thread(target=_start_background_loop, args=(_background_loop,), daemon=True)
t.start()


def run_async_tool(tool_coro):
    """Helper to run async tools in sync context"""
    print("[DEBUG] run_async_tool: scheduling on background loop")
    try:
        future = asyncio.run_coroutine_threadsafe(tool_coro, _background_loop)
        result = future.result()  # This blocks but safely waits for the result
        print("[DEBUG] run_async_tool: coroutine finished")
        return result
    except Exception as e:
        print(f"[ERROR] Exception in run_async_tool: {e}")
        return json.dumps({
            "success": False,
            "error": f"Exception during async tool run: {str(e)}"
        })


# LangChain Tools
@tool
def get_current_courses() -> str:
    """
    Get all current courses for the student.
    
    Returns:
        str: A JSON string containing information about all enrolled courses.
    """
    courses = _canvas_service.get_current_courses()
    return json.dumps(courses)


@tool
def get_course_assignments(course_identifier: str) -> str:
    """
    Get upcoming assignments for a specific course.
    
    Args:
        course_identifier: The course name, code, or ID (e.g., "CS115", "Machine Learning")
        
    Returns:
        str: A JSON string containing assignment information for the specified course.
    """
    assignments = _canvas_service.get_assignments_for_course(course_identifier)
    return json.dumps(assignments)


@tool
def get_upcoming_courses_assignments() -> str:
    """
    Get upcoming assignments for all enrolled courses.
    
    Returns:
        str: A JSON string containing assignments for all courses.
    """
    courses = _canvas_service.get_current_courses()
    all_assignments = []

    for course in courses:
        assignments = _canvas_service.get_assignments_for_course(course['id'])
        if assignments:
            all_assignments.append({
                "course_name": course["name"],
                "assignments": assignments
            })

    return json.dumps({"courses": all_assignments})


@tool
def get_grades() -> str:
    """
    Get grades for all enrolled courses in a simplified format.
    
    Returns:
        str: A JSON string containing grades information for all courses.
    """
    grades = _canvas_service.get_simplified_grades()
    return json.dumps(grades)


@tool
def get_grades_for_course(course_identifier: str) -> str:
    """
    Get grades for a specific course in a simplified format.
    
    Args:
        course_identifier: The course name, code, or ID (e.g., "CS115", "Machine Learning")
        
    Returns:
        str: A JSON string containing grades information for the specified course.
    """
    grades = _canvas_service.get_simplified_grades(course_identifier)
    return json.dumps(grades)


@tool
def get_announcements_for_all_courses() -> str:
    """
    Get announcements for all enrolled courses.
    
    Returns:
        str: A JSON string containing announcements for all courses.
    """
    courses = _canvas_service.get_current_courses()
    all_announcements = []

    for course in courses:
        announcements = _canvas_service.get_announcements_for_course(course['id'])
        if announcements:
            all_announcements.append({
                "course_name": course["name"],
                "announcements": announcements
            })

    return json.dumps({"courses": all_announcements})


@tool
def get_announcements_for_specific_courses(course_identifier: str) -> str:
    """
    Get announcements for a specific course.
    
    Args:
        course_identifier: Course code or name (e.g., 'EE 553', 'C++')
        
    Returns:
        str: A JSON string containing announcements for the specified course.
    """
    announcements = _canvas_service.get_announcements_for_course(course_identifier)
    return json.dumps(announcements)


@tool
def get_program_requirements(program: str) -> str:
    """
    Get course requirements for a specific degree program.
    
    Args:
        program: Degree program name (e.g., 'AAI masters', 'Computer Science PhD')
        
    Returns:
        str: A JSON string containing program requirements.
    """
    requirements = _stevens_service.get_program_requirements(program)
    return json.dumps(requirements)


@tool
def get_academic_calendar_event(event_type: str) -> str:
    """
    Get information about academic calendar events.
    
    Args:
        event_type: Type of academic calendar event (e.g., 'spring break', 'finals week')
        
    Returns:
        str: A JSON string containing calendar event information.
    """
    event = _stevens_service.get_calendar_event(event_type)
    return json.dumps(event)


@tool
def navigate_to_workday_registration(mock_mode: bool = False, stay_open: bool = False) -> str:
    """
    Navigate to the course registration page in Workday.
    This will open a browser and prompt you to enter your credentials if not already logged in.
    
    Args:
        mock_mode: Use mock mode for testing without Playwright installed
        stay_open: Keep the browser open after navigation
        
    Returns:
        str: A JSON string containing navigation results.
    """
    async def _navigate():
        try:
            service = await get_workday_service()
            result = await service.navigate_to_workday_registration(stay_open)

            print(f"***************Navigated to Workday registration page: {result}")

            final_result = {
                "success": result["success"],
                "message": result["message"],
                "screenshot": result.get("screenshot"),
                "human_message": (
                    "✅ I've redirected you to the Workday course registration page.\n\n"
                    "ℹ️ Here's more information on how you can register for courses: "
                    "https://support.stevens.edu/support/solutions/articles/19000082229"
                ) if result["success"] else "❌ I couldn't navigate to the registration page."
            }
            
            if not stay_open:
                await service.close()

            print("[DEBUG] Tool result returned to agent:", json.dumps(final_result))
            return json.dumps(final_result)

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error navigating to registration: {str(e)}",
                "human_message": "❌ I couldn't navigate to the registration page. Try logging in manually at https://stevens.okta.com/"
            })
    
    return run_async_tool(_navigate())


@tool
def navigate_to_workday_financial_account(mock_mode: bool = False, stay_open: bool = False) -> str:
    """
    Navigate to the financial account page in Workday.
    This will open a browser and prompt you to enter your credentials if not already logged in.
    
    Args:
        mock_mode: Use mock mode for testing without Playwright installed
        stay_open: Keep the browser open after navigation
        
    Returns:
        str: A JSON string containing navigation results.
    """
    async def _navigate():
        try:
            service = await get_workday_service()
            result = await service.navigate_to_workday_financial_account(stay_open)

            if not stay_open:
                await service.close()

            return json.dumps({
                "success": result["success"],
                "message": result["message"],
                "screenshot": result.get("screenshot"),
                "human_message": (
                    "✅ I've redirected you to the Workday financial account page.\n\n"
                ) if result["success"] else "❌ I couldn't navigate to the financial account page."
            })

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error navigating to financial account: {str(e)}"
            })
    
    return run_async_tool(_navigate())


@tool
def get_advisors_info() -> str:
    """
    Retrieve advisor information scraped from Workday.
    
    Returns:
        str: A JSON string containing advisor contact information.
    """
    async def _get_advisors():
        try:
            service = await get_workday_service()
            advisors = service.get_advisors_list()
            return json.dumps({
                "success": True,
                "advisors": advisors,
                "human_message": (
                    "📘 Here are your advisors:\n" +
                    "\n".join(f"- {a['role']}: {a['person']} ({a['email']})" for a in advisors)
                    if advisors else "⚠️ No advisor information available. Try visiting Workday first."
                )
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "human_message": "⚠️ I couldn't retrieve your advisor info."
            })
    
    return run_async_tool(_get_advisors())


@tool
def shutdown_workday_browser() -> str:
    """
    Close the Workday browser session.
    
    Returns:
        str: A JSON string indicating success or failure.
    """
    async def _shutdown():
        try:
            if _workday_service:
                await _workday_service.close()
                return json.dumps({
                    "success": True,
                    "message": "Browser closed successfully."
                })
            return json.dumps({
                "success": False,
                "message": "WorkdayService is not active."
            })
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    return run_async_tool(_shutdown())


# RAG (Retrieval-Augmented Generation) Tools
@tool
def search_stevens_knowledge(query: str) -> str:
    """
    Search the Stevens Institute knowledge base for relevant information.
    This tool retrieves information from official Stevens documents, policies,
    academic information, and institutional knowledge.
    
    Args:
        query: The search query (e.g., "computer science requirements", "academic calendar", "tuition costs")
        
    Returns:
        str: A JSON string containing relevant information from the knowledge base.
    """
    if not _rag_service:
        return json.dumps({
            "success": False,
            "error": "RAG service not available",
            "message": "Knowledge base search is currently unavailable."
        })
    
    try:
        # Search for relevant documents
        results = _rag_service.search_similar(query, top_k=3)
        
        if not results:
            return json.dumps({
                "success": True,
                "results": [],
                "message": f"No relevant information found for '{query}'. Try rephrasing your question."
            })
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result["content"].strip(),
                "source": result["metadata"].get("source", "unknown"),
                "category": result["metadata"].get("category", "general"),
                "relevance_score": round(1 - result["score"], 3)  # Convert distance to relevance
            })
        
        return json.dumps({
            "success": True,
            "query": query,
            "results": formatted_results,
            "message": f"Found {len(formatted_results)} relevant documents about '{query}'"
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Error searching knowledge base."
        })


@tool
def get_stevens_info(topic: str) -> str:
    """
    Get specific information about Stevens Institute topics like academic programs,
    policies, deadlines, requirements, or general institutional information.
    
    Args:
        topic: The specific topic to search for (e.g., "CS program requirements", 
               "academic calendar", "registration deadlines", "faculty contacts")
               
    Returns:
        str: A JSON string containing detailed information about the topic.
    """
    if not _rag_service:
        return json.dumps({
            "success": False,
            "error": "Knowledge base not available"
        })
    
    try:
        # Search for relevant documents
        docs = _rag_service.retrieve_documents(topic, top_k=5)
        
        if not docs:
            return json.dumps({
                "success": True,
                "topic": topic,
                "information": "No specific information found about this topic.",
                "suggestion": "Try asking about general topics like 'academic calendar', 'course requirements', or 'student services'."
            })
        
        # Combine and format the information
        combined_info = []
        sources = set()
        
        for doc in docs:
            content = doc.page_content.strip()
            source = doc.metadata.get("source", "Stevens Information")
            category = doc.metadata.get("category", "general")
            
            if content and len(content) > 50:  # Filter out very short chunks
                combined_info.append({
                    "content": content,
                    "source": source,
                    "category": category
                })
                sources.add(source)
        
        return json.dumps({
            "success": True,
            "topic": topic,
            "information": combined_info[:3],  # Limit to top 3 results
            "sources": list(sources),
            "message": f"Found detailed information about '{topic}' from {len(sources)} sources."
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "topic": topic
        })


@tool
def get_rag_stats() -> str:
    """
    Get statistics about the knowledge base including number of documents,
    embedding model used, and other configuration details.
    
    Returns:
        str: A JSON string containing knowledge base statistics.
    """
    if not _rag_service:
        return json.dumps({
            "success": False,
            "error": "RAG service not available"
        })
    
    try:
        stats = _rag_service.get_collection_stats()
        return json.dumps({
            "success": True,
            "stats": stats,
            "message": f"Knowledge base contains {stats.get('total_documents', 0)} documents."
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


# Export all tools
all_tools = [
    get_current_courses,
    get_course_assignments,
    get_upcoming_courses_assignments,
    get_grades,
    get_grades_for_course,
    get_announcements_for_all_courses,
    get_announcements_for_specific_courses,
    get_program_requirements,
    get_academic_calendar_event,
    navigate_to_workday_registration,
    navigate_to_workday_financial_account,
    get_advisors_info,
    shutdown_workday_browser,
    # RAG tools
    search_stevens_knowledge,
    get_stevens_info,
    get_rag_stats,
]
