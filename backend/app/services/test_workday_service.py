# test_workday_service.py

import asyncio
from playwright.async_api import async_playwright
from app.services.workday_service_async import WorkdayService  # Adjust the import path as needed

async def main():
    async with async_playwright() as playwright:
        service = WorkdayService(playwright)
        await service.start()

        # Test one of the navigation methods
        result = await service.navigate_to_workday_registration()
        # result = await service.navigate_to_workday_financial_account()

        print("Result:", result)

        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
