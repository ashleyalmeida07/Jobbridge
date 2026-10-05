# Country-level configuration: visa types, default hour caps, and registered scraper IDs.
# Add a new country block to extend support; the scraper registry will only run scrapers
# whose IDs appear in the active country's "scrapers" list.

COUNTRY_CONFIG = {
    "AU": {
        "name": "Australia",
        "currency": "AUD",
        "visa_types": [
            {"code": "student_500", "label": "Student Visa (Subclass 500)"},
            {"code": "working_holiday_417", "label": "Working Holiday (Subclass 417)"},
            {"code": "tss_482", "label": "TSS Visa (Subclass 482)"},
            {"code": "other", "label": "Other"},
        ],
        # Default weekly hour caps: [term, break]
        "default_hour_caps": {
            "student_500": [48, None],  # 48 per fortnight = 24/wk term; None = unlimited break
            "working_holiday_417": [None, None],
            "tss_482": [None, None],
            "other": [None, None],
        },
        # Registered scraper IDs for this country
        "scrapers": ["seek_au", "gumtree_au", "sample_au"],
        # Brand career page scrapers (for "any field" jobs)
        "brand_scrapers": ["mcdonalds_au", "starbucks_au"],
    },
    "US": {
        "name": "United States",
        "currency": "USD",
        "visa_types": [
            {"code": "f1", "label": "F-1 Student Visa"},
            {"code": "j1", "label": "J-1 Exchange Visitor"},
            {"code": "opt", "label": "OPT (Optional Practical Training)"},
            {"code": "stem_opt", "label": "STEM OPT Extension"},
            {"code": "h1b", "label": "H-1B"},
            {"code": "other", "label": "Other"},
        ],
        "default_hour_caps": {
            "f1": [20, None],   # 20/wk term; unlimited during break
            "j1": [20, None],
            "opt": [None, None],
            "stem_opt": [None, None],
            "h1b": [None, None],
            "other": [None, None],
        },
        "scrapers": ["indeed_us", "sample_us"],
        "brand_scrapers": ["mcdonalds_us"],
    },
    "GB": {
        "name": "United Kingdom",
        "currency": "GBP",
        "visa_types": [
            {"code": "student_uk", "label": "UK Student Visa"},
            {"code": "graduate_route", "label": "Graduate Route"},
            {"code": "skilled_worker", "label": "Skilled Worker Visa"},
            {"code": "other", "label": "Other"},
        ],
        "default_hour_caps": {
            "student_uk": [20, None],
            "graduate_route": [None, None],
            "skilled_worker": [None, None],
            "other": [None, None],
        },
        "scrapers": ["reed_uk", "sample_uk"],
        "brand_scrapers": [],
    },
}

# Category → keyword mapping used by the search-plan builder
CATEGORY_KEYWORDS = {
    "food_cafe": ["barista", "cafe staff", "food service", "kitchen hand", "waiter", "waitress", "chef"],
    "retail": ["retail assistant", "sales assistant", "cashier", "shop assistant", "store associate"],
    "delivery": ["delivery driver", "courier", "rideshare driver", "food delivery"],
    "tutoring": ["tutor", "academic tutor", "online tutor", "private tutor"],
    "warehouse": ["warehouse", "picker", "packer", "forklift operator", "logistics"],
    "campus": ["campus job", "library assistant", "student ambassador", "research assistant"],
}

# Domain → keyword mapping for professional/intern searches
DOMAIN_KEYWORDS = {
    "Computer Science": ["software engineer", "developer", "data analyst", "it support", "intern software"],
    "Business": ["business analyst", "marketing", "finance intern", "operations", "admin"],
    "Nursing": ["registered nurse", "student nurse", "nursing assistant", "care worker"],
    "Hospitality": ["hotel", "front desk", "hospitality intern", "events assistant"],
    "Engineering": ["engineering intern", "mechanical", "civil", "electrical engineer"],
    "Education": ["teaching assistant", "teacher", "education intern", "tutor"],
    "Law": ["paralegal", "legal assistant", "law clerk", "intern law"],
    "Medicine": ["medical intern", "research assistant", "clinical assistant"],
    "Other": ["intern", "graduate", "assistant"],
}
