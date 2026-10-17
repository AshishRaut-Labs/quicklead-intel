# QuickLead Intel V6.6.4 - Publisher Trust Guardrails

import asyncio
import html as html_lib
import json
import os
import re
import urllib.parse
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="QuickLead Intel - Global Sales Intelligence Engine",
    version="6.6.4",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "QUICKLEAD_CORS_ORIGINS",
        "*",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HTTP
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Keep bulk scans conservative. Reliability matters more than shaving a few
# seconds off a 20-50 site run, especially on consumer DNS/network links.
BULK_SCAN_CONCURRENCY = 4
FETCH_RETRY_ROUNDS = 3
FETCH_RETRY_BACKOFF_SECONDS = (0.45, 1.0)


def build_http_timeout() -> httpx.Timeout:
    """Bound connection/pool waits without making normal pages too fragile."""
    return httpx.Timeout(
        25.0,
        connect=8.0,
        pool=5.0,
    )


def build_http_limits() -> httpx.Limits:
    """Avoid opening a large burst of sockets during bulk scans."""
    return httpx.Limits(
        max_connections=8,
        max_keepalive_connections=4,
        keepalive_expiry=10.0,
    )


def describe_http_error(exc: Exception) -> str:
    """Return a useful network error instead of only `ConnectError`."""
    parts: list[str] = []
    current: Optional[BaseException] = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen and len(parts) < 3:
        seen.add(id(current))
        label = current.__class__.__name__
        detail = clean_text(str(current))
        parts.append(f"{label}: {detail}" if detail else label)
        current = current.__cause__ or current.__context__

    return " <- ".join(parts)


class WebsiteFetchError(RuntimeError):
    """Network/access failure with a buyer-friendly classification."""

    def __init__(
        self,
        message: str,
        *,
        failure_type: str = "FETCH_FAILED",
        status: str = "Failed",
        diagnostic: str = "",
    ) -> None:
        super().__init__(message)
        self.failure_type = failure_type
        self.status = status
        self.diagnostic = diagnostic


# =========================================================
# REGEX / KEYWORDS
# =========================================================

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+\-]+"
    r"@"
    r"[A-Za-z0-9.\-]+"
    r"\.[A-Za-z]{2,}"
)

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
}

PLACEHOLDER_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "yourdomain.com",
    "yourwebsite.com",
    "website.com",
}

PLACEHOLDER_EMAIL_LOCAL_PARTS = {
    "example",
    "test",
    "user",
    "name",
    "yourname",
    "you",
    "john",
    "jane",
}

NON_CONTACT_EMAIL_LOCAL_PARTS = {
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "mailer-daemon",
}

# Telemetry / platform implementation addresses are not prospect contacts.
# Keep this deliberately conservative: only well-known machine-generated
# domains/patterns are filtered.
TECHNICAL_EMAIL_DOMAIN_SUFFIXES = {
    "wixpress.com",
    "sentry.io",
    "sentry-cdn.com",
}

BUSINESS_EMAIL_LOCAL_PARTS = {
    "info",
    "hello",
    "contact",
    "sales",
    "office",
    "admin",
    "support",
    "service",
    "services",
    "marketing",
    "team",
    "reception",
    "enquiry",
    "enquiries",
    "inquiry",
    "inquiries",
    "accounting",
    "rentals",
}

PHONE_CANDIDATE_REGEX = re.compile(
    r"""
    (?<!\d)
    (?:
        \+\d{1,3}[\s.\-()]*
    )?
    (?:\d[\s.\-()]*){7,15}
    (?!\d)
    """,
    re.VERBOSE,
)

# Explicit Indian international numbers.
# This is intentionally separate from the generic phone regex.
INDIA_PHONE_REGEX = re.compile(
    r"""
    (?<!\d)
    \+91
    [\s().-]*
    (?:\d[\s().-]*){10}
    (?!\d)
    """,
    re.VERBOSE,
)

INDIA_PHONE_WITHOUT_PLUS_REGEX = re.compile(
    r"""
    (?<!\d)
    91
    [\s().-]*
    (?:\d[\s().-]*){10}
    (?!\d)
    """,
    re.VERBOSE,
)

INDIA_LOCAL_MOBILE_REGEX = re.compile(
    r"""
    (?<!\d)
    (?:0[\s().-]*)?
    [6789]
    (?:[\s().-]*\d){9}
    (?!\d)
    """,
    re.VERBOSE,
)

CTA_KEYWORDS = [
    "book",
    "book now",
    "book a call",
    "schedule",
    "schedule a call",
    "demo",
    "request demo",
    "contact",
    "contact us",
    "get started",
    "start now",
    "buy now",
    "shop now",
    "request",
    "request quote",
    "request a quote",
    "get quote",
    "get a quote",
    "quote",
    "call",
    "call us",
    "learn more",
    "enquire",
    "enquiry",
    "inquire",
    "inquiry",
    "appointment",
    "reserve",
    "consultation",
    "consult",
    "talk to us",
    "get in touch",
    "send message",
]

CONVERSION_LINK_KEYWORDS = [
    "contact",
    "quote",
    "pricing",
    "price",
    "demo",
    "appointment",
    "booking",
    "book",
    "consultation",
    "estimate",
    "enquiry",
    "inquiry",
    "request",
    "schedule",
    "get in touch",
]

COMMERCIAL_KEYWORDS = [
    "services",
    "service",
    "solutions",
    "products",
    "product",
    "pricing",
    "quote",
    "request a quote",
    "contact us",
    "book",
    "appointment",
    "consultation",
    "case studies",
    "portfolio",
    "industries",
    "clients",
    "customers",
    "commercial",
    "enterprise",
    "manufacturer",
    "manufacturing",
    "agency",
    "consulting",
    "consultancy",
    "contractor",
    "construction",
    "law firm",
    "lawyer",
    "dentist",
    "clinic",
    "real estate",
    "property",
    "restaurant",
    "hotel",
    "ecommerce",
    "shop",
    "store",
    "software",
    "saas",
    "technology",
    "wholesale",
    "supplier",
    "dealer",
    "distributor",
    "engineering",
    "architect",
    "architecture",
    "accounting",
    "insurance",
    "finance",
    "logistics",
    "transport",
    "automotive",
    "education",
    "training",
]

BUSINESS_SCHEMA_TYPES = {
    "Organization",
    "Corporation",
    "LocalBusiness",
    "ProfessionalService",
    "Store",
    "Restaurant",
    "Hotel",
    "MedicalBusiness",
    "Dentist",
    "Attorney",
    "RealEstateAgent",
    "FinancialService",
    "Manufacturer",
    "SportsActivityLocation",
    "Airline",
    "EducationalOrganization",
    "GovernmentOrganization",
}

GENERIC_NAME_PATTERNS = {
    "home",
    "homepage",
    "home page",
    "landing page",
    "welcome",
    "welcome to",
    "official website",
    "official site",
    "website",
    "site",
    "company",
    "your company",
    "image",
    "logo",
    "banner",
    "picture",
    "photo",
    "graphic",
}

BUSINESS_NAME_NOISE = {
    "download",
    "download brochure",
    "download broucher",
    "brochure",
    "broucher",
    "read more",
    "learn more",
    "know more",
    "contact us",
    "contact",
    "get started",
    "start now",
    "book now",
    "book a call",
    "request quote",
    "request a quote",
    "get quote",
    "get a quote",
    "enquire",
    "enquiry",
    "inquire",
    "inquiry",
    "send message",
    "view details",
    "view more",
    "click here",
    "submit",
    "subscribe",
    "privacy policy",
    "cookie policy",
    "terms of use",
}

# Words which are frequently picked up from ordinary
# English sentences, image alt text or CTA copy.
INVALID_STANDALONE_NAME_WORDS = {
    "javascript",
    "she",
    "her",
    "hers",
    "he",
    "him",
    "his",
    "it",
    "this",
    "that",
    "what",
    "which",
    "who",
    "whom",
    "whose",
    "we",
    "you",
    "our",
    "your",
    "their",
    "they",
    "them",
    "us",
    "me",
    "my",
    "its",
    "the",
    "and",
    "or",
    "but",
    "for",
    "with",
    "from",
    "into",
    "onto",
    "about",
    "after",
    "before",
    "over",
    "under",
    "more",
    "less",
    "new",
    "best",
    "better",
    "great",
    "top",
    "leading",
    "trusted",
    "discover",
    "explore",
    "solutions",
    "services",
    "service",
    "products",
    "product",
    "professional",
    "professionals",
    "business",
    "businesses",
    "company",
    "companies",
    "page",
    "pages",
    "team",
    "welcome",
    "irresistible",
    "amazing",
    "awesome",
    "excellent",
    "perfect",
    "ultimate",
    "unbeatable",
    "powerful",
    "innovative",
    "premium",
    "quality",
    "smart",
    "simple",
    "effective",
    "affordable",
    "reliable",
    "modern",
    "creative",
    "beautiful",
    "special",
    "expert",
    "experts",
    "success",
    "results",
    "growth",
}

DESCRIPTIVE_NAME_WORDS = {
    "manufacturer",
    "manufacturing",
    "supplier",
    "suppliers",
    "solutions",
    "services",
    "service",
    "products",
    "product",
    "company",
    "business",
    "agency",
    "consulting",
    "consultancy",
    "construction",
    "engineering",
    "technology",
    "technologies",
    "software",
    "marketing",
    "digital",
    "law",
    "legal",
    "clinic",
    "dental",
    "dentist",
    "dentistry",
    "cpa",
    "accountant",
    "accounting",
    "hvac",
    "plumbing",
    "roofing",
    "restaurant",
    "hotel",
    "real estate",
    "property",
    "contractor",
    "wholesale",
    "distributor",
    "dealer",
    "india",
    "usa",
    "uk",
    "canada",
    "australia",
    "singapore",
    "dubai",
    "uae",
}

# Common Indian location / identity clues.
# These are intentionally supplemental, not authoritative by themselves.
INDIA_LOCATION_CLUES = {
    "india",
    "bharat",
    "new delhi",
    "delhi",
    "mumbai",
    "bombay",
    "pune",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "chennai",
    "kolkata",
    "calcutta",
    "ahmedabad",
    "surat",
    "vadodara",
    "baroda",
    "jaipur",
    "lucknow",
    "bhubaneswar",
    "bbsr",
    "cuttack",
    "rourkela",
    "patna",
    "ranchi",
    "noida",
    "gurugram",
    "gurgaon",
    "faridabad",
    "coimbatore",
    "kochi",
    "thiruvananthapuram",
    "visakhapatnam",
    "vizag",
    "nagpur",
    "indore",
    "mysore",
    "mysuru",
    "goa",
    "odisha",
    "orissa",
    "karnataka",
    "maharashtra",
    "gujarat",
    "tamil nadu",
    "telangana",
    "west bengal",
    "rajasthan",
    "kerala",
    "uttar pradesh",
    "uttarakhand",
    "bihar",
    "jharkhand",
    "punjab",
    "haryana",
    "madhya pradesh",
    "andhra pradesh",
    "pin code",
    "pincode",
    "gstin",
    "gst no",
    "gst number",
    "cin",
}

US_STATE_ABBREVIATIONS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}

US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "district of columbia",
}

COUNTRY_NAMES = {
    "india": "IN",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "america": "US",
    "united kingdom": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "canada": "CA",
    "australia": "AU",
    "new zealand": "NZ",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
    "portugal": "PT",
    "netherlands": "NL",
    "belgium": "BE",
    "switzerland": "CH",
    "austria": "AT",
    "ireland": "IE",
    "japan": "JP",
    "china": "CN",
    "singapore": "SG",
    "malaysia": "MY",
    "indonesia": "ID",
    "thailand": "TH",
    "philippines": "PH",
    "vietnam": "VN",
    "south korea": "KR",
    "korea": "KR",
    "united arab emirates": "AE",
    "uae": "AE",
    "saudi arabia": "SA",
    "qatar": "QA",
    "kuwait": "KW",
    "bahrain": "BH",
    "oman": "OM",
    "south africa": "ZA",
    "nigeria": "NG",
    "kenya": "KE",
    "ghana": "GH",
    "egypt": "EG",
    "brazil": "BR",
    "mexico": "MX",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
    "peru": "PE",
}

TLD_COUNTRY_MAP = {
    "uk": "GB",
    "de": "DE",
    "fr": "FR",
    "it": "IT",
    "es": "ES",
    "pt": "PT",
    "nl": "NL",
    "be": "BE",
    "ch": "CH",
    "at": "AT",
    "ie": "IE",
    "in": "IN",
    "au": "AU",
    "nz": "NZ",
    "ca": "CA",
    "us": "US",
    "ae": "AE",
    "sg": "SG",
    "jp": "JP",
    "cn": "CN",
    "br": "BR",
    "mx": "MX",
    "za": "ZA",
    "ng": "NG",
    "ke": "KE",
    "gh": "GH",
    "my": "MY",
    "id": "ID",
    "th": "TH",
    "ph": "PH",
    "vn": "VN",
    "kr": "KR",
    "sa": "SA",
    "qa": "QA",
    "kw": "KW",
    "bh": "BH",
    "om": "OM",
    "eg": "EG",
    "ar": "AR",
    "cl": "CL",
    "co": "CO",
    "pe": "PE",
}

COUNTRY_DIAL_CODES = {
    "US": "1",
    "CA": "1",
    "RU": "7",
    "EG": "20",
    "ZA": "27",
    "GR": "30",
    "NL": "31",
    "BE": "32",
    "FR": "33",
    "ES": "34",
    "HU": "36",
    "IT": "39",
    "RO": "40",
    "CH": "41",
    "AT": "43",
    "GB": "44",
    "DK": "45",
    "SE": "46",
    "NO": "47",
    "PL": "48",
    "DE": "49",
    "PE": "51",
    "MX": "52",
    "AR": "54",
    "BR": "55",
    "CL": "56",
    "CO": "57",
    "MY": "60",
    "AU": "61",
    "ID": "62",
    "PH": "63",
    "NZ": "64",
    "SG": "65",
    "TH": "66",
    "JP": "81",
    "KR": "82",
    "VN": "84",
    "CN": "86",
    "TR": "90",
    "IN": "91",
    "PK": "92",
    "LK": "94",
    "MM": "95",
    "IR": "98",
    "BD": "880",
    "TW": "886",
    "MV": "960",
    "LB": "961",
    "JO": "962",
    "SY": "963",
    "IQ": "964",
    "KW": "965",
    "SA": "966",
    "YE": "967",
    "OM": "968",
    "PS": "970",
    "AE": "971",
    "IL": "972",
    "BH": "973",
    "QA": "974",
    "BT": "975",
    "MN": "976",
    "NP": "977",
    "TJ": "992",
    "TM": "993",
    "AZ": "994",
    "GE": "995",
    "KG": "996",
    "UZ": "998",
    "NG": "234",
    "KE": "254",
    "GH": "233",
    "TZ": "255",
    "UG": "256",
    "ZM": "260",
    "ZW": "263",
    "NA": "264",
    "BW": "267",
    "MZ": "258",
    "MA": "212",
    "DZ": "213",
    "TN": "216",
    "LY": "218",
    "SN": "221",
    "CI": "225",
    "BF": "226",
    "NE": "227",
    "BJ": "229",
    "CM": "237",
    "AO": "244",
    "RW": "250",
    "ET": "251",
    "SO": "252",
    "DJ": "253",
    "BI": "257",
    "MG": "261",
    "MW": "265",
    "LS": "266",
    "SZ": "268",
    "KM": "269",
    "SC": "248",
    "MU": "230",
    "LR": "231",
    "SL": "232",
    "TG": "228",
    "GA": "241",
    "CG": "242",
    "CD": "243",
    "GQ": "240",
    "ER": "291",
    "EC": "593",
    "BO": "591",
    "PY": "595",
    "UY": "598",
    "CR": "506",
    "PA": "507",
    "GT": "502",
    "SV": "503",
    "HN": "504",
    "NI": "505",
}

COUNTRY_CURRENCY_MAP = {
    "US": ("USD", "$"),
    "CA": ("CAD", "C$"),
    "GB": ("GBP", "£"),
    "IN": ("INR", "₹"),
    "AU": ("AUD", "A$"),
    "NZ": ("NZD", "NZ$"),
    "SG": ("SGD", "S$"),
    "JP": ("JPY", "¥"),
    "CN": ("CNY", "¥"),
    "AE": ("AED", "د.إ"),
    "SA": ("SAR", "﷼"),
    "MY": ("MYR", "RM"),
    "BR": ("BRL", "R$"),
    "ZA": ("ZAR", "R"),
    "MX": ("MXN", "MX$"),
}

CURRENCY_SYMBOL_MAP = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "CAD": "C$",
    "AUD": "A$",
    "JPY": "¥",
    "CNY": "¥",
    "AED": "د.إ",
    "SAR": "﷼",
    "SGD": "S$",
    "NZD": "NZ$",
    "MYR": "RM",
    "BRL": "R$",
    "ZAR": "R",
    "MXN": "MX$",
}

INDICATIVE_USD_RATES = {
    "USD": 1.0,
    "CAD": 1.36,
    "GBP": 0.79,
    "INR": 88.0,
    "AUD": 1.51,
    "NZD": 1.68,
    "SGD": 1.29,
    "JPY": 157.0,
    "CNY": 7.18,
    "AED": 3.67,
    "SAR": 3.75,
    "MYR": 4.20,
    "BRL": 5.40,
    "ZAR": 17.20,
    "MXN": 18.50,
    "EUR": 0.86,
}


# =========================================================
# URL HELPERS
# =========================================================

def normalize_url(raw_url: str) -> str:
    """Return a safe first-choice HTTP(S) URL without doing network I/O."""

    value = clean_text(
        raw_url
    )

    if not value:
        return ""

    if value.lower().startswith(
        (
            "http://",
            "https://",
        )
    ):
        return value

    return f"https://{value}"


def build_url_candidates(
    raw_url: str,
) -> list[str]:
    """Build resilient http/https + www/non-www candidates."""

    value = clean_text(
        raw_url
    )

    if not value:
        return []

    has_explicit_scheme = bool(
        re.match(
            r"^https?://",
            value,
            flags=re.I,
        )
    )

    parse_target = (
        value
        if has_explicit_scheme
        else f"//{value}"
    )

    try:
        parsed = urllib.parse.urlparse(
            parse_target
        )
    except Exception:
        return [normalize_url(value)]

    host = clean_text(
        parsed.netloc
    ).lower()

    if not host:
        return [normalize_url(value)]

    host = host.split("@")[-1]

    path = parsed.path or ""
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    suffix = f"{path}{query}{fragment}"

    bare_host = host.removeprefix("www.")
    www_host = f"www.{bare_host}"

    explicit_scheme = (
        parsed.scheme.lower()
        if has_explicit_scheme
        else ""
    )

    candidates: list[str] = []

    def add(
        scheme: str,
        candidate_host: str,
    ) -> None:
        candidate = f"{scheme}://{candidate_host}{suffix}"
        if candidate not in candidates:
            candidates.append(candidate)

    if explicit_scheme in {
        "http",
        "https",
    }:
        add(explicit_scheme, host)
        add(
            explicit_scheme,
            bare_host if host.startswith("www.") else www_host,
        )

        alternate_scheme = (
            "http"
            if explicit_scheme == "https"
            else "https"
        )

        add(alternate_scheme, host)
        add(
            alternate_scheme,
            bare_host if host.startswith("www.") else www_host,
        )

    else:
        add("https", bare_host)
        add("https", www_host)
        add("http", bare_host)
        add("http", www_host)

    return candidates


def canonical_url_key(
    raw_url: str,
) -> str:
    """Deduplicate equivalent scheme/www variants in bulk input."""

    normalized = normalize_url(raw_url)

    if not normalized:
        return ""

    try:
        parsed = urllib.parse.urlparse(normalized)
        host = (
            parsed.netloc
            .lower()
            .split("@")[-1]
            .split(":")[0]
            .removeprefix("www.")
        )
        path = parsed.path.rstrip("/") or "/"
        return f"{host}{path}?{parsed.query}"
    except Exception:
        return normalized.casefold()


async def fetch_url_with_fallback(
    client: httpx.AsyncClient,
    raw_url: str,
) -> tuple[httpx.Response, list[str]]:
    """Fetch a site with URL fallback plus bounded transient-network retries.

    Each round tries HTTPS/HTTP and www/non-www variants. A second/third round
    is used only when we saw a transient connection/protocol/timeout failure.
    Normal 4xx responses are not retried endlessly.
    """

    candidates = build_url_candidates(raw_url)

    if not candidates:
        raise ValueError("A website URL is required.")

    attempts: list[str] = []
    failures: list[str] = []
    status_counts: dict[int, int] = {}
    timeout_failures = 0

    transient_errors = (
        httpx.ConnectError,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.WriteTimeout,
        httpx.PoolTimeout,
        httpx.RemoteProtocolError,
    )
    transient_statuses = {408, 425, 429, 500, 502, 503, 504}

    for round_index in range(FETCH_RETRY_ROUNDS):
        saw_transient_failure = False

        for candidate in candidates:
            if candidate not in attempts:
                attempts.append(candidate)

            try:
                response = await client.get(
                    candidate,
                    headers=HEADERS,
                )

                if response.status_code >= 400:
                    status_counts[response.status_code] = (
                        status_counts.get(response.status_code, 0) + 1
                    )
                    failures.append(
                        f"round {round_index + 1} {candidate} -> "
                        f"HTTP {response.status_code}"
                    )
                    if response.status_code in transient_statuses:
                        saw_transient_failure = True
                    continue

                return response, attempts

            except transient_errors as exc:
                saw_transient_failure = True
                if isinstance(
                    exc,
                    (
                        httpx.ConnectTimeout,
                        httpx.ReadTimeout,
                        httpx.WriteTimeout,
                        httpx.PoolTimeout,
                    ),
                ):
                    timeout_failures += 1
                failures.append(
                    f"round {round_index + 1} {candidate} -> "
                    f"{describe_http_error(exc)}"
                )

            except httpx.HTTPError as exc:
                failures.append(
                    f"round {round_index + 1} {candidate} -> "
                    f"{describe_http_error(exc)}"
                )

        # If most URL variants are explicitly refusing automated access,
        # retrying every variant for more rounds only makes a 50-site batch
        # slower without improving the result.
        blocked_attempts = (
            status_counts.get(401, 0)
            + status_counts.get(403, 0)
        )

        if blocked_attempts >= 3:
            break

        if not saw_transient_failure:
            break

        if round_index < FETCH_RETRY_ROUNDS - 1:
            backoff_index = min(
                round_index,
                len(FETCH_RETRY_BACKOFF_SECONDS) - 1,
            )
            await asyncio.sleep(
                FETCH_RETRY_BACKOFF_SECONDS[backoff_index]
            )

    # Keep diagnostics available for engineering while returning a concise,
    # buyer-friendly outcome to the UI/CSV.
    failure_summary = "; ".join(failures[-8:])
    blocked_attempts = (
        status_counts.get(401, 0)
        + status_counts.get(403, 0)
    )

    if blocked_attempts >= 2:
        raise WebsiteFetchError(
            "Site blocked automated access. Browser verification required.",
            failure_type="ACCESS_BLOCKED",
            status="Blocked",
            diagnostic=failure_summary,
        )

    if status_counts.get(429, 0):
        raise WebsiteFetchError(
            "Site rate-limited automated access. Retry later or verify in a browser.",
            failure_type="RATE_LIMITED",
            status="Blocked",
            diagnostic=failure_summary,
        )

    if timeout_failures and not status_counts:
        raise WebsiteFetchError(
            "Site did not respond within the scan timeout. Browser verification required.",
            failure_type="TIMEOUT",
            status="Failed",
            diagnostic=failure_summary,
        )

    raise WebsiteFetchError(
        "Unable to fetch the website after resilient URL fallback/retries.",
        failure_type="FETCH_FAILED",
        status="Failed",
        diagnostic=failure_summary,
    )


