"""
Service for retrieving and managing user data.
This will be replaced with a database-backed implementation in the future.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for retrieving and managing user information.
    Currently using hardcoded data, but designed to be replaced with
    database queries in the future.
    """

    def __init__(self):
        """Initialize the user service."""
        logger.info("Initializing UserService")

        # This will be replaced with database connection setup in the future
        self._mock_db_initialized = True

    def get_user_info(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user information.
        
        Args:
            user_id: Optional user ID. If not provided, returns for the current user.
        
        Returns:
            Dictionary containing user information
        """
        logger.info(
            f"Getting user info for user_id: {user_id or 'current user'}")

        # This is a dummy implementation - in the future, this would query a database
        return {
            "user_id": "123456",
            "name": "Yian Chen",
            "email": "ychen@stevens.edu",
            "academic_level": "graduate",
            "major": "applied artificial intelligence",
            "phone": "201-555-1234",
            "address": "1 Castle Point Terrace, Hoboken, NJ 07030",
            "preferences": {
                "notify_due_dates": True,
                "notify_grades": True,
                "theme": "default"
            }
        }

    def get_user_context(self, context_types: list) -> Dict[str, Any]:
        """
        Get comprehensive user context based on requested types.
        
        Args:
            context_types: List of context types to retrieve 
                          (only "profile" is supported directly by this service)
        
        Returns:
            Dictionary containing requested user context data
        """
        logger.info(f"Getting user context for types: {context_types}")

        result = {
            "context_meta": {
                "retrieved_at": self._get_current_timestamp(),
                "requested_types": context_types,
                "source": "User Service (Mock)"
            }
        }

        # Add profile information regardless of what's requested
        # since this is the only information this service provides directly
        result["profile"] = self.get_user_info()

        return result

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format for metadata."""
        from datetime import datetime
        return datetime.now().isoformat()
