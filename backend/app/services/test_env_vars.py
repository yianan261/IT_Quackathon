"""
Simple script to verify environment variable access.
"""

import os
import sys


def print_env_vars():
    """Print environment variables to verify they're accessible."""
    print("Python version:", sys.version)
    print("\nChecking for Workday credentials in environment variables:")

    # Check for username
    username = os.environ.get("WORKDAY_USERNAME")
    print(f"WORKDAY_USERNAME: {username if username else 'Not found'}")

    # Check for password (don't print actual password)
    password = os.environ.get("WORKDAY_PASSWORD")
    print(f"WORKDAY_PASSWORD: {'Found' if password else 'Not found'}")

    # Print all environment variables (be careful with this in production)
    print("\nAll environment variables:")
    for key, value in os.environ.items():
        # Don't print sensitive values
        if 'password' in key.lower() or 'secret' in key.lower(
        ) or 'key' in key.lower():
            print(f"{key}: {'*' * len(value) if value else 'Not set'}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    print_env_vars()
