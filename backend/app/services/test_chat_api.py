"""
Test script for the Chat API that can trigger the Workday service automation.
This script makes a request to your FastAPI chat endpoint with a message that
should trigger the agent to call the WorkdayService functions.
"""

import requests
import json
import logging
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API endpoint
API_URL = "http://localhost:8000/api/chat"


def test_chat_api_with_workday_automation():
    """Test the chat API by sending a message that should trigger Workday automation."""
    logger.info("Testing Chat API with Workday automation...")

    # Example messages that might trigger Workday automation
    messages = [{
        "role": "user",
        "content": "Take me to the course registration page in Workday"
    }, {
        "role":
        "user",
        "content":
        "Help me search for courses in Workday for Fall 2023"
    }]

    # Make sure your environment variables are set if needed
    if not os.environ.get("WORKDAY_USERNAME") or not os.environ.get(
            "WORKDAY_PASSWORD"):
        logger.warning(
            "WORKDAY_USERNAME or WORKDAY_PASSWORD environment variables not set"
        )
        logger.warning("The automation might fail if credentials are required")

    for i, message in enumerate(messages):
        logger.info(f"Sending message {i+1}: {message['content']}")

        # Prepare the request data
        data = {"messages": [message]}

        try:
            # Send the request to the API
            response = requests.post(API_URL, json=data)
            response.raise_for_status(
            )  # Raise exception for 4XX/5XX responses

            result = response.json()
            logger.info(f"Response received: {result}")

            # Sleep to allow time to observe the browser if it was opened
            logger.info(
                "Waiting 10 seconds to observe any browser automation...")
            time.sleep(10)

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")

        logger.info("---")

    logger.info("Test completed.")


if __name__ == "__main__":
    logger.info("Starting Chat API test with Workday automation...")

    try:
        test_chat_api_with_workday_automation()
        logger.info("Test completed successfully!")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
