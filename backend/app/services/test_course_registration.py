"""
Test script for the open_course_registration function.
This test will verify that we can open a browser window and navigate to the course registration page.
"""

import os
import json
import time
from user_functions import open_course_registration


def test_course_registration():
    """Test the open_course_registration function."""
    print("=" * 80)
    print("TESTING COURSE REGISTRATION FUNCTION")
    print("=" * 80)

    # Check if we have credentials in environment
    username = os.environ.get("WORKDAY_USERNAME")
    password = os.environ.get("WORKDAY_PASSWORD")

    if not username or not password:
        print(
            "\nERROR: Workday credentials not found in environment variables!")
        print("Please run set_credentials.py first to set your credentials:")
        print("python set_credentials.py test_course_registration.py")
        return

    print(f"\nFound credentials in environment. Username: {username[:2]}***")

    # Call the function with debug output
    print("\nCalling open_course_registration()...")
    result_str = open_course_registration(mock_mode=False)

    # Parse and display the result
    try:
        result = json.loads(result_str)

        print("\nFunction returned:")
        print(f"Success: {result.get('success', False)}")

        if result.get('success', False):
            print(f"Message: {result.get('message', 'No message')}")
            print(
                f"Browser visible: {result.get('browser_visible', 'Unknown')}")

            # Allow time to observe the browser
            print(
                "\nBrowser should be visible now. Taking a 10 second pause...")
            time.sleep(10)
            print("Test complete.")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            if 'details' in result:
                print("\nDetails:")
                for key, value in result['details'].items():
                    print(f"  {key}: {value}")

    except json.JSONDecodeError:
        print(f"Error: Could not parse result as JSON. Raw output:")
        print(result_str)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_course_registration()
