"""
Direct browser test that bypasses most of the application.
This script directly uses the Workday service to test browser visibility.
"""

import os
import time
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_direct_browser():
    """Test opening a browser window directly."""
    try:
        print("=" * 80)
        print("BROWSER VISIBILITY TEST")
        print("=" * 80)

        # First, check the environment variables
        username = os.environ.get("WORKDAY_USERNAME")
        password = os.environ.get("WORKDAY_PASSWORD")

        print(f"Found WORKDAY_USERNAME: {'YES' if username else 'NO'}")
        print(f"Found WORKDAY_PASSWORD: {'YES' if password else 'NO'}")

        if not username or not password:
            print("\nPlease set your credentials before continuing.")
            print("For example:")
            print("export WORKDAY_USERNAME=your_username")
            print("export WORKDAY_PASSWORD=your_password")
            return

        # Try to import and check Playwright directly
        try:
            print("\nChecking for Playwright...")
            from playwright.sync_api import sync_playwright
            print("✅ Playwright is installed")

            # Try to launch a browser
            print("\nAttempting to launch a browser...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, slow_mo=1000)
                page = browser.new_page()
                page.goto("https://example.com")

                print(
                    "✅ Browser successfully launched and navigated to example.com"
                )
                print(
                    "   You should see a Chrome window open with the example.com website"
                )
                print("   Waiting 5 seconds before continuing...")
                time.sleep(5)

                # Take a screenshot for verification
                os.makedirs("browser_dumps", exist_ok=True)
                screenshot_path = "browser_dumps/test_screenshot.png"
                page.screenshot(path=screenshot_path)
                print(
                    f"✅ Screenshot saved to {os.path.abspath(screenshot_path)}"
                )

                browser.close()
                print("✅ Browser closed successfully")

        except ImportError:
            print("❌ Playwright is not installed")
            print("Run: pip install playwright")
            print("Then: playwright install")
            return
        except Exception as e:
            print(f"❌ Error launching browser: {str(e)}")
            return

        # If we got here, Playwright is working. Now test the WorkdayService directly.
        print("\n" + "=" * 80)
        print("TESTING WORKDAY SERVICE")
        print("=" * 80)

        # Import the service directly to avoid module issues
        try:
            from workday_service import WorkdayService
            print("✅ WorkdayService imported successfully")

            # Create service with explicit settings
            print(
                "\nCreating WorkdayService with headless=False, mock_for_testing=False"
            )
            service = WorkdayService(headless=False, mock_for_testing=False)

            print(f"Service created. Using mock mode: {service.using_mock}")

            if service.using_mock:
                print(
                    "⚠️ WARNING: Service is using mock mode despite being told not to."
                )
                print(
                    "   This suggests issues with Playwright or browser availability."
                )
                print("   Check the error messages above.")

            # Try logging in
            print("\nAttempting to log in to Workday...")
            login_result = service.login(username, password)

            if login_result["success"]:
                print("✅ Login successful!")
                print("   You should see a browser window displaying Workday")

                # Pause to let user see the browser
                print("   Waiting 5 seconds before continuing...")
                time.sleep(5)

                # Try navigating
                print("\nAttempting to navigate to academics...")
                academics_result = service.navigate_to_academics()

                if academics_result["success"]:
                    print("✅ Navigation successful!")
                    print(
                        "   You should see the browser navigate to the academics section"
                    )
                    print("   Waiting 5 seconds before closing...")
                    time.sleep(5)
                else:
                    print(
                        f"❌ Navigation failed: {academics_result.get('error', 'Unknown error')}"
                    )
            else:
                print(
                    f"❌ Login failed: {login_result.get('error', 'Unknown error')}"
                )

            # Always close the service
            service.close()
            print("\n✅ Service closed successfully")

        except ImportError as e:
            print(f"❌ Failed to import WorkdayService: {str(e)}")
            return
        except Exception as e:
            print(f"❌ Error using WorkdayService: {str(e)}")
            return

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

    finally:
        print("\n" + "=" * 80)
        print("TEST COMPLETED")
        print("=" * 80)


if __name__ == "__main__":
    test_direct_browser()
