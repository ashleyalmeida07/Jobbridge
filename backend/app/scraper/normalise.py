"""
Normalisation utilities — pure rule-based, no AI.

Exported functions:
  parse_pay(text)          -> PayResult(min, max, period, text)
  classify_job_type(title, description) -> str
  classify_category(title, description) -> str
  parse_posted_date(text)  -> datetime | None
  extract_email(text)      -> str | None
  make_dedupe_hash(employer, title, location) -> str
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


# ── Pay parser ────────────────────────────────────────────────────────────────

@dataclass
class PayResult:
    pay_min: Optional[float]
    pay_max: Optional[float]
    pay_period: Optional[str]   # hourly | weekly | yearly | daily
    pay_text: str               # original text, cleaned


_CURRENCY_STRIP = re.compile(r"[A-Z]{0,3}\$|£|€|USD|AUD|GBP")
_RANGE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*[-–—to]+\s*(\d[\d,]*(?:\.\d+)?)")
_SINGLE = re.compile(r"(\d[\d,]*(?:\.\d+)?)")
_PERIOD_MAP = {
    r"p\.?\s?h|per\s+hour|/\s*hr|hourly": "hourly",
    r"p\.?\s?a|per\s+ann|per\s+year|yearly|annual|/\s*yr": "yearly",
    r"p\.?\s?w|per\s+week|weekly|/\s*wk":  "weekly",
    r"per\s+day|daily|/\s*day|p\.?\s?d":   "daily",
}


def parse_pay(text: str) -> PayResult:
    if not text:
        return PayResult(None, None, None, "")

    raw = text.strip()
    cleaned = _CURRENCY_STRIP.sub("", raw).strip()

    # Detect period
    period: Optional[str] = None
    for pattern, label in _PERIOD_MAP.items():
        if re.search(pattern, cleaned, re.IGNORECASE):
            period = label
            break
    # Default heuristic: if value > 500 assume yearly
    # (resolved after we extract the number)

    # Extract range or single value
    pay_min = pay_max = None
    m_range = _RANGE.search(cleaned)
    if m_range:
        pay_min = float(m_range.group(1).replace(",", ""))
        pay_max = float(m_range.group(2).replace(",", ""))
    else:
        m_single = _SINGLE.search(cleaned)
        if m_single:
            val = float(m_single.group(1).replace(",", ""))
            pay_min = pay_max = val

    # Default period heuristic
    if period is None and pay_min is not None:
        if pay_min > 5000:
            period = "yearly"
        elif pay_min > 100:
            period = "weekly"
        else:
            period = "hourly"

    return PayResult(pay_min=pay_min, pay_max=pay_max, pay_period=period, pay_text=raw)


# ── Job type classifier ───────────────────────────────────────────────────────

_JOB_TYPE_RULES = [
    ("internship", r"intern(?:ship)?|placement|work\s+experience|wex"),
    ("part_time",  r"part[\s-]time|pt\b|p\.t\."),
    ("casual",     r"casual|on[\s-]call|zero[\s-]hour|flexible\s+hour"),
    ("full_time",  r"full[\s-]time|ft\b|f\.t\.|permanent"),
]


def classify_job_type(title: str, description: str = "") -> str:
    combined = f"{title} {description}".lower()
    for jtype, pattern in _JOB_TYPE_RULES:
        if re.search(pattern, combined, re.IGNORECASE):
            return jtype
    return "full_time"  # conservative default


_CATEGORY_RULES = [
    ("food_cafe",     r"barista|caf[eé]|coffee|food\s*serv|kitchen|waiter|waitress|cook|chef|restaurant|fast\s*food|mcdonald|burger|subway|kfc|domino"),
    ("retail",        r"retail|cashier|sales\s*assist|shop\s*assist|store\s*assoc|customer\s*serv|woolworth|coles|aldi|target|kmart"),
    ("delivery",      r"deliver|courier|driver|doordash|uber\s*eat|menulog|rideshare"),
    ("tutoring",      r"tutor|teaching\s*assist|academic\s*support|private\s*lesson"),
    ("warehouse",     r"warehouse|picker|packer|forklift|logistics|distribution|supply\s*chain"),
    ("campus",        r"campus|library\s*assist|student\s*ambassador|research\s*assist|lab\s*assist|uni\s*job"),
    ("professional",  r"engineer|developer|analyst|accountant|nurse|doctor|lawyer|architect"),
]


def classify_category(title: str, description: str = "") -> str:
    combined = f"{title} {description}".lower()
    for cat, pattern in _CATEGORY_RULES:
        if re.search(pattern, combined, re.IGNORECASE):
            return cat
    return "other"


# ── Date parser ───────────────────────────────────────────────────────────────

_RELATIVE_PATTERNS = [
    (re.compile(r"just\s+now|today|this\s+morning", re.I), 0),
    (re.compile(r"yesterday", re.I), 1),
    (re.compile(r"(\d+)\s+hour", re.I), None),    # hours ago
    (re.compile(r"(\d+)\s+day",  re.I), None),    # days ago
    (re.compile(r"(\d+)\s+week", re.I), None),    # weeks ago
    (re.compile(r"(\d+)\s+month",re.I), None),    # months ago
]

_ABS_FORMATS = [
    "%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y",
    "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y",
]


def parse_posted_date(text: str) -> Optional[datetime]:
    if not text:
        return None
    text = text.strip()
    now = datetime.now(timezone.utc)

    # Relative dates
    for pattern, fixed_days in _RELATIVE_PATTERNS:
        m = pattern.search(text)
        if m:
            if fixed_days is not None:
                return now - timedelta(days=fixed_days)
            n = int(m.group(1))
            if "hour" in text.lower():
                return now - timedelta(hours=n)
            elif "week" in text.lower():
                return now - timedelta(weeks=n)
            elif "month" in text.lower():
                return now - timedelta(days=n * 30)
            else:
                return now - timedelta(days=n)

    # Absolute dates
    for fmt in _ABS_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


# ── Email extractor ───────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)


def extract_email(text: str) -> Optional[str]:
    if not text:
        return None
    m = _EMAIL_RE.search(text)
    return m.group(0).lower() if m else None


# ── Dedupe hash ───────────────────────────────────────────────────────────────

def make_dedupe_hash(employer: str, title: str, location: str) -> str:
    raw = f"{employer.lower().strip()}|{title.lower().strip()}|{location.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]
