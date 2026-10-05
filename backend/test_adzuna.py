import asyncio
import httpx

async def test():
    # Test Adzuna
    url = "https://www.adzuna.com.au/search?q=software+engineer&loc=Melbourne"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
            print("Adzuna Status:", resp.status_code)
            if resp.status_code != 200:
                print("Adzuna Text:", resp.text[:500])
        except Exception as e:
            print("Adzuna Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
