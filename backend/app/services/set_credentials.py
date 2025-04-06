"""
Helper script that sets Workday credentials in environment variables
and then runs a test script of your choice.

Usage:
python set_credentials.py test_browser_direct.py
"""

import os
import sys
import subprocess
import getpass


def set_credentials_and_run(script_to_run=None):
    print("=" * 80)
    print("WORKDAY CREDENTIALS SETUP")
    print("=" * 80)

    # Prompt for credentials
    print("\nPlease enter your Stevens Workday credentials:")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    if not username or not password:
        print("Error: Both username and password are required.")
        return

    # Set environment variables
    os.environ["WORKDAY_USERNAME"] = username
    os.environ["WORKDAY_PASSWORD"] = password

    print("\n✅ Credentials set in environment variables for this session.")

    # Run the specified script if provided
    if script_to_run:
        print(f"\nRunning {script_to_run}...")
        try:
            # We need to use the same Python interpreter and pass the environment
            result = subprocess.run([sys.executable, script_to_run],
                                    env=os.environ)
            if result.returncode != 0:
                print(
                    f"\n❌ Script exited with error code: {result.returncode}")
            else:
                print(f"\n✅ Script completed successfully")
        except Exception as e:
            print(f"\n❌ Error running script: {str(e)}")
    else:
        print(
            "\nNo script specified to run. You can now run your own script in this terminal session."
        )
        print("For example:")
        print("  python test_browser_direct.py")


if __name__ == "__main__":
    # Get the script to run from command line args
    script_to_run = sys.argv[1] if len(sys.argv) > 1 else None
    set_credentials_and_run(script_to_run)
