"""
Test script for WorkdayService with visible browser.
Run this script to see the browser automation in action.
"""

import json
import logging
import time
from workday_service import WorkdayService
import os
import getpass

WORKDAY_USERNAME = "ychen17@stevens.edu"
WORKDAY_PASSWORD = "08376Lemonrox!"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_visible_browser():
    """Test the WorkdayService with a visible browser."""
    logger.info("Testing WorkdayService with visible browser...")

    # Create a WorkdayService instance with headless=False
    service = WorkdayService(headless=False, mock_for_testing=False)

    try:
        # Step 1: Log in to Workday
        # Try to get credentials from environment variables
        username = os.environ.get("WORKDAY_USERNAME") or WORKDAY_USERNAME
        password = os.environ.get("WORKDAY_PASSWORD") or WORKDAY_PASSWORD

        print(f"Username from env: {'Found' if username else 'Not found'}")
        print(f"Password from env: {'Found' if password else 'Not found'}")

        # If credentials aren't in environment variables, prompt the user
        if not username or not password:
            logger.warning("No credentials found in environment variables.")
            print("\nPlease enter your Stevens Workday credentials:")
            username = input("Username: ")
            password = getpass.getpass("Password: ")

            if not username or not password:
                logger.error("No credentials provided. Exiting.")
                return

        login_result = service.login(username, password)
        logger.info(f"Login result: {login_result['success']}")

        if not login_result['success']:
            logger.error(
                f"Login failed: {login_result.get('error', 'Unknown error')}")
            return

        # Small pause to observe the browser
        logger.info("Login successful! Pausing for 3 seconds...")
        time.sleep(3)

        # Step 2: Navigate to Academics
        academics_result = service.navigate_to_academics()
        logger.info(
            f"Navigate to Academics result: {academics_result['success']}")

        if not academics_result['success']:
            logger.error(
                f"Navigation failed: {academics_result.get('error', 'Unknown error')}"
            )
            return

        # Longer pause to observe the final state
        logger.info(
            "Navigation successful! Pausing for 5 seconds before closing...")
        time.sleep(5)

    finally:
        # Close the browser
        logger.info("Closing browser...")
        if hasattr(service, 'browser') and service.browser:
            service.close()

    logger.info("Test completed.")


if __name__ == "__main__":
    logger.info("Starting visible browser test...")

    try:
        test_visible_browser()
        logger.info("Test completed successfully!")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
