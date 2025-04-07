# app/services/workday_service_async.py

import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from playwright.async_api import async_playwright, BrowserContext, Page

logger = logging.getLogger(__name__)
user_data_dir = str(Path(__file__).parent / "chrome_profile")


class WorkdayService:

    def __init__(self,
                 current_academic_year="",
                 current_academic_semester="",
                 graduate_level=""):
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
        self.password = os.getenv("WORKDAY_PASSWORD")
        self.logged_in = False
        self.advisors = []

    async def start(self):
        playwright = await async_playwright().start()
        self.browser_context = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir, headless=False)
        self.page = self.browser_context.pages[0]

    async def login(self):
        html_content = await self.page.content()
        if "Stevens Institute of Technology - Sign In" in html_content:
            print("Login page detected")
            await self.page.fill("input[name='credentials.passcode']",
                                 self.password)
            await self.page.get_by_role("button", name="Sign in").click()
            await self.page.wait_for_url("**/home.htmld", timeout=60_000)

        landing_page_html = await self.page.content()
        if "window.workday" in landing_page_html:
            self.logged_in = True
            return True
        else:
            return False

    async def navigate_to_workday_registration(self):
        try:
            print("======Navigating to Workday registration page")
            await self.page.goto("https://www.stevens.edu/it/services/workday")
            await self.page.click("text=Log in to Workday")
            await self.page.wait_for_timeout(2000)

            if await self.login():
                await self.page.wait_for_timeout(3000)
                await self.page.click("text=Academics")
                if not self.advisors:
                    self.get_advisors()
                await self.page.wait_for_timeout(2000)
                await self.page.click("text=Find Course Sections")
                await self.page.wait_for_timeout(6000)

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
                await self.page.wait_for_selector(
                    "[data-automation-id='resultsContainer']", timeout=30_000)

                screenshot_path = os.path.join(
                    self.screenshots_dir,
                    f"workday_course_section/selected_calendar_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
                )
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                await self.page.wait_for_timeout(2000)
                await self.page.screenshot(path=screenshot_path)

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

    async def navigate_to_workday_financial_account(self):
        try:
            await self.page.goto("https://www.stevens.edu/it/services/workday")
            await self.page.click("text=Log in to Workday")
            await self.page.wait_for_timeout(2000)

            if await self.login():
                await self.page.click("text=Finances")
                await self.page.wait_for_timeout(5000)
                screenshot_path = os.path.join(
                    self.screenshots_dir,
                    f"workday_financial_account/financial_account_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
                )
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                await self.page.screenshot(path=screenshot_path)

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
        # Wait for the specific section to be visible
        await self.page.wait_for_selector(
            "[aria-label='Important Contacts Support Network'] table",
            timeout=10_000)

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

    async def close(self):
        if self.browser_context:
            await self.browser_context.close()
