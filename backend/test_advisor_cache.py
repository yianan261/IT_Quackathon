#!/usr/bin/env python3
"""
Test script for advisor caching functionality
Run this to test the advisor cache features
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the app directory to path so we can import services
sys.path.append(str(Path(__file__).parent / "app"))

from services.workday_service import WorkdayService
from playwright.async_api import async_playwright

async def test_advisor_cache():
    """Test the advisor caching functionality"""
    print("🧪 Testing Advisor Cache Functionality\n")
    
    # Start playwright
    playwright = await async_playwright().start()
    
    # Create WorkdayService instance
    workday_service = WorkdayService(
        playwright=playwright,
        current_academic_year="2025-2026 Semester Academic Calendar",
        current_academic_semester="2025 Fall Semester(09/02/2025-12/22/2025)",
        graduate_level="Graduate"
    )
    
    print("1. Testing cache loading (before any data is fetched):")
    workday_service.test_advisor_cache()
    
    print("\n2. Cache file location:")
    print(f"   📁 Cache directory: {workday_service.cache_dir}")
    print(f"   📄 Cache file: {workday_service.advisor_cache_file}")
    
    print("\n3. To test full functionality:")
    print("   - Run the Workday service normally to fetch advisor data")
    print("   - The advisor info will be automatically saved to cache")
    print("   - Run this test again to see cached data")
    
    print("\n4. Future enhancement (currently commented out):")
    print("   - Uncomment the cache-first logic in workday_service.py")
    print("   - The service will check cache before fetching from Workday")
    print("   - Cache expires after 24 hours for fresh data")
    
    # Cleanup
    await playwright.stop()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_advisor_cache()) 