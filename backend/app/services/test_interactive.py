"""
Interactive test script for WorkdayService.
This script prompts for credentials to test the browser automation.
"""

import logging
import time
from backend.app.services.workday_service2 import WorkdayService
import getpass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_interactive():
    """Test the WorkdayService with credentials from user input."""
    print("\n====== Stevens Workday Browser Test ======")
    print("This script will open a browser and automate Workday tasks.")
    print("You'll be able to see the browser window during automation.\n")

    # Prompt for credentials
    print("Enter your Stevens Workday credentials:")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    if not username or not password:
        print("No credentials provided. Exiting.")
        return

    # Create a WorkdayService instance with headless=False (visible browser)
    service = WorkdayService(headless=False, mock_for_testing=False)

    try:
        # Step 1: Log in to Workday
        print("\nAttempting to log in to Workday...")
        login_result = service.login(username, password)

        if not login_result['success']:
            print(
                f"❌ Login failed: {login_result.get('error', 'Unknown error')}"
            )
            return

        print("✅ Login successful!")

        # Small pause to observe the browser
        print("Pausing for 3 seconds to observe the browser...")
        time.sleep(3)

        # Step 2: Navigate to Academics
        print("\nNavigating to Academics section...")
        academics_result = service.navigate_to_academics()

        if not academics_result['success']:
            print(
                f"❌ Navigation failed: {academics_result.get('error', 'Unknown error')}"
            )
            return

        print("✅ Navigation successful!")

        # Longer pause to observe the final state
        print("Pausing for 5 seconds to observe the browser...")
        time.sleep(5)

        # Ask if the user wants to explore more
        action = input("\nDo you want to explore more? (y/n): ").lower()
        if action == 'y':
            term = input(
                "Enter a term to search for courses (e.g., 'Fall 2023'): ")
            subject = input(
                "Enter a subject (optional, press Enter to skip): ")

            if term:
                print(f"\nSearching for courses in {term}...")
                if subject:
                    print(f"Filtering by subject: {subject}")

                search_result = service.search_courses(
                    term, subject if subject else None)

                if not search_result['success']:
                    print(
                        f"❌ Search failed: {search_result.get('error', 'Unknown error')}"
                    )
                else:
                    print("✅ Search successful!")
                    print("Pausing for 10 seconds to observe the results...")
                    time.sleep(10)

    finally:
        # Close the browser
        print("\nClosing browser...")
        service.close()

    print("\n✅ Test completed. Thanks for testing!")


if __name__ == "__main__":
    try:
        test_interactive()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user. Exiting.")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n❌ Test failed: {str(e)}")
