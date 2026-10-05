"""
Tests for the generic job extractor (all 4 strategies) and normalisation utilities.

Run with:
    cd backend
    pytest tests/test_extractor.py -v
"""

import pathlib
import pytest
from datetime import datetime, timezone

# ── Fixture helpers ───────────────────────────────────────────────────────────

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════════
# Strategy 1: JSON-LD
# ══════════════════════════════════════════════════════════════════════════════

class TestJsonLdExtractor:
    def test_extracts_job_posting(self):
        from app.scraper.generic_extractor import extract_json_ld
        html = read_fixture("json_ld_page.html")
        jobs = extract_json_ld(html, "https://thecornercafe.com.au/careers")
        assert len(jobs) == 1
        j = jobs[0]
        assert "Barista" in j["title"]
        assert j["employer"] == "The Corner Café"
        assert "Melbourne" in j["location"]
        assert j["pay_min"] == 26.0
        assert j["pay_max"] == 28.0
        assert j["pay_period"] == "hourly"
        assert j["job_type"] == "part_time"
        assert "thecornercafe.com.au" in j["source_url"]

    def test_no_jobs_returns_empty(self):
        from app.scraper.generic_extractor import extract_json_ld
        html = read_fixture("no_jobs_page.html")
        jobs = extract_json_ld(html, "https://example.com/about")
        assert jobs == []

    def test_date_is_parsed(self):
        from app.scraper.generic_extractor import extract_json_ld
        html = read_fixture("json_ld_page.html")
        jobs = extract_json_ld(html, "")
        # posted_text set; actual datetime parsed in _finalise
        assert jobs[0]["posted_text"] == "2026-09-30"


# ══════════════════════════════════════════════════════════════════════════════
# Strategy 2: Embedded JSON
# ══════════════════════════════════════════════════════════════════════════════

class TestEmbeddedJsonExtractor:
    def test_extracts_next_data_jobs(self):
        from app.scraper.generic_extractor import extract_embedded_json
        html = read_fixture("embedded_json_page.html")
        jobs = extract_embedded_json(html, "https://fashionhub.com.au/careers")
        assert len(jobs) == 2

    def test_first_job_fields(self):
        from app.scraper.generic_extractor import extract_embedded_json
        html = read_fixture("embedded_json_page.html")
        jobs = extract_embedded_json(html, "")
        j = jobs[0]
        assert "Retail" in j["title"]
        assert "Fashion Hub" in j["employer"]
        assert "Sydney" in j["location"]

    def test_no_embedded_json_returns_empty(self):
        from app.scraper.generic_extractor import extract_embedded_json
        html = read_fixture("no_jobs_page.html")
        assert extract_embedded_json(html, "") == []


# ══════════════════════════════════════════════════════════════════════════════
# Strategy 3: Heuristic HTML
# ══════════════════════════════════════════════════════════════════════════════

class TestHeuristicHtmlExtractor:
    def test_extracts_job_cards(self):
        from app.scraper.generic_extractor import extract_heuristic_html
        html = read_fixture("html_list_page.html")
        jobs = extract_heuristic_html(html, "https://warehouseco.com.au/careers")
        assert len(jobs) >= 2

    def test_titles_extracted(self):
        from app.scraper.generic_extractor import extract_heuristic_html
        html = read_fixture("html_list_page.html")
        jobs = extract_heuristic_html(html, "https://warehouseco.com.au/careers")
        titles = [j["title"] for j in jobs]
        assert any("Picker" in t or "Forklift" in t or "Leader" in t for t in titles)

    def test_no_jobs_returns_empty(self):
        from app.scraper.generic_extractor import extract_heuristic_html
        html = read_fixture("no_jobs_page.html")
        jobs = extract_heuristic_html(html, "")
        assert jobs == []


# ══════════════════════════════════════════════════════════════════════════════
# Finalise / normalisation
# ══════════════════════════════════════════════════════════════════════════════

class TestFinalise:
    def test_dedupe_hash_generated(self):
        from app.scraper.generic_extractor import _finalise
        raw = [{"title": "Barista", "employer": "Café X", "location": "Melbourne", "source_url": "http://x.com"}]
        result = _finalise(raw, "Café X", "http://x.com")
        assert len(result) == 1
        assert len(result[0]["dedupe_hash"]) == 40

    def test_empty_title_skipped(self):
        from app.scraper.generic_extractor import _finalise
        raw = [{"title": "", "employer": "X", "location": "Y", "source_url": ""}]
        assert _finalise(raw, "X", "") == []

    def test_category_classified(self):
        from app.scraper.generic_extractor import _finalise
        raw = [{"title": "Barista Part-time", "employer": "Café", "location": "Sydney", "source_url": ""}]
        result = _finalise(raw, "Café", "")
        assert result[0]["category"] == "food_cafe"


# ══════════════════════════════════════════════════════════════════════════════
# Pay parser
# ══════════════════════════════════════════════════════════════════════════════

