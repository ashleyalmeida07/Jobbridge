import asyncio
from app.scraper.board_scraper import scrape_all_boards
from app.core.config import settings

async def test():
    jobs = await scrape_all_boards(["software engineer"], "Melbourne", "AU")
    print(f"Total boards found {len(jobs)} jobs")
    if jobs:
        print(jobs[0])

if __name__ == "__main__":
    asyncio.run(test())