def get_domain(url: str) -> str:
    try:

        parsed = urllib.parse.urlparse(
            normalize_url(url)
        )

        return (
            parsed.netloc
            .lower()
            .split("@")[-1]
            .split(":")[0]
            .removeprefix("www.")
        )

    except Exception:
        return ""


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(
    value: Optional[str],
) -> str:

    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        html_lib.unescape(str(value)),
    ).strip()


def looks_like_non_brand_phrase(
    value: str,
) -> bool:
    """Reject short UI/review/sentence fragments that mimic brand names.

    Keep this rule pattern-based rather than site-specific so stress-test
    discoveries improve the general scanner instead of overfitting domains.
    """

    raw = clean_text(value)
    lowered = raw.casefold()

    if not lowered:
        return True

    # Generic product/category labels are not reliable company identities.
    generic_category_words = {
        "website",
        "web",
        "site",
        "builder",
        "scanner",
        "checker",
        "tool",
        "tools",
        "generator",
        "platform",
        "software",
        "service",
        "services",
        "solution",
        "solutions",
    }

    phrase_words = re.findall(
        r"[a-z0-9]+",
        lowered,
    )

    # Browser/runtime fallback messages are not brands.
    if re.search(
        r"\bjavascript\b.{0,30}\b(?:disabled|enable|enabled|required|support)\b",
        lowered,
    ):
        return True

    # Generic professional-role labels and service/location headings are not
    # business identities. These often appear as title fragments on SMB sites.
    if re.fullmatch(
        r"(?:tax|business|financial|accounting|marketing|legal|management)\s+"
        r"(?:consultant|consultants|advisor|advisors|firm|services?)",
        lowered,
    ):
        return True

    if (
        len(phrase_words) >= 3
        and phrase_words[0] in {
            "cpa", "accounting", "accountant", "dentist", "dentistry",
            "dental", "law", "lawyer", "attorney", "hvac", "plumbing",
            "roofer", "roofing", "clinic", "tax",
        }
        and re.search(r"\b(?:firm|services?|consultants?|advisors?)\b", lowered)
        and re.search(r"\b(?:in|near|serving)\b", lowered)
    ):
        return True

    if (
        1 <= len(phrase_words) <= 4
        and all(
            word in generic_category_words
            for word in phrase_words
        )
    ):
        return True

    # Marketing/product titles are descriptions, not company identities.
    if (
        re.match(
            r"^(?:free|online|best|top|leading)\b",
            lowered,
        )
        and re.search(
            r"\b(?:scanner|checker|tool|generator|builder|platform|"
            r"software|service|services|website|websites)\b",
            lowered,
        )
    ):
        return True

    # Multiple sentence-like fragments usually indicate a title + slogan,
    # not a clean business name.
    sentence_breaks = len(
        re.findall(
            r"[!?](?:\s|$)|\.(?:\s|$)",
            raw,
        )
    )

    if sentence_breaks >= 2:
        return True

    # Generic service/location title fragments are not reliable brands.
    # Examples: "CPA Austin", "Dentist Matthews", "HVAC Dallas".
    profession_heads = {
        "cpa",
        "accountant",
        "accounting",
        "dentist",
        "dentistry",
        "dental",
        "lawyer",
        "attorney",
        "plumber",
        "plumbing",
        "hvac",
        "roofer",
        "roofing",
        "clinic",
    }

    if (
        2 <= len(phrase_words) <= 4
        and phrase_words[0] in profession_heads
        and not re.search(
            r"\b(?:llc|pllc|inc|corp|ltd|company|group|associates?|partners?)\b",
            lowered,
        )
    ):
        return True

    # Slogan / sentence fragments should never receive high business-name
    # confidence simply because they appear in a title or heading.
    if (
        len(phrase_words) >= 4
        and re.search(r"\b(?:we|you|your|our|they|their|us)\b", lowered)
        and re.search(
            r"\b(?:make|makes|work|works|help|helps|find|finds|get|gets|"
            r"connect|connects|build|builds|grow|grows|save|saves|learn|"
            r"discover|see|start)\b",
            lowered,
        )
    ):
        return True

    if (
        len(phrase_words) >= 5
        and re.match(
            r"^(?:find|discover|see|learn|get|build|make|meet|experience|"
            r"unlock|start)\b",
            lowered,
        )
    ):
        return True

    # Navigation / content labels such as "Our team" or "Our Yelp profile".
    if re.match(
        r"^(?:our|your|their|my|this|that)\s+"
        r"(?:team|staff|profile|story|reviews?|services?|work|clients?|"
        r"customers?|company|practice|office|locations?|blog|gallery|"
        r"mission|values?|yelp|google|facebook|instagram|linkedin)\b",
        lowered,
    ):
        return True

    # Review/social-platform UI text is not the site's business identity.
    if re.search(
        r"\b(?:yelp|google|facebook|instagram|linkedin|tripadvisor|houzz)\b"
        r".{0,30}\b(?:profile|page|reviews?|listing)\b",
        lowered,
    ):
        return True

    # Short sentence fragments such as "Nick and Ivy." should not outrank
    # explicit title/header/footer business identity. Preserve legal-name
    # endings such as "Co." / "Inc." / "DDS.".
    words = re.findall(r"[a-z0-9&'’.-]+", lowered)
    has_terminal_sentence_punctuation = bool(
        re.search(r"[!?]$", raw)
        or (
            raw.endswith(".")
            and not re.search(
                r"\b(?:co|inc|corp|ltd|llc|pllc|pc|pa|dds|dmd)\.$",
                lowered,
            )
        )
    )

    if (
        has_terminal_sentence_punctuation
        and 2 <= len(words) <= 6
        and re.search(r"\b(?:and|we|you|our|your|their|his|her)\b", lowered)
    ):
        return True

    # Short slogan fragments such as "start to finish." can be captured by
    # visible-text brand regexes even though they are not business names.
    # Keep legal/business-looking names exempt from this sentence-fragment rule.
    if (
        has_terminal_sentence_punctuation
        and 2 <= len(words) <= 5
        and re.search(r"\b(?:to|from|with|for)\b", lowered)
        and not re.search(
            r"\b(?:llc|pllc|inc|corp|ltd|company|group|realty|dental|dentistry|"
            r"builders?|construction|contractors?|management|properties|services?)\b",
            lowered,
        )
    ):
        return True

    return False


def looks_generic_business_name(
    value: str,
) -> bool:

    text = clean_text(
        value
    ).lower()

    if not text:
        return True

    if len(text) < 2:
        return True

    if len(text) > 120:
        return True

    if text in GENERIC_NAME_PATTERNS:
        return True

    if text in BUSINESS_NAME_NOISE:
        return True

    if text in INVALID_STANDALONE_NAME_WORDS:
        return True

    # Punctuation-wrapped one-word fragments such as "me." or "she!"
    # are still UI/sentence noise, not business identities.
    standalone_token = re.sub(
        r"[^a-z0-9]+",
        "",
        text,
    )

    if (
        standalone_token
        and len(re.findall(r"[a-z0-9]+", text)) == 1
        and standalone_token in INVALID_STANDALONE_NAME_WORDS
    ):
        return True

    # SEO-style profession titles with multiple profession descriptors are
    # descriptions rather than identities, e.g. "Austin CPA Accounting Firm".
    profession_descriptor_hits = sum(
        1
        for token in {
            "cpa", "accounting", "accountant", "tax", "dental",
            "dentist", "dentistry", "law", "legal", "attorney",
            "hvac", "plumbing", "roofing", "clinic",
        }
        if re.search(rf"\b{re.escape(token)}\b", text)
    )

    if (
        profession_descriptor_hits >= 2
        and re.search(r"\b(?:firm|services?|consultants?|advisors?|practice)\b", text)
        and not re.search(
            r"\b(?:llc|pllc|llp|inc|corp|ltd|company|co\.?|group|associates?|partners?)\b",
            text,
        )
    ):
        return True

    # Concatenated responsive-menu labels are not company identities.
    # Example: "WG About Us Proven Process".
    navigation_phrases = (
        "about us",
        "proven process",
        "main menu",
        "menu toggle",
        "client portal",
        "contact us",
        "our services",
        "learn more",
        "read more",
        "get started",
    )

    navigation_hits = sum(
        1
        for phrase in navigation_phrases
        if phrase in text
    )

    if navigation_hits >= 2:
        return True

    if re.fullmatch(
        r"[\d\s.,+%/():\-]+",
        text,
    ):
        return True

    if not re.search(
        r"[a-zA-Z]",
        text,
    ):
        return True

    if looks_like_non_brand_phrase(value):
        return True

    action_words = [
        "download",
        "click",
        "submit",
        "view",
        "read",
        "learn",
        "contact",
        "request",
        "get",
        "book",
        "schedule",
        "subscribe",
        "enquire",
        "inquire",
    ]

    action_count = sum(
        1
        for word in action_words
        if re.search(
            rf"\b{re.escape(word)}\b",
            text,
        )
    )

    if action_count >= 2:
        return True

    if len(text.split()) > 8:
        return True

        # Reject sentence-like fragments that are unlikely to be
    # legitimate company names.
    sentence_fragment_words = {
        "a", "an", "the", "is", "are", "was", "were",
        "be", "been", "being", "to", "of", "in", "on",
        "at", "by", "for", "from", "with", "that", "this",
        "which", "who", "what", "how", "why", "when",
        "where", "can", "could", "will", "would", "should",
        "has", "have", "had", "do", "does", "did",
        "and", "or", "but", "as", "than", "into",
        "about", "more", "less", "not", "your", "our",
        "their", "its", "new", "all",
    }

    words = text.split()

    sentence_word_hits = sum(
        1
        for word in words
        if word in sentence_fragment_words
    )

    if len(words) >= 3 and sentence_word_hits >= 2:
        return True

    if len(words) >= 3 and words[-1] in {
        "that", "this", "which", "who", "what",
        "and", "or", "to", "of", "for", "with",
        "from", "in", "on", "at", "by", "as",
        "is", "are", "was", "were", "be",
    }:
        return True

    # A single ordinary English word is almost never
    # enough evidence to call something a company name.
    words = text.split()

    if (
        len(words) == 1
        and text in INVALID_STANDALONE_NAME_WORDS
    ):
        return True

    return False


def looks_like_agency_credit_element(
    element,
) -> bool:

    try:
        element_text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        parent = getattr(
            element,
            "parent",
            None,
        )

        parent_text = clean_text(
            parent.get_text(
                " ",
                strip=True,
            )
        ) if parent else ""

        context = (
            f"{element_text} {parent_text}"
        ).lower()

        return bool(
            re.search(
                r"\b(?:website|site|web(?:site)?\s+design|"
                r"web\s+development|marketing|seo|"
                r"powered|designed|developed|built|created)"
                r"\s+(?:by|from)\b",
                context,
                flags=re.I,
            )
        )

    except Exception:
        return False


def clean_business_name_candidate(
    value: str,
) -> str:

    value = clean_text(
        value
    )

    if not value:
        return ""

    # Normalize brand + marketing-descriptor titles such as
    # "Ahrefs—AI Marketing Platform" to the actual brand token.
    value = re.sub(
        r"\s*[—–]\s*(?:ai\s+)?(?:marketing|software|seo|sales|"
        r"commerce|business|customer|work|productivity)\s+"
        r"(?:platform|software|suite|tool|tools|solution|solutions)\b.*$",
        "",
        value,
        flags=re.I,
    ).strip()

    # Agency/website credits are not the client business name.
    # Reject the whole candidate instead of accidentally turning
    # "Website by Agency Name" into "Agency Name".
    if re.search(
        r"^(?:website|site|web(?:site)?\s+design|web\s+development|"
        r"marketing|seo|powered|designed|developed|built|created)\s+by\b",
        value,
        flags=re.I,
    ):
        return ""

    value = re.sub(
        r"\s*,?\s*(all rights reserved\.?).*$",
        "",
        value,
        flags=re.I,
    )

    value = re.sub(
        r"\s+(developed|designed|powered|created)\s+by\b.*$",
        "",
        value,
        flags=re.I,
    )

    value = re.split(
        r"\b(?:terms? of use|cookie policy|privacy policy|privacy)\b",
        value,
        maxsplit=1,
        flags=re.I,
    )[0]

    value = re.sub(
        r"\s*[|•·]\s*.*$",
        "",
        value,
    )

    value = re.sub(
        r"\s+[-–—:]\s+.*$",
        "",
        value,
    )

    value = re.sub(
        r"\b(?:download|read|learn|view)\s+"
        r"(?:the\s+)?(?:brochure|broucher|more|details?)\b.*$",
        "",
        value,
        flags=re.I,
    ).strip()

    value = re.sub(
        r"^[|•·,\-–—:\s]+",
        "",
        value,
    )

    value = re.sub(
        r"[|•·,\-–—:\s]+$",
        "",
        value,
    )

    return clean_text(
        value
    )


def name_quality(
    value: str,
) -> int:

    value = clean_business_name_candidate(
        value
    )

    if looks_generic_business_name(value):
        return 0

    lowered = value.lower()
    words = lowered.split()

    score = 50

    if 1 <= len(words) <= 6:
        score += 15

    if len(words) <= 3:
        score += 10

    if len(value) <= 40:
        score += 10

    for descriptive_word in DESCRIPTIVE_NAME_WORDS:

        if re.search(
            rf"\b{re.escape(descriptive_word)}\b",
            lowered,
        ):

            score -= 12

    if re.search(
        r"\b(india|usa|uk|canada|australia|"
        r"singapore|dubai|uae|germany|france)\b",
        lowered,
    ):

        score -= 15

    if len(value) > 70:
        score -= 20

    return max(
        0,
        min(
            100,
            score,
        ),
    )


def is_likely_descriptive_business_name(
    value: str,
) -> bool:

    cleaned = clean_business_name_candidate(
        value
    )

    if not cleaned:
        return True

    lowered = cleaned.lower()

    descriptive_hits = 0

    for word in DESCRIPTIVE_NAME_WORDS:

        if re.search(
            rf"\b{re.escape(word)}\b",
            lowered,
        ):

            descriptive_hits += 1

    return descriptive_hits >= 1


# =========================================================
# JSON-LD
# =========================================================

def iter_jsonld_objects(
    soup: BeautifulSoup,
) -> list[dict]:

    objects: list[dict] = []

    for script in soup.find_all(
        "script",
        attrs={
            "type": re.compile(
                r"application/ld\+json",
                re.I,
            )
        },
    ):

        raw = (
            script.string
            or script.get_text()
        )

        if not raw:
            continue

        try:

            parsed = json.loads(
                raw
            )

        except Exception:
            continue

        if isinstance(
            parsed,
            dict,
        ):

            objects.append(
                parsed
            )

            graph = parsed.get(
                "@graph"
            )

            if isinstance(
                graph,
                list,
            ):

                objects.extend(
                    item
                    for item in graph
                    if isinstance(
                        item,
                        dict,
                    )
                )

        elif isinstance(
            parsed,
            list,
        ):

            objects.extend(
                item
                for item in parsed
                if isinstance(
                    item,
                    dict,
                )
            )

    return objects


# =========================================================
# DOMAIN NAME INFERENCE
# =========================================================

def infer_business_name_from_domain(
    url_or_domain: str,
) -> str:

    value = clean_text(
        str(url_or_domain)
    ).lower()

    if not value:
        return ""

    if "://" in value:

        domain = get_domain(
            value
        )

    else:

        domain = (
            value
            .split("/")[0]
            .split(":")[0]
            .removeprefix("www.")
        )

    if not domain:
        return ""

    hostname = domain.split(
        "."
    )[0]

    if not hostname:
        return ""

    suffixes = [
        "manufacturing",
        "manufacturer",
        "engineering",
        "engineerings",
        "technology",
        "technologies",
        "solutions",
        "consulting",
        "consultancy",
        "construction",
        "contractor",
        "contractors",
        "distributor",
        "distributors",
        "wholesale",
        "supplier",
        "suppliers",
        "logistics",
        "software",
        "digital",
        "marketing",
        "services",
        "service",
        "dental",
        "dentist",
        "clinic",
        "hospital",
        "restaurant",
        "hotel",
        "realestate",
        "property",
        "finance",
        "financial",
        "insurance",
        "accounting",
        "cpa",
        "architect",
        "architecture",
        "automotive",
        "academy",
        "school",
        "education",
    ]

    normalized_hostname = re.sub(
        r"(?:group|company|corp|corporation|inc|ltd|limited|llc)$",
        "",
        hostname,
        flags=re.I,
    )

    words = re.split(
        r"[-_]+",
        normalized_hostname,
    )

    words = [
        word.strip()
        for word in words
        if word.strip()
    ]

    if len(words) == 1:

        original_word = words[0]

        for suffix in sorted(
            suffixes,
            key=len,
            reverse=True,
        ):

            if not original_word.endswith(
                suffix
            ):
                continue

            prefix = original_word[
                : -len(suffix)
            ]

            if not prefix:
                continue

            normalized_suffix = suffix

            if normalized_suffix == "engineerings":
                normalized_suffix = "engineering"

            elif normalized_suffix == "contractors":
                normalized_suffix = "contractor"

            elif normalized_suffix == "distributors":
                normalized_suffix = "distributor"

            elif normalized_suffix == "suppliers":
                normalized_suffix = "supplier"

            words = [
                prefix,
                normalized_suffix,
            ]

            break

        else:

            parts = re.findall(
                r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|\d+",
                original_word,
            )

            if parts:
                words = parts

    cleaned_words = []

    for word in words:

        word = re.sub(
            r"[^a-zA-Z0-9&'.’]+",
            "",
            word,
        )

        if not word:
            continue

        if (
            len(word) <= 3
            and word.isalpha()
        ):

            formatted = word.upper()

        else:

            formatted = word.capitalize()

        cleaned_words.append(
            formatted
        )

    if not cleaned_words:
        return ""

    result = " ".join(
        cleaned_words
    )

    if looks_generic_business_name(
        result
    ):
        return ""

    return result


def business_name_matches_domain(
    business_name: str,
    inferred_name: str,
) -> bool:

    current = clean_business_name_candidate(
        business_name
    ).casefold()

    inferred = clean_business_name_candidate(
        inferred_name
    ).casefold()

    if not current or not inferred:
        return False

    if current == inferred:
        return True

    current_words = set(
        re.findall(
            r"[a-z0-9]+",
            current,
        )
    )

    inferred_words = set(
        re.findall(
            r"[a-z0-9]+",
            inferred,
        )
    )

    if not current_words or not inferred_words:
        return False

    overlap = current_words.intersection(
        inferred_words
    )

    return bool(
        overlap
    )


def business_names_equivalent(
    left: str,
    right: str,
) -> bool:
    """Return True only when two names are effectively the same identity.

    Unlike business_name_matches_domain(), a single shared token is not enough.
    That distinction lets "Chicago" lose to "Fairy Cleaning Chicago" while
    still treating small punctuation/legal-suffix variants as equivalent.
    """

    def tokens(value: str) -> list[str]:
        cleaned = clean_business_name_candidate(
            value
        ).casefold()

        parts = re.findall(
            r"[a-z0-9]+",
            cleaned,
        )

        legal_noise = {
            "llc", "pllc", "inc", "corp", "corporation",
            "ltd", "limited", "co", "company", "pc", "pa",
        }

        return [
            part
            for part in parts
            if part not in legal_noise
        ]

    left_cleaned = clean_business_name_candidate(left).casefold().strip()
    right_cleaned = clean_business_name_candidate(right).casefold().strip()

    # Some businesses intentionally use the .com form as the brand.
    # Preserve that canonical spelling instead of treating it as a different
    # identity from the bare domain token.
    left_without_dotcom = re.sub(r"\.com$", "", left_cleaned)
    right_without_dotcom = re.sub(r"\.com$", "", right_cleaned)

    if (
        left_without_dotcom
        and right_without_dotcom
        and left_without_dotcom == right_without_dotcom
    ):
        return True

    left_tokens = tokens(left)
    right_tokens = tokens(right)

    if not left_tokens or not right_tokens:
        return False

    if left_tokens == right_tokens:
        return True

    left_compact = "".join(left_tokens)
    right_compact = "".join(right_tokens)

    if left_compact == right_compact:
        return True

    if min(len(left_tokens), len(right_tokens)) < 2:
        return False

    overlap = len(
        set(left_tokens).intersection(
            right_tokens
        )
    )

    shorter = min(
        len(set(left_tokens)),
        len(set(right_tokens)),
    )

    return bool(
        shorter
        and overlap / shorter >= 0.8
    )


def looks_like_seo_marketing_title(
    value: str,
) -> bool:
    normalized = clean_text(
        value
    ).casefold()

    if not normalized:
        return True

    if re.search(
        r"^(?:best|top|cheap|affordable|local|leading|expert|professional)\b",
        normalized,
    ):
        return True

    if re.search(
        r"\b(?:near me|services? in|service in|company in|contractors? in|dentist in|plumber in|hvac in)\b",
        normalized,
    ):
        return True

    return False


def title_identity_matches_domain(
    business_name: str,
    inferred_name: str,
) -> bool:
    """Return True when a title brand is plausibly encoded in the domain.

    This is deliberately conservative: the first meaningful title token must
    appear in the inferred domain identity, and at least two meaningful title
    tokens/stems should match. It protects cases such as
    "VIP Air Conditioning & Heating" vs "vipairheat" without letting
    generic SEO titles automatically beat the domain fallback.
    """

    title_words = [
        word
        for word in re.findall(
            r"[a-z0-9]+",
            clean_business_name_candidate(
                business_name
            ).casefold(),
        )
        if len(word) >= 3
    ]

    domain_compact = re.sub(
        r"[^a-z0-9]+",
        "",
        clean_business_name_candidate(
            inferred_name
        ).casefold(),
    )

    if not title_words or not domain_compact:
        return False

    def token_matches(word: str) -> bool:
        if word in domain_compact:
            return True

        if len(word) >= 5:
            return word[:4] in domain_compact

        return False

    first_token_matches = token_matches(
        title_words[0]
    )

    # One-word brands can legitimately be the entire domain identity
    # (for example, a brand like HomeScoutz).
    if (
        len(title_words) == 1
        and first_token_matches
    ):
        return True

    # Some SMB domains compress the brand plus descriptor initials, e.g.
    # "Omyra Property Management" -> "omyrapm". Treat that as domain
    # consensus without allowing an unrelated geo/service title to win.
    if first_token_matches and len(title_words) >= 2:
        trailing_initials = "".join(
            word[0]
            for word in title_words[1:]
            if word
        )
        if (
            len(trailing_initials) >= 2
            and trailing_initials in domain_compact
        ):
            return True

    # Other brands use initials for the whole visible name, e.g. a domain
    # like "hsrpm" can still strongly support "Home Spot Rentals".
    if len(title_words) >= 2:
        full_initials = "".join(
            word[0]
            for word in title_words
            if word
        )
        if (
            len(full_initials) >= 3
            and domain_compact.startswith(full_initials)
        ):
            return True

    if not first_token_matches:
        return False

    match_count = sum(
        1
        for word in title_words
        if token_matches(word)
    )

    return match_count >= 2


def strong_business_identity_matches_domain(
    business_name: str,
    inferred_name: str,
) -> bool:
    """Use strict brand/domain consensus when replacing an identity.

    The general token-overlap helper is useful elsewhere, but a single shared
    token (for example "WG") is not enough evidence to replace a business
    name with navigation or testimonial text.
    """

    if not business_name or not inferred_name:
        return False

    if business_names_equivalent(
        business_name,
        inferred_name,
    ):
        return True

    return title_identity_matches_domain(
        business_name,
        inferred_name,
    )


