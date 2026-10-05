import asyncio
import httpx

async def test():
    url = "https://www.simplyhired.com.au/search?q=software+engineer&l=Melbourne"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
            print("Status:", resp.status_code)
            if resp.status_code != 200:
                print("Text:", resp.text[:500])
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
