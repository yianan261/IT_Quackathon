from typing import Any, List, Dict, Optional, Union
import json
import asyncio
import logging
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

# Configure logging
logger = logging.getLogger(__name__)

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
    
    # Check if service exists and is healthy
    if _workday_service is not None:
        try:
            # Check if playwright instance is still valid
            if not _workday_service.playwright:
                print("[DEBUG] Playwright instance is None, recreating service")
                _workday_service = None
            # Test if browser context is still valid
            elif _workday_service.browser_context and not _workday_service.browser_context.pages is None:
                if _workday_service.page and not _workday_service.page.is_closed():
                    print("[DEBUG] Reusing existing WorkdayService")
                    return _workday_service
        except Exception as e:
            print(f"[DEBUG] Existing service unhealthy: {e}, creating new one")
            # Cleanup old service
            try:
                if _workday_service and _workday_service.browser_context:
                    await _workday_service.close()
            except:
                pass
            _workday_service = None
    
    # Create new service if needed
    if _workday_service is None:
        print("[DEBUG] Creating new WorkdayService")
        try:
            playwright = await async_playwright().start()
            _workday_service = WorkdayService(playwright)
            await _workday_service.start()
        except Exception as e:
            print(f"[ERROR] Failed to create WorkdayService: {e}")
            _workday_service = None
            raise
        
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
    Get upcoming assignments for all enrolled courses in structured format for UI rendering.
    
    IMPORTANT: This tool returns structured JSON data with response_type, data, and ui_component fields.
    Return the JSON response exactly as provided without modification.
    
    Returns:
        str: A structured JSON string containing assignments data for frontend rendering.
    """
    from datetime import datetime, timezone
    import re
    
    courses = _canvas_service.get_current_courses()
    all_assignments_data = _canvas_service.get_assignments_for_course(courses)
    
    # Transform to structured format
    structured_courses = []
    total_assignments = 0
    due_today = 0
    due_this_week = 0 
    due_next_week = 0
    high_priority = 0
    medium_priority = 0
    low_priority = 0
    
    current_date = datetime.now(timezone.utc)
    
    for course_data in all_assignments_data.get("courses", []):
        course_assignments = []
        
        for assignment in course_data.get("assignments", []):
            # Parse due date
            due_at = assignment.get("due_at", "")
            if due_at:
                try:
                    due_datetime = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                    days_until_due = (due_datetime - current_date).days
                    
                    # Determine priority based on days until due
                    if days_until_due <= 2:
                        priority = "high"
                        high_priority += 1
                        if days_until_due == 0:
                            due_today += 1
                    elif days_until_due <= 7:
                        priority = "medium" 
                        medium_priority += 1
                        due_this_week += 1
                    else:
                        priority = "low"
                        low_priority += 1
                        if days_until_due <= 14:
                            due_next_week += 1
                    
                    # Extract assignment ID from URL if available
                    assignment_id = None
                    html_url = assignment.get("html_url", "")
                    if html_url:
                        match = re.search(r'/assignments/(\d+)', html_url)
                        assignment_id = match.group(1) if match else str(hash(assignment.get("name", "")))
                    
                    # Structure assignment data
                    structured_assignment = {
                        "assignment_id": assignment_id or str(hash(assignment.get("name", ""))),
                        "name": assignment.get("name", ""),
                        "title": assignment.get("name", ""),
                        "due_date": due_datetime.strftime("%Y-%m-%d"),
                        "due_time": due_datetime.strftime("%H:%M"),
                        "due_datetime": due_datetime.isoformat(),
                        "priority": priority,
                        "status": "pending",
                        "days_until_due": days_until_due,
                        "details_url": html_url,
                        "points_possible": assignment.get("points_possible"),
                        "additional_resources": []
                    }
                    
                    course_assignments.append(structured_assignment)
                    total_assignments += 1
                    
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Error parsing assignment date: {e}")
                    continue
        
        if course_assignments:
            # Sort assignments by due date
            course_assignments.sort(key=lambda x: x["due_datetime"])
            
            structured_course = {
                "course_id": str(course_data.get("course_id", "")),
                "course_code": course_data.get("course_name", "").split("(")[0].strip(),
                "course_name": course_data.get("course_name", ""),
                "assignments": course_assignments
            }
            structured_courses.append(structured_course)
    
    # Create structured response
    structured_response = {
        "response_type": "assignments",
        "message": "Here are your upcoming assignments across all courses:",
        "data": {
            "courses": structured_courses,
            "summary": {
                "total_assignments": total_assignments,
                "due_today": due_today,
                "due_this_week": due_this_week,
                "due_next_week": due_next_week,
                "overdue": 0,
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority
            }
        },
        "ui_component": "AssignmentTimeline",
        "suggestions": [
            "Take me to course registration page",
            "Get my grades",
            "Can you provide me details about cs 549?"
        ]
    }
    
    return json.dumps(structured_response)


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
    Get announcements for all enrolled courses in structured format for UI rendering.
    
    IMPORTANT: This tool returns structured JSON data with response_type, data, and ui_component fields.
    Return the JSON response exactly as provided without modification.
    
    Returns:
        str: A structured JSON string containing announcements data for frontend rendering.
    """
    from datetime import datetime, timezone, timedelta
    
    # Get announcement data from Canvas service
    announcements_data = _canvas_service.get_announcements_for_all_courses()
    courses_data = announcements_data.get("courses", [])
    
    # Transform to structured format
    structured_courses = []
    total_announcements = 0
    recent_announcements = 0
    courses_with_announcements = 0
    
    current_date = datetime.now(timezone.utc)
    # Set cutoff date to February 1st of current year  
    february_first = datetime(current_date.year, 2, 1, tzinfo=timezone.utc)
    
    for course_data in courses_data:
        course_name = course_data.get("course_name", "")
        announcements_link = course_data.get("course_announcements_link", "")
        announcements = course_data.get("announcements", [])
        
        # Process announcements
        processed_announcements = []
        for announcement in announcements:
            try:
                posted_at = announcement.get("posted_at", "")
                posted_datetime = datetime.fromisoformat(posted_at.replace("Z", "+00:00")) if posted_at else current_date
                
                # Determine if announcement is recent (within past week from current date)
                one_week_ago = current_date - timedelta(days=7)
                is_recent = posted_datetime >= one_week_ago
                
                # Only include announcements from February 1st onwards
                if posted_datetime < february_first:
                    continue
                if is_recent:
                    recent_announcements += 1
                
                # Clean message content (remove HTML tags for preview)
                import re
                message = announcement.get("message", "")
                clean_message = re.sub(r'<[^>]+>', '', message).strip()
                preview = clean_message[:150] + "..." if len(clean_message) > 150 else clean_message
                
                processed_announcement = {
                    "title": announcement.get("title", "Announcement"),
                    "author": announcement.get("author", {}).get("display_name", "Instructor"),
                    "posted_at": posted_at,
                    "posted_datetime": posted_datetime.isoformat(),
                    "posted_date": posted_datetime.strftime("%Y-%m-%d"),
                    "posted_time": posted_datetime.strftime("%H:%M"),
                    "message_preview": preview,
                    "full_message": message,
                    "is_recent": is_recent,
                    "url": announcement.get("url", "")
                }
                
                processed_announcements.append(processed_announcement)
                total_announcements += 1
                
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error processing announcement: {e}")
                continue
        
        if processed_announcements:
            courses_with_announcements += 1
        
        # Sort announcements by posted date (most recent first)
        processed_announcements.sort(key=lambda x: x["posted_datetime"], reverse=True)
        
        # Limit to 3 announcements per course
        processed_announcements = processed_announcements[:3]
        
        structured_course = {
            "course_name": course_name,
            "course_code": course_name.split()[0] if course_name else "",
            "announcements_link": announcements_link,
            "announcements": processed_announcements,
            "announcement_count": len(processed_announcements)
        }
        structured_courses.append(structured_course)
    
    # Create structured response
    if total_announcements > 0:
        message = f"Here are your course announcements since February 1st ({total_announcements} total, max 3 per course):"
        suggestions = [
            "Show me recent announcements only", 
            "What announcements are from this week?",
            "Open all announcement links"
        ]
    else:
        message = "No announcements found since February 1st. Here are links to check each course directly:"
        suggestions = [
            "Get my assignments instead", 
            "Show me my current courses",
            "What's due this week?"
        ]
    
    structured_response = {
        "response_type": "announcements",
        "message": message,
        "data": {
            "courses": structured_courses,
            "summary": {
                "total_announcements": total_announcements,
                "recent_announcements": recent_announcements,
                "courses_with_announcements": courses_with_announcements,
                "total_courses": len(structured_courses)
            }
        },
        "ui_component": "AnnouncementsList",
        "suggestions": suggestions
    }
    
    return json.dumps(structured_response)


