from bs4 import BeautifulSoup
import httpx
import asyncio
from typing import List, Dict
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


# TODO: rewrite/ rescrape (can switch to playwright)
class StevensScraper:

    def __init__(self):
        self.base_url = "https://web.stevens.edu"
        self.course_catalog_url = f"{self.base_url}/catalog"
        self.headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def get_page_content(self, url: str) -> str:
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def scrape_courses(self) -> List[Dict]:
        pass
