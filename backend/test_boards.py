import asyncio
import httpx

async def test_board(url):
    print(f"\nFetching {url}")
    headers = {
        "User-Agent": "JobBridge/1.0 (student job discovery; +https://github.com/jobbridge)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers, timeout=10)
            print("Status:", resp.status_code)
            print("Content len:", len(resp.text))
        except Exception as e:
            print("Error:", e)

async def test():
    await test_board("https://www.adzuna.com.au/search?q=software+engineer&loc=Melbourne")
    await test_board("https://www.careerone.com.au/jobs/search?q=software+engineer&where=Melbourne")
    await test_board("https://au.jora.com/jobs?q=software+engineer&l=Melbourne")

if __name__ == "__main__":
    asyncio.run(test())
