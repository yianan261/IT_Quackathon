import os
import logging
import argparse
from app.services.workday_service import WorkdayService
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """
    Simple test script for the WorkdayService.
    
    This script allows testing the WorkdayService functionality
    from the command line. It can perform different actions
    like logging in, navigating to academics, and extracting pages.
    """
    parser = argparse.ArgumentParser(description='Test the Workday service')
    parser.add_argument(
        '--username',
        help='Workday username (or set WORKDAY_USERNAME env var)')
    parser.add_argument(
        '--password',
        help='Workday password (or set WORKDAY_PASSWORD env var)')
    parser.add_argument('--headless',
                        action='store_true',
                        help='Run browser in headless mode')
    parser.add_argument(
        '--action',
        choices=['login', 'academics', 'extract', 'validate', 'register'],
        default='login',
        help='Action to perform')
    parser.add_argument('--term', help='Academic term for course search')
    parser.add_argument('--subject', help='Subject for course search')
    parser.add_argument('--step',
                        default='test_extract',
                        help='Step name for extract action')
    parser.add_argument('--course',
                        help='Course code for registration (e.g., "CS 101")')
    parser.add_argument(
        '--screenshot',
        action='store_true',
        help='Take screenshot when extracting (final pages only)')
    parser.add_argument('--mock',
                        action='store_true',
                        help='Use mock mode (no Playwright required)')

    args = parser.parse_args()

    # Use command line args or env vars for credentials
    username = args.username or os.environ.get("WORKDAY_USERNAME")
    password = args.password or os.environ.get("WORKDAY_PASSWORD")

    if not username or not password:
        logger.error(
            "Credentials required. Provide username/password args or set env vars."
        )
        return

    # Create the Workday service
    workday = WorkdayService(headless=args.headless,
                             mock_for_testing=args.mock)

    try:
        if args.action == 'login':
            logger.info("Testing login...")
            result = workday.login(username, password)
            logger.info(f"Login success: {result['success']}")
            if not result['success']:
                logger.error(f"Login error: {result.get('error')}")
            else:
                logger.info("Login successful! Landing page saved.")

        elif args.action == 'academics':
            logger.info("Testing navigation to academics...")
            # First login
            login_result = workday.login(username, password)
            if not login_result['success']:
                logger.error(f"Login failed: {login_result.get('error')}")
                return

            # Then navigate to academics
            result = workday.navigate_to_academics()
            logger.info(f"Navigation success: {result['success']}")
            if not result['success']:
                logger.error(f"Navigation error: {result.get('error')}")
            else:
                logger.info("Navigation successful! Academics page saved.")

                # If term is provided, also test course search
                if args.term:
                    logger.info(f"Testing course search for term: {args.term}")
                    search_result = workday.search_courses(
                        args.term, args.subject)
                    logger.info(f"Search success: {search_result['success']}")
                    if not search_result['success']:
                        logger.error(
                            f"Search error: {search_result.get('error')}")
                    else:
                        logger.info("Search successful! Results page saved.")

        elif args.action == 'extract':
            logger.info(f"Testing page extraction with step name: {args.step}")
            # First login
            login_result = workday.login(username, password)
            if not login_result['success']:
                logger.error(f"Login failed: {login_result.get('error')}")
                return

            # Then extract current page
            result = workday.extract_current_page(
                args.step, take_screenshot=args.screenshot)
            logger.info(f"Extraction success: {result['success']}")
            if not result['success']:
                logger.error(f"Extraction error: {result.get('error')}")
            else:
                logger.info(
                    f"Extraction successful! Page saved to {result.get('html_file')}"
                )
                if result.get('screenshot'):
                    logger.info(
                        f"Screenshot saved to {result.get('screenshot')}")
                else:
                    logger.info(
                        "No screenshot taken (use --screenshot for final pages)"
                    )

        elif args.action == 'validate':
            logger.info("Testing registration page validation...")
            # First login
            login_result = workday.login(username, password)
            if not login_result['success']:
                logger.error(f"Login failed: {login_result.get('error')}")
                return

            # Navigate to academics (if not already on registration page)
            workday.navigate_to_academics()

            # Check if on registration page
            result = workday.check_if_on_registration_page()
            logger.info(f"Validation success: {result['success']}")
            if not result['success']:
                logger.error(f"Validation error: {result.get('error')}")
            else:
                logger.info(
                    f"Page title: {result.get('page_title', 'No title detected')}"
                )
                logger.info(f"Screenshot saved to {result.get('screenshot')}")

        elif args.action == 'register':
            if not args.course:
                logger.error(
                    "Course code is required for registration action. Use --course parameter."
                )
                return

            logger.info(f"Testing course registration for {args.course}...")
            # First login
            login_result = workday.login(username, password)
            if not login_result['success']:
                logger.error(f"Login failed: {login_result.get('error')}")
                return

            # Register for course
            result = workday.automate_course_registration(args.course)
            logger.info(f"Registration success: {result['success']}")
            if not result['success']:
                logger.error(f"Registration error: {result.get('error')}")
            else:
                logger.info(f"Registration result: {result.get('message')}")
                logger.info(f"Screenshots: {result.get('screenshots', [])}")

    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
    finally:
        workday.close()


if __name__ == "__main__":
    main()
