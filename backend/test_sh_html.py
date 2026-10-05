import asyncio
import httpx
from bs4 import BeautifulSoup

async def test():
    url = "https://www.simplyhired.com.au/search?q=software+engineer&l=Melbourne"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        jobs = soup.select("[data-jobkey], .SerpJob-jobCard")
        print(f"Found {len(jobs)} job nodes")
        for j in jobs[:2]:
            print("---")
            title = j.select_one(".jobposting-title, h2, h3")
            print("Title:", title.text.strip() if title else None)
            comp = j.select_one("[data-testid='companyName'], .jobposting-company, .company, span.chakra-text")
            print("Company:", comp.text.strip() if comp else None)
            loc = j.select_one("[data-testid='searchSerpJobLocation'], .jobposting-location, .location")
            print("Location:", loc.text.strip() if loc else None)
            link = j.select_one("a")
            print("Link:", link['href'] if link and link.has_attr('href') else None)

if __name__ == "__main__":
    asyncio.run(test())
