import logging
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

load_dotenv()

logger = logging.getLogger(__name__)
user_data_dir = str(Path(__file__).parent / "chrome_profile")


class WorkdayService:

    def __init__(self,
                 playwright,
                 current_academic_year="",
                 current_academic_semester="",
                 graduate_level=""):
        self.browser = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir, headless=False)
        self.page = self.browser.pages[0]
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

    def scroll_until_visible(self,
                             label: str,
                             max_scrolls: int = 30,
                             delay: int = 300):
        for _ in range(max_scrolls):
            el = self.page.locator(f"[data-automation-label='{label}']")
            if el.count() > 0:
                el.scroll_into_view_if_needed()
                el.wait_for(state="visible", timeout=3000)
                el.click()
                print("True")
                return True
            else:
                # Scroll the last loaded option to load more
                last_visible = self.page.locator(
                    "[data-automation-id='promptOption']").last
                last_visible.scroll_into_view_if_needed()
                self.page.wait_for_timeout(delay)
        raise Exception(
            f"Could not find label '{label}' after {max_scrolls} scrolls")

    def login(self):
        html_content = self.page.content()

        if "Stevens Institute of Technology - Sign In" in html_content:
            print("Login page detected")
            self.page.locator("input[name='credentials.passcode']").fill(
                self.password)
            self.page.get_by_role("button", name="Sign in").click()

            self.page.wait_for_url("**/home.htmld", timeout=60_000)

        landing_page_html = self.page.content()
        if "https://wd5.myworkday.com/stevens/d/home.htmld" in landing_page_html or "window.workday" in landing_page_html:
            self.logged_in = True
            return True
        else:
            return False

    def navigate_to_workday_registration(self):
        try:
            self.page.goto("https://www.stevens.edu/it/services/workday")
            self.page.click("text=Log in to Workday")
            self.page.wait_for_timeout(2000)

            time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            if self.login():
                logger.info("Already logged in or login successful")
                self.page.wait_for_timeout(3000)

                # self.page.pause()

                self.page.wait_for_selector("text=Academics", timeout=3000)
                self.page.click("text=Academics")
                if not self.advisors:
                    self.get_advisors()
                self.page.wait_for_selector("text=Find Course Sections",
                                            timeout=3000)
                self.page.click("text=Find Course Sections")

                self.page.wait_for_timeout(6000)

                print(
                    "Clicking Start Date within field via stable selector...")
                start_date_input = self.page.locator(
                    "[data-uxi-element-id='selectinput-15$456818']")
                start_date_input.wait_for(state="visible")
                start_date_input.scroll_into_view_if_needed()
                start_date_input.click()

                self.page.wait_for_timeout(500)

                # Select "Semester Academic Calendar"
                self.page.locator(
                    "[data-automation-label='Semester Academic Calendar']"
                ).click()

                # select academic year
                self.scroll_until_visible(self.current_academic_year)

                semester = self.page.locator(
                    f"[data-automation-label='{self.current_academic_semester}']"
                )
                semester.scroll_into_view_if_needed()
                semester.wait_for(state="visible")
                semester.click()

                # academic level input
                level_input = self.page.locator(
                    "[data-uxi-element-id='selectinput-15$463917']")
                level_input.type(self.graduate_level, delay=100)
                self.page.keyboard.press("Enter")
                self.page.wait_for_timeout(2000)

                grad_option = self.page.locator(
                    f"[data-automation-label='{self.graduate_level}']")
                grad_option.scroll_into_view_if_needed()
                grad_option.wait_for(state="visible", timeout=5000)
                grad_option.click()

                # Submit the form
                ok_button = self.page.locator(
                    "[data-automation-id='wd-CommandButton_uic_okButton']")
                with self.page.expect_navigation(wait_until='load',
                                                 timeout=10000):
                    ok_button.click()
                self.page.wait_for_load_state("networkidle")

                self.page.wait_for_selector(
                    "[data-automation-id='resultsContainer']", timeout=30_000)

                self.page.wait_for_timeout(3000)

                # Final screenshot
                course_reg_screenshot_path = os.path.join(
                    self.screenshots_dir,
                    f"workday_course_section/selected_calendar_{time}.png")
                os.makedirs(os.path.dirname(course_reg_screenshot_path),
                            exist_ok=True)
                self.page.wait_for_timeout(2000)
                self.page.screenshot(path=course_reg_screenshot_path)

                input("Press Enter to exit and close the browser...")

                return {
                    "success": True,
                    "message":
                    "Navigated to Workday Course Registration successfully.",
                    "screenshot": course_reg_screenshot_path
                }
            else:
                logger.error("Login failed - Welcome page not detected")
                return {
                    "success": False,
                    "error":
                    "Login failed - could not reach Workday registration page",
                    "html": None
                }

        except Exception as e:
            logger.error(
                f"Error during navigation to Workday registration: {str(e)}")
            return {"success": False, "error": str(e), "html": None}

    def navigate_to_workday_financial_account(self):
        try:
            self.page.goto("https://www.stevens.edu/it/services/workday")
            self.page.click("text=Log in to Workday")
            self.page.wait_for_timeout(2000)
            if self.login():
                logger.info("Already logged in or login successful")
                self.page.wait_for_timeout(3000)
                self.page.click("text=Finances")
                self.page.wait_for_timeout(5000)
                screenshot_path = os.path.join(
                    self.screenshots_dir,
                    f"workday_financial_account/financial_account_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
                )

                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                self.page.screenshot(path=screenshot_path)

                return {
                    "success": True,
                    "message":
                    "Navigated to financial account section successfully.",
                    "screenshot": screenshot_path
                }
            else:
                logger.error("Login failed - Welcome page not detected")
                return {
                    "success": False,
                    "error":
                    "Login failed - could not reach Workday finance page",
                    "html": None
                }

        except Exception as e:
            logger.error(
                f"Error during navigation to Workday financial account: {str(e)}"
            )
            return {"success": False, "error": str(e), "html": None}

    def get_advisors(self):
        # Wait for the specific section to be visible
        self.page.wait_for_selector(
            "[aria-label='Important Contacts Support Network'] table",
            timeout=10_000)

        advisors = self.page.evaluate("""
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

    def close(self):
        self.browser.close()
