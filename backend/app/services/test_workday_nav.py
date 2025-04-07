"""
Test script for Workday navigation functionality.
This script tests the browser automation for navigating to the Workday course registration page.
"""

import json
import time
from user_functions import navigate_to_workday_registration


def test_workday_navigation():
    """Test navigating to the Workday course registration page."""
    print("=" * 80)
    print("TESTING WORKDAY REGISTRATION NAVIGATION")
    print("=" * 80)

    print("\nCalling navigate_to_workday_registration()...")
    result_str = navigate_to_workday_registration(mock_mode=False)

    # Parse and display the result
    try:
        result = json.loads(result_str)

        print("\nFunction returned:")
        print(f"Success: {result.get('success', False)}")
        print(f"Message: {result.get('message', 'No message')}")

        # Check if we need user input
        if result.get('needs_user_input', False):
            print("\nUSER ACTION REQUIRED:")
            print(
                result.get(
                    'message',
                    'Please enter your credentials in the browser window'))
            print(
                "\nThe browser window should be open. Please enter your credentials."
            )
            print(
                "This script will continue after 60 seconds or when you press Enter..."
            )

            # Create a timeout of 60 seconds or until user presses Enter
            timeout = 60
            print(
                f"Waiting up to {timeout} seconds for you to complete the login..."
            )

            for remaining in range(timeout, 0, -1):
                print(
                    f"\rTime remaining: {remaining} seconds (press Enter to continue)...",
                    end="")

                # Check if user pressed Enter (non-blocking)
                import select
                import sys
                if select.select([sys.stdin], [], [], 0.0)[0]:
                    sys.stdin.readline()
                    print("\nContinuing...")
                    break

                time.sleep(1)

            print("\nContinuing with the test...")

            # After user logs in, we can try again to navigate to registration
            print("\nCalling navigate_to_workday_registration() again...")
            result_str = navigate_to_workday_registration(mock_mode=False)

            # Parse and display the new result
            try:
                result = json.loads(result_str)
                print("\nFunction returned (after login):")
                print(f"Success: {result.get('success', False)}")
                print(f"Message: {result.get('message', 'No message')}")
            except json.JSONDecodeError:
                print(f"Error: Could not parse result as JSON. Raw output:")
                print(result_str)

        # If we have a screenshot, show the path
        if "screenshot" in result:
            print(f"\nScreenshot saved at: {result['screenshot']}")

        # Allow time to observe the browser
        if result.get('success', False):
            print("\nBrowser should be on the academics/registration page.")
            print("Taking a 10 second pause to observe...")
            time.sleep(10)

    except json.JSONDecodeError:
        print(f"Error: Could not parse result as JSON. Raw output:")
        print(result_str)

    print("\n" + "=" * 80)
    print("Test complete.")


if __name__ == "__main__":
    test_workday_navigation()
