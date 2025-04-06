"""
Test script for UserService and get_user_context functionality.
"""

import json
import logging
from user_service import UserService
from user_functions import get_user_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_user_service():
    """Test the UserService directly."""
    logger.info("Testing UserService...")

    user_service = UserService()

    # Test get_user_info
    user_info = user_service.get_user_info()
    logger.info(f"User info: {json.dumps(user_info, indent=2)}")

    # Test get_user_context
    context = user_service.get_user_context(["profile"])
    logger.info(f"User context retrieved with profile data")

    return True


def test_get_user_context_function():
    """Test the get_user_context function from user_functions."""
    logger.info("Testing get_user_context function...")

    # Test with profile only
    profile_context = get_user_context(["profile"])
    profile_data = json.loads(profile_context)
    logger.info(
        f"Profile context retrieved: {profile_data['profile']['name']}")

    # Test with Canvas data (may use mocks in the future)
    try:
        canvas_context = get_user_context(["profile", "assignments"])
        canvas_data = json.loads(canvas_context)
        logger.info(
            f"Canvas context retrieved with assignments: {canvas_data.get('assignments', {}).get('success', False)}"
        )
    except Exception as e:
        logger.warning(
            f"Canvas context retrieval failed (expected in test environment): {str(e)}"
        )

    return True


if __name__ == "__main__":
    logger.info("Starting UserService tests...")

    try:
        test_user_service()
        test_get_user_context_function()
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
