"""
Direct browser test script that doesn't rely on app.core.config.
This is a completely standalone script that will open a browser window
and show you Workday automation.
"""

import os
import time
import getpass
import logging
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_playwright_installed():
    """Check if Playwright is installed and install it if it's not."""
    try:
        import playwright
        print("✅ Playwright is installed.")

        # Check if browsers are installed
        try:
            result = subprocess.run(["playwright", "install", "--help"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    check=True)
            print("✅ Playwright CLI is available.")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("⚠️ Playwright CLI might not be installed properly.")
            print("Running browser check may fail. If it does, please run:")
            print("pip install playwright")
            print("playwright install")
            return False

        return True
    except ImportError:
        print("❌ Playwright is not installed.")
        install = input("Do you want to install Playwright now? (y/n): ")
        if install.lower() == 'y':
            print("\nInstalling Playwright...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "playwright"])

            print("\nInstalling Playwright browsers...")
            subprocess.run([sys.executable, "-m", "playwright", "install"])

            print(
                "\nPlaywright installation completed. Please restart this script."
            )
        else:
            print(
                "\nPlaywright installation skipped. The test will run in mock mode."
            )
        return False


def run_direct_test():
    """Run a direct browser test using WorkdayService without relying on other imports."""
    print("\n===== Direct Browser Test =====")
    print("This test will open a browser and show you Workday automation.")

    # Check if Playwright is installed
    playwright_ok = check_playwright_installed()
    if not playwright_ok:
        print(
            "\n⚠️ WARNING: The test will run in mock mode since Playwright is not fully set up."
        )
        print(
            "You won't see a real browser window, only simulated operations.")
        print(
            "To see the actual browser, please install Playwright properly.\n")

    # Import here to avoid module import issues
    from backend.app.services.workday_service2 import WorkdayService

    # Prompt for credentials
    print("\nPlease enter your Stevens Workday credentials:")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    if not username or not password:
        print("No credentials provided. Exiting.")
        return

    # EXPLICITLY disable mock mode
    mock_mode = not playwright_ok  # Only use mock if Playwright isn't available

    # Create WorkdayService with visible browser
    print(f"\nStarting browser... (mock_mode={mock_mode}, headless=False)")
    service = WorkdayService(headless=False, mock_for_testing=mock_mode)

    # Verify we're using the right mode
    if service.using_mock:
        print("⚠️ Using MOCK browser (you won't see a real browser window)")
    else:
        print("✅ Using REAL browser (you should see a browser window)")

    try:
        # Login
        print("\nAttempting to log in...")
        login_result = service.login(username, password)

        if not login_result['success']:
            print(
                f"❌ Login failed: {login_result.get('error', 'Unknown error')}"
            )
            return

        print("✅ Login successful!")

        # Pause for user to see
        print("Observing browser for 3 seconds...")
        time.sleep(3)

        # Navigate to academics
        print("\nNavigating to academics section...")
        academics_result = service.navigate_to_academics()

        if not academics_result['success']:
            print(
                f"❌ Navigation failed: {academics_result.get('error', 'Unknown error')}"
            )
            return

        print("✅ Navigation successful!")

        # Longer pause to observe
        print("Observing browser for 5 seconds...")
        time.sleep(5)

    finally:
        # Always clean up
        print("\nClosing browser...")
        if hasattr(service, 'browser') and service.browser:
            service.close()

    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    try:
        run_direct_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n❌ Test failed: {str(e)}")