def extract_page_title_identity_candidate(
    soup: BeautifulSoup,
    inferred_domain_name: str = "",
) -> tuple[str, str, int]:

    if not soup.title:
        return (
            "",
            "unknown",
            0,
        )

    page_title = clean_text(
        soup.title.get_text()
    )

    if not page_title:
        return (
            "",
            "unknown",
            0,
        )

    normalized_title = page_title

    for separator in [
        " | ",
        " - ",
        " — ",
        " – ",
        " :: ",
        ": ",
    ]:
        normalized_title = normalized_title.replace(
            separator,
            " | ",
        )

    parts = [
        clean_text(part)
        for part in normalized_title.split(" | ")
        if clean_text(part)
    ]

    if not parts:
        parts = [page_title]

    candidates: list[tuple[str, str, int, int, int]] = []

    state_pattern = "|".join(
        sorted(
            US_STATE_ABBREVIATIONS
        )
    )

    for index, part in enumerate(parts):
        value = clean_business_name_candidate(
            part
        )
        word_count = len(
            value.split()
        )

        # Do not mistake a location-only title fragment such as
        # "Arlington, TX" for the business identity.
        if re.fullmatch(
            rf"[A-Za-z .'-]+,?\s+(?:{state_pattern})(?:\s+\d{{5}}(?:-\d{{4}})?)?",
            value,
            re.I,
        ):
            continue

        if not (
            2 <= len(value) <= 100
            and 1 <= word_count <= 9
            and name_quality(value) >= 45
            and not looks_generic_business_name(value)
            and not looks_like_seo_marketing_title(value)
        ):
            continue

        confidence = 90

        if word_count == 1:
            confidence = 76

        # The first title segment is commonly the actual brand name, but
        # domain-aligned brand text is stronger than an unrelated practitioner
        # or agency name. This helps cases such as:
        #   "Myles Williams, DDS | Atlanta Dental Arts"
        # where the site's domain clearly encodes the practice brand.
        position_bonus = (
            18
            if index == 0
            else 0
        )

        domain_bonus = (
            40
            if (
                inferred_domain_name
                and title_identity_matches_domain(
                    value,
                    inferred_domain_name,
                )
            )
            else 0
        )

        candidates.append(
            (
                value,
                "title_identity",
                confidence,
                position_bonus,
                domain_bonus,
            )
        )

    if candidates:
        candidates.sort(
            key=lambda item: (
                item[2] + item[3] + item[4],
                name_quality(item[0]),
                -len(item[0]),
            ),
            reverse=True,
        )
        best = candidates[0]
        return (
            best[0],
            best[1],
            best[2],
        )

    return (
        "",
        "unknown",
        0,
    )


def extract_meta_description_business_identity_candidate(
    soup: BeautifulSoup,
) -> tuple[str, str, int]:
    """Recover an explicit legal business name from the meta description.

    This is deliberately conservative: it only accepts a description prefix
    that ends in a legal/company suffix, e.g.
    "Meck Noonan & Co., LLC. is a full service accounting firm...".
    """

    tag = (
        soup.find(
            "meta",
            attrs={"name": re.compile(r"^description$", re.I)},
        )
        or soup.find(
            "meta",
            attrs={"property": re.compile(r"^og:description$", re.I)},
        )
    )

    if not tag:
        return ("", "unknown", 0)

    description = clean_text(str(tag.get("content") or ""))
    if not description:
        return ("", "unknown", 0)

    legal_suffix = (
        r"(?:LLC|L\.?L\.?C\.?|LLP|L\.?L\.?P\.?|PLLC|"
        r"Inc\.?|Incorporated|Corporation|Corp\.?|Company|Co\.?|"
        r"P\.?C\.?|Ltd\.?|Limited)"
    )

    match = re.match(
        rf"^(.{{2,100}}?\b{legal_suffix})(?=\s*\.?\s+(?:is|provides|offers|has|serves)\b|\s*$)",
        description,
        flags=re.I,
    )

    if not match:
        return ("", "unknown", 0)

    candidate = clean_business_name_candidate(match.group(1)).rstrip(" .,:;-")

    if (
        not candidate
        or looks_generic_business_name(candidate)
        or looks_like_non_brand_phrase(candidate)
        or name_quality(candidate) < 55
    ):
        return ("", "unknown", 0)

    return (candidate, "meta_description_identity", 90)


def business_identity_has_non_agency_visible_mention(
    soup: BeautifulSoup,
    business_name: str,
) -> bool:

    needle = clean_business_name_candidate(
        business_name
    ).casefold()

    if not needle:
        return False

    for element in soup.find_all(
        [
            "h1", "h2", "h3", "h4",
            "p", "span", "a", "strong", "b",
        ]
    ):
        text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        if needle not in text.casefold():
            continue

        if looks_like_agency_credit_element(
            element
        ):
            continue

        return True

    return False


def extract_visible_business_identity_candidate(
    soup: BeautifulSoup,
) -> tuple[str, str, int]:
    """Find a concise business identity that is visibly presented to users.

    This is used as a conflict guard when structured metadata names an agency
    or platform instead of the actual site owner.
    """

    candidates: list[tuple[str, str, int]] = []

    for tag_name in ["h1", "h2"]:
        for element in soup.find_all(tag_name)[:12]:
            value = clean_business_name_candidate(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if not value:
                continue

            word_count = len(
                value.split()
            )

            if not (
                2 <= len(value) <= 90
                and 1 <= word_count <= 8
                and name_quality(value) >= 45
                and not looks_generic_business_name(value)
                and not looks_like_seo_marketing_title(value)
            ):
                continue

            confidence = (
                92
                if tag_name == "h1"
                else 84
            )

            candidates.append(
                (
                    value,
                    f"visible_{tag_name}_identity",
                    confidence,
                )
            )

    if candidates:
        candidates.sort(
            key=lambda item: (
                item[2],
                name_quality(item[0]),
                -len(item[0]),
            ),
            reverse=True,
        )
        return candidates[0]

    return (
        "",
        "unknown",
        0,
    )



def extract_repeated_visible_business_identity_candidate(
    soup: BeautifulSoup,
) -> tuple[str, str, int]:
    """Recover a business identity from repeated/legal visible copy.

    Older SMB sites often use generic page titles while the actual business
    name appears in body/footer copy. This remains pattern-based rather than
    domain-specific.
    """

    scored: list[tuple[str, int]] = []

    legal_or_professional_suffix = (
        r"(?:LLC|L\.?L\.?C\.?|LLP|L\.?L\.?P\.?|PLLC|"
        r"Inc\.?|Incorporated|Corporation|Corp\.?|Company|Co\.?|"
        r"P\.?C\.?|Ltd\.?|Limited|CPA|CPAs|DDS|DMD)"
    )

    legal_pattern = re.compile(
        rf"\b([A-Z][A-Za-z0-9&.'’\-]*"
        rf"(?:\s+(?:&\s+)?[A-Z][A-Za-z0-9&.'’\-]*){{1,7}}"
        rf"\s*,?\s*{legal_or_professional_suffix})\b",
        re.I,
    )

    context_pattern = re.compile(
        r"\b(?:at|about|from|welcome\s+to)\s+"
        r"([A-Z][A-Za-z0-9&.'’\-]*(?:\s+[A-Z][A-Za-z0-9&.'’\-]*){1,5})"
        r"(?=\s*(?:,|\.|!|\?|\bis\b|\bwe\b|\bour\b|$))",
        re.I,
    )

    elements = soup.find_all(
        ["h1", "h2", "h3", "h4", "p", "li", "span", "strong", "b", "address", "footer"]
    )

    for element in elements[:500]:
        if looks_like_agency_credit_element(element):
            continue

        text_value = clean_text(element.get_text(" ", strip=True))
        if not text_value or len(text_value) > 600:
            continue

        for match in legal_pattern.finditer(text_value):
            candidate = clean_business_name_candidate(match.group(1)).rstrip(" .,:;-")
            if (
                candidate
                and not looks_generic_business_name(candidate)
                and not looks_like_non_brand_phrase(candidate)
                and name_quality(candidate) >= 55
            ):
                scored.append((candidate, 88))

        for match in context_pattern.finditer(text_value):
            candidate = clean_business_name_candidate(match.group(1)).rstrip(" .,:;-")
            if (
                candidate
                and not looks_generic_business_name(candidate)
                and not looks_like_non_brand_phrase(candidate)
                and not looks_like_seo_marketing_title(candidate)
                and name_quality(candidate) >= 55
            ):
                scored.append((candidate, 90))

    if not scored:
        return ("", "unknown", 0)

    counts: dict[str, int] = {}
    best_spelling: dict[str, str] = {}
    max_confidence: dict[str, int] = {}

    for candidate, confidence in scored:
        key = clean_business_name_candidate(candidate).casefold()
        counts[key] = counts.get(key, 0) + 1
        best_spelling.setdefault(key, candidate)
        max_confidence[key] = max(max_confidence.get(key, 0), confidence)

    best_key = max(
        counts,
        key=lambda key: (
            max_confidence[key] + min(8, (counts[key] - 1) * 3),
            name_quality(best_spelling[key]),
            -len(best_spelling[key]),
        ),
    )

    confidence = min(
        96,
        max_confidence[best_key] + min(6, (counts[best_key] - 1) * 2),
    )

    return (
        best_spelling[best_key],
        "repeated_visible_identity",
        confidence,
    )


def business_identity_has_primary_brand_evidence(
    soup: BeautifulSoup,
    business_name: str,
) -> bool:
    """Return True when an identity is presented in primary brand locations.

    Footer/agency mentions are deliberately excluded. A business name that only
    appears in a site-credit area should not beat a title/header/logo identity.
    """

    needle = clean_business_name_candidate(
        business_name
    ).casefold()

    if not needle:
        return False

    def contains_identity(value: str) -> bool:
        cleaned = clean_business_name_candidate(
            value
        ).casefold()

        return bool(
            cleaned
            and (
                needle == cleaned
                or needle in cleaned
                or cleaned in needle
            )
        )

    if soup.title and contains_identity(
        soup.title.get_text()
    ):
        return True

    for property_name in [
        "og:site_name",
        "application-name",
    ]:
        tag = (
            soup.find(
                "meta",
                attrs={
                    "property": property_name
                },
            )
            or soup.find(
                "meta",
                attrs={
                    "name": property_name
                },
            )
        )

        if tag and contains_identity(
            str(tag.get("content") or "")
        ):
            return True

    for element in soup.select(
        "header, nav, h1, h2, "
        "header [class*='logo'], header [class*='brand'], "
        "nav [class*='logo'], nav [class*='brand']"
    ):
        if looks_like_agency_credit_element(element):
            continue

        if contains_identity(
            element.get_text(" ", strip=True)
        ):
            return True

        for image in element.find_all("img"):
            for attribute_name in [
                "alt",
                "title",
                "aria-label",
            ]:
                if contains_identity(
                    str(
                        image.get(
                            attribute_name
                        )
                        or ""
                    )
                ):
                    return True

    return False



def business_identity_has_publisher_evidence(
    soup: BeautifulSoup,
    business_name: str,
) -> bool:
    """Return True only for publisher-level brand evidence.

    Body H1/H2 copy is intentionally excluded. Customer stories, case studies,
    campaign headings and article titles can contain real company names that do
    not own the scanned domain. Publisher evidence is limited to the document
    title/site metadata and header/navigation/logo regions.
    """

    needle = clean_business_name_candidate(business_name).casefold()

    if not needle:
        return False

    def contains_identity(value: str) -> bool:
        cleaned = clean_business_name_candidate(value).casefold()
        return bool(
            cleaned
            and (
                needle == cleaned
                or needle in cleaned
                or cleaned in needle
            )
        )

    if soup.title and contains_identity(soup.title.get_text(" ", strip=True)):
        return True

    for property_name in [
        "og:site_name",
        "application-name",
    ]:
        tag = (
            soup.find("meta", attrs={"property": property_name})
            or soup.find("meta", attrs={"name": property_name})
        )
        if tag and contains_identity(str(tag.get("content") or "")):
            return True

    for element in soup.select(
        "header, nav, "
        "header [class*='logo'], header [class*='brand'], "
        "nav [class*='logo'], nav [class*='brand'], "
        "[class*='site-logo'], [class*='brand-name']"
    ):
        if looks_like_agency_credit_element(element):
            continue

        if contains_identity(element.get_text(" ", strip=True)):
            return True

        for image in element.find_all("img"):
            for attribute_name in ["alt", "title", "aria-label"]:
                if contains_identity(str(image.get(attribute_name) or "")):
                    return True

    return False


def extract_domain_aligned_publisher_identity_candidate(
    soup: BeautifulSoup,
    inferred_domain_name: str,
) -> tuple[str, str, int]:
    """Recover the site owner from publisher-level brand signals.

    This is deliberately conservative and domain-aligned. It is used as a
    final guard against customer/case-study names or campaign headings taking
    over the prospect identity on content-heavy sites.
    """

    if not inferred_domain_name:
        return ("", "unknown", 0)

    candidates: list[tuple[str, str, int]] = []

    def add_candidate(value: str, source: str, confidence: int) -> None:
        cleaned = clean_business_name_candidate(value).rstrip(" .,:;-")
        if (
            not cleaned
            or looks_generic_business_name(cleaned)
            or looks_like_non_brand_phrase(cleaned)
            or not strong_business_identity_matches_domain(
                cleaned,
                inferred_domain_name,
            )
        ):
            return
        candidates.append((cleaned, source, confidence))

    for property_name, confidence in [
        ("og:site_name", 96),
        ("application-name", 95),
    ]:
        tag = (
            soup.find("meta", attrs={"property": property_name})
            or soup.find("meta", attrs={"name": property_name})
        )
        if tag:
            add_candidate(
                str(tag.get("content") or ""),
                "publisher_meta_identity",
                confidence,
            )

    if soup.title:
        page_title = clean_text(soup.title.get_text(" ", strip=True))
        title_parts = [page_title]
        for separator in [" | ", " - ", " — ", " – ", " :: ", ": "]:
            if separator in page_title:
                title_parts.extend(
                    clean_text(part)
                    for part in page_title.split(separator)
                    if clean_text(part)
                )
        for part in title_parts:
            if len(part) <= 100:
                add_candidate(part, "publisher_title_identity", 94)

    for element in soup.select(
        "header [class*='logo'], header [class*='brand'], "
        "nav [class*='logo'], nav [class*='brand'], "
        "[class*='site-logo'], [class*='brand-name']"
    ):
        if looks_like_agency_credit_element(element):
            continue
        add_candidate(
            element.get_text(" ", strip=True),
            "publisher_logo_identity",
            94,
        )
        for image in element.find_all("img"):
            for attribute_name in ["alt", "title", "aria-label"]:
                add_candidate(
                    str(image.get(attribute_name) or ""),
                    "publisher_logo_identity",
                    94,
                )

    # If the compact domain identity itself is visibly present in publisher
    # locations, it is safer than an unrelated customer/story/content entity.
    if business_identity_has_publisher_evidence(soup, inferred_domain_name):
        add_candidate(
            inferred_domain_name,
            "publisher_domain_identity",
            92,
        )

    if not candidates:
        return ("", "unknown", 0)

    candidates.sort(
        key=lambda item: (
            item[2],
            item[0].casefold().endswith(".com"),
            name_quality(item[0]),
            -len(item[0]),
        ),
        reverse=True,
    )
    return candidates[0]


def business_name_has_legal_or_professional_suffix(
    business_name: str,
) -> bool:
    cleaned = clean_business_name_candidate(business_name)
    return bool(
        re.search(
            r"\b(?:LLC|PLLC|LLP|Inc\.?|Corp\.?|Corporation|Ltd\.?|"
            r"Limited|Company|Co\.?|P\.?C\.?|CPA|CPAs|DDS|DMD)\b",
            cleaned,
            re.I,
        )
    )


def apply_publisher_identity_guard(
    soup: BeautifulSoup,
    business_name: str,
    business_name_source: str,
    business_name_confidence: int,
    inferred_domain_name: str,
    domain_name_is_valid: bool,
) -> tuple[str, str, int]:
    """Prefer domain-aligned publisher identity over unrelated page entities.

    This guard runs after the normal resolver. It intentionally does not replace
    legal/professional identities and it does not override a brand that already
    has publisher-level evidence of its own.
    """

    if not domain_name_is_valid:
        return business_name, business_name_source, business_name_confidence

    publisher_name, publisher_source, publisher_confidence = (
        extract_domain_aligned_publisher_identity_candidate(
            soup,
            inferred_domain_name,
        )
    )

    if not publisher_name:
        return business_name, business_name_source, business_name_confidence

    if business_names_equivalent(business_name, publisher_name):
        # Preserve canonical publisher spelling such as Booking.com when the
        # current identity is only the bare equivalent "Booking".
        if (
            publisher_name.casefold().endswith(".com")
            and not clean_text(business_name).casefold().endswith(".com")
        ):
            return (
                publisher_name,
                publisher_source,
                max(business_name_confidence, publisher_confidence),
            )
        return business_name, business_name_source, business_name_confidence

    if strong_business_identity_matches_domain(
        business_name,
        inferred_domain_name,
    ):
        return business_name, business_name_source, business_name_confidence

    if business_identity_has_publisher_evidence(soup, business_name):
        return business_name, business_name_source, business_name_confidence

    if business_name_has_legal_or_professional_suffix(business_name):
        return business_name, business_name_source, business_name_confidence

    return (
        publisher_name,
        publisher_source,
        max(92, publisher_confidence),
    )


def resolve_business_identity_conflict(
    soup: BeautifulSoup,
    business_name: str,
    business_name_source: str,
    business_name_confidence: int,
    inferred_domain_name: str,
    email_identity_name: str,
    domain_name_is_valid: bool,
    email_identity_is_valid: bool,
) -> tuple[str, str, int]:
    """Resolve agency/person metadata conflicts using visible site identity.

    A number of SMB sites publish JSON-LD for a developer, agency, doctor, or
    platform rather than the actual business brand. This guard only overrides
    when visible/title identity has stronger consensus with the site's domain
    or the structured identity is not genuinely visible outside agency credit.
    """

    visible_identity = extract_visible_business_identity_candidate(
        soup
    )
    title_identity = extract_page_title_identity_candidate(
        soup,
        inferred_domain_name,
    )
    repeated_identity = extract_repeated_visible_business_identity_candidate(
        soup
    )
    meta_identity = extract_meta_description_business_identity_candidate(
        soup
    )

    identity_candidates = [
        candidate
        for candidate in [
            visible_identity,
            title_identity,
            repeated_identity,
            meta_identity,
        ]
        if candidate[0]
    ]

    def identity_consensus_score(
        candidate: tuple[str, str, int],
    ) -> int:
        candidate_name, _source, confidence = candidate
        score = int(confidence)

        if (
            domain_name_is_valid
            and strong_business_identity_matches_domain(
                candidate_name,
                inferred_domain_name,
            )
        ):
            score += 28

        if (
            email_identity_is_valid
            and business_name_matches_domain(
                candidate_name,
                email_identity_name,
            )
        ):
            score += 22

        if len(candidate_name.split()) == 1:
            score -= 14

            # A lone visible/person-like word unrelated to the domain is
            # especially risky. Legitimate one-word brands such as Zoom and
            # Nike retain domain consensus and avoid this penalty.
            if (
                domain_name_is_valid
                and not strong_business_identity_matches_domain(
                    candidate_name,
                    inferred_domain_name,
                )
            ):
                score -= 30

        return score

    if not identity_candidates:
        return (
            business_name,
            business_name_source,
            business_name_confidence,
        )

    best_identity_candidate = max(
        identity_candidates,
        key=identity_consensus_score,
    )

    current_matches_domain = bool(
        domain_name_is_valid
        and strong_business_identity_matches_domain(
            business_name,
            inferred_domain_name,
        )
    )

    current_has_real_visible_mention = (
        business_identity_has_non_agency_visible_mention(
            soup,
            business_name,
        )
    )

    current_has_primary_brand_evidence = (
        business_identity_has_primary_brand_evidence(
            soup,
            business_name,
        )
    )

    structured_sources = {
        "json_ld_name",
        "json_ld_legalName",
        "json_ld_alternateName",
        "json_ld_brand",
        "json_ld_logo",
        "meta_site_identity",
        # page_brand can be polluted by footer phrases such as
        # "Website by Mindstorm". Only trust it over a strong title
        # when it has a genuine non-agency visible mention.
        "page_brand",
    }

    candidate_name, candidate_source, candidate_confidence = (
        best_identity_candidate
    )
    candidate_score = identity_consensus_score(
        best_identity_candidate
    )
    candidate_matches_domain = bool(
        domain_name_is_valid
        and strong_business_identity_matches_domain(
            candidate_name,
            inferred_domain_name,
        )
    )

    candidate_has_primary_brand_evidence = (
        business_identity_has_primary_brand_evidence(
            soup,
            candidate_name,
        )
    )

    should_override_identity = False

    current_tokens = re.findall(
        r"[a-z0-9]+",
        clean_business_name_candidate(business_name).casefold(),
    )
    candidate_tokens = re.findall(
        r"[a-z0-9]+",
        clean_business_name_candidate(candidate_name).casefold(),
    )

    current_is_unaligned_single_word = bool(
        len(current_tokens) == 1
        and domain_name_is_valid
        and not current_matches_domain
        and business_name_source not in {
            "json_ld_brand",
            "json_ld_legalName",
        }
    )

    candidate_is_stronger_primary_identity = bool(
        len(candidate_tokens) >= 2
        and candidate_confidence >= 86
        and not looks_generic_business_name(candidate_name)
        and (
            candidate_has_primary_brand_evidence
            or candidate_matches_domain
            or candidate_source in {
                "meta_description_identity",
                "repeated_visible_identity",
            }
        )
    )

    # Review/staff first names must not become the business when a stronger
    # multi-word title/header/legal identity is available.
    if (
        current_is_unaligned_single_word
        and candidate_is_stronger_primary_identity
    ):
        should_override_identity = True

    if (
        not should_override_identity
        and candidate_matches_domain
        and not current_matches_domain
        and candidate_score >= 105
    ):
        should_override_identity = True

    elif (
        not should_override_identity
        and business_name_source in structured_sources
        and not current_matches_domain
        and not current_has_real_visible_mention
        and candidate_score >= 88
    ):
        should_override_identity = True

    # A footer/agency-derived page brand can sometimes look like a real
    # visible mention even though it is not the client brand. If the current
    # identity has no title/header/logo evidence and another candidate does,
    # prefer the primary brand candidate. This protects against agency names
    # such as "Mindstorm" becoming the prospect identity.
    elif (
        business_name_source in {
            "page_brand",
            "meta_site_identity",
            "meta_application-name",
            "meta_publisher",
        }
        and not current_has_primary_brand_evidence
        and candidate_has_primary_brand_evidence
        and candidate_score >= 86
    ):
        should_override_identity = True

    # Domain/email inference is a fallback. A clean H1 identity visibly
    # presented as the site's primary brand should beat a guessed domain token
    # even when the brand is not encoded in the domain (for example legacy or
    # practitioner-owned domains).
    if (
        not should_override_identity
        and business_name_source in {
            "domain_inference",
            "domain_inference_verified",
            "email_domain_inference",
        }
        and candidate_source in {
            "visible_h1_identity",
            "repeated_visible_identity",
            "meta_description_identity",
        }
        and candidate_confidence >= 88
        and (
            candidate_source == "meta_description_identity"
            or candidate_has_primary_brand_evidence
            or business_identity_has_non_agency_visible_mention(
                soup,
                candidate_name,
            )
        )
        and not current_has_primary_brand_evidence
    ):
        should_override_identity = True

    if (
        should_override_identity
        and not business_names_equivalent(
            business_name,
            candidate_name,
        )
    ):
        return (
            candidate_name,
            candidate_source,
            min(
                96,
                max(
                    candidate_confidence,
                    86,
                ),
            ),
        )

    return (
        business_name,
        business_name_source,
        business_name_confidence,
    )


# =========================================================
# EMAIL DOMAIN IDENTITY
# =========================================================

def infer_business_name_from_email(
    email: str,
) -> str:

    value = clean_text(
        email
    ).lower()

    if "@" not in value:
        return ""

    domain = value.split(
        "@",
        1,
    )[1]

    return infer_business_name_from_domain(
        domain
    )


def is_generic_email_local_part(
    local_part: str,
) -> bool:

    normalized = clean_text(
        local_part
    ).lower()

    return normalized in {
        "info",
        "hello",
        "support",
        "sales",
        "contact",
        "office",
        "admin",
        "enquiry",
        "inquiry",
        "marketing",
        "care",
        "help",
        "service",
        "services",
        "hr",
        "jobs",
        "career",
        "careers",
    }


# =========================================================
# BUSINESS NAME
# =========================================================

def extract_business_name(
    soup: BeautifulSoup,
) -> tuple[str, str, int]:

    candidates: list[
        tuple[str, str, int]
    ] = []

    # -----------------------------------------------------
    # JSON-LD
    # -----------------------------------------------------

    for item in iter_jsonld_objects(
        soup
    ):

        schema_type = item.get(
            "@type"
        )

        if isinstance(
            schema_type,
            str,
        ):

            types = [
                schema_type
            ]

        elif isinstance(
            schema_type,
            list,
        ):

            types = [
                str(v)
                for v in schema_type
            ]

        else:

            types = []

        if not any(
            schema_type_value
            in BUSINESS_SCHEMA_TYPES
            for schema_type_value in types
        ):
            continue

        for field in [
            "name",
            "legalName",
            "alternateName",
        ]:

            value = item.get(
                field
            )

            if not isinstance(
                value,
                str,
            ):
                continue

            cleaned = clean_business_name_candidate(
                value
            )

            quality = name_quality(
                cleaned
            )

            if (
                quality >= 35
                and not looks_generic_business_name(
                    cleaned
                )
            ):

                confidence = (
                    92
                    if field == "alternateName"
                    else 95
                )

                if is_likely_descriptive_business_name(
                    cleaned
                ):

                    confidence -= 20

                candidates.append(
                    (
                        cleaned,
                        f"json_ld_{field}",
                        confidence,
                    )
                )

        brand = item.get(
            "brand"
        )

        if isinstance(
            brand,
            str,
        ):

            cleaned = clean_business_name_candidate(
                brand
            )

            quality = name_quality(
                cleaned
            )

            if (
                quality >= 40
                and not looks_generic_business_name(
                    cleaned
                )
            ):

                candidates.append(
                    (
                        cleaned,
                        "json_ld_brand",
                        96,
                    )
                )

        elif isinstance(
            brand,
            dict,
        ):

            brand_name = brand.get(
                "name"
            )

            if isinstance(
                brand_name,
                str,
            ):

                cleaned = clean_business_name_candidate(
                    brand_name
                )

                quality = name_quality(
                    cleaned
                )

                if (
                    quality >= 40
                    and not looks_generic_business_name(
                        cleaned
                    )
                ):

                    candidates.append(
                        (
                            cleaned,
                            "json_ld_brand",
                            98,
                        )
                    )

        logo = item.get(
            "logo"
        )

        if isinstance(
            logo,
            dict,
        ):

            logo_name = logo.get(
                "name"
            )

            if isinstance(
                logo_name,
                str,
            ):

                cleaned = clean_business_name_candidate(
                    logo_name
                )

                quality = name_quality(
                    cleaned
                )

                if (
                    quality >= 40
                    and not looks_generic_business_name(
                        cleaned
                    )
                ):

                    candidates.append(
                        (
                            cleaned,
                            "json_ld_logo",
                            88,
                        )
                    )

    # -----------------------------------------------------
    # Meta site identity
    # -----------------------------------------------------

    for property_name in [
        "og:site_name",
        "twitter:title",
    ]:

        tag = soup.find(
            "meta",
            attrs={
                "property": property_name
            },
        )

        if not tag:

            tag = soup.find(
                "meta",
                attrs={
                    "name": property_name
                },
            )

        if not tag:
            continue

        value = tag.get(
            "content"
        )

        if not isinstance(
            value,
            str,
        ):
            continue

        cleaned = clean_business_name_candidate(
            value
        )

        if (
            name_quality(cleaned) >= 45
            and not looks_generic_business_name(
                cleaned
            )
        ):

            confidence = 91

            if is_likely_descriptive_business_name(
                cleaned
            ):
                confidence = 74

            candidates.append(
                (
                    cleaned,
                    "meta_site_identity",
                    confidence,
                )
            )

    # -----------------------------------------------------
    # Page title identity
    #
    # A clean business-like title is stronger than a
    # guessed domain token. Domain inference remains a
    # fallback, not a replacement for explicit page identity.
    # -----------------------------------------------------

    page_title = ""

    if soup.title:
        page_title = clean_text(
            soup.title.get_text()
        )

    if page_title:
        title_parts: list[str] = []

        for separator in [
            " | ",
            " - ",
            " — ",
            " – ",
            " :: ",
            ": ",
        ]:
            if separator in page_title:
                title_parts.extend(
                    clean_text(part)
                    for part in page_title.split(separator)
                    if clean_text(part)
                )

        # If there was no separator, evaluate the whole title.
        if not title_parts:
            title_parts = [page_title]

        # Also evaluate the full title when it is concise. This
        # protects names such as "VIP Air Conditioning & Heating".
        if (
            page_title not in title_parts
            and len(page_title) <= 100
        ):
            title_parts.append(page_title)

        for part in title_parts:
            cleaned = clean_business_name_candidate(
                part
            )

            word_count = len(
                cleaned.split()
            )

            quality = name_quality(
                cleaned
            )

            if (
                2 <= len(cleaned) <= 100
                and 1 <= word_count <= 9
                and quality >= 45
                and not looks_generic_business_name(
                    cleaned
                )
                and not looks_like_seo_marketing_title(
                    cleaned
                )
            ):
                confidence = 86

                if word_count == 1:
                    confidence = 76

                if is_likely_descriptive_business_name(
                    cleaned
                ):
                    # Descriptive titles can still contain the real
                    # business name, but keep confidence conservative.
                    confidence = max(
                        78,
                        confidence - 6,
                    )

                candidates.append(
                    (
                        cleaned,
                        "title_identity",
                        confidence,
                    )
                )

    # -----------------------------------------------------
    # Explicit visible brand mentions
    # -----------------------------------------------------

    brand_candidates: list[str] = []

    brand_patterns = [
        re.compile(
            r"\b(?:about|welcome\s+to|at)\s+"
            r"([A-Z][A-Za-z0-9&.'’\-]*(?:\s+[A-Z][A-Za-z0-9&.'’\-]*){0,4})"
            r"(?=\s+(?:is|was|offers|provides|specializes|delivers|we\b)|[,.!?]|$)",
            re.I,
        ),
        re.compile(
            r"\b([A-Z][A-Za-z0-9&.'’\-]*(?:\s+[A-Z][A-Za-z0-9&.'’\-]*){0,4})\s+"
            r"(?:is|was|offers|provides|specializes|delivers)\b",
            re.I,
        ),
    ]

    for element in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "p",
            "strong",
            "b",
            "span",
        ]
    ):

        element_text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        if not element_text:
            continue

        if len(element_text) > 220:
            continue

        if looks_like_agency_credit_element(
            element
        ):
            continue

        for pattern in brand_patterns:

            for match in pattern.finditer(
                element_text
            ):

                candidate = clean_business_name_candidate(
                    match.group(1)
                )

                if (
                    candidate
                    and not looks_generic_business_name(
                        candidate
                    )
                    and name_quality(candidate) >= 40
                ):

                    brand_candidates.append(
                        candidate
                    )

    if brand_candidates:

        counts: dict[str, int] = {}

        for candidate in brand_candidates:

            key = candidate.casefold()

            counts[key] = (
                counts.get(
                    key,
                    0,
                )
                + 1
            )

        for candidate in set(
            brand_candidates
        ):

            occurrence_count = counts.get(
                candidate.casefold(),
                0,
            )

            confidence = 86

            if occurrence_count >= 3:
                confidence = 94

            elif occurrence_count >= 2:
                confidence = 91

            candidates.append(
                (
                    candidate,
                    "page_brand",
                    confidence,
                )
            )

    # -----------------------------------------------------
    # Image alt / title / aria-label
    #
    # This is deliberately lower confidence.
    # Image attributes frequently contain generic words.
    # -----------------------------------------------------

    for image in soup.find_all(
        "img"
    ):

        attributes = [
            image.get("alt"),
            image.get("title"),
            image.get("aria-label"),
        ]

        for raw_value in attributes:

            if not isinstance(
                raw_value,
                str,
            ):
                continue

            cleaned = clean_business_name_candidate(
                raw_value
            )

            if not (
                2
                <= len(cleaned)
                <= 80
            ):
                continue

            if looks_generic_business_name(
                cleaned
            ):
                continue

            if name_quality(cleaned) < 45:
                continue

            candidates.append(
                (
                    cleaned,
                    "image_brand",
                    70,
                )
            )

    # -----------------------------------------------------
    # Logo / header textual signals
    # -----------------------------------------------------

    logo_selectors = [
        "header .logo",
        "header .brand",
        "header [class*='logo']",
        "header [class*='brand']",
        "nav .logo",
        "nav .brand",
        "[class*='site-logo']",
        "[class*='brand-name']",
    ]

    for selector in logo_selectors:

        element = soup.select_one(
            selector
        )

        if not element:
            continue

        text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        cleaned = clean_business_name_candidate(
            text
        )

        if (
            2
            <= len(cleaned)
            <= 100
            and name_quality(cleaned)
            >= 45
            and not looks_generic_business_name(
                cleaned
            )
        ):

            candidates.append(
                (
                    cleaned,
                    "logo_or_brand",
                    90,
                )
            )

    # -----------------------------------------------------
    # itemprop name
    # -----------------------------------------------------

    for element in soup.select(
        '[itemprop="name"]'
    ):

        text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        cleaned = clean_business_name_candidate(
            text
        )

        if (
            name_quality(cleaned)
            >= 40
            and not looks_generic_business_name(
                cleaned
            )
        ):

            confidence = 85

            if is_likely_descriptive_business_name(
                cleaned
            ):

                confidence = 72

            candidates.append(
                (
                    cleaned,
                    "itemprop_name",
                    confidence,
                )
            )

    # -----------------------------------------------------
    # Meta application / publisher
    # -----------------------------------------------------

    for attr_name in [
        "application-name",
        "publisher",
    ]:

        tag = soup.find(
            "meta",
            attrs={
                "name": attr_name
            },
        )

        if not tag:
            continue

        value = tag.get(
            "content"
        )

        if isinstance(
            value,
            str,
        ):

            cleaned = clean_business_name_candidate(
                value
            )

            if (
                name_quality(cleaned)
                >= 40
                and not looks_generic_business_name(
                    cleaned
                )
            ):

                candidates.append(
                    (
                        cleaned,
                        f"meta_{attr_name}",
                        78,
                    )
                )

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------

    footer_candidates: list[
        tuple[str, int]
    ] = []

    for selector in [
        "footer",
        "[class*='footer']",
    ]:

        footer = soup.select_one(
            selector
        )

        if not footer:
            continue

        text = clean_text(
            footer.get_text(
                " ",
                strip=True,
            )
        )

        copyright_patterns = [
            r"(?:©|copyright)\s*(?:\d{4}\s*)?([^|•]+)",
            r"(?:©|copyright)\s*(?:\d{4}\s*)?([A-Za-z0-9&.,'’\- ]{2,80})",
        ]

        for pattern in copyright_patterns:

            matches = re.findall(
                pattern,
                text,
                re.I,
            )

            for match in matches:

                cleaned = clean_business_name_candidate(
                    match
                )

                if re.fullmatch(
                    r"[\d\s.,+%/():\-]+",
                    cleaned,
                ):
                    continue

                quality = name_quality(
                    cleaned
                )

                if (
                    cleaned
                    and quality >= 40
                    and not looks_generic_business_name(
                        cleaned
                    )
                ):

                    footer_candidates.append(
                        (
                            cleaned,
                            quality,
                        )
                    )

        for child in footer.find_all(
            [
                "a",
                "span",
                "div",
                "p",
            ],
        ):

            if looks_like_agency_credit_element(
                child
            ):
                continue

            child_text = clean_text(
                child.get_text(
                    " ",
                    strip=True,
                )
            )

            if not (
                2
                <= len(child_text)
                <= 80
            ):
                continue

            if re.fullmatch(
                r"[\d\s.,+%/():\-]+",
                child_text,
            ):
                continue

            cleaned = clean_business_name_candidate(
                child_text
            )

            if re.fullmatch(
                r"[\d\s.,+%/():\-]+",
                cleaned,
            ):
                continue

            quality = name_quality(
                cleaned
            )

            if (
                quality >= 55
                and not looks_generic_business_name(
                    cleaned
                )
            ):

                footer_candidates.append(
                    (
                        cleaned,
                        quality,
                    )
                )

    for candidate, quality in footer_candidates:

        candidates.append(
            (
                candidate,
                "footer",
                min(
                    80,
                    quality + 10,
                ),
            )
        )

    # -----------------------------------------------------
    # Choose strongest structured candidate.
    #
    # Image signals are intentionally weighted lower.
    # Ordinary one-word text signals are rejected.
    # -----------------------------------------------------

    if candidates:

        deduped: dict[
            str,
            tuple[str, str, int],
        ] = {}

        for candidate, source, confidence in candidates:

            candidate = clean_business_name_candidate(
                candidate
            )

            if looks_generic_business_name(
                candidate
            ):
                continue

            key = candidate.casefold()

            existing = deduped.get(
                key
            )

            if (
                existing is None
                or confidence > existing[2]
            ):

                deduped[key] = (
                    candidate,
                    source,
                    confidence,
                )

        ranked_candidates = list(
            deduped.values()
        )

        ranked_candidates.sort(
            key=lambda item: (
                item[2]
                + (
                    10
                    if item[1] == "json_ld_brand"
                    else 0
                )
                + (
                    8
                    if item[1] in {
                        "json_ld_name",
                        "json_ld_legalName",
                    }
                    else 0
                )
                + (
                    6
                    if item[1] in {
                        "page_brand",
                        "logo_or_brand",
                    }
                    and not is_likely_descriptive_business_name(
                        item[0]
                    )
                    else 0
                )
                + (
                    5
                    if item[1] == "title_identity"
                    else 0
                )
                - (
                    20
                    if item[1] == "image_brand"
                    else 0
                ),
                name_quality(item[0]),
                -len(item[0]),
            ),
            reverse=True,
        )

        if ranked_candidates:
            return ranked_candidates[0]

    # -----------------------------------------------------
    # Title fallback
    # -----------------------------------------------------

    title = ""

    if soup.title:

        title = clean_text(
            soup.title.get_text()
        )

    if title:

        separators = [
            " | ",
            " - ",
            " — ",
            " – ",
            " :: ",
            ": ",
        ]

        title_candidates: list[
            tuple[str, int]
        ] = []

        for separator in separators:

            parts = [
                clean_text(part)
                for part in title.split(
                    separator
                )
                if clean_text(part)
            ]

            if len(parts) >= 2:

                for part in parts:

                    cleaned = clean_business_name_candidate(
                        part
                    )

                    quality = name_quality(
                        cleaned
                    )

                    if (
                        quality >= 40
                        and not looks_generic_business_name(
                            cleaned
                        )
                    ):

                        title_candidates.append(
                            (
                                cleaned,
                                quality,
                            )
                        )

        if title_candidates:

            title_candidates.sort(
                key=lambda item: item[1],
                reverse=True,
            )

            candidate, quality = (
                title_candidates[0]
            )

            return (
                candidate,
                "title_inference",
                int(
                    min(
                        60,
                        quality,
                    )
                ),
            )

    return (
        "",
        "unknown",
        0,
    )


