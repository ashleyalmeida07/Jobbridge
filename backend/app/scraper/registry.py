"""
Scraper registry — maps scraper IDs to their classes.
Add new scrapers here once implemented.
"""
from app.scraper.sample_au import SampleAUScraper
from app.scraper.sample_us import SampleUSScraper

SCRAPER_REGISTRY = {
    "sample_au": SampleAUScraper,
    "sample_us": SampleUSScraper,
    # Real scrapers (not yet implemented — placeholders):
    # "seek_au": SeekAUScraper,
    # "gumtree_au": GumtreeAUScraper,
    # "indeed_us": IndeedUSScraper,
    # "reed_uk": ReedUKScraper,
    # "mcdonalds_au": McDonaldsAUScraper,
}


def get_scraper(scraper_id: str):
    """Return an instantiated scraper, or None if not registered."""
    cls = SCRAPER_REGISTRY.get(scraper_id)
    return cls() if cls else None
