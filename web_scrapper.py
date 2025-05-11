import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp


class TelevisionScraper:
    BASE_URL = "https://m-velo.by/velosipedy?cpage=page-"

    def __init__(self):
        self.scraped_data = {}

    def _extract_data_from_html(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        models = soup.select("div.products__name.hidden-xs > a")
        prices = soup.select("div.prices__values.prices__values_simple > div > meta")

        for model, price in zip(models, prices):
            self.scraped_data[model["title"].split("Велосипед")[-1]] = price["content"]


class SynchronousScraper(TelevisionScraper):
    def __init__(self):
        super().__init__()
        self.current_page = 1

    def scrape_all_pages(self):
        while True:
            response = requests.get(self.BASE_URL + str(self.current_page))
            if response.status_code != 200 or self.current_page > 10:
                break
            self._extract_data_from_html(response.text)
            self.current_page += 1
        return self.scraped_data


class AsynchronousScraper(TelevisionScraper):
    def __init__(self):
        super().__init__()

    async def _fetch_page_content(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    async def _process_single_page(self, url):
        html = await self._fetch_page_content(url)
        self._extract_data_from_html(html)

    async def _scrape_multiple_pages(self):
        tasks = []
        for page_num in range(1, 11):
            url = self.BASE_URL + str(page_num)
            tasks.append(self._process_single_page(url))
        await asyncio.gather(*tasks)

    def scrape_all_pages(self):
        asyncio.run(self._scrape_multiple_pages())
        return self.scraped_data