# =========================================================
# PHONE COUNTRY
# =========================================================

def get_phone_country(
    phone: str,
) -> Optional[str]:
    """Infer a country only from an explicit international phone prefix.

    Bare local numbers such as 404..., 704..., or 817... must never be
    interpreted as Romania (+40), Russia (+7), or another country merely
    because their first digits resemble a dial code.
    """

    value = clean_text(
        str(phone or "")
    ).strip()

    if not value:
        return None

    explicit_plus = value.startswith("+")
    explicit_00 = value.startswith("00")

    if not (explicit_plus or explicit_00):
        return None

    digits = re.sub(
        r"\D",
        "",
        value,
    )

    if explicit_00 and digits.startswith("00"):
        digits = digits[2:]

    if not digits:
        return None

    unique_codes = sorted(
        set(
            COUNTRY_DIAL_CODES.values()
        ),
        key=len,
        reverse=True,
    )

    for code in unique_codes:

        if digits.startswith(code):

            matches = [
                country
                for country, dial_code
                in COUNTRY_DIAL_CODES.items()
                if dial_code == code
            ]

            if matches:

                if code == "1":
                    return "US"

                return matches[0]

    return None


def is_plausible_phone_for_country(
    digits: str,
    country_hint: Optional[str],
) -> bool:

    if not digits:
        return False

    if len(set(digits)) == 1:
        return False

    if digits.startswith(
        (
            "000000",
            "111111",
            "123456",
            "999999",
        )
    ):
        return False

    if country_hint in {"US", "CA"}:

        local = digits

        if len(local) == 11 and local.startswith("1"):
            local = local[1:]

        if len(local) != 10:
            return False

        # NANP area/exchange codes do not begin with 0 or 1.
        return (
            local[0] in "23456789"
            and local[3] in "23456789"
        )

    if country_hint == "IN":

        if len(digits) == 10:
            return digits[0] in "6789"

        if (
            len(digits) == 12
            and digits.startswith("91")
        ):

            local = digits[2:]

            return (
                len(local) == 10
                and local[0] in "6789"
            )

        if (
            len(digits) == 11
            and digits.startswith("0")
        ):

            local = digits[1:]

            if (
                len(local) == 10
                and local[0] in "234"
            ):
                return True

        if (
            len(digits) == 12
            and digits.startswith("91")
        ):

            local = digits[2:]

            if (
                len(local) == 10
                and local[0] in "234"
            ):
                return True

        return False

    return 8 <= len(digits) <= 15


def normalize_phone_for_country(
    candidate: str,
    country_hint: Optional[str],
) -> Optional[str]:

    if not candidate:
        return None

    value = (
        candidate
        .replace("\xa0", " ")
        .strip()
    )

    digits = re.sub(
        r"\D",
        "",
        value,
    )

    if not (
        8
        <= len(digits)
        <= 15
    ):
        return None

    if len(set(digits)) == 1:
        return None

    if digits.startswith(
        (
            "000000",
            "111111",
            "123456",
            "999999",
        )
    ):
        return None

    has_plus = value.startswith(
        "+"
    )
    has_00_prefix = value.startswith(
        "00"
    )

    if has_plus or has_00_prefix:

        international_digits = digits

        if has_00_prefix and international_digits.startswith("00"):
            international_digits = international_digits[2:]

        detected_country = get_phone_country(
            f"+{international_digits}"
        )

        digits = international_digits

        if country_hint == "IN":

            if digits.startswith(
                "91"
            ):

                local = digits[2:]

                if (
                    len(local) == 10
                    and local[0] in "6789"
                ):
                    return f"+{digits}"

                if (
                    len(local) == 10
                    and local[0] in "234"
                ):
                    return f"+{digits}"

            return None

        if detected_country:
            return f"+{digits}"

        return None

    if country_hint:

        dial_code = COUNTRY_DIAL_CODES.get(
            country_hint
        )

        if dial_code:

            if (
                digits.startswith(
                    dial_code
                )
                and len(digits)
                >= len(dial_code) + 6
            ):

                if is_plausible_phone_for_country(
                    digits,
                    country_hint,
                ):

                    return f"+{digits}"

            if country_hint == "IN":

                local_digits = digits

                if local_digits.startswith(
                    "0"
                ):

                    local_digits = local_digits[1:]

                if (
                    len(local_digits) == 10
                    and local_digits[0] in "6789"
                ):

                    return (
                        f"+91{local_digits}"
                    )

                if (
                    len(local_digits) == 10
                    and local_digits[0] in "234"
                ):

                    return (
                        f"+91{local_digits}"
                    )

                return None

            local_digits = digits

            if (
                len(local_digits) >= 9
                and local_digits.startswith(
                    "0"
                )
            ):

                local_digits = local_digits.lstrip(
                    "0"
                )

            international = (
                dial_code
                + local_digits
            )

            if (
                9
                <= len(international)
                <= 15
                and is_plausible_phone_for_country(
                    international,
                    country_hint,
                )
            ):

                return (
                    f"+{international}"
                )

    # Without a country hint or explicit international prefix, keep only
    # plausible local-length numbers. Long bare digit strings are commonly
    # tracking IDs or a phone number accidentally merged with an address.
    if 7 <= len(digits) <= 11:
        return digits

    return None


def revalidate_phone_list_for_country(
    phones: list[str],
    country_hint: Optional[str],
) -> list[str]:
    """Remove numeric noise once strong locale evidence is available.

    US/CA/IN formats have strict enough rules to safely revalidate after the
    locale pass. Other countries retain the existing conservative behavior.
    """

    if country_hint not in {"US", "CA", "IN"}:
        return phones[:8]

    cleaned: list[str] = []
    seen: set[str] = set()

    for phone in phones:
        normalized = normalize_phone_for_country(
            phone,
            country_hint,
        )

        if not normalized:
            continue

        digits = re.sub(
            r"\D",
            "",
            normalized,
        )

        if not is_plausible_phone_for_country(
            digits,
            country_hint,
        ):
            continue

        if digits in seen:
            continue

        cleaned.append(normalized)
        seen.add(digits)

    return cleaned[:8]


# =========================================================
# PHONE EXTRACTION
# =========================================================

def extract_explicit_india_phones(
    html_content: str,
) -> list[str]:

    phones: list[str] = []
    seen: set[str] = set()

    # First: explicit +91 numbers. Require nearby contact semantics so
    # technical/script data containing +91-like digit runs cannot force an
    # otherwise US/UK/etc. site to India.
    for pattern in [
        INDIA_PHONE_REGEX,
    ]:

        for match in pattern.finditer(
            html_content
        ):

            candidate = clean_text(
                match.group(0)
            )

            context = html_lib.unescape(
                html_content[
                    max(0, match.start() - 140):
                    min(len(html_content), match.end() + 140)
                ]
            ).lower()

            if not re.search(
                r"(?:tel:|phone|mobile|telephone|call|whatsapp|contact)",
                context,
                re.I,
            ):
                continue

            normalized = normalize_phone_for_country(
                candidate,
                "IN",
            )

            if not normalized:
                continue

            digits = re.sub(
                r"\D",
                "",
                normalized,
            )

            if digits not in seen:

                phones.append(
                    normalized
                )

                seen.add(
                    digits
                )

    return phones


