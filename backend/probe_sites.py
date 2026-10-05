"""Probe live pages to discover real selectors and API shapes."""
import asyncio
import pathlib
import json
import sys
sys.path.insert(0, '.')

from app.scraper.http_client import fetch, fetch_json
from bs4 import BeautifulSoup

FIXTURES = pathlib.Path('tests/fixtures')
FIXTURES.mkdir(parents=True, exist_ok=True)


async def probe_seek():
    """
    Seek.com.au embeds job data in a __NEXT_DATA__ script tag as JSON.
    We parse the search results page HTML and extract that JSON blob.
    """
    print("\n=== SEEK ===")
    try:
        html = await fetch(
            'https://www.seek.com.au/barista-jobs/in-Melbourne-VIC',
            rate_limit=2, check_robots=False, use_cache=False
        )
        (FIXTURES / 'seek_au.html').write_text(html[:50000], encoding='utf-8')
        soup = BeautifulSoup(html, 'lxml')

        # Check for JSON in __NEXT_DATA__
        nd = soup.find('script', id='__NEXT_DATA__')
        if nd:
            data = json.loads(nd.string)
            jobs = (data.get('props', {}).get('pageProps', {})
                    .get('jobSearch', {}).get('results', []))
            print(f"  __NEXT_DATA__ found, jobs: {len(jobs)}")
            if jobs:
                print(f"  First job keys: {list(jobs[0].keys())[:12]}")
            (FIXTURES / 'seek_au_next_data.json').write_text(json.dumps(jobs[:3], indent=2))
        else:
            # Fall back to HTML cards
            cards = soup.select('article[data-automation="normalJob"]')
            print(f"  HTML cards found: {len(cards)}")
            if cards:
                print(f"  First card: {cards[0].prettify()[:800]}")
    except Exception as e:
        print(f"  SEEK failed: {e}")


async def probe_gumtree():
    """Gumtree is static HTML with clear CSS classes."""
    print("\n=== GUMTREE ===")
    try:
        html = await fetch(
            'https://www.gumtree.com.au/s-jobs/barista/melbourne/k0c9300l3001954',
            rate_limit=2, check_robots=False, use_cache=False
        )
        (FIXTURES / 'gumtree_au.html').write_text(html[:50000], encoding='utf-8')
        soup = BeautifulSoup(html, 'lxml')
        # Try various card selectors
        for sel in [
            'article.user-ad-row',
            'li.user-ad-collection-new-design',
            'div[data-testid="listing-card"]',
            '.listing',
        ]:
            cards = soup.select(sel)
            if cards:
                print(f"  Selector '{sel}': {len(cards)} cards")
                print(f"  Sample: {cards[0].prettify()[:600]}")
                break
        else:
            print(f"  No known selectors matched; page title: {soup.title.text if soup.title else 'N/A'}")
    except Exception as e:
        print(f"  GUMTREE failed: {e}")


async def probe_mcdonalds():
    """McDonald's AU careers page."""
    print("\n=== McDONALD'S AU ===")
    try:
        html = await fetch(
            'https://careers.mcdonalds.com.au/search/?q=crew&locationsearch=melbourne',
            rate_limit=2, check_robots=False, use_cache=False
        )
        (FIXTURES / 'mcdonalds_au.html').write_text(html[:50000], encoding='utf-8')
        soup = BeautifulSoup(html, 'lxml')
        for sel in [
            'li.paginationHeader-resultListItem',
            'tr.data-row',
            'a.jobTitle-link',
            '.job-list-item',
            'article',
        ]:
            items = soup.select(sel)
            if items:
                print(f"  Selector '{sel}': {len(items)} items")
                print(f"  Sample: {items[0].prettify()[:500]}")
                break
        else:
            print(f"  Page title: {soup.title.text if soup.title else 'N/A'}")
            print(f"  Body snippet: {soup.body.get_text()[:400] if soup.body else 'N/A'}")
    except Exception as e:
        print(f"  McDONALDS failed: {e}")


async def probe_woolworths():
    """Woolworths careers — likely JSON API."""
    print("\n=== WOOLWORTHS ===")
    try:
        # Woolworths uses SmartRecruiters API
        data = await fetch_json(
            'https://api.smartrecruiters.com/v1/companies/WoolworthsGroupLimited/postings',
            params={'limit': '5', 'q': 'store assistant', 'city': 'Melbourne'},
            check_robots=False, use_cache=False
        )
        jobs = data.get('content', []) if isinstance(data, dict) else []
        print(f"  SmartRecruiters jobs: {len(jobs)}")
        if jobs:
            print(f"  First job keys: {list(jobs[0].keys())[:12]}")
        (FIXTURES / 'woolworths_au.json').write_text(json.dumps(data, indent=2)[:8000])
    except Exception as e:
        print(f"  WOOLWORTHS failed: {e}")
        # Try fallback HTML page
        try:
            html = await fetch(
                'https://careers.woolworthsgroup.com.au/search/?q=store+assistant&location=melbourne',
                rate_limit=2, check_robots=False, use_cache=False
            )
            (FIXTURES / 'woolworths_au.html').write_text(html[:30000], encoding='utf-8')
            soup = BeautifulSoup(html, 'lxml')
            print(f"  HTML page title: {soup.title.text if soup.title else 'N/A'}")
        except Exception as e2:
            print(f"  HTML fallback failed: {e2}")


async def probe_unijobs():
    """UniJobs AU student/campus board."""
    print("\n=== UNIJOBS ===")
    try:
        html = await fetch(
            'https://www.unijobs.com.au/jobs/?q=student&l=melbourne&jt=parttime',
            rate_limit=2, check_robots=False, use_cache=False
        )
        (FIXTURES / 'unijobs_au.html').write_text(html[:50000], encoding='utf-8')
        soup = BeautifulSoup(html, 'lxml')
        for sel in [
            '.job-listing',
            '.job-result',
            'article.job',
            'li.job',
            'div.job-card',
            'a[href*="/job/"]',
        ]:
            items = soup.select(sel)
            if items:
                print(f"  Selector '{sel}': {len(items)}")
                print(f"  Sample: {items[0].prettify()[:500]}")
                break
        else:
            print(f"  Title: {soup.title.text if soup.title else 'N/A'}")
    except Exception as e:
        print(f"  UNIJOBS failed: {e}")


async def main():
    await probe_seek()
    await probe_gumtree()
    await probe_mcdonalds()
    await probe_woolworths()
    await probe_unijobs()
    print("\nDone. Check tests/fixtures/ for saved HTML/JSON.")


if __name__ == '__main__':
    asyncio.run(main())
