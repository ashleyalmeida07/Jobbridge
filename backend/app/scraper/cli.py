"""
CLI for running scrapers locally and in CI.

Usage:
    python -m app.scraper.cli run --country AU --limit 50
    python -m app.scraper.cli run --country AU --source jora_au --keyword "barista" --city "Melbourne"
    python -m app.scraper.cli boards --country AU
    python -m app.scraper.cli discover --lat -37.81 --lng 144.96 --radius 10 --categories food_cafe retail

Examples (from backend/ with venv active):
    python -m app.scraper.cli run --country AU --limit 30
    python -m app.scraper.cli run --source jora_au --keyword "retail assistant" --city "Sydney"
"""

import argparse
import asyncio
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cli")


async def cmd_run(args):
    """Run board scrapers and print results."""
    from app.scraper.board_scraper import scrape_board, scrape_all_boards, get_boards_for_country

    country = args.country.upper()
    keyword = args.keyword or "jobs"
    city = args.city or ""
    limit = args.limit

    if args.source:
        # Single board
        boards = get_boards_for_country(country)
        board = next((b for b in boards if b["id"] == args.source), None)
        if not board:
            print(f"ERROR: board '{args.source}' not found for country {country}")
            sys.exit(1)
        jobs = await scrape_board(board, keyword, city, country, limit=limit)
    else:
        # All boards
        keywords = [keyword] if keyword != "jobs" else ["barista", "retail", "warehouse"]
        jobs = await scrape_all_boards(keywords, city, country, limit_per_board=limit)

    print(f"\n{'─'*60}")
    print(f"Results: {len(jobs)} jobs")
    print(f"{'─'*60}")
    for j in jobs:
        print(f"[{j.get('source','?')}] {j.get('title','?')} @ {j.get('employer','?')} — {j.get('location','?')} — {j.get('pay_text','N/A')}")
    print(f"{'─'*60}\n")


async def cmd_boards(args):
    """List available boards for a country."""
    from app.scraper.board_scraper import get_boards_for_country
    boards = get_boards_for_country(args.country.upper())
    print(f"\nBoards for {args.country.upper()}:")
    for b in boards:
        status = "[ON] " if b.get("enabled", True) else "[OFF]"
        print(f"  {status} {b['id']:20s} | rate={b.get('rate_limit',3)}s | pages={b.get('max_pages',2)} | json_ld={b.get('json_ld',False)}")
    print()


async def cmd_discover(args):
    """Run employer discovery via Overpass and print results."""
    from app.core.database import AsyncSessionLocal
    from app.scraper.discovery import discover_employers

    lat = args.lat
    lng = args.lng
    radius = args.radius
    categories = args.categories or ["food_cafe", "retail"]

    print(f"\nDiscovering employers near ({lat}, {lng}) within {radius}km")
    print(f"Categories: {categories}")

    async with AsyncSessionLocal() as db:
        employers = await discover_employers(lat, lng, radius, categories, db)

    print(f"\nFound {len(employers)} employers:")
    for e in employers:
        print(f"  [{e.category}] {e.name:30s} | {e.address[:40] if e.address else 'N/A':40s} | {e.website or 'no website'}")
    print()


async def cmd_find_careers(args):
    """Find the careers page for a given website."""
    from app.core.database import AsyncSessionLocal
    from app.scraper.careers_finder import find_careers_page

    async with AsyncSessionLocal() as db:
        url = await find_careers_page(args.website, db)

    if url:
        print(f"\n[FOUND] Careers page: {url}\n")
    else:
        print(f"\n[NOT FOUND] No careers page for {args.website}\n")


async def cmd_extract(args):
    """Extract jobs from a careers page URL."""
    from app.scraper.generic_extractor import extract_jobs

    jobs = await extract_jobs(args.url, follow_links=not args.no_follow)
    print(f"\nExtracted {len(jobs)} jobs from {args.url}:")
    for j in jobs:
        print(f"  {j.get('title','?'):40s} | {j.get('employer','?'):25s} | {j.get('job_type','?')}")
    print()


def main():
    parser = argparse.ArgumentParser(prog="python -m app.scraper.cli", description="JobBridge Scraper CLI")
    sub = parser.add_subparsers(dest="command")

    # run
    p_run = sub.add_parser("run", help="Scrape job boards")
    p_run.add_argument("--country", default="AU")
    p_run.add_argument("--source", help="Specific board ID (e.g. jora_au)")
    p_run.add_argument("--keyword", default="jobs")
    p_run.add_argument("--city", default="")
    p_run.add_argument("--limit", type=int, default=50)

    # boards
    p_boards = sub.add_parser("boards", help="List configured boards")
    p_boards.add_argument("--country", default="AU")

    # discover
    p_disc = sub.add_parser("discover", help="Discover employers via Overpass")
    p_disc.add_argument("--lat", type=float, required=True)
    p_disc.add_argument("--lng", type=float, required=True)
    p_disc.add_argument("--radius", type=float, default=10)
    p_disc.add_argument("--categories", nargs="+", default=["food_cafe", "retail"])

    # find-careers
    p_fc = sub.add_parser("find-careers", help="Find careers page for a website")
    p_fc.add_argument("website")

    # extract
    p_ex = sub.add_parser("extract", help="Extract jobs from a careers URL")
    p_ex.add_argument("url")
    p_ex.add_argument("--no-follow", action="store_true", help="Don't follow detail links")

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "boards":
        asyncio.run(cmd_boards(args))
    elif args.command == "discover":
        asyncio.run(cmd_discover(args))
    elif args.command == "find-careers":
        asyncio.run(cmd_find_careers(args))
    elif args.command == "extract":
        asyncio.run(cmd_extract(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