def looks_like_low_confidence_phone_candidate(
    candidate: str,
) -> bool:
    """Reject obvious dates/IDs/placeholders from free-text phone scans."""

    value = clean_text(candidate)
    digits = re.sub(r"\D", "", value)

    if not digits:
        return True

    if digits in {
        "0123456789", "1234567890", "9876543210", "0987654321",
        "123456789", "987654321",
    }:
        return True

    if re.search(r"(\d)\1{4,}", digits):
        return True

    # Bare short digit runs in ordinary page copy are more often dates,
    # counters or IDs than contact numbers. tel: links remain trusted.
    if value.isdigit() and 7 <= len(digits) <= 9:
        return True

    if len(digits) == 8 and value.isdigit():
        year_tail = int(digits[-4:])
        year_head = int(digits[:4])
        if 1900 <= year_tail <= 2100 or 1900 <= year_head <= 2100:
            return True

    return False


def extract_phone_numbers(
    soup: BeautifulSoup,
    html_content: str = "",
) -> list[str]:

    phones: list[str] = []
    seen_digits: set[str] = set()

    # -----------------------------------------------------
    # Strongest: explicit +91 numbers in raw HTML.
    # -----------------------------------------------------

    explicit_india_phones = (
        extract_explicit_india_phones(
            html_content
        )
        if html_content
        else []
    )

    for phone in explicit_india_phones:

        digits = re.sub(
            r"\D",
            "",
            phone,
        )

        if digits not in seen_digits:

            phones.append(
                phone
            )

            seen_digits.add(
                digits
            )

    # -----------------------------------------------------
    # tel: links
    # -----------------------------------------------------

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        href = clean_text(
            anchor.get(
                "href",
                "",
            )
        )

        if href.lower().startswith(
            "tel:"
        ):

            raw = urllib.parse.unquote(
                href[4:]
            ).strip()

            # A tel: attribute is strong contact evidence, but modern sites
            # sometimes place analytics IDs/dates in malformed tel links.
            # Reject bare 7-9 digit values and known placeholders before they
            # can enter the contact list; formatted or international numbers
            # continue through normal validation.
            if looks_like_low_confidence_phone_candidate(raw):
                continue

            normalized = normalize_phone_for_country(
                raw,
                None,
            )

            if normalized:

                digits = re.sub(
                    r"\D",
                    "",
                    normalized,
                )

                if digits not in seen_digits:

                    phones.append(
                        normalized
                    )

                    seen_digits.add(
                        digits
                    )

    # -----------------------------------------------------
    # Contact regions
    # -----------------------------------------------------

    contact_regions = []

    for selector in [
        "footer",
        "address",
        "#contact",
        "[id*='contact']",
        "[class*='contact']",
        "[class*='footer']",
        "[id*='footer']",
    ]:

        try:

            contact_regions.extend(
                soup.select(
                    selector
                )
            )

        except Exception:
            continue

    unique_region_ids = set()

    for region in contact_regions:

        region_id = id(
            region
        )

        if region_id in unique_region_ids:
            continue

        unique_region_ids.add(
            region_id
        )

        region_text = clean_text(
            region.get_text(
                " ",
                strip=True,
            )
        )

        if not region_text:
            continue

        for match in PHONE_CANDIDATE_REGEX.finditer(
            region_text
        ):

            candidate = clean_text(match.group(0))

            if looks_like_low_confidence_phone_candidate(candidate):
                continue

            normalized = normalize_phone_for_country(
                candidate,
                None,
            )

            if normalized:

                digits = re.sub(
                    r"\D",
                    "",
                    normalized,
                )

                if digits not in seen_digits:

                    phones.append(
                        normalized
                    )

                    seen_digits.add(
                        digits
                    )

    # -----------------------------------------------------
    # Visible text
    # -----------------------------------------------------

    visible_text = soup.get_text(
        " ",
        strip=True,
    )

    for match in PHONE_CANDIDATE_REGEX.finditer(
        visible_text
    ):

        candidate = clean_text(
            match.group(0)
        )

        raw_digits = re.sub(
            r"\D",
            "",
            candidate,
        )

        if looks_like_low_confidence_phone_candidate(candidate):
            continue

        if (
            len(raw_digits) >= 10
            and re.fullmatch(
                r"\d{10,15}",
                candidate,
            )
        ):

            context = visible_text[
                max(
                    0,
                    match.start() - 80,
                ):
                min(
                    len(visible_text),
                    match.end() + 80,
                )
            ]

            if not re.search(
                r"\b(?:phone|mobile|tel|telephone|"
                r"call|whatsapp|contact|sales|office)\b",
                context,
                re.I,
            ):
                continue

        normalized = normalize_phone_for_country(
            candidate,
            None,
        )

        if not normalized:
            continue

        digits = re.sub(
            r"\D",
            "",
            normalized,
        )

        if digits not in seen_digits:

            phones.append(
                normalized
            )

            seen_digits.add(
                digits
            )

    return phones[:12]


# =========================================================
# CONTACTS
# =========================================================

def is_platform_social_url(
    url: str,
) -> bool:
    """Reject known website-platform social accounts from prospect socials."""

    value = clean_text(url).lower()

    if not value:
        return True

    try:
        parsed = urllib.parse.urlparse(
            value
            if "://" in value
            else f"https://{value.lstrip('/')}"
        )
        host = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.lower().rstrip("/")
    except Exception:
        return False

    known_platform_accounts = {
        ("linkedin.com", "/company/wix-com"),
        ("linkedin.com", "/company/wix"),
        ("instagram.com", "/wixstudio"),
        ("instagram.com", "/wix"),
        ("facebook.com", "/wixstudio"),
        ("facebook.com", "/wix"),
    }

    return (host, path) in known_platform_accounts


def extract_contacts(
    soup: BeautifulSoup,
    html_content: str = "",
) -> tuple[list[str], dict]:

    phones = extract_phone_numbers(
        soup,
        html_content,
    )

    socials = {
        "linkedin": None,
        "twitter": None,
        "instagram": None,
        "facebook": None,
    }

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        original_href = clean_text(
            anchor.get(
                "href",
                "",
            )
        )

        href = original_href.lower()

        if (
            looks_like_agency_credit_element(
                anchor
            )
            or is_platform_social_url(
                original_href
            )
        ):
            continue

        if (
            "linkedin.com/company" in href
            or "linkedin.com/in/" in href
            or "linkedin.com/showcase/" in href
        ):

            socials["linkedin"] = (
                socials["linkedin"]
                or original_href
            )

        elif (
            (
                "twitter.com/" in href
                or "x.com/" in href
            )
            and "status" not in href
        ):

            socials["twitter"] = (
                socials["twitter"]
                or original_href
            )

        elif "instagram.com/" in href:

            socials["instagram"] = (
                socials["instagram"]
                or original_href
            )

        elif "facebook.com/" in href:

            socials["facebook"] = (
                socials["facebook"]
                or original_href
            )

    return phones, socials


# =========================================================
# EMAILS
# =========================================================

def is_technical_email_address(
    email: str,
) -> bool:

    clean = clean_text(
        email
    ).lower()

    if "@" not in clean:
        return True

    local_part, email_domain = clean.rsplit(
        "@",
        1,
    )

    if any(
        email_domain == suffix
        or email_domain.endswith(
            f".{suffix}"
        )
        for suffix in TECHNICAL_EMAIL_DOMAIN_SUFFIXES
    ):
        return True

    # Sentry/Wix telemetry commonly uses long hexadecimal local parts.
    if (
        len(local_part) >= 20
        and re.fullmatch(
            r"[a-f0-9]+",
            local_part,
        )
    ):
        return True

    # Retina/media asset filenames such as "video-name@2x.mp4" can be
    # misread by the email regex as an address. The local filename is not
    # predictable (hp-channels, claude-ai, etc.), so the pseudo-domain itself
    # is the reliable signal.
    if re.fullmatch(
        r"(?:1x|2x|3x|4x)\.(?:mp|mp4|webm|mov|m4v|png|jpe?g|gif|svg|webp)",
        email_domain,
    ):
        return True

    return False


def is_likely_vendor_email_address(
    email: str,
    site_domain: str,
) -> bool:
    """Reject obvious third-party website/platform support addresses.

    Only mismatched domains are considered. This keeps legitimate same-domain
    support@ addresses usable while preventing website-vendor contacts from
    becoming the preferred prospect email.
    """

    clean = clean_text(email).lower()
    site_domain = clean_text(site_domain).lower().removeprefix("www.")

    if "@" not in clean:
        return True

    local_part, email_domain = clean.rsplit("@", 1)

    if (
        site_domain
        and (
            email_domain == site_domain
            or email_domain.endswith(f".{site_domain}")
        )
    ):
        return False

    vendor_domain_hints = (
        "website",
        "websites",
        "webdesign",
        "web-design",
        "sitebuilder",
        "site-builder",
        "hosting",
        "webhost",
        "web-host",
        "webmaster",
    )

    vendor_local_parts = {
        "support",
        "webmaster",
        "accessibility",
        "privacy",
        "help",
    }

    return bool(
        local_part in vendor_local_parts
        and any(
            hint in email_domain
            for hint in vendor_domain_hints
        )
    )


def extract_emails(
    html_content: str,
) -> list[str]:

    candidates = EMAIL_REGEX.findall(
        html_content
    )

    emails: list[str] = []
    seen: set[str] = set()

    for email in candidates:

        clean = urllib.parse.unquote(email).strip().lower()

        if clean in seen:
            continue

        if clean.endswith(
            (
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".gif",
                ".svg",
                ".css",
                ".js",
            )
        ):
            continue

        if "@" not in clean:
            continue

        local_part, email_domain = clean.rsplit(
            "@",
            1,
        )

        if (
            local_part in PLACEHOLDER_EMAIL_LOCAL_PARTS
            or email_domain in PLACEHOLDER_EMAIL_DOMAINS
            or local_part in NON_CONTACT_EMAIL_LOCAL_PARTS
            or is_technical_email_address(clean)
        ):
            continue

        emails.append(
            clean
        )

        seen.add(
            clean
        )

    return emails[:8]


def score_email_for_outreach(
    email: str,
    site_domain: str,
) -> dict:

    clean = clean_text(
        email
    ).lower()

    if "@" not in clean:
        return {
            "email": clean,
            "score": 0,
            "same_domain": False,
            "role_address": False,
            "free_provider": False,
            "usable": False,
        }

    local_part, email_domain = clean.rsplit(
        "@",
        1,
    )

    site_domain = (
        clean_text(site_domain)
        .lower()
        .removeprefix("www.")
    )

    placeholder = (
        local_part in PLACEHOLDER_EMAIL_LOCAL_PARTS
        or email_domain in PLACEHOLDER_EMAIL_DOMAINS
        or local_part in NON_CONTACT_EMAIL_LOCAL_PARTS
        or is_technical_email_address(clean)
    )

    same_domain = bool(
        site_domain
        and (
            email_domain == site_domain
            or email_domain.endswith(
                f".{site_domain}"
            )
        )
    )

    role_address = (
        local_part in BUSINESS_EMAIL_LOCAL_PARTS
    )

    free_provider = (
        email_domain in FREE_EMAIL_DOMAINS
    )

    vendor_like = is_likely_vendor_email_address(
        clean,
        site_domain,
    )

    if placeholder or vendor_like:
        score = 0
    else:
        score = 35

        if same_domain:
            score += 35

        if role_address:
            score += 15

        if free_provider:
            score -= 5

        if len(local_part) >= 2:
            score += 5

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    return {
        "email": clean,
        "score": score,
        "same_domain": same_domain,
        "role_address": role_address,
        "free_provider": free_provider,
        "vendor_like": vendor_like,
        "usable": score >= 30,
    }


def build_contactability_signals(
    site_url: str,
    emails: list[str],
    phones: list[str],
    socials: dict,
    conversion_signals: dict,
    conversion_evidence: Optional[dict] = None,
) -> dict:

    site_domain = get_domain(
        site_url
    )

    email_profiles = [
        score_email_for_outreach(
            email,
            site_domain,
        )
        for email in emails
    ]

    usable_emails = [
        item
        for item in email_profiles
        if item.get(
            "usable"
        )
    ]

    preferred_email = ""
    best_email_score = 0

    if usable_emails:
        best_email = max(
            usable_emails,
            key=lambda item: int(
                item.get(
                    "score",
                    0,
                )
                or 0
            ),
        )

        preferred_email = clean_text(
            best_email.get(
                "email",
                "",
            )
        )

        best_email_score = int(
            best_email.get(
                "score",
                0,
            )
            or 0
        )

    score = round(
        best_email_score * 0.65
    )

    if phones:
        score += 20

    if conversion_signals.get(
        "has_form"
    ):
        score += 15

    if conversion_signals.get(
        "has_mailto"
    ):
        score += 5

    if conversion_signals.get(
        "has_whatsapp"
    ):
        score += 5

    if any(
        bool(value)
        for value in socials.values()
    ):
        score += 5

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    static_score = score

    has_static_contact_route = bool(
        preferred_email
        or phones
        or conversion_signals.get(
            "has_form"
        )
        or conversion_signals.get(
            "has_mailto"
        )
        or conversion_signals.get(
            "has_tel_link"
        )
        or conversion_signals.get(
            "has_whatsapp"
        )
    )

    evidence = (
        conversion_evidence
        if isinstance(
            conversion_evidence,
            dict,
        )
        else {}
    )

    unverified_missing = set(
        evidence.get(
            "unverified_missing",
            [],
        )
        or []
    )

    contact_path_unverified = (
        "contact_path"
        in unverified_missing
    )

    verification_required = (
        not has_static_contact_route
        or contact_path_unverified
    )

    # A low static score plus an unverified rendered contact path means
    # "not confirmed", not "this business is unreachable". Keep a neutral
    # baseline until a rendered browser check confirms absence.
    if verification_required:
        score = max(
            score,
            35,
        )
        level = "UNVERIFIED"
    elif score >= 60:
        level = "HIGH"
    elif score >= 35:
        level = "MEDIUM"
    else:
        level = "LOW"

    reasons: list[str] = []

    if preferred_email:
        reasons.append(
            "Usable public email detected"
        )

    if any(
        item.get(
            "same_domain"
        )
        for item in usable_emails
    ):
        reasons.append(
            "Business-domain email detected"
        )

    if phones:
        reasons.append(
            "Public phone detected"
        )

    if conversion_signals.get(
        "has_form"
    ):
        reasons.append(
            "Website contact form detected"
        )

    if contact_path_unverified:
        reasons.append(
            "Contact path is not confirmed in fetched HTML; rendered verification required"
        )

    if not reasons:
        reasons.append(
            "No reliable static contact route confirmed; rendered verification required"
        )

    return {
        "score": score,
        "static_score": static_score,
        "level": level,
        "verification_required": verification_required,
        "preferred_email": preferred_email or None,
        "email_ready": bool(preferred_email),
        "email_profiles": email_profiles[:8],
        "reasons": reasons[:6],
    }


def detect_template_residue(
    soup: BeautifulSoup,
    html_content: str,
) -> dict:

    visible_text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    ).lower()

    html_lower = html_content.lower()

    strong_patterns = {
        "Lorem ipsum placeholder copy": r"\blorem\s+ipsum\b",
        "Placeholder email: info@website.com": r"\binfo@website\.com\b",
        "Placeholder email: you@example.com": r"\byou@example\.com\b",
        "Placeholder email: john@example.com": r"\bjohn@example\.com\b",
        "Placeholder email: jane@example.com": r"\bjane@example\.com\b",
        "Placeholder domain reference": r"\b(?:example\.com|yourdomain\.com|yourwebsite\.com)\b",
    }

    weak_patterns = {
        "Template CTA: Send Brief": r"\bsend\s+brief\b",
        "Template CTA: Go to Shop": r"\bgo\s+to\s+shop\b",
        "Visible placeholder wording": r"\bplaceholder\s+(?:text|content|copy|image)\b",
        "Visible sample wording": r"\bsample\s+(?:text|content|copy)\b",
        "Generic 'Your Company' copy": r"\byour\s+company\b",
    }

    matches: list[str] = []
    strong_count = 0
    weak_count = 0

    for label, pattern in strong_patterns.items():
        if (
            re.search(
                pattern,
                visible_text,
                flags=re.I,
            )
            or re.search(
                pattern,
                html_lower,
                flags=re.I,
            )
        ):
            matches.append(
                label
            )
            strong_count += 1

    for label, pattern in weak_patterns.items():
        if re.search(
            pattern,
            visible_text,
            flags=re.I,
        ):
            matches.append(
                label
            )
            weak_count += 1

    severity_score = min(
        100,
        strong_count * 35
        + weak_count * 15,
    )

    if strong_count >= 1 or weak_count >= 2:
        level = "HIGH"
    elif weak_count == 1:
        level = "MEDIUM"
    else:
        level = "NONE"

    return {
        "template_residue_detected": bool(
            matches
        ),
        "template_residue_level": level,
        "template_residue_score": severity_score,
        "template_residue_count": len(
            matches
        ),
        "template_residue_matches": matches[:10],
    }


# =========================================================
# CONVERSION
# =========================================================

def extract_conversion_signals(
    soup: BeautifulSoup,
    html_lower: str,
) -> dict:

    form_count = len(
        soup.find_all("form")
    )

    has_form = (
        form_count > 0
    )

    has_whatsapp = (
        "wa.me/" in html_lower
        or "api.whatsapp.com" in html_lower
        or "whatsapp.com/" in html_lower
    )

    has_tel_link = any(
        str(
            anchor.get(
                "href",
                "",
            )
        )
        .lower()
        .startswith("tel:")
        for anchor in soup.find_all(
            "a",
            href=True,
        )
    )

    has_mailto = any(
        str(
            anchor.get(
                "href",
                "",
            )
        )
        .lower()
        .startswith("mailto:")
        for anchor in soup.find_all(
            "a",
            href=True,
        )
    )

    has_booking = False
    has_cta = False

    cta_examples: list[str] = []

    for tag in soup.find_all(
        [
            "a",
            "button",
            "input",
        ],
    ):

        text = (
            tag.get_text(
                " ",
                strip=True,
            )
            or tag.get(
                "value",
                "",
            )
            or tag.get(
                "aria-label",
                "",
            )
            or tag.get(
                "title",
                "",
            )
        )

        text = clean_text(
            text
        ).lower()

        if not text:
            continue

        if any(
            keyword in text
            for keyword in CTA_KEYWORDS
        ):

            has_cta = True

            if len(
                cta_examples
            ) < 6:

                cta_examples.append(
                    text[:100]
                )

        if any(
            keyword in text
            for keyword in [
                "book",
                "appointment",
                "schedule",
                "booking",
                "reserve",
                "calendar",
                "calendly",
            ]
        ):

            has_booking = True

    has_conversion_link = False

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        anchor_text = clean_text(
            anchor.get_text(
                " ",
                strip=True,
            )
        ).lower()

        href = clean_text(
            anchor.get(
                "href",
                "",
            )
        ).lower()

        combined = (
            f"{anchor_text} {href}"
        )

        if any(
            keyword in combined
            for keyword in CONVERSION_LINK_KEYWORDS
        ):

            has_conversion_link = True
            break

    return {
        "has_form": has_form,
        "form_count": form_count,
        "has_whatsapp": has_whatsapp,
        "has_tel_link": has_tel_link,
        "has_mailto": has_mailto,
        "has_booking": has_booking,
        "has_cta": has_cta,
        "has_conversion_link": has_conversion_link,
        "cta_examples": cta_examples,
    }


def build_conversion_evidence(
    conversion_signals: dict,
    emails: list[str],
    phones: list[str],
) -> dict:
    """Classify conversion findings by evidence quality.

    Positive findings in fetched HTML are confirmed. Negative findings
    for CTA/form/contact/booking are not treated as confirmed defects,
    because JavaScript-rendered widgets can be invisible to HTTP parsing.
    """

    has_contact_path = (
        bool(phones)
        or bool(emails)
        or bool(
            conversion_signals.get(
                "has_tel_link"
            )
        )
        or bool(
            conversion_signals.get(
                "has_mailto"
            )
        )
        or bool(
            conversion_signals.get(
                "has_whatsapp"
            )
        )
    )

    has_booking_path = (
        bool(
            conversion_signals.get(
                "has_conversion_link"
            )
        )
        or bool(
            conversion_signals.get(
                "has_booking"
            )
        )
    )

    checks = {
        "cta": bool(
            conversion_signals.get(
                "has_cta"
            )
        ),
        "form": bool(
            conversion_signals.get(
                "has_form"
            )
        ),
        "contact_path": has_contact_path,
        "booking_path": has_booking_path,
    }

    confirmed_present = [
        key
        for key, present in checks.items()
        if present
    ]

    unverified_missing = [
        key
        for key, present in checks.items()
        if not present
    ]

    status = (
        "CONFIRMED_PRESENT"
        if not unverified_missing
        else "RENDER_VERIFY"
    )

    return {
        "status": status,
        "confirmed_present": confirmed_present,
        "unverified_missing": unverified_missing,
        "render_verification_required": bool(
            unverified_missing
        ),
        "has_contact_path": has_contact_path,
        "has_booking_path": has_booking_path,
        "note": (
            "Missing CTA/form/contact/booking signals are unverified "
            "until the page is checked after JavaScript rendering."
            if unverified_missing
            else "Core conversion paths were confirmed in fetched HTML."
        ),
    }


# =========================================================
# TECHNICAL
# =========================================================

def extract_technical_signals(
    soup: BeautifulSoup,
    final_url: str,
) -> dict:

    viewport = soup.find(
        "meta",
        attrs={
            "name": re.compile(
                r"^viewport$",
                re.I,
            )
        },
    )

    canonical = soup.find(
        "link",
        rel=lambda value: (
            value
            and "canonical"
            in str(value).lower()
        ),
    )

    favicon = soup.find(
        "link",
        rel=lambda value: (
            value
            and "icon"
            in str(value).lower()
        ),
    )

    robots = soup.find(
        "meta",
        attrs={
            "name": re.compile(
                r"^robots$",
                re.I,
            )
        },
    )

    html_tag = soup.find(
        "html"
    )

    html_language = None

    if html_tag:

        raw_lang = html_tag.get(
            "lang"
        )

        if raw_lang:

            html_language = clean_text(
                raw_lang
            ).lower()

    return {
        "has_viewport": bool(
            viewport
        ),
        "has_favicon": bool(
            favicon
        ),
        "has_canonical": bool(
            canonical
        ),
        "has_robots_meta": bool(
            robots
        ),
        "html_language": html_language,
        "has_ssl": final_url.lower().startswith(
            "https://"
        ),
    }


# =========================================================
# COMMERCIAL SIGNALS
# =========================================================

def extract_business_signals(
    soup: BeautifulSoup,
    business_name: str,
    title: str,
) -> dict:

    visible_text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    ).lower()

    combined = (
        f"{business_name} "
        f"{title} "
        f"{visible_text[:30000]}"
    ).lower()

    commercial_matches: list[str] = []

    for keyword in COMMERCIAL_KEYWORDS:

        if keyword in combined:

            commercial_matches.append(
                keyword
            )

    internal_links: list[str] = []

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        text = clean_text(
            anchor.get_text(
                " ",
                strip=True,
            )
        )

        if text:

            internal_links.append(
                text.lower()
            )

    navigation_signals = 0

    for link_text in internal_links[:300]:

        if any(
            keyword in link_text
            for keyword in [
                "service",
                "product",
                "pricing",
                "quote",
                "contact",
                "solution",
                "portfolio",
                "case study",
                "appointment",
                "book",
                "about",
                "industries",
                "projects",
                "clients",
            ]
        ):
            navigation_signals += 1

    return {
        "commercial_keyword_count": len(
            set(
                commercial_matches
            )
        ),
        "commercial_keywords": list(
            dict.fromkeys(
                commercial_matches
            )
        )[:20],
        "commercial_navigation_signals": navigation_signals,
    }


