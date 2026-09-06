# QuickLead Intel V6 - Global Sales Intelligence + Data Quality Engine

import asyncio
import html as html_lib
import json
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
    version="6.0.2",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# =========================================================
# REGEX / KEYWORDS
# =========================================================

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+\-]+"
    r"@"
    r"[A-Za-z0-9.\-]+"
    r"\.[A-Za-z]{2,}"
)

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
    "welcome",
    "welcome to",
    "official website",
    "official site",
    "website",
    "site",
    "company",
    "your company",
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
    value = (raw_url or "").strip()

    if not value:
        return ""

    if value.startswith(
        (
            "http://",
            "https://",
        )
    ):
        return value

    return f"https://{value}"


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
        str(value),
    ).strip()


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

    return False


def clean_business_name_candidate(
    value: str,
) -> str:

    value = clean_text(
        value
    )

    if not value:
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
    ).strip()

    value = re.sub(
        r"\s+[-–—:]\s+.*$",
        "",
        value,
    ).strip()

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
        if descriptive_word in lowered:
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

    words = re.split(
        r"[-_]+",
        hostname,
    )

    if len(words) == 1:
        parts = re.findall(
            r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|\d+",
            words[0],
        )

        if parts:
            words = parts

    words = [
        word.strip()
        for word in words
        if word.strip()
    ]

    if not words:
        return ""

    result = " ".join(
        word.capitalize()
        for word in words
    )

    if looks_generic_business_name(
        result
    ):
        return ""

    return result


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
            types = [schema_type]
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
        ]:
            value = item.get(
                field
            )

            if isinstance(
                value,
                str,
            ):
                cleaned = clean_business_name_candidate(
                    value
                )

                quality = name_quality(
                    cleaned
                )

                if (
                    quality >= 50
                    and not looks_generic_business_name(
                        cleaned
                    )
                ):
                    candidates.append(
                        (
                            cleaned,
                            "json_ld",
                            95,
                        )
                    )

        brand = item.get(
            "brand"
        )

        if isinstance(
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
                    quality >= 50
                    and not looks_generic_business_name(
                        cleaned
                    )
                ):
                    candidates.append(
                        (
                            cleaned,
                            "json_ld_brand",
                            92,
                        )
                    )

    if candidates:
        candidates.sort(
            key=lambda item: (
                item[2],
                name_quality(
                    item[0]
                ),
            ),
            reverse=True,
        )

        return candidates[0]

    # -----------------------------------------------------
    # Explicit visible brand mentions
    # -----------------------------------------------------

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    brand_candidates: list[str] = []

    brand_patterns = [
        re.compile(
            r"\b(?:about|welcome\s+to|at|from|by)\s+"
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

        for pattern in brand_patterns:
            for match in pattern.finditer(
                element_text
            ):
                candidate = (
                    clean_business_name_candidate(
                        match.group(1)
                    )
                )

                if (
                    candidate
                    and not looks_generic_business_name(
                        candidate
                    )
                    and name_quality(candidate) >= 45
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

        ranked_brand_candidates = sorted(
            brand_candidates,
            key=lambda item: (
                counts.get(
                    item.casefold(),
                    0,
                ),
                name_quality(item),
            ),
            reverse=True,
        )

        if ranked_brand_candidates:
            best_brand = ranked_brand_candidates[0]

            return (
                best_brand,
                "page_brand",
                94
                if counts.get(
                    best_brand.casefold(),
                    0,
                )
                >= 2
                else 90,
            )

    # -----------------------------------------------------
    # OpenGraph site name
    # -----------------------------------------------------

    og_site_name = soup.find(
        "meta",
        attrs={
            "property": "og:site_name"
        },
    )

    if og_site_name:
        value = og_site_name.get(
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
                >= 45
                and not looks_generic_business_name(
                    cleaned
                )
            ):
                return (
                    cleaned,
                    "og_site_name",
                    90,
                )

    # -----------------------------------------------------
    # Schema itemprop name
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
            >= 50
            and not looks_generic_business_name(
                cleaned
            )
        ):
            return (
                cleaned,
                "itemprop_name",
                85,
            )

    # -----------------------------------------------------
    # Header / nav logo
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
            return (
                cleaned,
                "logo_or_brand",
                82,
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
                >= 45
                and not looks_generic_business_name(
                    cleaned
                )
            ):
                return (
                    cleaned,
                    f"meta_{attr_name}",
                    75,
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

    if footer_candidates:
        unique: dict[str, int] = {}

        for candidate, quality in footer_candidates:
            unique[candidate] = max(
                unique.get(
                    candidate,
                    0,
                ),
                quality,
            )

        ranked = sorted(
            unique.items(),
            key=lambda item: (
                item[1],
                -len(item[0]),
            ),
            reverse=True,
        )

        if ranked:
            candidate = ranked[0][0]

            return (
                candidate,
                "footer",
                70,
            )

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

    digits = re.sub(
        r"\D",
        "",
        phone,
    )

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
        if digits.startswith(
            code
        ):
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

    # -----------------------------------------------------
    # Already international.
    # -----------------------------------------------------

    if has_plus:

        detected_country = get_phone_country(
            digits
        )

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

        if 8 <= len(digits) <= 15:
            return f"+{digits}"

        return None

    # -----------------------------------------------------
    # Country-aware local conversion.
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # No country available.
    # -----------------------------------------------------

    if 8 <= len(digits) <= 15:
        return digits

    return None


# =========================================================
# PHONE EXTRACTION
# =========================================================

def extract_phone_numbers(
    soup: BeautifulSoup,
) -> list[str]:

    phones: list[str] = []
    seen_digits: set[str] = set()

    # High confidence: tel links.
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
    # Contact-region extraction.
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
        region_id = id(region)

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

        for candidate in PHONE_CANDIDATE_REGEX.findall(
            region_text
        ):
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
    # Whole-page fallback.
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

def extract_contacts(
    soup: BeautifulSoup,
) -> tuple[list[str], dict]:

    phones = extract_phone_numbers(
        soup
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

def extract_emails(
    html_content: str,
) -> list[str]:

    candidates = EMAIL_REGEX.findall(
        html_content
    )

    emails: list[str] = []
    seen: set[str] = set()

    for email in candidates:
        clean = email.strip().lower()

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

        if clean.startswith(
            (
                "example@",
                "test@",
                "user@",
                "name@",
            )
        ):
            continue

        emails.append(
            clean
        )
        seen.add(
            clean
        )

    return emails[:8]


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


def detect_locale_signals(
    soup: BeautifulSoup,
    url: str,
    phones: Optional[list[str]] = None,
) -> dict:

    html_tag = soup.find(
        "html"
    )

    language = None

    if html_tag:
        raw_lang = html_tag.get(
            "lang"
        )

        if raw_lang:
            language = clean_text(
                raw_lang
            ).lower()

    language_country = None
    language_country_confidence = (
        "None"
    )

    if language and "-" in language:
        possible = language.rsplit(
            "-",
            1,
        )[1].upper()

        if (
            len(possible) == 2
            and possible
            in set(
                TLD_COUNTRY_MAP.values()
            )
        ):
            language_country = possible
            language_country_confidence = (
                "Weak"
            )

    text = soup.get_text(
        " ",
        strip=True,
    )

    currency_patterns = {
        "USD": [
            "USD",
            "US$",
        ],
        "EUR": [
            "EUR",
            "€",
        ],
        "GBP": [
            "GBP",
            "£",
        ],
        "INR": [
            "INR",
            "₹",
            "Rs.",
            "Rs ",
            "INR.",
        ],
        "CAD": [
            "CAD",
            "C$",
        ],
        "AUD": [
            "AUD",
            "A$",
        ],
        "JPY": [
            "JPY",
            "¥",
        ],
        "CNY": [
            "CNY",
            "RMB",
        ],
        "AED": [
            "AED",
        ],
        "SAR": [
            "SAR",
        ],
        "SGD": [
            "SGD",
            "S$",
        ],
        "NZD": [
            "NZD",
            "NZ$",
        ],
        "MYR": [
            "MYR",
            "RM ",
        ],
        "BRL": [
            "BRL",
            "R$",
        ],
        "ZAR": [
            "ZAR",
        ],
        "MXN": [
            "MXN",
        ],
    }

    currency_hints: list[str] = []

    for currency, patterns in currency_patterns.items():
        if any(
            pattern in text
            for pattern in patterns
        ):
            currency_hints.append(
                currency
            )

    tld = ""

    hostname = get_domain(
        url
    )

    if "." in hostname:
        tld = hostname.rsplit(
            ".",
            1,
        )[1].lower()

    tld_country = TLD_COUNTRY_MAP.get(
        tld
    )

    explicit_countries = extract_country_names(
        text[:40000]
    )

    explicit_country = (
        explicit_countries[0]
        if explicit_countries
        else None
    )

    phone_countries: list[str] = []

    if phones:
        for phone in phones:
            country = get_phone_country(
                phone
            )

            if country:
                phone_countries.append(
                    country
                )

    phone_country = (
        max(
            set(phone_countries),
            key=phone_countries.count,
        )
        if phone_countries
        else None
    )

    evidence: dict[str, int] = {}

    def add(
        country: Optional[str],
        weight: int,
    ):
        if not country:
            return

        evidence[country] = (
            evidence.get(
                country,
                0,
            )
            + weight
        )

    add(
        phone_country,
        100,
    )

    add(
        explicit_country,
        80,
    )

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

    for currency in currency_hints:
        add(
            currency_country.get(
                currency
            ),
            35,
        )

    add(
        tld_country,
        25,
    )

    hreflang_countries: list[str] = []

    for link in soup.find_all(
        "link",
        href=True,
    ):
        hreflang = link.get(
            "hreflang"
        )

        if not hreflang:
            continue

        hreflang = str(
            hreflang
        ).lower()

        if "-" in hreflang:
            possible = hreflang.rsplit(
                "-",
                1,
            )[1].upper()

            if (
                len(possible) == 2
                and possible in set(
                    TLD_COUNTRY_MAP.values()
                )
            ):
                hreflang_countries.append(
                    possible
                )

    for country in set(
        hreflang_countries
    ):
        add(
            country,
            18,
        )

    add(
        language_country,
        5,
    )

    country_hint = None
    country_confidence = "Unknown"

    if evidence:
        country_hint = max(
            evidence,
            key=evidence.get,
        )

        score = evidence[
            country_hint
        ]

        if score >= 70:
            country_confidence = "High"
        elif score >= 35:
            country_confidence = "Medium"
        else:
            country_confidence = "Low"

    primary_currency = None
    primary_currency_symbol = None
    currency_source = "unknown"

    if currency_hints:

        primary_currency = (
            currency_hints[0]
        )

        primary_currency_symbol = (
            CURRENCY_SYMBOL_MAP.get(
                primary_currency
            )
        )

        currency_source = (
            "site_detected"
        )

    elif country_hint in COUNTRY_CURRENCY_MAP:

        (
            primary_currency,
            primary_currency_symbol,
        ) = COUNTRY_CURRENCY_MAP[
            country_hint
        ]

        currency_source = (
            "country_inferred"
        )

    country_evidence = {
        "phone_country": phone_country,
        "explicit_country": explicit_country,
        "tld_country": tld_country,
        "language_country": language_country,
        "language_country_confidence": (
            language_country_confidence
        ),
    }

    return {
        "language": language,
        "country_hint": country_hint,
        "country_confidence": country_confidence,
        "country_evidence": country_evidence,
        "currency_hints": currency_hints[:8],
        "primary_currency": primary_currency,
        "primary_currency_symbol": (
            primary_currency_symbol
        ),
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

    has_contact_path = (
        bool(
            data.get(
                "phones"
            )
        )
        or bool(
            data.get(
                "emails"
            )
        )
        or bool(
            conversion.get(
                "has_tel_link"
            )
        )
        or bool(
            conversion.get(
                "has_mailto"
            )
        )
        or bool(
            conversion.get(
                "has_whatsapp"
            )
        )
    )

    if not conversion.get(
        "has_cta"
    ):
        conversion_score -= 12
        problems.append(
            "No clear conversion CTA"
        )

    if not conversion.get(
        "has_form"
    ):
        conversion_score -= 10
        problems.append(
            "No lead capture form"
        )

    if not has_contact_path:
        conversion_score -= 10
        problems.append(
            "No obvious contact path"
        )

    if (
        not conversion.get(
            "has_conversion_link"
        )
        and not conversion.get(
            "has_booking"
        )
    ):
        conversion_score -= 5
        problems.append(
            "No clear enquiry or booking path"
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
        opportunity_score += 12
        opportunity_reasons.append(
            "No clear conversion CTA"
        )
        recommendations.append(
            "Add a strong primary CTA for the main customer action"
        )

    if not conversion.get(
        "has_form"
    ):
        opportunity_score += 16
        opportunity_reasons.append(
            "No lead capture form"
        )
        recommendations.append(
            "Add an enquiry or lead form"
        )

    if not has_contact_path:
        opportunity_score += 9
        opportunity_reasons.append(
            "Weak contact accessibility"
        )
        recommendations.append(
            "Make phone, email, WhatsApp or enquiry options more prominent"
        )

    if (
        not conversion.get(
            "has_conversion_link"
        )
        and not conversion.get(
            "has_booking"
        )
    ):
        opportunity_score += 7
        opportunity_reasons.append(
            "No clear enquiry or booking path"
        )
        recommendations.append(
            "Create a dedicated enquiry, booking or quote path"
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

    if data.get("emails"):
        opportunity_score += 2

    if data.get("phones"):
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

    if (
        not conversion.get(
            "has_form"
        )
        and not conversion.get(
            "has_cta"
        )
    ):
        best_sales_angle = (
            "Lead-generation redesign: make it easier "
            "for visitors to enquire."
        )

    elif (
        commercial_intent == "HIGH"
        and not conversion.get(
            "has_form"
        )
    ):
        best_sales_angle = (
            "High-intent commercial website with "
            "an obvious missed enquiry opportunity."
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
    # SERVICE / OFFER
    # =====================================================

    has_major_conversion_gap = (
        not conversion.get(
            "has_form"
        )
        or not conversion.get(
            "has_cta"
        )
        or (
            not conversion.get(
                "has_conversion_link"
            )
            and not conversion.get(
                "has_booking"
            )
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
        f"{outreach_business_name}'s website "
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

        "opportunity_score": opportunity_score,
        "opportunity_level": opportunity_level,

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

    target_url = normalize_url(
        raw_url
    )

    if not target_url:
        return None

    try:
        response = await client.get(
            target_url,
            headers=HEADERS,
        )

        response.raise_for_status()

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

        # -------------------------------------------------
        # Defensive compatibility handling.
        #
        # Correct tuple:
        # (business_name, source, confidence)
        #
        # Legacy broken tuple:
        # (business_name, confidence, source)
        # -------------------------------------------------

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
                # Legacy tuple:
                # (name, 95, "json_ld")
                business_name_source = third_value
                business_name_confidence = second_value

            else:
                # Correct tuple:
                # (name, "json_ld", 95)
                business_name_source = second_value
                business_name_confidence = third_value

        # -------------------------------------------------
        # Final type safety for name fields
        # -------------------------------------------------

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

        if (
            not business_name
            or looks_generic_business_name(
                business_name
            )
        ):
            inferred_name = (
                infer_business_name_from_domain(
                    final_url
                )
            )

            if inferred_name:
                business_name = inferred_name
                business_name_source = (
                    "domain_inference"
                )
                business_name_confidence = 55

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
            soup
        )

        emails = extract_emails(
            html_content
        )

        # -------------------------------------------------
        # First locale pass
        # -------------------------------------------------

        preliminary_locale = detect_locale_signals(
            soup,
            final_url,
            phones,
        )

        country_hint = preliminary_locale.get(
            "country_hint"
        )

        # -------------------------------------------------
        # Normalize phones using country evidence
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

        for region in contact_regions:
            region_text = clean_text(
                region.get_text(
                    " ",
                    strip=True,
                )
            )

            if region_text:
                raw_phone_candidates.extend(
                    PHONE_CANDIDATE_REGEX.findall(
                        region_text
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

        phones = normalized_phones[:8]

        # -------------------------------------------------
        # Final locale pass
        # -------------------------------------------------

        locale_signals = detect_locale_signals(
            soup,
            final_url,
            phones,
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

        # -------------------------------------------------
        # Raw data
        # -------------------------------------------------

        raw_data = {
            "url": final_url,
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

            "technical_signals": (
                technical_signals
            ),

            "locale_signals": (
                locale_signals
            ),

            "business_signals": (
                business_signals
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
        return {
            "url": target_url,
            "status": "Failed",
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
        timeout=25.0,
        follow_redirects=True,
    ) as client:

        result = await process_single_url(
            client,
            url,
        )

        if (
            not result
            or result.get("status")
            == "Failed"
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

    cleaned_urls = [
        normalize_url(url)
        for url in urls[:50]
        if url and url.strip()
    ]

    if not cleaned_urls:
        return {
            "results": []
        }

    semaphore = asyncio.Semaphore(
        8
    )

    async with httpx.AsyncClient(
        timeout=25.0,
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
        "version": "6.0.2",
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