@tool
def get_announcements_for_specific_courses(course_identifier: str) -> str:
    """
    Get announcements for a specific course in structured format for UI rendering.
    
    IMPORTANT: This tool returns structured JSON data with response_type, data, and ui_component fields.
    Return the JSON response exactly as provided without modification.
    
    Args:
        course_identifier: Course code or name (e.g., 'EE 553', 'C++')
        
    Returns:
        str: A structured JSON string containing announcements data for the specified course.
    """
    from datetime import datetime, timezone, timedelta
    
    # Get announcement data from Canvas service for specific course
    announcements_data = _canvas_service.get_announcements_for_course(course_identifier)
    courses_data = announcements_data.get("courses", [])
    
    # Handle case where no course found
    if not courses_data:
        return json.dumps({
            "response_type": "announcements",
            "message": f"No announcements found for course: {course_identifier}",
            "data": {"courses": [], "summary": {"total_announcements": 0, "recent_announcements": 0, "courses_with_announcements": 0, "total_courses": 0}},
            "ui_component": "AnnouncementsList",
            "suggestions": ["Get all my course announcements", "Show me my current courses", "What assignments are due?"]
        })
    
    # Transform to structured format (same logic as get_announcements_for_all_courses)
    structured_courses = []
    total_announcements = 0
    recent_announcements = 0
    courses_with_announcements = 0
    
    current_date = datetime.now(timezone.utc)
    # Set cutoff date to February 1st of current year  
    february_first = datetime(current_date.year, 2, 1, tzinfo=timezone.utc)
    
    for course_data in courses_data:
        course_name = course_data.get("course_name", "")
        announcements_link = course_data.get("course_announcements_link", "")
        announcements = course_data.get("announcements", [])
        
        # Process announcements
        processed_announcements = []
        for announcement in announcements:
            try:
                posted_at = announcement.get("posted_at", "")
                posted_datetime = datetime.fromisoformat(posted_at.replace("Z", "+00:00")) if posted_at else current_date
                
                # Determine if announcement is recent (within past week from current date)
                one_week_ago = current_date - timedelta(days=7)
                is_recent = posted_datetime >= one_week_ago
                
                # Only include announcements from February 1st onwards
                if posted_datetime < february_first:
                    continue
                    
                if is_recent:
                    recent_announcements += 1
                
                # Clean message content (remove HTML tags for preview)
                import re
                message = announcement.get("message", "")
                clean_message = re.sub(r'<[^>]+>', '', message).strip()
                preview = clean_message[:150] + "..." if len(clean_message) > 150 else clean_message
                
                processed_announcement = {
                    "title": announcement.get("title", "Announcement"),
                    "author": announcement.get("author", {}).get("display_name", "Instructor"),
                    "posted_at": posted_at,
                    "posted_datetime": posted_datetime.isoformat(),
                    "posted_date": posted_datetime.strftime("%Y-%m-%d"),
                    "posted_time": posted_datetime.strftime("%H:%M"),
                    "message_preview": preview,
                    "full_message": message,
                    "is_recent": is_recent,
                    "url": announcement.get("url", "")
                }
                
                processed_announcements.append(processed_announcement)
                total_announcements += 1
                
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error processing announcement: {e}")
                continue
        
        if processed_announcements:
            courses_with_announcements += 1
        
        # Sort announcements by posted date (most recent first)
        processed_announcements.sort(key=lambda x: x["posted_datetime"], reverse=True)
        
        # Limit to 3 announcements per course
        processed_announcements = processed_announcements[:3]
        
        structured_course = {
            "course_name": course_name,
            "course_code": course_name.split()[0] if course_name else "",
            "announcements_link": announcements_link,
            "announcements": processed_announcements,
            "announcement_count": len(processed_announcements)
        }
        structured_courses.append(structured_course)
    
    # Create structured response for specific course
    course_name = courses_data[0].get("course_name", course_identifier) if courses_data else course_identifier
    if total_announcements > 0:
        message = f"Here are announcements for {course_name} since February 1st ({total_announcements} total, max 3 shown):"
        suggestions = [
            "Get all my course announcements",
            "Show me recent announcements only", 
            "What assignments are due for this course?"
        ]
    else:
        message = f"No announcements found for {course_name} since February 1st. Here's a direct link to check:"
        suggestions = [
            "Get all my course announcements",
            "Show me my current courses",
            "What's due this week?"
        ]
    
    structured_response = {
        "response_type": "announcements",
        "message": message,
        "data": {
            "courses": structured_courses,
            "summary": {
                "total_announcements": total_announcements,
                "recent_announcements": recent_announcements,
                "courses_with_announcements": courses_with_announcements,
                "total_courses": len(structured_courses)
            }
        },
        "ui_component": "AnnouncementsList",
        "suggestions": suggestions
    }
    
    return json.dumps(structured_response)


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
def navigate_to_workday_registration(mock_mode: bool = False, stay_open: bool = True) -> str:
    """
    Navigate to the course registration page in Workday.
    This will open a browser and prompt you to enter your credentials if not already logged in.
    The browser will remain open by default so you can register for courses.
    
    Args:
        mock_mode: Use mock mode for testing without Playwright installed
        stay_open: Keep the browser open after navigation (default: True)
        
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
            
            # For course registration, we generally want to keep the browser open
            # so users can actually register for courses
            if not stay_open:
                print("[DEBUG] Browser close requested, but keeping open for course registration")
                # await service.close()  # Commented out to keep browser open
            else:
                print("[DEBUG] Keeping browser open for course registration")

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
def navigate_to_workday_financial_account(mock_mode: bool = False, stay_open: bool = True) -> str:
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
            advisors = service.load_advisors_from_cache()
            # First try to get cached advisors
            # advisors = service.get_advisors()
            
            # If no cached advisors, fetch them fresh
            # if not advisors:
            #     print("[DEBUG] No cached advisors, fetching fresh data...")
            #     advisors = await service.get_advisors()
            
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


@tool
def compare_courses(course1: str, course2: str) -> str:
    """
    Compare two courses using the knowledge base to provide detailed information about what you'll learn in each course and recommendations.
    
    IMPORTANT: This tool returns structured JSON data with response_type, data, and ui_component fields.
    Return the JSON response exactly as provided without modification.
    
    Args:
        course1: First course code or name (e.g., "CS 549", "Distributed Systems")
        course2: Second course code or name (e.g., "CS 548", "Enterprise Software")
        
    Returns:
        str: A structured JSON string containing course comparison data for frontend rendering.
    """
    if not _rag_service:
        return json.dumps({
            "response_type": "course_comparison",
            "message": "Course comparison service is currently unavailable.",
            "data": {"courses": [], "recommendations": []},
            "ui_component": "CourseComparison",
            "suggestions": ["Get my assignments instead", "Show me current courses", "Search Stevens knowledge base"]
        })
    
    try:
        # Search for information about both courses with more targeted queries
        search_queries = [
            f"{course1} course description learning objectives topics covered",
            f"{course2} course description learning objectives topics covered", 
            f"{course1} curriculum syllabus what students learn",
            f"{course2} curriculum syllabus what students learn",
            f"{course1} programming projects assignments implementation",
            f"{course2} programming projects assignments implementation",
            f"{course1} technologies tools frameworks used",
            f"{course2} technologies tools frameworks used"
        ]
        
        all_results = []
        for query in search_queries:
            try:
                results = _rag_service.search_similar(query, top_k=2)
                all_results.extend(results)
            except:
                continue
        
        # Process and organize results by course
        course1_info = []
        course2_info = []
        general_info = []
        
        # Extract course codes for better matching
        course1_code = course1.upper().replace(" ", "").replace("-", "")
        course2_code = course2.upper().replace(" ", "").replace("-", "")
        
        for result in all_results:
            content = result["content"].strip()
            content_upper = content.upper()
            
            # Simple matching based on course codes appearing in content
            if course1_code in content_upper or course1.upper() in content_upper:
                course1_info.append({
                    "content": content,
                    "source": result["metadata"].get("source", "Stevens Information"),
                    "relevance": round(1 - result["score"], 3)
                })
            elif course2_code in content_upper or course2.upper() in content_upper:
                course2_info.append({
                    "content": content,
                    "source": result["metadata"].get("source", "Stevens Information"),
                    "relevance": round(1 - result["score"], 3)
                })
            else:
                general_info.append({
                    "content": content,
                    "source": result["metadata"].get("source", "Stevens Information"),
                    "relevance": round(1 - result["score"], 3)
                })
        
        # Sort by relevance and limit results
        course1_info.sort(key=lambda x: x["relevance"], reverse=True)
        course2_info.sort(key=lambda x: x["relevance"], reverse=True)
        general_info.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Structure course information
        structured_courses = []
        
        def extract_learning_objectives(course_name, course_info_list):
            """Extract meaningful learning objectives and key concepts from course content"""
            import re
            
            learning_points = []
            combined_content = ""
            
            # Combine all relevant content for this course
            for info in course_info_list:
                content = info["content"].strip()
                # Basic cleanup
                content = re.sub(r'<[^>]+>', '', content)
                content = re.sub(r'\s+', ' ', content).strip()
                combined_content += " " + content
            
            if not combined_content.strip():
                return []
            
            # Clean combined content
            combined_content = re.sub(r'\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[\w\-+:]*\b', '', combined_content)
            combined_content = re.sub(r'https?://[^\s]+', '', combined_content)
            combined_content = re.sub(r'\b(Posted on|Updated on|Created on|Modified on)[:\s]*[^\n]*', '', combined_content)
            combined_content = re.sub(r'Page \d+ of', '', combined_content)
            combined_content = re.sub(r'Stevens Institute of Technology[^\n]*', '', combined_content)
            combined_content = re.sub(r'\s+', ' ', combined_content).strip()
            
            # Extract key technologies and concepts based on course
            if "549" in course_name or "distributed" in course_name.lower():
                # CS 549 - Distributed Systems focus
                concepts = [
                    "distributed consensus algorithms (Paxos, Raft)",
                    "distributed data storage systems (Cassandra, distributed databases)", 
                    "blockchain and consensus mechanisms",
                    "distributed computing frameworks (Hadoop, MapReduce)",
                    "real-time communication protocols (WebSockets, messaging systems)"
                ]
                learning_points.extend(concepts[:3])
                
            elif "548" in course_name or "enterprise" in course_name.lower():
                # CS 548 - Enterprise Software focus  
                concepts = [
                    "microservices architecture for enterprise applications",
                    "containerization and orchestration (Docker, Kubernetes)",
                    "event-driven architecture and message queues (Kafka)",
                    "domain-driven design (DDD) and CQRS patterns",
                    "enterprise data modeling (ORM, JSON Schema, NoSQL)"
                ]
                learning_points.extend(concepts[:3])
                
            else:
                # General course - try to extract from content
                sentences = re.split(r'[.!?]+', combined_content)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) < 30 or len(sentence) > 200:
                        continue
                        
                    # Look for sentences that describe learning or implementation
                    if any(keyword in sentence.lower() for keyword in ['learn', 'implement', 'develop', 'build', 'design', 'create', 'study', 'understand']):
                        if not any(skip in sentence.lower() for skip in ['http', 'www', 'page', 'catalog', 'stevens institute']):
                            learning_points.append(sentence.strip())
                            
                    if len(learning_points) >= 3:
                        break
            
            # If still no good content, provide fallback
            if not learning_points:
                learning_points = [
                    f"Advanced topics and practical implementation in {course_name}",
                    "Hands-on programming projects and system design",
                    "Real-world applications and case studies"
                ]
            
            return learning_points[:3]  # Limit to 3 points
        
        # Process Course 1
        course1_learning_points = extract_learning_objectives(course1, course1_info)
        structured_courses.append({
            "course_name": course1,
            "course_code": course1_code,
            "learning_points": course1_learning_points,
            "info_sources": [info.get("source", "Stevens Information") for info in course1_info[:2] if info.get("source")]
        })
        
        # Process Course 2
        course2_learning_points = extract_learning_objectives(course2, course2_info)
        structured_courses.append({
            "course_name": course2,
            "course_code": course2_code,
            "learning_points": course2_learning_points,
            "info_sources": [info.get("source", "Stevens Information") for info in course2_info[:2] if info.get("source")]
        })
        
        # Generate intelligent recommendations based on course content
        recommendations = []
        
        # Check if we have CS 549 and CS 548 specifically
        has_549 = any("549" in course.get("course_name", "") for course in structured_courses)
        has_548 = any("548" in course.get("course_name", "") for course in structured_courses)
        
        if has_549 and has_548:
            # Specific recommendations for CS 549 vs CS 548
            recommendations.extend([
                {
                    "title": "For Systems & Infrastructure Focus",
                    "description": f"If you're interested in distributed systems, cloud platforms, and scalable architecture, consider {course1 if '549' in course1 else course2}. Focus on distributed systems theory and core algorithm implementation.",
                    "course_preference": course1 if "549" in course1 else course2
                },
                {
                    "title": "For Enterprise & Application Development",
                    "description": f"If you prefer practical engineering development, architecture design, and enterprise applications, consider {course1 if '548' in course1 else course2}. Emphasizes enterprise-level application development and modern software engineering practices.",
                    "course_preference": course1 if "548" in course1 else course2
                },
                {
                    "title": "For Future Architect & Technical Leadership Roles",
                    "description": "Consider taking both courses. Start with theoretical foundations (distributed systems), then practical engineering (enterprise software) to build a complete technical stack.",
                    "course_preference": "both"
                }
            ])
        elif course1_info or course2_info:
            # General recommendations when we have some course info
            recommendations.extend([
                {
                    "title": "Based on Your Career Goals",
                    "description": f"Choose {course1} if you prefer theoretical foundations and system-level programming. Choose {course2} if you prefer application development and practical engineering.",
                    "course_preference": "evaluate_goals"
                },
                {
                    "title": "Consider Prerequisites and Workload",
                    "description": "Check which course aligns better with your current skills and available time commitment for projects and assignments.",
                    "course_preference": "check_prereqs"  
                }
            ])
        else:
            recommendations.append({
                "title": "Limited Information Available",
                "description": "For more detailed course comparisons, check the official Stevens course catalog or speak with your academic advisor.",
                "course_preference": "consult_advisor"
            })
        
        # Create contextual response message
        if has_549 and has_548:
            message = f"Here's a detailed comparison between {course1} and {course2} based on available course information:"
            suggestions = [
                f"Tell me more about {course1} prerequisites",
                f"Tell me more about {course2} workload", 
                "What other distributed systems courses are available?",
                "Show me my current computer science courses"
            ]
        elif structured_courses and any(course.get("learning_points") for course in structured_courses):
            message = f"Here's a detailed comparison between {course1} and {course2} based on available course information:"
            suggestions = [
                f"What are the prerequisites for {course1}?",
                f"What are the prerequisites for {course2}?",
                "Show me my current courses",
                "Get more information about computer science program requirements"
            ]
        else:
            message = f"I found limited specific information for comparing {course1} and {course2}. Here's a general comparison based on course patterns:"
            suggestions = [
                "Search Stevens knowledge base for more course details",
                "Get my current courses",
                "Show me CS program requirements"
            ]
        
        # Set appropriate comparison title
        if has_549 and has_548:
            comparison_title = f"What will you learn in {course1} vs {course2}? (Specific examples)"
        else:
            comparison_title = f"What will you learn in {course1} vs {course2}?"
        
        structured_response = {
            "response_type": "course_comparison",
            "message": message,
            "data": {
                "courses": structured_courses,
                "recommendations": recommendations,
                "comparison_title": comparison_title,
                "total_sources": len(set([info.get("source", "") for info in (course1_info + course2_info) if info.get("source")]))
            },
            "ui_component": "CourseComparison",
            "suggestions": suggestions
        }
        
        return json.dumps(structured_response)
        
    except Exception as e:
        logger.error(f"Error in course comparison: {e}")
        return json.dumps({
            "response_type": "course_comparison",
            "message": f"Error comparing courses {course1} and {course2}: {str(e)}",
            "data": {"courses": [], "recommendations": []},
            "ui_component": "CourseComparison",
            "suggestions": ["Search Stevens knowledge base", "Get my current courses"]
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
    
    get_academic_calendar_event,
    navigate_to_workday_registration,
    navigate_to_workday_financial_account,
    get_advisors_info,
    shutdown_workday_browser,
    # RAG tools
    search_stevens_knowledge,
    get_stevens_info,
    get_rag_stats,
    compare_courses,
]
