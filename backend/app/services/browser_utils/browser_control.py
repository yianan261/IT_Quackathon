import sys
import os
import logging
import subprocess
from typing import Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Try to import Playwright with better error handling
PLAYWRIGHT_AVAILABLE = False
BROWSER_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True

    # Check if browsers are installed by actually trying to launch
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        BROWSER_AVAILABLE = True
        logger.info("Playwright and browser binaries are available")
    except Exception as e:
        logger.warning(
            f"Playwright is installed but browser binaries may be missing: {str(e)}"
        )
        logger.warning("You may need to run: playwright install")

except ImportError:
    logger.error("Playwright not found. Please install it using:")
    logger.error("    pip install playwright")
    logger.error("    playwright install")
    logger.error("Or if using conda:")
    logger.error("    conda config --add channels conda-forge")
    logger.error("    conda config --add channels microsoft")
    logger.error("    conda install playwright")
    logger.error("    playwright install")


class BrowserControl:
    """
    Low-level browser automation wrapper for Playwright.
    Provides methods for common browser operations like navigation,
    clicking elements, and extracting HTML content.
    """

    def __init__(self, headless=True, slow_mo=500, debug_wait=2000):
        """
        Initialize a browser controller with Playwright.
        
        Args:
            headless (bool): Whether to run browser in headless mode
            slow_mo (int): Slow down operations by this amount of milliseconds
            debug_wait (int): Additional wait time in milliseconds for debugging
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed or not available")

        logger.info(f"Initializing browser controller (headless={headless})")

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless,
                                                           slow_mo=slow_mo)
            self.page = self.browser.new_page()
            self.page.set_viewport_size({"width": 1280, "height": 800})
            self.debug_wait = debug_wait
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            logger.error("You may need to run: playwright install")
            raise

        # Create directory for HTML dumps if it doesn't exist
        os.makedirs("browser_dumps", exist_ok=True)

    def goto(self, url: str):
        """Navigate to a URL and wait for page to load."""
        logger.info(f"Navigating to {url}")
        self.page.goto(url)
        self.page.wait_for_load_state("load")
        # Add debug wait
        self.page.wait_for_timeout(self.debug_wait)

    def get_html(self) -> str:
        """Get the HTML content of the current page."""
        return self.page.content()

    def save_html(self, step_name: str) -> str:
        """
        Save the current HTML to a file and return the filename.
        
        Args:
            step_name (str): Name to identify this step in the filename
            
        Returns:
            str: Path to the saved HTML file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"browser_dumps/{step_name}_{timestamp}.html"

        html_content = self.get_html()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Saved HTML to {filename}")
        return filename

    def click_text(self, text: str, exact=False, timeout=30000, retry_count=2):
        """
        Click an element containing the specified text, with automatic waiting and retries.
        
        Args:
            text (str): The text to find and click
            exact (bool): Whether to match the exact text or partial text
            timeout (int): Timeout in milliseconds to wait for the element
            retry_count (int): Number of retries if the element is not found
        """
        selector = f"text=\"{text}\"" if exact else f"text={text}"
        logger.info(f"Attempting to click element with {selector}")

        for attempt in range(retry_count + 1):
            try:
                # Wait for the element to be visible before clicking
                self.page.wait_for_selector(selector,
                                            timeout=timeout,
                                            state='visible')
                # Add debug wait before clicking
                self.page.wait_for_timeout(self.debug_wait)
                self.page.click(selector)
                logger.info(f"Successfully clicked element with {selector}")
                # Add debug wait after clicking
                self.page.wait_for_timeout(self.debug_wait)
                return
            except Exception as e:
                if attempt < retry_count:
                    logger.warning(
                        f"Retry {attempt+1}/{retry_count} clicking '{text}': {str(e)}"
                    )
                    # Wait a moment before retrying
                    self.page.wait_for_timeout(1000)
                else:
                    logger.error(
                        f"Failed to click '{text}' after {retry_count+1} attempts: {str(e)}"
                    )
                    raise

    def fill_input(self, selector: str, value: str):
        """Fill an input field with the specified value."""
        logger.info(
            f"Filling input {selector} with value (hidden for privacy)")
        self.page.fill(selector, value)
        # Add debug wait after filling
        self.page.wait_for_timeout(self.debug_wait)

    def wait_for_selector(self, selector: str, timeout=30000):
        """Wait for an element matching the selector to appear."""
        logger.info(f"Waiting for selector: {selector}")
        self.page.wait_for_selector(selector, timeout=timeout)

    def wait_for_navigation(self):
        """Wait for navigation to complete."""
        logger.info("Waiting for navigation to complete")
        self.page.wait_for_load_state("networkidle")
        # Add debug wait after navigation
        self.page.wait_for_timeout(self.debug_wait)

    def screenshot(self, path: str, full_page: bool = True):
        """
        Take a screenshot of the current page.
        
        Args:
            path (str): Path where the screenshot will be saved
            full_page (bool): Whether to capture the full scrollable page (True) or just the viewport (False)
        
        Returns:
            str: Path to the saved screenshot
        """
        logger.info(
            f"Taking {'full page' if full_page else 'viewport'} screenshot: {path}"
        )

        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path))
                    if os.path.dirname(path) else ".",
                    exist_ok=True)

        self.page.screenshot(path=path, full_page=full_page)
        return path

    def close(self):
        """Close the browser and stop Playwright."""
        logger.info("Closing browser")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