# =========================================================
# LEAD TYPE
# =========================================================

def detect_lead_type(
    data: dict,
) -> tuple[str, str]:

    text_parts = [
        data.get(
            "business_name",
            "",
        ),
        data.get(
            "title",
            "",
        ),
    ]

    business_signals = data.get(
        "business_signals",
        {},
    )

    text_parts.extend(
        business_signals.get(
            "commercial_keywords",
            [],
        )
    )

    text = clean_text(
        " ".join(
            str(x)
            for x in text_parts
        )
    ).lower()

    if any(
        keyword in text
        for keyword in [
            "restaurant",
            "hotel",
            "dentist",
            "clinic",
            "salon",
            "plumber",
            "electrician",
            "roofing",
            "hvac",
            "lawyer",
            "attorney",
            "real estate",
            "property",
            "accounting",
        ]
    ):
        return (
            "LOCAL_SERVICE",
            "High",
        )

    if any(
        keyword in text
        for keyword in [
            "manufacturer",
            "manufacturing",
            "engineering",
            "supplier",
            "distributor",
            "wholesale",
            "logistics",
            "contractor",
            "construction",
            "industrial",
            "factory",
        ]
    ):
        return (
            "B2B",
            "High",
        )

    if any(
        keyword in text
        for keyword in [
            "shop",
            "store",
            "ecommerce",
            "e-commerce",
            "online store",
        ]
    ):
        return (
            "ECOMMERCE",
            "High",
        )

    if any(
        keyword in text
        for keyword in [
            "saas",
            "software",
            "technology",
            "app",
            "platform",
        ]
    ):
        return (
            "SOFTWARE_TECH",
            "Medium",
        )

    return (
        "PROFESSIONAL",
        "Medium",
    )


# =========================================================
# COUNTRY DETECTION
# =========================================================

def extract_country_names(
    text: str,
) -> list[str]:

    lowered = clean_text(
        text
    ).lower()

    found: list[str] = []

    for name, code in COUNTRY_NAMES.items():

        if re.search(
            rf"\b{re.escape(name)}\b",
            lowered,
        ):

            found.append(
                code
            )

    return list(
        dict.fromkeys(
            found
        )
    )


def detect_india_location_score(
    text: str,
) -> int:

    lowered = clean_text(
        text
    ).lower()

    hits = 0

    for clue in INDIA_LOCATION_CLUES:

        if re.search(
            rf"\b{re.escape(clue)}\b",
            lowered,
        ):

            hits += 1

    return min(
        4,
        hits,
    )


def detect_us_location_score(
    text: str,
) -> int:
    """Return strong US address evidence without guessing from phone digits."""

    normalized = clean_text(
        text
    )

    if not normalized:
        return 0

    score = 0

    state_pattern = "|".join(
        sorted(
            US_STATE_ABBREVIATIONS
        )
    )

    # Strong: state abbreviation immediately followed by a ZIP code.
    if re.search(
        rf"\b(?:{state_pattern})\s+\d{{5}}(?:-\d{{4}})?\b",
        normalized,
        re.I,
    ):
        score += 3

    # Strong: city-style comma + state abbreviation.
    if re.search(
        rf",\s*(?:{state_pattern})(?:\s+\d{{5}}(?:-\d{{4}})?)?\b",
        normalized,
        re.I,
    ):
        score += 2

    lowered = normalized.lower()

    if any(
        re.search(
            rf"\b{re.escape(state_name)}\b",
            lowered,
        )
        for state_name in US_STATE_NAMES
    ):
        score += 1

    return min(
        4,
        score,
    )


def normalize_country_value(
    value,
) -> Optional[str]:
    """Normalize JSON-LD/meta country values to an ISO-like 2-letter code."""

    if isinstance(value, dict):
        value = (
            value.get("name")
            or value.get("addressCountry")
            or value.get("@id")
        )

    if not isinstance(value, str):
        return None

    cleaned = clean_text(value)

    if not cleaned:
        return None

    upper = cleaned.upper()
    known_codes = set(TLD_COUNTRY_MAP.values()) | {
        "US", "GB", "CA", "AU", "NZ", "IN", "DE", "FR", "IT", "ES",
        "PT", "NL", "BE", "CH", "AT", "IE", "JP", "CN", "SG", "MY",
        "ID", "TH", "PH", "VN", "KR", "AE", "SA", "QA", "KW", "BH",
        "OM", "ZA", "NG", "KE", "GH", "EG", "BR", "MX", "AR", "CL",
        "CO", "PE",
    }

    if len(upper) == 2 and upper in known_codes:
        return upper

    lowered = cleaned.casefold()

    if lowered in COUNTRY_NAMES:
        return COUNTRY_NAMES[lowered]

    # Handle values such as "US-TX" or "en-US" conservatively.
    if re.fullmatch(r"[A-Za-z]{2}[-_][A-Za-z]{2,3}", cleaned):
        possible = cleaned.split("-")[-1].split("_")[-1].upper()
        if possible in known_codes:
            return possible

    return None


def extract_structured_country_candidates(
    soup: BeautifulSoup,
    local_only: bool = False,
) -> list[str]:
    """Extract country evidence from structured organization/address data.

    When local_only=True, only schemas that strongly describe a local/service
    business are considered. This keeps global Organization addresses from
    being mistaken for the visitor-facing market/country.
    """

    found: list[str] = []
    local_schema_types = {
        "LocalBusiness", "ProfessionalService", "Store", "Restaurant",
        "Hotel", "MedicalBusiness", "Dentist", "Attorney",
        "RealEstateAgent", "FinancialService", "Manufacturer",
        "SportsActivityLocation",
    }

    def item_types(item: dict) -> set[str]:
        raw = item.get("@type")
        if isinstance(raw, str):
            return {raw}
        if isinstance(raw, list):
            return {str(v) for v in raw}
        return set()

    def add_value(value) -> None:
        code = normalize_country_value(value)
        if code:
            found.append(code)

    def inspect_address(address) -> None:
        if isinstance(address, dict):
            add_value(address.get("addressCountry"))
        elif isinstance(address, list):
            for entry in address:
                inspect_address(entry)

    for item in iter_jsonld_objects(soup):
        if local_only and not item_types(item).intersection(local_schema_types):
            continue

        inspect_address(item.get("address"))

        location = item.get("location")
        if isinstance(location, dict):
            inspect_address(location.get("address"))

    return found


