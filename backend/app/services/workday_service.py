# app/services/workday_service_async.py

import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from playwright.async_api import async_playwright, BrowserContext, Page
from dotenv import load_dotenv
import asyncio

logger = logging.getLogger(__name__)
user_data_dir = str(Path(__file__).parent / "chrome_profile")

load_dotenv()


class WorkdayService:

    def __init__(self,
                 playwright,
                 current_academic_year="",
                 current_academic_semester="",
                 graduate_level=""):
        self.playwright = playwright
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshots_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..",
                         "navigation_screenshots"))
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.current_academic_year = current_academic_year or "2025-2026 Semester Academic Calendar"
        self.current_academic_semester = current_academic_semester or "2025 Fall Semester(09/02/2025-12/22/2025)"
        self.graduate_level = graduate_level or "Graduate"
        self.username = os.getenv("WORKDAY_USERNAME")
        print(f"WORKDAY_USERNAME: {self.username}")
        self.password = os.getenv("WORKDAY_PASSWORD")
        self.logged_in = False
        self.advisors = []
        self.browser_context = None

    async def start(self):
        print("[DEBUG] WorkdayService.start() called")
        # playwright = await async_playwright().start()
        print("[DEBUG] Playwright started")
        self.browser_context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir, headless=False)
        pages = self.browser_context.pages
        if pages and len(pages) > 0:
            self.page = pages[0]
        else:
            self.page = await self.browser_context.new_page()

        self.page.set_default_timeout(30_000)
        self.page.set_default_navigation_timeout(60_000)
        asyncio.create_task(self._monitor_browser_close())

    async def close(self):
        print("[DEBUG] Closing WorkdayService browser...")
        if self.browser_context:
            await self.browser_context.close()
            self.browser_context = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None  # Optional

    async def _monitor_browser_close(self):
        print("[DEBUG] Starting browser close watcher")
        while True:
            await asyncio.sleep(2)
            if self.page and self.page.is_closed():
                print("[DEBUG] Page was closed manually")
                try:
                    await self.close()
                except Exception as e:
                    print(f"[DEBUG] Browser was already closed: {e}")
                break

    async def login(self):
        print("======Login called")
        print(self.page.url)
        html_content = await self.page.content()
        if "Stevens Institute of Technology - Sign In" in html_content:
            print("Login page detected")
            if not self.password:
                raise ValueError(
                    "WORKDAY_PASSWORD environment variable is not set")

            await self.page.locator("input[name='credentials.passcode']").fill(
                self.password)
            await self.page.get_by_role("button", name="Sign in").click()
            await self.page.wait_for_url("**/home.htmld", timeout=60_000)

        # Check multiple indicators that we're successfully logged into Workday
        current_url = self.page.url
        landing_page_html = await self.page.content()
        
        # Method 1: Check URL pattern (most reliable)
        if "myworkday.com" in current_url and "home.htmld" in current_url:
            print("[DEBUG] Login detected via URL pattern")
            self.logged_in = True
            return True
            
        # Method 2: Check for Workday dashboard elements
        if "Hi There" in landing_page_html or "Awaiting Your Action" in landing_page_html:
            print("[DEBUG] Login detected via dashboard content")
            self.logged_in = True
            return True
            
        # Method 3: Fallback to original check
        if "window.workday" in landing_page_html:
            print("[DEBUG] Login detected via window.workday")
            self.logged_in = True
            return True
            
        print(f"[DEBUG] Login detection failed. Current URL: {current_url}")
        print(f"[DEBUG] Page title: {await self.page.title()}")
        return False

    async def navigate_to_workday_registration(self, stay_open: bool = True):
        try:
            print("======Navigating to Workday registration page")
            await self._navigate_with_retry("https://www.stevens.edu/it/services/workday")
            
            # Wait for popup window to open after clicking "Log in to Workday"
            async with self.browser_context.expect_page() as page_info:
                await self.page.click("text=Log in to Workday")
            
            # Switch to the popup window
            popup_page = await page_info.value
            await popup_page.wait_for_load_state('networkidle')
            
            print(f"[DEBUG] Original window URL: {self.page.url}")
            print(f"[DEBUG] Popup window URL: {popup_page.url}")
            
            # Update our page reference to the popup
            self.page = popup_page
            await self.page.wait_for_timeout(2000)

            if await self.login():
                await self.page.wait_for_timeout(3000)
                await self.page.click("text=Academics", timeout=10_000)
                if not self.advisors:
                    self.advisors = await self.get_advisors_in_workday()
                await self.page.click("text=Find Course Sections",
                                      timeout=10_000)

                # Select calendar start date
                start_date_input = self.page.locator(
                    "[data-uxi-element-id='selectinput-15$456818']")
                await start_date_input.wait_for(state="visible")
                await start_date_input.scroll_into_view_if_needed()
                await start_date_input.click()
                await self.page.wait_for_timeout(500)
                await self.page.locator(
                    "[data-automation-label='Semester Academic Calendar']"
                ).click()
                await self.scroll_until_visible(self.current_academic_year)

                semester = self.page.locator(
                    f"[data-automation-label='{self.current_academic_semester}']"
                )
                await semester.scroll_into_view_if_needed()
                await semester.wait_for(state="visible")
                await semester.click()

                # Academic level
                level_input = self.page.locator(
                    "[data-uxi-element-id='selectinput-15$463917']")
                await level_input.type(self.graduate_level, delay=100)
                await self.page.keyboard.press("Enter")
                await self.page.wait_for_timeout(2000)
                grad_option = self.page.locator(
                    f"[data-automation-label='{self.graduate_level}']")
                await grad_option.scroll_into_view_if_needed()
                await grad_option.wait_for(state="visible", timeout=5000)
                await grad_option.click()

                # Submit
                ok_button = self.page.locator(
                    "[data-automation-id='wd-CommandButton_uic_okButton']")
                async with self.page.expect_navigation(wait_until='load',
                                                       timeout=10000):
                    await ok_button.click()
                await self.page.wait_for_load_state("networkidle")
                try:
                    await self.page.get_by_text(
                        "Find Course Sections",
                        exact=True).wait_for(timeout=10000)
                except Exception as e:
                    print(
                        f"[DEBUG] Error waiting for 'Find Course Sections' button: {e}"
                    )

                screenshot_path = os.path.join(
                    self.screenshots_dir,
                    f"workday_course_section/selected_calendar_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
                )
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                await self.page.wait_for_timeout(2000)
                await self.page.screenshot(path=screenshot_path)

                if not stay_open:
                    print("[DEBUG] Delaying close for 10 sec (demo mode)")
                    await asyncio.sleep(10)  # Delay for demo purposes
                    await self.close()
                else:
                    print("[DEBUG] Leaving browser open (stay_open=True)")

                return {
                    "success": True,
                    "message":
                    "Navigated to Workday Course Registration successfully.",
                    "screenshot": screenshot_path
                }
            else:
                return {
                    "success":
                    False,
                    "error":
                    "Login failed - could not reach Workday registration page",
                }

        except Exception as e:
            logger.error(f"[navigate_to_workday_registration] Error: {str(e)}")
            return {"success": False, "error": str(e), "html": None}

    async def navigate_to_workday_financial_account(self, stay_open: bool = True):
        try:
            await self._navigate_with_retry("https://www.stevens.edu/it/services/workday")
            
            # Wait for popup window to open after clicking "Log in to Workday"
            async with self.browser_context.expect_page() as page_info:
                await self.page.click("text=Log in to Workday")
            
            # Switch to the popup window
            popup_page = await page_info.value
            await popup_page.wait_for_load_state('networkidle')
            
            print(f"[DEBUG] Original window URL: {self.page.url}")
            print(f"[DEBUG] Popup window URL: {popup_page.url}")
            
            # Update our page reference to the popup
            self.page = popup_page
            await self.page.wait_for_timeout(2000)
            
            if await self.login():
                # await self.page.click("text=Finances")
                # await self.page.wait_for_timeout(5000)
                finances_button = self.page.locator(
                    "button[aria-label='Finances']")
                await finances_button.scroll_into_view_if_needed()
                await finances_button.wait_for(state="visible")
                await finances_button.click()
                screenshot_path = os.path.join(
                    self.screenshots_dir,
                    f"workday_financial_account/financial_account_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
                )
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                await self.page.screenshot(path=screenshot_path)
                if not stay_open:
                    print("[DEBUG] Delaying close for 5 sec (demo mode)")
                    await asyncio.sleep(5)  # Delay for demo purposes
                    await self.close()
                else:
                    print("[DEBUG] Leaving browser open (stay_open=True)")

                return {
                    "success": True,
                    "message":
                    "Navigated to financial account section successfully.",
                    "screenshot": screenshot_path
                }
            else:
                return {
                    "success": False,
                    "error":
                    "Login failed - could not reach Workday finance page",
                    "html": None
                }

        except Exception as e:
            logger.error(
                f"[navigate_to_workday_financial_account] Error: {str(e)}")
            return {"success": False, "error": str(e), "html": None}

    async def scroll_until_visible(self,
                                   label: str,
                                   max_scrolls: int = 30,
                                   delay: int = 300):
        for _ in range(max_scrolls):
            el = self.page.locator(f"[data-automation-label='{label}']")
            if await el.count() > 0:
                await el.scroll_into_view_if_needed()
                await el.wait_for(state="visible", timeout=3000)
                await el.click()
                return True
            else:
                last_visible = self.page.locator(
                    "[data-automation-id='promptOption']").last
                await last_visible.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(delay)
        raise Exception(
            f"Could not find label '{label}' after {max_scrolls} scrolls")

    async def get_advisors(self):
        try:
            print("======Navigating to Workday registration page")
            await self._navigate_with_retry("https://www.stevens.edu/it/services/workday")
            
            # Wait for popup window to open after clicking "Log in to Workday"
            async with self.browser_context.expect_page() as page_info:
                await self.page.click("text=Log in to Workday")
            
            # Switch to the popup window
            popup_page = await page_info.value
            await popup_page.wait_for_load_state('networkidle')
            
            print(f"[DEBUG] Original window URL: {self.page.url}")
            print(f"[DEBUG] Popup window URL: {popup_page.url}")
            
            # Update our page reference to the popup
            self.page = popup_page
            await self.page.wait_for_timeout(2000)

            if await self.login():
                await self.page.wait_for_timeout(3000)
                await self.page.click("text=Academics", timeout=10_000)
                if not self.advisors:
                # Wait for the specific section to be visible
                    await self.page.wait_for_selector(
                        "[aria-label='Important Contacts Support Network'] table",
                        timeout=20_000)

                    advisors = await self.page.evaluate("""
                        () => {
                            const section = document.querySelector("[aria-label='Important Contacts Support Network']");
                            if (!section) return [];

                            const rows = section.querySelectorAll("table[data-automation-id='table'] tbody tr");

                            const advisors = Array.from(rows)
                                .map(row => {
                                    const cells = row.querySelectorAll("td");
                                    return {
                                        role: cells[0]?.innerText.trim(),
                                        cohort: cells[1]?.innerText.trim(),
                                        person: cells[3]?.innerText.trim(),
                                        email: cells[4]?.innerText.trim()
                                    };
                                })
                                .filter(row => row.role?.includes("Advisor"));

                            return advisors;
                        }
                    """)

            print("Advisor info:", advisors)
            self.advisors = advisors
            return self.advisors
        except Exception as e:
            logger.error(f"[get_advisors] Error: {str(e)}")
            return []
        
    async def get_advisors_in_workday(self):
        await self.page.wait_for_selector(
                    "[aria-label='Important Contacts Support Network'] table",
                    timeout=20_000)

        advisors = await self.page.evaluate("""
            () => {
                const section = document.querySelector("[aria-label='Important Contacts Support Network']");
                if (!section) return [];

                const rows = section.querySelectorAll("table[data-automation-id='table'] tbody tr");

                const advisors = Array.from(rows)
                    .map(row => {
                        const cells = row.querySelectorAll("td");
                        return {
                            role: cells[0]?.innerText.trim(),
                            cohort: cells[1]?.innerText.trim(),
                            person: cells[3]?.innerText.trim(),
                            email: cells[4]?.innerText.trim()
                        };
                    })
                    .filter(row => row.role?.includes("Advisor"));

                return advisors;
            }
        """)
        print("Advisor info:", advisors)
        self.advisors = advisors
        return self.advisors
    
    async def get_advisors_list(self):
        # if not self.advisors:
        #     await self.get_advisors()
        return self.advisors

    async def _ensure_browser_ready(self):
        """Ensure browser context and page are ready for navigation"""
        try:
            # Check if browser context is still valid
            if not self.browser_context or self.browser_context.pages is None:
                print("[DEBUG] Browser context is invalid, restarting...")
                await self._restart_browser()
                return True
                
            # Check if page is still valid
            if not self.page or self.page.is_closed():
                print("[DEBUG] Page is closed, creating new page...")
                self.page = await self.browser_context.new_page()
                self.page.set_default_timeout(30_000)
                self.page.set_default_navigation_timeout(60_000)
                return True
                
            # Test if page is responsive
            try:
                await self.page.evaluate("() => window.location.href", timeout=5000)
                print("[DEBUG] Browser is healthy and ready")
                return True
            except Exception as e:
                print(f"[DEBUG] Page unresponsive: {e}, restarting browser...")
                await self._restart_browser()
                return True
                
        except Exception as e:
            print(f"[ERROR] Browser health check failed: {e}")
            await self._restart_browser()
            return True

    async def _restart_browser(self):
        """Restart the browser context from scratch"""
        try:
            # Close existing browser if it exists
            if self.browser_context:
                try:
                    await self.browser_context.close()
                except:
                    pass
            
            # Ensure we have a valid playwright instance
            if not self.playwright:
                print("[DEBUG] Playwright instance is None, recreating...")
                from playwright.async_api import async_playwright
                self.playwright = await async_playwright().start()
                    
            # Restart browser context
            print("[DEBUG] Restarting browser context...")
            self.browser_context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir, headless=False)
            
            # Create new page
            pages = self.browser_context.pages
            if pages and len(pages) > 0:
                self.page = pages[0]
            else:
                self.page = await self.browser_context.new_page()

            self.page.set_default_timeout(30_000)
            self.page.set_default_navigation_timeout(60_000)
            
            # Reset login state
            self.logged_in = False
            
            print("[DEBUG] Browser restarted successfully")
            
        except Exception as e:
            print(f"[ERROR] Failed to restart browser: {e}")
            raise

    async def _navigate_with_retry(self, url: str, max_retries: int = 3):
        """Navigate to URL with retry logic"""
        for attempt in range(max_retries):
            try:
                await self._ensure_browser_ready()
                await self.page.goto(url, wait_until='networkidle', timeout=30000)
                print(f"[DEBUG] Successfully navigated to {url}")
                return True
            except Exception as e:
                print(f"[DEBUG] Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"[DEBUG] Retrying navigation...")
                    await asyncio.sleep(2)
                else:
                    print(f"[ERROR] All navigation attempts failed")
                    raise
        return False


# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         from playwright.async_api import async_playwright

#         async with async_playwright() as playwright:
#             service = WorkdayService(playwright)
#             await service.start()

#             # Choose what to test:
#             result = await service.navigate_to_workday_registration()
#             # result = await service.navigate_to_workday_financial_account()

#             print("Result:", result)

#             await service.close()

#     asyncio.run(main())
