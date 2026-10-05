import asyncio
from app.scraper.discovery import _build_overpass_query, _fetch_overpass

async def test():
    query = _build_overpass_query(-37.81, 144.96, 10000, ["campus"])
    print("QUERY:\n", query)
    try:
        data = await _fetch_overpass(query)
        print("SUCCESS! Data keys:", data.keys())
        print("Elements:", len(data.get("elements", [])))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