def detect_locale_signals(
    soup: BeautifulSoup,
    url: str,
    phones: Optional[list[str]] = None,
    html_content: str = "",
) -> dict:
    """Infer locale conservatively.

    v6.6 deliberately prefers Unknown over a confident but wrong country.
    Global websites often contain many hreflang regions, currencies and
    support phone numbers; those weak signals must not masquerade as a local
    business location.
    """

    html_tag = soup.find("html")
    language = None

    if html_tag:
        raw_lang = html_tag.get("lang")
        if raw_lang:
            language = clean_text(raw_lang).lower()

    language_country = None
    language_country_confidence = "None"

    if language and "-" in language:
        possible = language.rsplit("-", 1)[1].upper()
        if len(possible) == 2 and possible in set(TLD_COUNTRY_MAP.values()):
            language_country = possible
            language_country_confidence = "Weak"

    text = soup.get_text(" ", strip=True)
    combined_country_text = (
        f"{text} {html_content[:50000]}"
        if html_content
        else text
    )

    currency_patterns = {
        "USD": ["USD", "US$"],
        "EUR": ["EUR", "€"],
        "GBP": ["GBP", "£"],
        "INR": ["INR", "₹", "Rs.", "Rs ", "INR."],
        "CAD": ["CAD", "C$"],
        "AUD": ["AUD", "A$"],
        "JPY": ["JPY", "¥"],
        "CNY": ["CNY", "RMB"],
        "AED": ["AED"],
        "SAR": ["SAR"],
        "SGD": ["SGD", "S$"],
        "NZD": ["NZD", "NZ$"],
        "MYR": ["MYR", "RM "],
        "BRL": ["BRL", "R$"],
        "ZAR": ["ZAR"],
        "MXN": ["MXN"],
    }

    currency_hints: list[str] = []
    for currency, patterns in currency_patterns.items():
        if any(pattern in combined_country_text for pattern in patterns):
            currency_hints.append(currency)

    hostname = get_domain(url)
    tld = hostname.rsplit(".", 1)[1].lower() if "." in hostname else ""
    tld_country = TLD_COUNTRY_MAP.get(tld)

    explicit_countries = extract_country_names(
        combined_country_text[:70000]
    )
    explicit_country = (
        explicit_countries[0]
        if len(explicit_countries) == 1
        else None
    )

    structured_countries = extract_structured_country_candidates(soup)
    local_structured_countries = extract_structured_country_candidates(
        soup,
        local_only=True,
    )
    structured_country = None
    if structured_countries:
        counts: dict[str, int] = {}
        for country in structured_countries:
            counts[country] = counts.get(country, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        if len(ranked) == 1 or ranked[0][1] > ranked[1][1]:
            structured_country = ranked[0][0]

    structured_country_is_local = bool(
        structured_country
        and structured_country in set(local_structured_countries)
    )

    phone_countries: list[str] = []
    if phones:
        for phone in phones:
            country = get_phone_country(str(phone))
            if country:
                phone_countries.append(country)

    # Keep one source-level +91 clue if the normalized phone list missed it.
    # Do not multiply it or make India automatically win on global sites.
    html_india_phone_matches = (
        extract_explicit_india_phones(html_content)
        if html_content
        else []
    )
    if html_india_phone_matches and "IN" not in phone_countries:
        phone_countries.append("IN")

    phone_country = None
    phone_country_counts: dict[str, int] = {}
    for country in phone_countries:
        phone_country_counts[country] = phone_country_counts.get(country, 0) + 1

    if phone_country_counts:
        ranked_phones = sorted(
            phone_country_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        if len(ranked_phones) == 1:
            phone_country = ranked_phones[0][0]
        elif ranked_phones[0][1] > ranked_phones[1][1]:
            phone_country = ranked_phones[0][0]

    hreflang_countries: list[str] = []
    for link in soup.find_all("link", href=True):
        hreflang = link.get("hreflang")
        if not hreflang:
            continue
        hreflang = str(hreflang).lower()
        if "-" in hreflang:
            possible = hreflang.rsplit("-", 1)[1].upper()
            if len(possible) == 2 and possible in set(TLD_COUNTRY_MAP.values()):
                hreflang_countries.append(possible)

    unique_hreflang_countries = set(hreflang_countries)

    currency_country = {
        "USD": "US",
        "EUR": None,
        "GBP": "GB",
        "INR": "IN",
        "CAD": "CA",
        "AUD": "AU",
        "JPY": "JP",
        "CNY": "CN",
        "AED": "AE",
        "SAR": "SA",
        "SGD": "SG",
        "NZD": "NZ",
        "MYR": "MY",
        "BRL": "BR",
        "ZAR": "ZA",
        "MXN": "MX",
    }

    currency_country_candidates = {
        country
        for currency in currency_hints
        if (country := currency_country.get(currency))
    }

    # Many regional hreflangs/currencies/country mentions are a hallmark of a
    # global site. On those sites, a single support phone must not define the
    # company's country.
    global_locale_surface = bool(
        len(unique_hreflang_countries) >= 3
        or len(explicit_countries) >= 4
        or len(currency_country_candidates) >= 3
        or len(set(phone_countries)) >= 3
    )

    india_location_score = detect_india_location_score(
        combined_country_text[:70000]
    )
    us_location_score = detect_us_location_score(
        combined_country_text[:70000]
    )

    evidence: dict[str, int] = {}
    evidence_sources: dict[str, set[str]] = {}

    def add(country: Optional[str], weight: int, source: str) -> None:
        if not country or weight <= 0:
            return
        evidence[country] = evidence.get(country, 0) + weight
        evidence_sources.setdefault(country, set()).add(source)

    add(
        structured_country,
        120 if structured_country_is_local or not global_locale_surface else 25,
        "structured_local_country"
        if structured_country_is_local
        else "structured_country",
    )

    if us_location_score:
        add("US", 35 * us_location_score, "us_address")

    if india_location_score:
        add("IN", 25 * india_location_score, "india_location")

    add(tld_country, 55, "tld")

    if explicit_country:
        add(explicit_country, 55, "explicit_country")

    if phone_country:
        add(
            phone_country,
            25 if global_locale_surface else 65,
            "phone",
        )

    if len(currency_country_candidates) == 1:
        add(next(iter(currency_country_candidates)), 25, "currency")

    if len(unique_hreflang_countries) == 1:
        add(next(iter(unique_hreflang_countries)), 18, "hreflang")

    add(language_country, 6, "language")

    country_hint = None
    country_confidence = "Unknown"

    if evidence:
        winner = max(evidence, key=evidence.get)
        score = evidence[winner]
        sources = evidence_sources.get(winner, set())

        strong_local_sources = (
            {"structured_local_country", "tld"}
            if global_locale_surface
            else {
                "structured_local_country",
                "structured_country",
                "us_address",
                "india_location",
                "tld",
            }
        )

        # If this looks like a global site and the winner comes only from
        # weak regional/support signals, abstain instead of guessing.
        if global_locale_surface and not sources.intersection(strong_local_sources):
            winner = None
        else:
            country_hint = winner

            if (
                "structured_local_country" in sources
                or (
                    "structured_country" in sources
                    and not global_locale_surface
                )
                or (winner == "US" and us_location_score >= 2 and not global_locale_surface)
                or (winner == "IN" and india_location_score >= 2)
                or (score >= 100 and len(sources) >= 2)
            ):
                country_confidence = "High"
            elif score >= 55 and (
                len(sources) >= 2
                or "phone" in sources
                or "tld" in sources
            ):
                country_confidence = "Medium"
            else:
                country_confidence = "Low"

    primary_currency = None
    primary_currency_symbol = None
    currency_source = "unknown"

    country_currency = (
        COUNTRY_CURRENCY_MAP.get(country_hint)
        if country_hint
        else None
    )

    strong_country_currency_match = False
    if (
        country_hint
        and country_confidence in {"High", "Medium"}
        and country_currency
    ):
        expected_currency = country_currency[0]
        expected_country = currency_country.get(expected_currency)
        if expected_country == country_hint:
            strong_country_currency_match = True

    if strong_country_currency_match and country_currency:
        primary_currency, primary_currency_symbol = country_currency
        currency_source = "country_inferred"
    elif len(currency_hints) == 1:
        primary_currency = currency_hints[0]
        primary_currency_symbol = CURRENCY_SYMBOL_MAP.get(primary_currency)
        currency_source = "site_detected"
    elif country_currency:
        primary_currency, primary_currency_symbol = country_currency
        currency_source = "country_inferred"

    country_evidence = {
        "phone_country": phone_country,
        "structured_country": structured_country,
        "structured_country_is_local": structured_country_is_local,
        "explicit_country": explicit_country,
        "tld_country": tld_country,
        "language_country": language_country,
        "language_country_confidence": language_country_confidence,
        "us_location_score": us_location_score,
        "india_location_score": india_location_score,
        "global_locale_surface": global_locale_surface,
        "hreflang_country_count": len(unique_hreflang_countries),
    }

    return {
        "language": language,
        "country_hint": country_hint,
        "country_confidence": country_confidence,
        "country_evidence": country_evidence,
        "currency_hints": currency_hints[:8],
        "primary_currency": primary_currency,
        "primary_currency_symbol": primary_currency_symbol,
        "currency_source": currency_source,
    }


# =========================================================
# TECHNOLOGY
# =========================================================

def detect_tech_stack(
    html_lower: str,
) -> dict:

    return {
        "wordpress": (
            "wp-content" in html_lower
            or "wp-includes" in html_lower
            or "wordpress" in html_lower
        ),
        "shopify": (
            "cdn.shopify.com" in html_lower
            or "myshopify.com" in html_lower
            or "shopify.theme" in html_lower
        ),
        "nextjs": (
            "__next_data__" in html_lower
            or "/_next/static/" in html_lower
            or 'id="__next"' in html_lower
        ),
    }


# =========================================================
# TRACKERS
# =========================================================

def detect_trackers(
    html_lower: str,
) -> dict:

    return {
        "google_analytics": (
            "google-analytics.com"
            in html_lower
            or "gtag("
            in html_lower
            or "gtag.js"
            in html_lower
            or "google-analytics"
            in html_lower
        ),
        "facebook_pixel": (
            "connect.facebook.net"
            in html_lower
            or "fbevents.js"
            in html_lower
            or "fbq("
            in html_lower
        ),
        "google_tag_manager": (
            "googletagmanager.com"
            in html_lower
            or "gtm-"
            in html_lower
        ),
        "linkedin_insight": (
            "snap.licdn.com"
            in html_lower
            or "lintrk"
            in html_lower
            or "linkedininsighttag"
            in html_lower
        ),
        "hubspot": (
            "js.hs-scripts.com"
            in html_lower
            or "_hsq"
            in html_lower
            or "hubspotutk"
            in html_lower
        ),
    }


# =========================================================
# PRICE HELPERS
# =========================================================

def convert_usd_project_value(
    minimum: int,
    maximum: int,
    currency: Optional[str],
) -> tuple[int, int]:

    if not currency:

        return (
            minimum,
            maximum,
        )

    rate = INDICATIVE_USD_RATES.get(
        currency
    )

    if not rate:

        return (
            minimum,
            maximum,
        )

    localized_min = int(
        round(
            minimum * rate
        )
    )

    localized_max = int(
        round(
            maximum * rate
        )
    )

    return (
        localized_min,
        localized_max,
    )


def format_currency_value(
    value: int,
    currency: Optional[str],
    symbol: Optional[str],
) -> str:

    if not currency:
        return str(value)

    currency_symbol = (
        symbol
        or CURRENCY_SYMBOL_MAP.get(
            currency,
            currency,
        )
    )

    return (
        f"{currency_symbol}"
        f"{value:,}"
    )


def build_localized_project_value(
    minimum: int,
    maximum: int,
    locale_signals: dict,
) -> dict:

    currency = (
        locale_signals.get(
            "primary_currency"
        )
    )

    symbol = (
        locale_signals.get(
            "primary_currency_symbol"
        )
    )

    if not currency:

        return {
            "currency": "USD",
            "symbol": "$",
            "min": minimum,
            "max": maximum,
            "formatted": (
                f"${minimum:,} - "
                f"${maximum:,}"
            ),
            "source": "default",
        }

    localized_min, localized_max = (
        convert_usd_project_value(
            minimum,
            maximum,
            currency,
        )
    )

    formatted_min = format_currency_value(
        localized_min,
        currency,
        symbol,
    )

    formatted_max = format_currency_value(
        localized_max,
        currency,
        symbol,
    )

    return {
        "currency": currency,
        "symbol": symbol,
        "min": localized_min,
        "max": localized_max,
        "formatted": (
            f"{formatted_min} - "
            f"{formatted_max}"
        ),
        "source": locale_signals.get(
            "currency_source",
            "unknown",
        ),
    }


# =========================================================
# SALES INTELLIGENCE
# =========================================================

def generate_sales_intel(
    data: dict,
) -> dict:

    problems: list[str] = []
    opportunity_reasons: list[str] = []
    recommendations: list[str] = []

    title = clean_text(
        data.get(
            "title",
            "",
        )
    )

    meta_description = clean_text(
        data.get(
            "meta_description",
            "",
        )
    )

    try:

        h1_count = int(
            data.get(
                "h1_count",
                0,
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        h1_count = 0

    conversion = data.get(
        "conversion_signals",
        {},
    )

    conversion_evidence = data.get(
        "conversion_evidence",
        {},
    )

    technical = data.get(
        "technical_signals",
        {},
    )

    trackers = data.get(
        "trackers",
        {},
    )

    locale_signals = data.get(
        "locale_signals",
        {},
    )

    locale_country_evidence = locale_signals.get(
        "country_evidence",
        {},
    )
    global_locale_surface = bool(
        locale_country_evidence.get(
            "global_locale_surface",
            False,
        )
    )

    contactability = data.get(
        "contactability",
        {},
    )

    quality_signals = data.get(
        "quality_signals",
        {},
    )

    try:
        contactability_score = int(
            contactability.get(
                "score",
                0,
            )
            or 0
        )
    except (TypeError, ValueError):
        contactability_score = 0

    template_residue_count = int(
        quality_signals.get(
            "template_residue_count",
            0,
        )
        or 0
    )

    business_name = clean_business_name_candidate(
        data.get(
            "business_name",
            "",
        )
    )

    raw_business_name_confidence = data.get(
        "business_name_confidence",
        0,
    )

    if isinstance(
        raw_business_name_confidence,
        int,
    ):

        business_name_confidence = (
            raw_business_name_confidence
        )

    else:

        try:

            business_name_confidence = int(
                raw_business_name_confidence
            )

        except (
            TypeError,
            ValueError,
        ):

            business_name_confidence = 0

    # =====================================================
    # WEBSITE HEALTH
    # =====================================================

    seo_score = 35

    if not title:

        seo_score -= 15

        problems.append(
            "Missing page title"
        )

    elif len(title) < 10:

        seo_score -= 8

        problems.append(
            "Weak page title"
        )

    if not meta_description:

        seo_score -= 10

        problems.append(
            "Missing meta description"
        )

    elif len(meta_description) < 50:

        seo_score -= 5

        problems.append(
            "Short or weak meta description"
        )

    if h1_count == 0:

        seo_score -= 10

        problems.append(
            "No H1 heading detected"
        )

    elif h1_count > 1:

        seo_score -= 5

        problems.append(
            "Multiple H1 headings"
        )

    seo_score = max(
        0,
        seo_score,
    )

    conversion_score = 40

    has_contact_path = bool(
        conversion_evidence.get(
            "has_contact_path"
        )
    )

    has_booking_path = bool(
        conversion_evidence.get(
            "has_booking_path"
        )
    )

    render_verification_required = bool(
        conversion_evidence.get(
            "render_verification_required"
        )
    )

    if not conversion.get(
        "has_cta"
    ):

        conversion_score -= 3

        problems.append(
            "CTA not confirmed in fetched HTML — render verification required"
        )

    if not conversion.get(
        "has_form"
    ):

        conversion_score -= 3

        problems.append(
            "Form not confirmed in fetched HTML — render verification required"
        )

    if not has_contact_path:

        conversion_score -= 2

        problems.append(
            "Contact path not confirmed in fetched HTML — render verification required"
        )

    if not has_booking_path:

        conversion_score -= 2

        problems.append(
            "Enquiry/booking path not confirmed in fetched HTML — render verification required"
        )

    conversion_score = max(
        0,
        conversion_score,
    )

    technical_score = 25

    if not technical.get(
        "has_viewport"
    ):

        technical_score -= 8

        problems.append(
            "Missing mobile viewport"
        )

    if not technical.get(
        "has_canonical"
    ):

        technical_score -= 5

        problems.append(
            "Canonical URL not detected"
        )

    if not technical.get(
        "has_favicon"
    ):

        technical_score -= 2

        problems.append(
            "Favicon not detected"
        )

    if not technical.get(
        "has_ssl"
    ):

        technical_score -= 3

        problems.append(
            "HTTPS not detected"
        )

    if not any(
        bool(value)
        for value in trackers.values()
    ):

        technical_score -= 7

        problems.append(
            "No marketing or analytics tracking detected"
        )

    technical_score = max(
        0,
        technical_score,
    )

    website_score = max(
        0,
        min(
            100,
            seo_score
            + conversion_score
            + technical_score,
        ),
    )

    # =====================================================
    # COMMERCIAL / LEAD CLASSIFICATION
    # =====================================================

    lead_type, lead_type_confidence = detect_lead_type(
        data
    )

    business_signals = data.get(
        "business_signals",
        {},
    )

    try:

        commercial_keyword_count = int(
            business_signals.get(
                "commercial_keyword_count",
                0,
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        commercial_keyword_count = 0

    try:

        navigation_signals = int(
            business_signals.get(
                "commercial_navigation_signals",
                0,
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        navigation_signals = 0

    if commercial_keyword_count >= 10:

        commercial_intent = "HIGH"

    elif commercial_keyword_count >= 5:

        commercial_intent = "MEDIUM"

    else:

        commercial_intent = "LOW"

    # =====================================================
    # SALES OPPORTUNITY
    # =====================================================

    opportunity_score = 0

    if not conversion.get(
        "has_cta"
    ):

        opportunity_score += 3

        opportunity_reasons.append(
            "CTA not confirmed in fetched HTML"
        )

        recommendations.append(
            "Verify the rendered CTA before treating this as a redesign gap"
        )

    if not conversion.get(
        "has_form"
    ):

        opportunity_score += 4

        opportunity_reasons.append(
            "Form not confirmed in fetched HTML"
        )

        recommendations.append(
            "Verify forms or booking widgets after JavaScript renders"
        )

    if not has_contact_path:

        opportunity_score += 2

        opportunity_reasons.append(
            "Contact route not confirmed in fetched HTML"
        )

        recommendations.append(
            "Verify phone, email and contact widgets in a rendered browser"
        )

    if not has_booking_path:

        opportunity_score += 2

        opportunity_reasons.append(
            "Enquiry/booking path not confirmed in fetched HTML"
        )

        recommendations.append(
            "Verify the rendered enquiry or booking path before recommending a rebuild"
        )

    if not meta_description:

        opportunity_score += 5

        opportunity_reasons.append(
            "Missing meta description"
        )

        recommendations.append(
            "Rewrite the meta title and meta description for search and conversion"
        )

    if h1_count == 0:

        opportunity_score += 5

        opportunity_reasons.append(
            "Missing H1 structure"
        )

        recommendations.append(
            "Create a clear primary H1 focused on the main service or offer"
        )

    if not technical.get(
        "has_canonical"
    ):

        opportunity_score += 2

        opportunity_reasons.append(
            "Canonical URL not detected"
        )

        recommendations.append(
            "Add canonical URL and strengthen technical SEO"
        )

    if not data.get(
        "og_image"
    ):

        opportunity_score += 3

        opportunity_reasons.append(
            "No social sharing image detected"
        )

        recommendations.append(
            "Add a professional Open Graph/social sharing image"
        )

    if not trackers.get(
        "google_analytics"
    ):

        opportunity_score += 2

        opportunity_reasons.append(
            "Google Analytics not detected"
        )

        recommendations.append(
            "Add analytics tracking to measure lead and visitor behaviour"
        )

    if not trackers.get(
        "facebook_pixel"
    ):

        opportunity_score += 2

        opportunity_reasons.append(
            "Meta/Facebook Pixel not detected"
        )

        recommendations.append(
            "Add Meta tracking if paid social acquisition is relevant"
        )

    if commercial_keyword_count >= 10:

        opportunity_score += 9

        opportunity_reasons.append(
            "Strong commercial intent detected"
        )

    elif commercial_keyword_count >= 5:

        opportunity_score += 7

        opportunity_reasons.append(
            "Clear commercial intent detected"
        )

    elif commercial_keyword_count >= 3:

        opportunity_score += 5

        opportunity_reasons.append(
            "Commercial website intent detected"
        )

    if navigation_signals >= 5:

        opportunity_score += 6

    elif navigation_signals >= 3:

        opportunity_score += 4

    elif navigation_signals >= 1:

        opportunity_score += 2

    if website_score < 50:

        opportunity_score += 12

    elif website_score < 65:

        opportunity_score += 10

    elif website_score < 75:

        opportunity_score += 7

    elif website_score < 85:

        opportunity_score += 4

    elif website_score < 92:

        opportunity_score += 2

    if data.get(
        "emails"
    ):

        opportunity_score += 2

    if data.get(
        "phones"
    ):

        opportunity_score += 2

    if conversion.get(
        "has_whatsapp"
    ):

        opportunity_score += 2

    if (
        business_name_confidence >= 75
        and business_name
    ):

        opportunity_score += 1

    if quality_signals.get(
        "template_residue_detected"
    ):
        residue_boost = min(
            14,
            6 + template_residue_count * 3,
        )

        opportunity_score += residue_boost

        opportunity_reasons.append(
            "Visible template or placeholder residue detected"
        )

        recommendations.append(
            "Remove unfinished template content and tighten brand consistency"
        )

    # A prospect is more actionable when there is a real
    # public contact route. Keep this small so contactability
    # does not masquerade as website quality.
    if contactability_score >= 70:
        opportunity_score += 3
    elif (
        contactability_score < 20
        and not contactability.get(
            "verification_required"
        )
    ):
        opportunity_score -= 5

    opportunity_score = max(
        0,
        min(
            100,
            opportunity_score,
        ),
    )

    opportunity_reasons = list(
        dict.fromkeys(
            opportunity_reasons
        )
    )[:12]

    recommendations = list(
        dict.fromkeys(
            recommendations
        )
    )[:10]

    # =====================================================
    # BEST SALES ANGLE
    # =====================================================

    if render_verification_required:

        best_sales_angle = (
            "Verify the rendered customer journey first, then pitch only confirmed "
            "conversion or presentation gaps."
        )

    elif not meta_description or h1_count == 0:

        best_sales_angle = (
            "SEO and messaging improvements that can "
            "strengthen visibility and conversion."
        )

    elif not any(
        bool(value)
        for value in trackers.values()
    ):

        best_sales_angle = (
            "Conversion tracking and marketing measurement."
        )

    else:

        best_sales_angle = (
            "Website growth and conversion optimization."
        )

    # =====================================================
    # OPPORTUNITY LEVEL
    # =====================================================

    if opportunity_score >= 75:

        opportunity_level = "HOT"

    elif opportunity_score >= 55:

        opportunity_level = "HIGH"

    elif opportunity_score >= 35:

        opportunity_level = "MEDIUM"

    else:

        opportunity_level = "LOW"

    # =====================================================
    # PROSPECT PRIORITY
    # =====================================================

    identity_score = max(
        0,
        min(
            100,
            business_name_confidence,
        ),
    )

    prospect_score = round(
        opportunity_score * 0.60
        + contactability_score * 0.30
        + identity_score * 0.10
    )

    if commercial_intent == "HIGH":
        prospect_score += 5
    elif commercial_intent == "MEDIUM":
        prospect_score += 2

    # Multi-region/global product sites are usually poor fits for the local-SMB
    # outbound workflow QuickLead is designed to prioritize. Keep them visible
    # for research, but prevent them from outranking actionable local prospects.
    if global_locale_surface:
        prospect_score -= 18

    prospect_score = max(
        0,
        min(
            100,
            prospect_score,
        ),
    )

    preferred_email = clean_text(
        contactability.get(
            "preferred_email",
            "",
        )
    )

    if global_locale_surface:
        prospect_decision = (
            "VERIFY"
            if opportunity_score >= 60
            else "SKIP"
        )
    elif (
        prospect_score >= 60
        and preferred_email
        and opportunity_score >= 40
        and not contactability.get(
            "verification_required"
        )
    ):
        prospect_decision = "CONTACT"
    elif (
        contactability.get(
            "verification_required"
        )
        and opportunity_score >= 35
        and business_name_confidence >= 60
    ):
        prospect_decision = "VERIFY"
    elif (
        prospect_score >= 45
        and opportunity_score >= 35
    ):
        prospect_decision = "VERIFY"
    else:
        prospect_decision = "SKIP"

    prospect_reasons: list[str] = []

    if global_locale_surface:
        prospect_reasons.append(
            "Global or multi-region site detected; deprioritized for local-SMB outreach"
        )

    if opportunity_score >= 55:
        prospect_reasons.append(
            "Meaningful website improvement opportunity"
        )

    if contactability_score >= 70:
        prospect_reasons.append(
            "Strong public contactability"
        )
    elif not preferred_email:
        prospect_reasons.append(
            "No preferred outreach email verified from the page"
        )

    if business_name_confidence >= 75:
        prospect_reasons.append(
            "Business identity confidence is strong"
        )

    if quality_signals.get(
        "template_residue_detected"
    ):
        prospect_reasons.append(
            "Template residue creates a concrete redesign angle"
        )

    manual_verification: list[str] = []

    if not conversion.get(
        "has_cta"
    ):
        manual_verification.append(
            "Verify visible CTA in a rendered browser"
        )

    if not conversion.get(
        "has_form"
    ):
        manual_verification.append(
            "Verify forms or booking widgets after JavaScript renders"
        )

    if contactability.get(
        "verification_required"
    ):
        manual_verification.append(
            "Verify public phone/email/contact routes in a rendered browser"
        )

    if business_name_confidence < 75:
        manual_verification.append(
            "Verify business identity against the live site"
        )

    # =====================================================
    # SERVICE / OFFER
    # =====================================================

    has_major_conversion_gap = (
        not render_verification_required
        and (
            not conversion.get(
                "has_form"
            )
            or not conversion.get(
                "has_cta"
            )
            or not has_booking_path
        )
    )

    potential_conversion_gap = bool(
        conversion_evidence.get(
            "unverified_missing"
        )
    )

    has_major_seo_gap = (
        not meta_description
        or h1_count == 0
        or not title
    )

    has_tracking_gap = not any(
        bool(value)
        for value in trackers.values()
    )

    if (
        opportunity_score >= 75
        and has_major_conversion_gap
    ):

        suggested_offer = (
            "Website Redesign + Lead Generation System"
        )

        suggested_price = (
            "$1,000 - $2,500"
        )

        project_value = {
            "min": 1000,
            "max": 2500,
            "currency": "USD",
        }

        service_reason = (
            "Strong commercial intent combined with "
            "significant conversion improvement potential."
        )

    elif (
        opportunity_score >= 55
        and has_major_conversion_gap
    ):

        suggested_offer = (
            "Website Conversion Upgrade"
        )

        suggested_price = (
            "$750 - $1,500"
        )

        project_value = {
            "min": 750,
            "max": 1500,
            "currency": "USD",
        }

        service_reason = (
            "The business appears commercially active, "
            "but the website has identifiable conversion friction."
        )

    elif (
        opportunity_score >= 45
        and has_tracking_gap
    ):

        suggested_offer = (
            "Website + Analytics + Conversion Optimization"
        )

        suggested_price = (
            "$600 - $1,200"
        )

        project_value = {
            "min": 600,
            "max": 1200,
            "currency": "USD",
        }

        service_reason = (
            "The website has measurable marketing "
            "and conversion improvements available."
        )

    elif (
        opportunity_score >= 35
        and has_major_seo_gap
    ):

        suggested_offer = (
            "SEO + Website Conversion Improvements"
        )

        suggested_price = (
            "$500 - $1,000"
        )

        project_value = {
            "min": 500,
            "max": 1000,
            "currency": "USD",
        }

        service_reason = (
            "SEO and conversion improvements "
            "are the clearest entry point."
        )

    elif opportunity_score >= 35:

        suggested_offer = (
            "Website Growth Optimization"
        )

        suggested_price = (
            "$500 - $900"
        )

        project_value = {
            "min": 500,
            "max": 900,
            "currency": "USD",
        }

        service_reason = (
            "The website has commercially relevant "
            "improvement opportunities."
        )

    else:

        suggested_offer = (
            "Website Review / Minor Optimization"
        )

        suggested_price = (
            "$250 - $500"
        )

        project_value = {
            "min": 250,
            "max": 500,
            "currency": "USD",
        }

        service_reason = (
            "Only limited commercial opportunities "
            "were detected."
        )

    localized_project_value = (
        build_localized_project_value(
            project_value["min"],
            project_value["max"],
            locale_signals,
        )
    )

    primary_currency = (
        locale_signals.get(
            "primary_currency"
        )
        or "USD"
    )

    primary_currency_symbol = (
        locale_signals.get(
            "primary_currency_symbol"
        )
        or "$"
    )

    if (
        localized_project_value.get(
            "currency"
        )
        and localized_project_value.get(
            "currency"
        ) != "USD"
    ):

        suggested_price_localized = (
            localized_project_value.get(
                "formatted"
            )
        )

    else:

        suggested_price_localized = (
            suggested_price
        )

    # =====================================================
    # OUTREACH
    # =====================================================

    outreach_business_name = (
        business_name
        if (
            business_name
            and business_name_confidence >= 60
            and not looks_generic_business_name(
                business_name
            )
        )
        else "your company"
    )

    pitch_reason = (
        "your website's lead-generation flow"
        if has_major_conversion_gap
        else (
            "several opportunities to improve "
            "your website"
        )
    )

    pitch = (
        f"Hi, I was reviewing "
        f"the {outreach_business_name} website "
        f"and noticed {pitch_reason}. "
        f"I found a few areas where the customer journey "
        f"could be clearer and easier for potential customers "
        f"to take action. I put together a few ideas for "
        f"improving the website and conversion flow. "
        f"Would you be open to seeing a quick preview?"
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "website_score": website_score,
        "seo_score": seo_score,
        "conversion_score": conversion_score,
        "technical_score": technical_score,
        "conversion_evidence": conversion_evidence,
        "potential_conversion_gap": potential_conversion_gap,

        "opportunity_score": opportunity_score,
        "opportunity_level": opportunity_level,

        "prospect_score": prospect_score,
        "prospect_decision": prospect_decision,
        "prospect_reasons": prospect_reasons[:8],
        "manual_verification": manual_verification[:8],

        "contactability_score": contactability_score,
        "contactability_level": contactability.get(
            "level",
            "LOW",
        ),
        "preferred_email": preferred_email or None,
        "email_ready": bool(preferred_email),

        "template_residue_count": template_residue_count,
        "template_residue_level": quality_signals.get(
            "template_residue_level",
            "NONE",
        ),

        "opportunity_reasons": opportunity_reasons,
        "recommendations": recommendations,

        "best_sales_angle": best_sales_angle,

        "service_reason": service_reason,

        "suggested_offer": suggested_offer,
        "suggested_price": suggested_price,
        "suggested_price_localized": (
            suggested_price_localized
        ),

        "project_value": project_value,
        "localized_project_value": (
            localized_project_value
        ),

        "primary_currency": primary_currency,
        "primary_currency_symbol": (
            primary_currency_symbol
        ),

        "lead_type": lead_type,
        "lead_type_confidence": lead_type_confidence,

        "commercial_intent": commercial_intent,

        "problems_found": list(
            dict.fromkeys(
                problems
            )
        )[:15],

        "personalized_pitch": pitch,
    }


# =========================================================
# SINGLE URL PROCESSOR
# =========================================================

async def process_single_url(
    client: httpx.AsyncClient,
    raw_url: str,
) -> Optional[dict]:

    input_url = clean_text(
        raw_url
    )

    target_url = normalize_url(
        input_url
    )

    if not target_url:
        return None

    attempted_urls: list[str] = []

    try:

        response, attempted_urls = await fetch_url_with_fallback(
            client,
            input_url,
        )

        html_content = response.text
        html_lower = html_content.lower()

        soup = BeautifulSoup(
            html_content,
            "html.parser",
        )

        final_url = str(
            response.url
        )

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        title = ""

        if soup.title:

            title = clean_text(
                soup.title.get_text()
            )

        # -------------------------------------------------
        # Business name
        # -------------------------------------------------

        name_result = extract_business_name(
            soup
        )

        if not isinstance(
            name_result,
            tuple,
        ):

            business_name = ""
            business_name_source = "unknown"
            business_name_confidence = 0

        elif len(name_result) < 3:

            business_name = ""
            business_name_source = "unknown"
            business_name_confidence = 0

        else:

            business_name = name_result[0]
            second_value = name_result[1]
            third_value = name_result[2]

            if (
                isinstance(
                    second_value,
                    int,
                )
                and isinstance(
                    third_value,
                    str,
                )
            ):

                business_name_source = third_value
                business_name_confidence = second_value

            else:

                business_name_source = second_value
                business_name_confidence = third_value

        business_name = clean_text(
            str(
                business_name
                or ""
            )
        )

        if not isinstance(
            business_name_source,
            str,
        ):

            business_name_source = "unknown"

        if isinstance(
            business_name_confidence,
            bool,
        ):

            business_name_confidence = int(
                business_name_confidence
            )

        elif not isinstance(
            business_name_confidence,
            int,
        ):

            try:

                business_name_confidence = int(
                    business_name_confidence
                )

            except (
                TypeError,
                ValueError,
            ):

                business_name_confidence = 0

        # -------------------------------------------------
        # Domain identity
        # -------------------------------------------------

        inferred_domain_name = (
            infer_business_name_from_domain(
                final_url
            )
        )

        title_identity_name, title_identity_source, title_identity_confidence = (
            extract_page_title_identity_candidate(
                soup,
                inferred_domain_name,
            )
        )

        (
            meta_identity_name,
            meta_identity_source,
            meta_identity_confidence,
        ) = extract_meta_description_business_identity_candidate(soup)

        (
            repeated_identity_name,
            repeated_identity_source,
            repeated_identity_confidence,
        ) = extract_repeated_visible_business_identity_candidate(soup)

        # -------------------------------------------------
        # Meta
        # -------------------------------------------------

        meta_tag = (
            soup.find(
                "meta",
                attrs={
                    "name": re.compile(
                        r"^description$",
                        re.I,
                    )
                },
            )
            or soup.find(
                "meta",
                attrs={
                    "property": re.compile(
                        r"^og:description$",
                        re.I,
                    )
                },
            )
        )

        meta_description = ""

        if meta_tag:

            content = meta_tag.get(
                "content"
            )

            if isinstance(
                content,
                str,
            ):

                meta_description = clean_text(
                    content
                )

        # -------------------------------------------------
        # H1
        # -------------------------------------------------

        h1_tags = soup.find_all(
            "h1"
        )

        h1_text = [
            clean_text(
                h1.get_text(
                    " ",
                    strip=True,
                )
            )
            for h1 in h1_tags
            if clean_text(
                h1.get_text(
                    " ",
                    strip=True,
                )
            )
        ]

        # -------------------------------------------------
        # OG image
        # -------------------------------------------------

        og_image_tag = soup.find(
            "meta",
            attrs={
                "property": "og:image"
            },
        )

        og_image = None

        if og_image_tag:

            content = og_image_tag.get(
                "content"
            )

            if isinstance(
                content,
                str,
            ):

                og_image = clean_text(
                    content
                )

        # -------------------------------------------------
        # Contacts
        # -------------------------------------------------

        phones, socials = extract_contacts(
            soup,
            html_content,
        )

        emails = extract_emails(
            html_content
        )

        # -------------------------------------------------
        # Email/domain identity candidates
        # -------------------------------------------------

        email_identity_candidates: list[
            tuple[str, int]
        ] = []

        for email in emails:

            if "@" not in email:
                continue

            local_part = email.split(
                "@",
                1,
            )[0]

            domain_name = infer_business_name_from_email(
                email
            )

            if not domain_name:
                continue

            if is_generic_email_local_part(
                local_part
            ):

                email_identity_candidates.append(
                    (
                        domain_name,
                        74,
                    )
                )

            else:

                email_identity_candidates.append(
                    (
                        domain_name,
                        78,
                    )
                )

        email_identity_name = ""

        if email_identity_candidates:

            counts: dict[str, int] = {}

            for candidate, _confidence in email_identity_candidates:

                counts[candidate.casefold()] = (
                    counts.get(
                        candidate.casefold(),
                        0,
                    )
                    + 1
                )

            email_identity_name = max(
                email_identity_candidates,
                key=lambda item: (
                    counts.get(
                        item[0].casefold(),
                        0,
                    ),
                    item[1],
                ),
            )[0]

        # -------------------------------------------------
        # Identity validation
        # -------------------------------------------------

        current_name_is_invalid = (
            not business_name
            or looks_generic_business_name(
                business_name
            )
            or looks_like_non_brand_phrase(
                business_name
            )
        )

        current_name_is_descriptive = (
            is_likely_descriptive_business_name(
                business_name
            )
            if business_name
            else True
        )

        current_name_word_count = len(
            clean_business_name_candidate(
                business_name
            ).split()
        )

        current_name_is_suspicious = (
            current_name_is_invalid
            or looks_like_non_brand_phrase(
                business_name
            )
            or current_name_word_count > 5
        )

        title_identity_is_valid = (
            bool(title_identity_name)
            and not looks_generic_business_name(
                title_identity_name
            )
            and not looks_like_non_brand_phrase(
                title_identity_name
            )
        )

        meta_identity_is_valid = (
            bool(meta_identity_name)
            and not looks_generic_business_name(meta_identity_name)
            and not looks_like_non_brand_phrase(meta_identity_name)
        )

        repeated_identity_is_valid = (
            bool(repeated_identity_name)
            and not looks_generic_business_name(repeated_identity_name)
            and not looks_like_non_brand_phrase(repeated_identity_name)
        )

        domain_name_is_valid = (
            bool(
                inferred_domain_name
            )
            and not looks_generic_business_name(
                inferred_domain_name
            )
            and name_quality(
                inferred_domain_name
            ) >= 50
        )

        email_identity_is_valid = (
            bool(
                email_identity_name
            )
            and not looks_generic_business_name(
                email_identity_name
            )
        )

        source_is_weak = (
            business_name_source
            in {
                "image_brand",
                "footer",
                "title_inference",
                "itemprop_name",
                "meta_application-name",
                "meta_publisher",
            }
        )

        # -------------------------------------------------
        # Strong fallback for false one-word names
        #
        # Examples:
        #   It
        #   What
        #   This
        # -------------------------------------------------

        if current_name_is_invalid:

            if title_identity_is_valid:

                business_name = (
                    title_identity_name
                )

                business_name_source = (
                    title_identity_source
                )

                business_name_confidence = max(
                    86,
                    int(title_identity_confidence),
                )

            elif meta_identity_is_valid:

                business_name = meta_identity_name
                business_name_source = meta_identity_source
                business_name_confidence = int(meta_identity_confidence)

            elif repeated_identity_is_valid:

                business_name = repeated_identity_name
                business_name_source = repeated_identity_source
                business_name_confidence = int(repeated_identity_confidence)

            elif email_identity_is_valid:

                business_name = (
                    email_identity_name
                )

                business_name_source = (
                    "email_domain_inference"
                )

                business_name_confidence = 78

            elif domain_name_is_valid:

                business_name = (
                    inferred_domain_name
                )

                business_name_source = (
                    "domain_inference"
                )

                business_name_confidence = 75

        # -------------------------------------------------
        # A one-word location/UI identity should lose to a stronger title
        # brand when the title is domain-aligned or shown in primary brand
        # positions. This catches values such as a city name without hardcoding
        # particular cities.
        # -------------------------------------------------

        if (
            not current_name_is_invalid
            and current_name_word_count == 1
            and title_identity_is_valid
            and not business_names_equivalent(
                business_name,
                title_identity_name,
            )
            and (
                (
                    domain_name_is_valid
                    and title_identity_matches_domain(
                        title_identity_name,
                        inferred_domain_name,
                    )
                )
                or business_identity_has_primary_brand_evidence(
                    soup,
                    title_identity_name,
                )
            )
        ):
            business_name = title_identity_name
            business_name_source = title_identity_source
            business_name_confidence = max(
                86,
                int(title_identity_confidence),
            )
            current_name_is_descriptive = (
                is_likely_descriptive_business_name(
                    business_name
                )
            )

        # -------------------------------------------------
        # Descriptive page names lose to an actual domain
        # identity unless structured data provides a strong
        # explicit business/brand name.
        # -------------------------------------------------

        elif current_name_is_descriptive:

            title_domain_match = (
                business_name_source == "title_identity"
                and (
                    not looks_like_seo_marketing_title(
                        business_name
                    )
                    or (
                        domain_name_is_valid
                        and title_identity_matches_domain(
                            business_name,
                            inferred_domain_name,
                        )
                    )
                )
            )

            if (
                business_name_source
                not in {
                    "json_ld_name",
                    "json_ld_legalName",
                    "json_ld_alternateName",
                    "json_ld_brand",
                    "logo_or_brand",
                    "page_brand",
                }
                and not title_domain_match
            ):

                if domain_name_is_valid:

                    business_name = (
                        inferred_domain_name
                    )

                    business_name_source = (
                        "domain_inference"
                    )

                    business_name_confidence = 82

                elif email_identity_is_valid:

                    business_name = (
                        email_identity_name
                    )

                    business_name_source = (
                        "email_domain_inference"
                    )

                    business_name_confidence = 78

        # -------------------------------------------------
        # Weak visual/page result loses to domain/email
        # identity.
        # -------------------------------------------------

        elif (
            source_is_weak
            and business_name_confidence < 85
        ):

            if (
                domain_name_is_valid
                and not business_name_matches_domain(
                    business_name,
                    inferred_domain_name,
                )
            ):

                business_name = (
                    inferred_domain_name
                )

                business_name_source = (
                    "domain_inference_verified"
                )

                business_name_confidence = 82

            elif (
                email_identity_is_valid
                and not business_name_matches_domain(
                    business_name,
                    email_identity_name,
                )
            ):

                business_name = (
                    email_identity_name
                )

                business_name_source = (
                    "email_domain_inference"
                )

                business_name_confidence = 78

        # -------------------------------------------------
        # Keep strong JSON-LD business names.
        #
        # This intentionally allows something like
        # "AB ConnectZ" to remain when structured data
        # explicitly identifies it as the organization.
        # -------------------------------------------------

        # No overwrite here for:
        # json_ld_name
        # json_ld_legalName
        # json_ld_alternateName
        # json_ld_brand

        # -------------------------------------------------
        # Final safety check
        # -------------------------------------------------

        if (
            not business_name
            or looks_generic_business_name(
                business_name
            )
            or looks_like_non_brand_phrase(
                business_name
            )
        ):

            if title_identity_is_valid:

                business_name = title_identity_name
                business_name_source = title_identity_source
                business_name_confidence = max(
                    86,
                    int(title_identity_confidence),
                )

            elif meta_identity_is_valid:

                business_name = meta_identity_name
                business_name_source = meta_identity_source
                business_name_confidence = int(meta_identity_confidence)

            elif repeated_identity_is_valid:

                business_name = repeated_identity_name
                business_name_source = repeated_identity_source
                business_name_confidence = int(repeated_identity_confidence)

            elif domain_name_is_valid:

                business_name = (
                    inferred_domain_name
                )

                business_name_source = (
                    "domain_inference"
                )

                business_name_confidence = 75

            elif email_identity_is_valid:

                business_name = (
                    email_identity_name
                )

                business_name_source = (
                    "email_domain_inference"
                )

                business_name_confidence = 74

        # -------------------------------------------------
        # Identity conflict guard
        # -------------------------------------------------

        (
            business_name,
            business_name_source,
            business_name_confidence,
        ) = resolve_business_identity_conflict(
            soup,
            business_name,
            business_name_source,
            business_name_confidence,
            inferred_domain_name,
            email_identity_name,
            domain_name_is_valid,
            email_identity_is_valid,
        )

        (
            business_name,
            business_name_source,
            business_name_confidence,
        ) = apply_publisher_identity_guard(
            soup,
            business_name,
            business_name_source,
            business_name_confidence,
            inferred_domain_name,
            domain_name_is_valid,
        )

        # -------------------------------------------------
        # Locale first pass
        # -------------------------------------------------

        preliminary_locale = detect_locale_signals(
            soup,
            final_url,
            phones,
            html_content,
        )

        country_hint = preliminary_locale.get(
            "country_hint"
        )

        # -------------------------------------------------
        # Normalize phones with country evidence
        # -------------------------------------------------

        normalized_phones: list[str] = []

        contact_regions = []

        for selector in [
            "footer",
            "address",
            "#contact",
            "[id*='contact']",
            "[class*='contact']",
            "[class*='footer']",
            "[id*='footer']",
        ]:

            try:

                contact_regions.extend(
                    soup.select(
                        selector
                    )
                )

            except Exception:
                continue

        raw_phone_candidates = list(
            phones
        )

        # Explicit +91 values are always added first.
        raw_phone_candidates.extend(
            extract_explicit_india_phones(
                html_content
            )
        )

        for region in contact_regions:

            region_text = clean_text(
                region.get_text(
                    " ",
                    strip=True,
                )
            )

            if region_text:

                raw_phone_candidates.extend(
                    clean_text(match.group(0))
                    for match in PHONE_CANDIDATE_REGEX.finditer(region_text)
                    if not looks_like_low_confidence_phone_candidate(
                        clean_text(match.group(0))
                    )
                )

        for anchor in soup.find_all(
            "a",
            href=True,
        ):

            href = clean_text(
                anchor.get(
                    "href",
                    "",
                )
            )

            if href.lower().startswith(
                "tel:"
            ):

                raw_phone_candidates.append(
                    urllib.parse.unquote(
                        href[4:]
                    ).strip()
                )

        seen_normalized = set()

        for phone in raw_phone_candidates:

            # tel: attributes and contact widgets can contain dates/tracking
            # IDs. If locale is still unknown/global, do not promote a bare
            # short numeric run to a prospect phone. Known local markets keep
            # their legitimate national formats.
            if (
                not country_hint
                and looks_like_low_confidence_phone_candidate(
                    str(phone or "")
                )
            ):
                continue

            normalized = normalize_phone_for_country(
                phone,
                country_hint,
            )

            if normalized:

                digits = re.sub(
                    r"\D",
                    "",
                    normalized,
                )

                if (
                    digits
                    not in seen_normalized
                ):

                    normalized_phones.append(
                        normalized
                    )

                    seen_normalized.add(
                        digits
                    )

        # -------------------------------------------------
        # If explicit +91 evidence exists, ensure those
        # valid Indian numbers are not lost.
        # -------------------------------------------------

        if extract_explicit_india_phones(
            html_content
        ):

            explicit_india = (
                extract_explicit_india_phones(
                    html_content
                )
            )

            combined_phone_list = (
                explicit_india
                + normalized_phones
            )

            final_phone_list: list[str] = []
            final_phone_digits: set[str] = set()

            for phone in combined_phone_list:

                digits = re.sub(
                    r"\D",
                    "",
                    phone,
                )

                if digits not in final_phone_digits:

                    final_phone_list.append(
                        phone
                    )

                    final_phone_digits.add(
                        digits
                    )

            normalized_phones = (
                final_phone_list
            )

        phones = normalized_phones[:8]

        # -------------------------------------------------
        # Final locale pass
        # -------------------------------------------------

        locale_signals = detect_locale_signals(
            soup,
            final_url,
            phones,
            html_content,
        )

        final_country_hint = locale_signals.get(
            "country_hint"
        )

        revalidated_phones = revalidate_phone_list_for_country(
            phones,
            final_country_hint,
        )

        if revalidated_phones != phones:
            phones = revalidated_phones
            locale_signals = detect_locale_signals(
                soup,
                final_url,
                phones,
                html_content,
            )

        # -------------------------------------------------
        # Other signals
        # -------------------------------------------------

        tech_stack = detect_tech_stack(
            html_lower
        )

        trackers = detect_trackers(
            html_lower
        )

        conversion_signals = (
            extract_conversion_signals(
                soup,
                html_lower,
            )
        )

        conversion_evidence = (
            build_conversion_evidence(
                conversion_signals,
                emails,
                phones,
            )
        )

        technical_signals = (
            extract_technical_signals(
                soup,
                final_url,
            )
        )

        business_signals = (
            extract_business_signals(
                soup,
                business_name,
                title,
            )
        )

        contactability = (
            build_contactability_signals(
                final_url,
                emails,
                phones,
                socials,
                conversion_signals,
                conversion_evidence,
            )
        )

        quality_signals = (
            detect_template_residue(
                soup,
                html_content,
            )
        )

        # -------------------------------------------------
        # Raw data
        # -------------------------------------------------

        raw_data = {
            "input_url": input_url,
            "resolved_url": final_url,
            "url": final_url,
            "attempted_urls": attempted_urls,
            "domain": get_domain(
                final_url
            ),

            "business_name": business_name,
            "business_name_source": (
                business_name_source
            ),
            "business_name_confidence": (
                business_name_confidence
            ),

            "title": title,
            "meta_description": meta_description,

            "h1_count": len(
                h1_tags
            ),
            "h1_tags": h1_text[:8],

            "og_image": og_image,

            "phones": phones,
            "emails": emails,
            "socials": socials,

            "tech_stack": tech_stack,
            "trackers": trackers,

            "conversion_signals": (
                conversion_signals
            ),

            "conversion_evidence": (
                conversion_evidence
            ),

            "technical_signals": (
                technical_signals
            ),

            "locale_signals": (
                locale_signals
            ),

            "business_signals": (
                business_signals
            ),

            "contactability": (
                contactability
            ),

            "quality_signals": (
                quality_signals
            ),
        }

        intelligence = generate_sales_intel(
            raw_data
        )

        return {
            **raw_data,
            "status": "Success",
            "intelligence": intelligence,
        }

    except Exception as exc:

        if isinstance(exc, WebsiteFetchError):
            return {
                "input_url": input_url,
                "resolved_url": "",
                "url": target_url,
                "attempted_urls": attempted_urls,
                "status": exc.status,
                "failure_type": exc.failure_type,
                "error": str(exc),
                "diagnostic": exc.diagnostic,
            }

        return {
            "input_url": input_url,
            "resolved_url": "",
            "url": target_url,
            "attempted_urls": attempted_urls,
            "status": "Failed",
            "failure_type": "PROCESSING_ERROR",
            "error": str(exc),
        }


# =========================================================
# SINGLE SCAN
# =========================================================

@app.get("/api/scan")
async def scan_target(
    url: str = Query(
        ...,
        description="Target URL to scan",
    ),
):

    async with httpx.AsyncClient(
        timeout=build_http_timeout(),
        limits=build_http_limits(),
        follow_redirects=True,
    ) as client:

        result = await process_single_url(
            client,
            url,
        )

        if (
            not result
            or result.get("status")
            != "Success"
        ):

            raise HTTPException(
                status_code=500,
                detail=(
                    result.get(
                        "error"
                    )
                    if result
                    else "Unable to scan URL."
                ),
            )

        return result


# =========================================================
# BULK SCAN
# =========================================================

@app.post("/api/bulk-scan")
async def bulk_scan_targets(
    urls: list[str] = Body(
        ...,
        description="List of URLs to scan",
    ),
):

    cleaned_urls: list[str] = []
    seen_url_keys: set[str] = set()

    for url in urls[:50]:
        value = clean_text(url)

        if not value:
            continue

        dedupe_key = canonical_url_key(value)

        if dedupe_key and dedupe_key in seen_url_keys:
            continue

        if dedupe_key:
            seen_url_keys.add(dedupe_key)

        cleaned_urls.append(value)

    if not cleaned_urls:

        return {
            "results": []
        }

    semaphore = asyncio.Semaphore(
        BULK_SCAN_CONCURRENCY
    )

    async with httpx.AsyncClient(
        timeout=build_http_timeout(),
        limits=build_http_limits(),
        follow_redirects=True,
    ) as client:

        async def limited_scan(
            target: str
        ):

            async with semaphore:

                return await process_single_url(
                    client,
                    target,
                )

        tasks = [
            limited_scan(url)
            for url in cleaned_urls
        ]

        results = await asyncio.gather(
            *tasks
        )

    return {
        "results": [
            result
            for result in results
            if result is not None
        ]
    }


# =========================================================
# GENERATED WEBSITE PREVIEW
# =========================================================

@app.post("/api/generate-website")
async def generate_website(
    payload: dict = Body(...)
):

    business_name = (
        payload.get(
            "business_name"
        )
        or payload.get(
            "title"
        )
        or "Your Business"
    )

    business_name = clean_business_name_candidate(
        str(
            business_name
        )
    )

    if (
        not business_name
        or looks_generic_business_name(
            business_name
        )
    ):

        business_name = (
            payload.get(
                "domain"
            )
            or "Your Business"
        )

        business_name = (
            infer_business_name_from_domain(
                str(
                    business_name
                )
            )
            or "Your Business"
        )

    title = business_name

    page_description = (
        payload.get(
            "meta_description"
        )
        or (
            f"Discover what "
            f"{business_name} "
            f"can do for you."
        )
    )

    page_description = str(
        page_description
    )

    h1_tags = (
        payload.get(
            "h1_tags"
        )
        or []
    )

    hero_title = (
        h1_tags[0]
        if h1_tags
        else business_name
    )

    phones = (
        payload.get(
            "phones"
        )
        or []
    )

    emails = (
        payload.get(
            "emails"
        )
        or []
    )

    socials = (
        payload.get(
            "socials"
        )
        or {}
    )

    og_image = (
        payload.get(
            "og_image"
        )
        or ""
    )

    title = html_lib.escape(
        str(title)
    )

    business_name = html_lib.escape(
        str(business_name)
    )

    hero_title = html_lib.escape(
        str(hero_title)
    )

    page_description = html_lib.escape(
        page_description
    )

    # -----------------------------------------------------
    # Image
    # -----------------------------------------------------

    if og_image:

        safe_image = html_lib.escape(
            str(og_image),
            quote=True,
        )

        image_html = f"""
        <div class="hero-image-wrap">
            <img
                src="{safe_image}"
                alt="{hero_title}"
                class="hero-image"
            />
        </div>
        """

    else:

        image_html = """
        <div class="hero-image-placeholder">
            <div class="placeholder-inner">
                <span>Modern digital presence</span>
            </div>
        </div>
        """

    # -----------------------------------------------------
    # Contact buttons
    # -----------------------------------------------------

    contact_items = ""

    if phones:

        phone_value = str(
            phones[0]
        )

        phone_href = re.sub(
            r"[^\d+]",
            "",
            phone_value,
        )

        safe_phone_href = html_lib.escape(
            phone_href,
            quote=True,
        )

        contact_items += f"""
        <a
            href="tel:{safe_phone_href}"
            class="button button-dark"
        >
            Call Us
        </a>
        """

    if emails:

        email_value = str(
            emails[0]
        )

        safe_email_value = html_lib.escape(
            email_value,
            quote=True,
        )

        contact_items += f"""
        <a
            href="mailto:{safe_email_value}"
            class="button button-primary"
        >
            Send an Enquiry
        </a>
        """

    if not contact_items:

        contact_items = """
        <a
            href="#contact"
            class="button button-primary"
        >
            Get Started
        </a>
        """

    # -----------------------------------------------------
    # Socials
    # -----------------------------------------------------

    socials_html = ""

    for label, key in [
        ("LinkedIn", "linkedin"),
        ("Instagram", "instagram"),
        ("Facebook", "facebook"),
        ("X", "twitter"),
    ]:

        social_url = socials.get(
            key
        )

        if social_url:

            safe_social_url = html_lib.escape(
                str(social_url),
                quote=True,
            )

            socials_html += f"""
            <a
                href="{safe_social_url}"
                target="_blank"
                rel="noopener noreferrer"
                class="social-link"
            >
                {label}
            </a>
            """

    # -----------------------------------------------------
    # Services
    # -----------------------------------------------------

    services_html = """
    <div class="cards">

        <article class="card">
            <div class="card-number">01</div>
            <h3>Professional Service</h3>
            <p>
                A clear, credible way to present
                your services and make it easier
                for potential customers to take
                the next step.
            </p>
        </article>

        <article class="card">
            <div class="card-number">02</div>
            <h3>Simple Customer Journey</h3>
            <p>
                Strong messaging and clear calls
                to action help visitors quickly
                understand what to do next.
            </p>
        </article>

        <article class="card">
            <div class="card-number">03</div>
            <h3>Built for Growth</h3>
            <p>
                A flexible digital foundation
                designed to support future
                marketing and business growth.
            </p>
        </article>

    </div>
    """

    # -----------------------------------------------------
    # Full HTML
    # -----------------------------------------------------

    preview_html = f"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1.0"
>

<title>{title}</title>

<meta
    name="description"
    content="{page_description}"
>

<style>

:root {{
    --ink: #111827;
    --muted: #64748b;
    --line: #e5e7eb;
    --surface: #ffffff;
    --primary: #2563eb;
}}

* {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    margin: 0;
    background: #f8fafc;
    color: var(--ink);
    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}}

a {{
    text-decoration: none;
}}

.container {{
    width: min(
        1160px,
        calc(100% - 40px)
    );
    margin: 0 auto;
}}

nav {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 0;
}}

.logo {{
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.03em;
}}

.nav-link {{
    color: var(--ink);
    font-weight: 650;
    font-size: 14px;
}}

.hero {{
    padding: 70px 0 100px;
}}

.hero-grid {{
    display: grid;
    grid-template-columns:
        minmax(0, 1.05fr)
        minmax(0, 0.95fr);
    gap: 64px;
    align-items: center;
}}

.kicker {{
    display: inline-flex;
    padding: 8px 12px;
    background: #eff6ff;
    color: #1d4ed8;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 750;
    letter-spacing: 0.02em;
    margin-bottom: 20px;
}}

h1 {{
    margin: 0;
    font-size: clamp(
        48px,
        7vw,
        84px
    );
    line-height: 0.98;
    letter-spacing: -0.055em;
}}

.hero-copy {{
    margin-top: 24px;
    color: var(--muted);
    font-size: 19px;
    line-height: 1.75;
    max-width: 620px;
}}

.actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 32px;
}}

.button {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 15px 21px;
    border-radius: 11px;
    font-weight: 750;
    font-size: 14px;
}}

.button-dark {{
    background: var(--ink);
    color: white;
}}

.button-primary {{
    background: var(--primary);
    color: white;
}}

.hero-image-wrap,
.hero-image-placeholder {{
    min-height: 440px;
    border-radius: 28px;
    overflow: hidden;
    background: #e2e8f0;
    box-shadow:
        0 25px 70px
        rgba(
            15,
            23,
            42,
            0.12
        );
}}

.hero-image {{
    width: 100%;
    height: 100%;
    min-height: 440px;
    object-fit: cover;
    display: block;
}}

.hero-image-placeholder {{
    display: flex;
    align-items: center;
    justify-content: center;
}}

.placeholder-inner {{
    width: 72%;
    height: 70%;
    border-radius: 24px;
    background:
        linear-gradient(
            135deg,
            #cbd5e1,
            #f8fafc
        );
    display: flex;
    align-items: flex-end;
    padding: 28px;
    color: #475569;
    font-weight: 700;
}}

.section {{
    padding: 100px 0;
}}

.section-label {{
    color: #2563eb;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 14px;
}}

.section-title {{
    margin: 0;
    font-size: clamp(
        36px,
        5vw,
        58px
    );
    line-height: 1;
    letter-spacing: -0.045em;
    max-width: 760px;
}}

.section-copy {{
    margin-top: 18px;
    color: var(--muted);
    font-size: 18px;
    line-height: 1.7;
    max-width: 700px;
}}

.cards {{
    display: grid;
    grid-template-columns:
        repeat(
            3,
            minmax(0, 1fr)
        );
    gap: 20px;
    margin-top: 44px;
}}

.card {{
    background: var(--surface);
    border: 1px solid var(--line);
    padding: 30px;
    border-radius: 20px;
}}

.card-number {{
    color: #2563eb;
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 26px;
}}

.card h3 {{
    margin: 0;
    font-size: 23px;
    letter-spacing: -0.03em;
}}

.card p {{
    color: var(--muted);
    line-height: 1.7;
    margin-bottom: 0;
}}

.contact {{
    margin: 40px 0 80px;
    padding: 78px 34px;
    text-align: center;
    border-radius: 30px;
    background: var(--ink);
    color: white;
}}

.contact h2 {{
    margin: 0;
    font-size: clamp(
        40px,
        5vw,
        60px
    );
    letter-spacing: -0.05em;
}}

.contact p {{
    color: #cbd5e1;
    font-size: 18px;
    line-height: 1.7;
    max-width: 620px;
    margin: 18px auto 0;
}}

.contact .button {{
    margin-top: 26px;
}}

footer {{
    padding: 40px 0;
    border-top: 1px solid var(--line);
    margin-bottom: 20px;
}}

.footer-row {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}}

.socials {{
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
}}

.social-link {{
    color: var(--muted);
    font-size: 14px;
    font-weight: 650;
}}

.copyright {{
    color: #94a3b8;
    font-size: 13px;
}}

@media (max-width: 860px) {{

    .hero {{
        padding-top: 45px;
    }}

    .hero-grid {{
        grid-template-columns: 1fr;
        gap: 42px;
    }}

    .cards {{
        grid-template-columns: 1fr;
    }}

    .hero-image-wrap,
    .hero-image-placeholder,
    .hero-image {{
        min-height: 340px;
    }}
}}

@media (max-width: 560px) {{

    .container {{
        width: min(
            100% - 28px,
            1160px
        );
    }}

    nav {{
        padding: 18px 0;
    }}

    .hero {{
        padding-bottom: 65px;
    }}

    h1 {{
        font-size: 50px;
    }}

    .hero-copy {{
        font-size: 17px;
    }}

    .actions {{
        flex-direction: column;
    }}

    .button {{
        width: 100%;
    }}

    .section {{
        padding: 70px 0;
    }}

    .contact {{
        padding: 58px 22px;
    }}

    .footer-row {{
        align-items: flex-start;
        flex-direction: column;
    }}
}}

</style>

</head>

<body>

<div class="container">

    <nav>

        <div class="logo">
            {business_name}
        </div>

        <a
            href="#contact"
            class="nav-link"
        >
            Contact
        </a>

    </nav>

    <main>

        <section class="hero">

            <div class="hero-grid">

                <div>

                    <div class="kicker">
                        Modern • Professional • Conversion-focused
                    </div>

                    <h1>
                        {hero_title}
                    </h1>

                    <p class="hero-copy">
                        {page_description}
                    </p>

                    <div class="actions">
                        {contact_items}
                    </div>

                </div>

                <div>
                    {image_html}
                </div>

            </div>

        </section>

        <section class="section">

            <div class="section-label">
                Why choose us
            </div>

            <h2 class="section-title">
                A clearer path from
                visitor to customer.
            </h2>

            <p class="section-copy">
                Present your business clearly,
                build trust quickly and make it
                simple for interested visitors
                to take the next step.
            </p>

            {services_html}

        </section>

        <section
            id="contact"
            class="contact"
        >

            <h2>
                Ready to get started?
            </h2>

            <p>
                Make it easier for customers
                to understand your value and
                contact your business.
            </p>

            <div>
                {contact_items}
            </div>

        </section>

    </main>

    <footer>

        <div class="footer-row">

            <div class="socials">
                {socials_html}
            </div>

            <div class="copyright">
                © {business_name}
            </div>

        </div>

    </footer>

</div>

</body>
</html>
"""

    return {
        "status": "success",
        "html": preview_html,
        "title": business_name,
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
async def root():

    return {
        "status": "online",
        "service": "QuickLead Intel",
        "version": "6.6.4",
        "message": (
            "Global Sales Intelligence + Data Quality Engine"
        ),
    }


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
