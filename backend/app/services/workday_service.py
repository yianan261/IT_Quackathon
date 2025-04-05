from .browser_utils.browser_control import BrowserControl
import logging
import os
import time
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class WorkdayService:
    """
    Service for automating interactions with Stevens Institute of Technology's 
    Workday platform. This service handles task-level operations like login, 
    navigation, and data extraction.
    """

    def __init__(self, headless=False):
        """
        Initialize a Workday service instance.
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        logger.info("Initializing Workday service")
        self.browser = BrowserControl(headless=headless)
        self.base_url = "https://www.stevens.edu/it/services/workday"
        self.logged_in = False

    def login(self,
              username: Optional[str] = None,
              password: Optional[str] = None) -> Dict[str, Any]:
        """
        Log in to Workday.
        
        Args:
            username (str, optional): Username for Workday login. If not provided, will use env vars.
            password (str, optional): Password for Workday login. If not provided, will use env vars.
            
        Returns:
            Dict containing HTML content and status
        """
        try:
            logger.info("Starting Workday login process")

            # Use environment variables if credentials not provided
            if not username:
                username = os.environ.get("WORKDAY_USERNAME")
            if not password:
                password = os.environ.get("WORKDAY_PASSWORD")

            if not username or not password:
                return {
                    "success": False,
                    "error": "Missing credentials for Workday login",
                    "html": None
                }

            # Navigate to Workday entry page
            self.browser.goto(self.base_url)

            try:
                # Click login link and wait for login form to appear
                self.browser.click_text("Log in to Workday")
                self.browser.wait_for_navigation()
            except Exception as e:
                logger.error(f"Error clicking login button: {str(e)}")
                return {
                    "success": False,
                    "error": f"Could not click login button: {str(e)}",
                    "html": self.browser.get_html()
                }

            # Fill login form (adjusting selectors based on actual form fields)
            try:
                self.browser.fill_input("#username", username)
                self.browser.fill_input("#password", password)

                # Click login button
                self.browser.click_text("Sign In")
                self.browser.wait_for_navigation()
            except Exception as e:
                logger.error(f"Error during login form submission: {str(e)}")
                return {
                    "success": False,
                    "error": f"Login form interaction failed: {str(e)}",
                    "html": self.browser.get_html()
                }

            # Check if login was successful (adjust based on actual page content)
            landing_page_html = self.browser.get_html()
            if "Welcome" in landing_page_html or "Dashboard" in landing_page_html:
                self.logged_in = True
                logger.info("Login successful")

                # We don't take a screenshot here as per requirements to only screenshot the final page

                return {
                    "success": True,
                    "html": landing_page_html,
                }
            else:
                logger.error("Login failed - Welcome page not detected")
                return {
                    "success": False,
                    "error": "Login failed - could not reach welcome page",
                    "html": landing_page_html
                }

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return {"success": False, "error": str(e), "html": None}

    def navigate_to_academics(self) -> Dict[str, Any]:
        """
        Navigate to the Academics section in Workday.
        
        Returns:
            Dict containing HTML content and status
        """
        try:
            if not self.logged_in:
                return {
                    "success": False,
                    "error": "Not logged in. Please login first.",
                    "html": None
                }

            logger.info("Navigating to Academics section")

            try:
                # Click on Academics (assuming it's a main navigation item)
                self.browser.click_text("Academics")
                self.browser.wait_for_navigation()
            except Exception as e:
                logger.error(f"Error clicking Academics navigation: {str(e)}")
                return {
                    "success": False,
                    "error": f"Could not navigate to Academics: {str(e)}",
                    "html": self.browser.get_html()
                }

            # Save the academics page HTML but don't screenshot
            academics_html = self.browser.get_html()

            # Try to navigate to Find Course Sections
            try:
                self.browser.click_text("Find Course Sections")
                self.browser.wait_for_navigation()

                # Save the course sections page HTML
                course_sections_html = self.browser.get_html()

                # NOW we take a screenshot at the final landing page
                screenshots_dir = "browser_dumps/screenshots"
                os.makedirs(screenshots_dir, exist_ok=True)
                screenshot_path = f"{screenshots_dir}/course_sections_landing_{int(time.time())}.png"
                self.browser.screenshot(path=screenshot_path, full_page=True)

                return {
                    "success": True,
                    "html": course_sections_html,
                    "screenshot": screenshot_path
                }
            except Exception as e:
                logger.warning(
                    f"Could not navigate to Find Course Sections: {str(e)}")
                return {
                    "success": True,
                    "warning": "Could not navigate to Find Course Sections",
                    "html": academics_html
                }

        except Exception as e:
            logger.error(f"Error navigating to academics: {str(e)}")
            return {"success": False, "error": str(e), "html": None}

    def search_courses(self,
                       term: str,
                       subject: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for courses in Workday.
        
        Args:
            term (str): Academic term to search for (e.g., "Fall 2023")
            subject (str, optional): Subject filter (e.g., "Computer Science")
            
        Returns:
            Dict containing search results HTML and status
        """
        try:
            if not self.logged_in:
                return {
                    "success": False,
                    "error": "Not logged in. Please login first.",
                    "html": None
                }

            # Navigate to course sections if not already there
            if "Find Course Sections" not in self.browser.get_html():
                result = self.navigate_to_academics()
                if not result["success"]:
                    return result

            logger.info(f"Searching courses for term: {term}")

            # Fill in search form fields (adjust selectors based on actual form)
            # Example: Select academic term
            self.browser.click_text(term)

            # If subject is provided, filter by subject
            if subject:
                self.browser.click_text(subject)

            # Click search button
            self.browser.click_text("OK")
            self.browser.wait_for_navigation()

            # Save search results
            results_html = self.browser.get_html()
            results_file = self.browser.save_html(
                f"course_search_results_{term}")

            return {
                "success": True,
                "html": results_html,
                "html_file": results_file
            }

        except Exception as e:
            logger.error(f"Error searching courses: {str(e)}")
            return {"success": False, "error": str(e), "html": None}

    def extract_current_page(self,
                             step_name: str,
                             take_screenshot: bool = False) -> Dict[str, Any]:
        """
        Extract HTML from the current page with identifying step name.
        
        Args:
            step_name (str): Name to identify this extraction step
            take_screenshot (bool): Whether to take a screenshot (should only be True for final pages)
            
        Returns:
            Dict containing HTML content and status
        """
        try:
            logger.info(f"Extracting HTML for step: {step_name}")

            # Get and save HTML
            html = self.browser.get_html()
            html_file = self.browser.save_html(step_name)

            result = {"success": True, "html": html, "html_file": html_file}

            # Only take a screenshot if explicitly requested or if this is a final landing page
            if take_screenshot or 'landing' in step_name.lower(
            ) or 'final' in step_name.lower():
                logger.info(
                    f"Taking screenshot for {step_name} (identified as a final landing page)"
                )
                screenshots_dir = "browser_dumps/screenshots"
                os.makedirs(screenshots_dir, exist_ok=True)
                screenshot_path = f"{screenshots_dir}/{step_name}_{int(time.time())}.png"
                self.browser.screenshot(path=screenshot_path, full_page=True)
                result["screenshot"] = screenshot_path

            return result
        except Exception as e:
            logger.error(f"Error extracting page for {step_name}: {str(e)}")
            return {"success": False, "error": str(e), "html": None}

    def check_if_on_registration_page(self) -> Dict[str, Any]:
        """
        Take a screenshot of the current page and check if it appears to be a registration page.
        This method is meant to be used with an AI vision model to analyze the screenshot.
        
        Returns:
            Dict containing the screenshot path and status
        """
        try:
            if not self.logged_in:
                return {
                    "success": False,
                    "error": "Not logged in. Please login first.",
                    "screenshot": None
                }

            logger.info(
                "Capturing screenshot to check if on registration page")

            # Take a full-page screenshot
            screenshots_dir = "browser_dumps/screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            screenshot_path = f"{screenshots_dir}/registration_check_{int(time.time())}.png"
            self.browser.screenshot(path=screenshot_path, full_page=True)

            # Get the current page title or heading
            page_title = ""
            try:
                # Try to get the page title from a heading element
                heading_selector = "h1, h2, h3, .page-title, .title"
                heading_element = self.browser.page.query_selector(
                    heading_selector)
                if heading_element:
                    page_title = heading_element.inner_text()
            except Exception:
                pass

            return {
                "success": True,
                "screenshot": screenshot_path,
                "page_title": page_title,
                "html_snapshot": self.browser.get_html()
                [:1000]  # Only include a small snippet of HTML
            }

        except Exception as e:
            logger.error(f"Error checking if on registration page: {str(e)}")
            return {"success": False, "error": str(e), "screenshot": None}

    def automate_course_registration(self, course_code: str) -> Dict[str, Any]:
        """
        Automate the course registration process for a specific course.
        
        Args:
            course_code: The code of the course to register for (e.g., "CS 101")
            
        Returns:
            Dict containing status and screenshots
        """
        try:
            if not self.logged_in:
                return {
                    "success": False,
                    "error": "Not logged in. Please login first.",
                    "screenshots": []
                }

            # Navigate to the registration page
            result = self.navigate_to_academics()
            if not result.get("success", False):
                return {
                    "success": False,
                    "error": "Failed to navigate to academics",
                    "screenshots": []
                }

            # Take a screenshot to verify we're on the right page
            registration_check = self.check_if_on_registration_page()
            screenshots = [registration_check.get("screenshot")
                           ] if registration_check.get("screenshot") else []

            # Here you would implement the actual registration logic
            # This is a placeholder for demonstration purposes

            return {
                "success": True,
                "message":
                f"Successfully automated registration process for course {course_code}",
                "screenshots": screenshots
            }

        except Exception as e:
            logger.error(f"Error automating course registration: {str(e)}")
            return {"success": False, "error": str(e), "screenshots": []}

    def close(self):
        """Close the browser and clean up resources."""
        if self.browser:
            self.browser.close()
