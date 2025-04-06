"""
Script to install and verify Playwright and its browser dependencies.
Run this script if you're having issues with Playwright in the application.
"""

import sys
import subprocess
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_playwright_installed():
    """Check if Playwright is installed."""
    try:
        import playwright
        logger.info(
            f"✅ Playwright is installed (version: {playwright.__version__})")
        return True
    except ImportError:
        logger.error("❌ Playwright is not installed.")
        return False


def install_playwright():
    """Install Playwright Python package."""
    logger.info("Installing Playwright Python package...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "playwright"],
            check=True,
            capture_output=True,
            text=True)
        logger.info("✅ Playwright package installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install Playwright: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False


def install_browser_binaries():
    """Install Playwright browser binaries."""
    logger.info("Installing Playwright browser binaries...")
    try:
        import playwright

        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install"],
            check=True,
            capture_output=True,
            text=True)
        logger.info("✅ Browser binaries installed successfully")
        return True
    except (subprocess.CalledProcessError, ImportError) as e:
        logger.error(f"❌ Failed to install browser binaries: {e}")
        return False


def verify_browser_works():
    """Verify that a browser can be launched."""
    logger.info("Verifying browser functionality...")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://example.com")
            title = page.title()
            browser.close()

        logger.info(f"✅ Browser verification successful. Page title: {title}")
        return True
    except Exception as e:
        logger.error(f"❌ Browser verification failed: {e}")
        return False


def print_installation_path():
    """Print installation paths for debugging."""
    try:
        import playwright
        logger.info(
            f"Playwright package location: {Path(playwright.__file__).parent}")

        try:
            import site
            user_site = site.getusersitepackages()
            sys_site = site.getsitepackages()
            logger.info(f"User site packages: {user_site}")
            logger.info(f"System site packages: {sys_site}")
        except Exception as e:
            logger.warning(f"Could not determine site packages: {e}")

    except ImportError:
        logger.warning("Cannot determine Playwright location (not installed)")


def main():
    """Main function to install and verify Playwright."""
    logger.info("=" * 60)
    logger.info("Playwright Installation and Verification Tool")
    logger.info("=" * 60)

    print_installation_path()

    # Check if Playwright is already installed
    if not check_playwright_installed():
        print("\nDo you want to install the Playwright package? (y/n)")
        if input().lower() == 'y':
            install_playwright()
        else:
            logger.info("Skipping Playwright package installation.")
            return

    # Check if browser binaries are installed
    print("\nDo you want to install or update the browser binaries? (y/n)")
    if input().lower() == 'y':
        install_browser_binaries()
    else:
        logger.info("Skipping browser binaries installation.")

    # Verify that everything works
    print("\nDo you want to verify browser functionality? (y/n)")
    if input().lower() == 'y':
        verify_browser_works()

    logger.info("\n" + "=" * 60)
    logger.info("Installation and verification complete.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