class TestPayParser:
    @pytest.mark.parametrize("text,expected_min,expected_max,expected_period", [
        ("$26–$28/hr",    26.0, 28.0, "hourly"),
        ("$30 per hour",  30.0, 30.0, "hourly"),
        ("AUD$70,000/yr", 70000.0, 70000.0, "yearly"),
        ("$1,200 p.w.",   1200.0, 1200.0, "weekly"),
        ("$800–$1,000 pw", 800.0, 1000.0, "weekly"),
        ("$23.50/hr",     23.5, 23.5, "hourly"),
        ("",              None, None, None),
    ])
    def test_parse_pay(self, text, expected_min, expected_max, expected_period):
        from app.scraper.normalise import parse_pay
        result = parse_pay(text)
        assert result.pay_min == expected_min
        assert result.pay_max == expected_max
        assert result.pay_period == expected_period


# ══════════════════════════════════════════════════════════════════════════════
# Date parser
# ══════════════════════════════════════════════════════════════════════════════

class TestDateParser:
    def test_today(self):
        from app.scraper.normalise import parse_posted_date
        result = parse_posted_date("today")
        assert result is not None
        assert (datetime.now(timezone.utc) - result).total_seconds() < 3600

    def test_days_ago(self):
        from app.scraper.normalise import parse_posted_date
        result = parse_posted_date("3 days ago")
        assert result is not None
        diff = (datetime.now(timezone.utc) - result).days
        assert 2 <= diff <= 4

    def test_absolute_date(self):
        from app.scraper.normalise import parse_posted_date
        result = parse_posted_date("01 October 2026")
        assert result is not None
        assert result.year == 2026 and result.month == 10 and result.day == 1

    def test_iso_date(self):
        from app.scraper.normalise import parse_posted_date
        result = parse_posted_date("2026-09-30")
        assert result is not None
        assert result.month == 9

    def test_empty_returns_none(self):
        from app.scraper.normalise import parse_posted_date
        assert parse_posted_date("") is None


# ══════════════════════════════════════════════════════════════════════════════
# Job type classifier
# ══════════════════════════════════════════════════════════════════════════════

class TestJobTypeClassifier:
    @pytest.mark.parametrize("title,expected", [
        ("Barista Part-Time",    "part_time"),
        ("Software Engineer Intern", "internship"),
        ("Casual Kitchen Hand",  "casual"),
        ("Store Manager Full-Time", "full_time"),
        ("Graduate Developer",   "full_time"),  # default
    ])
    def test_classify(self, title, expected):
        from app.scraper.normalise import classify_job_type
        assert classify_job_type(title) == expected


# ══════════════════════════════════════════════════════════════════════════════
# Category classifier
# ══════════════════════════════════════════════════════════════════════════════

class TestCategoryClassifier:
    @pytest.mark.parametrize("title,expected", [
        ("Barista",                "food_cafe"),
        ("Retail Sales Assistant", "retail"),
        ("Warehouse Picker",       "warehouse"),
        ("Private Maths Tutor",    "tutoring"),
        ("Software Engineer",      "professional"),
        ("Delivery Driver",        "delivery"),
        ("Campus Library Assistant","campus"),
    ])
    def test_classify(self, title, expected):
        from app.scraper.normalise import classify_category
        assert classify_category(title) == expected


# ══════════════════════════════════════════════════════════════════════════════
# Dedupe hash
# ══════════════════════════════════════════════════════════════════════════════

class TestDedupeHash:
    def test_same_inputs_same_hash(self):
        from app.scraper.normalise import make_dedupe_hash
        h1 = make_dedupe_hash("Café X", "Barista", "Melbourne")
        h2 = make_dedupe_hash("Café X", "Barista", "Melbourne")
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        from app.scraper.normalise import make_dedupe_hash
        h1 = make_dedupe_hash("Café X", "Barista", "Melbourne")
        h2 = make_dedupe_hash("Café X", "Barista", "Sydney")
        assert h1 != h2

    def test_case_insensitive(self):
        from app.scraper.normalise import make_dedupe_hash
        h1 = make_dedupe_hash("CAFÉ X", "BARISTA", "MELBOURNE")
        h2 = make_dedupe_hash("café x", "barista", "melbourne")
        assert h1 == h2

    def test_hash_length(self):
        from app.scraper.normalise import make_dedupe_hash
        assert len(make_dedupe_hash("a", "b", "c")) == 40


# ══════════════════════════════════════════════════════════════════════════════
# Careers page finder (homepage scan — no network)
# ══════════════════════════════════════════════════════════════════════════════

class TestCareersFinder:
    def test_finds_careers_link(self):
        from app.scraper.careers_finder import _find_career_links
        html = read_fixture("homepage_with_careers_link.html")
        links = _find_career_links(html, "https://greatcafe.com.au")
        assert any("careers" in url.lower() for url, _ in links)

    def test_confidence_text_match_is_high(self):
        from app.scraper.careers_finder import _find_career_links
        html = read_fixture("homepage_with_careers_link.html")
        links = _find_career_links(html, "https://greatcafe.com.au")
        assert links[0][1] >= 0.7

    def test_no_career_links_on_no_jobs_page(self):
        from app.scraper.careers_finder import _find_career_links
        html = read_fixture("no_jobs_page.html")
        links = _find_career_links(html, "https://genericco.com.au")
        assert links == []
