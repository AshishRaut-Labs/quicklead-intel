# QuickLead Intel V4 - Global Sales Intelligence Engine

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
    version="4.0.0",
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

GENERIC_NAME_PATTERNS = [
    "home",
    "homepage",
    "welcome",
    "welcome to",
    "official website",
    "official site",
    "website",
    "site",
]

DESCRIPTIVE_TITLE_WORDS = {
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

PHONE_COUNTRY_CODES = {
    "1": "US",
    "7": "RU",
    "20": "EG",
    "27": "ZA",
    "30": "GR",
    "31": "NL",
    "32": "BE",
    "33": "FR",
    "34": "ES",
    "36": "HU",
    "39": "IT",
    "40": "RO",
    "41": "CH",
    "43": "AT",
    "44": "GB",
    "45": "DK",
    "46": "SE",
    "47": "NO",
    "48": "PL",
    "49": "DE",
    "51": "PE",
    "52": "MX",
    "53": "CU",
    "54": "AR",
    "55": "BR",
    "56": "CL",
    "57": "CO",
    "58": "VE",
    "60": "MY",
    "61": "AU",
    "62": "ID",
    "63": "PH",
    "64": "NZ",
    "65": "SG",
    "66": "TH",
    "81": "JP",
    "82": "KR",
    "84": "VN",
    "86": "CN",
    "90": "TR",
    "91": "IN",
    "92": "PK",
    "93": "AF",
    "94": "LK",
    "95": "MM",
    "98": "IR",
    "211": "SS",
    "212": "MA",
    "213": "DZ",
    "216": "TN",
    "218": "LY",
    "220": "GM",
    "221": "SN",
    "222": "MR",
    "223": "ML",
    "224": "GN",
    "225": "CI",
    "226": "BF",
    "227": "NE",
    "228": "TG",
    "229": "BJ",
    "230": "MU",
    "231": "LR",
    "232": "SL",
    "233": "GH",
    "234": "NG",
    "235": "TD",
    "236": "CF",
    "237": "CM",
    "238": "CV",
    "239": "ST",
    "240": "GQ",
    "241": "GA",
    "242": "CG",
    "243": "CD",
    "244": "AO",
    "245": "GW",
    "248": "SC",
    "249": "SD",
    "250": "RW",
    "251": "ET",
    "252": "SO",
    "253": "DJ",
    "254": "KE",
    "255": "TZ",
    "256": "UG",
    "257": "BI",
    "258": "MZ",
    "260": "ZM",
    "261": "MG",
    "262": "RE",
    "263": "ZW",
    "264": "NA",
    "265": "MW",
    "266": "LS",
    "267": "BW",
    "268": "SZ",
    "269": "KM",
    "290": "SH",
    "291": "ER",
    "297": "AW",
    "298": "FO",
    "299": "GL",
    "350": "GI",
    "351": "PT",
    "352": "LU",
    "353": "IE",
    "354": "IS",
    "355": "AL",
    "356": "MT",
    "357": "CY",
    "358": "FI",
    "359": "BG",
    "370": "LT",
    "371": "LV",
    "372": "EE",
    "373": "MD",
    "374": "AM",
    "375": "BY",
    "376": "AD",
    "377": "MC",
    "378": "SM",
    "380": "UA",
    "381": "RS",
    "382": "ME",
    "383": "XK",
    "385": "HR",
    "386": "SI",
    "387": "BA",
    "389": "MK",
    "420": "CZ",
    "421": "SK",
    "423": "LI",
    "500": "FK",
    "501": "BZ",
    "502": "GT",
    "503": "SV",
    "504": "HN",
    "505": "NI",
    "506": "CR",
    "507": "PA",
    "508": "PM",
    "509": "HT",
    "590": "GP",
    "591": "BO",
    "592": "GY",
    "593": "EC",
    "594": "GF",
    "595": "PY",
    "596": "MQ",
    "597": "SR",
    "598": "UY",
    "599": "CW",
    "670": "TL",
    "672": "AQ",
    "673": "BN",
    "674": "NR",
    "675": "PG",
    "676": "TO",
    "677": "SB",
    "678": "VU",
    "679": "FJ",
    "680": "PW",
    "681": "WF",
    "682": "CK",
    "683": "NU",
    "685": "WS",
    "686": "KI",
    "687": "NC",
    "688": "TV",
    "689": "PF",
    "690": "TK",
    "691": "FM",
    "692": "MH",
    "850": "KP",
    "852": "HK",
    "853": "MO",
    "855": "KH",
    "856": "LA",
    "880": "BD",
    "886": "TW",
    "960": "MV",
    "961": "LB",
    "962": "JO",
    "963": "SY",
    "964": "IQ",
    "965": "KW",
    "966": "SA",
    "967": "YE",
    "968": "OM",
    "970": "PS",
    "971": "AE",
    "972": "IL",
    "973": "BH",
    "974": "QA",
    "975": "BT",
    "976": "MN",
    "977": "NP",
    "992": "TJ",
    "993": "TM",
    "994": "AZ",
    "995": "GE",
    "996": "KG",
    "998": "UZ",
}


# =========================================================
# URL HELPERS
# =========================================================

def normalize_url(raw_url: str) -> str:
    value = (raw_url or "").strip()

    if not value:
        return ""

    if value.startswith(("http://", "https://")):
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
# GENERIC CLEANING
# =========================================================

def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def looks_generic_business_name(value: str) -> bool:
    text = clean_text(value).lower()

    if not text:
        return True

    if len(text) < 2 or len(text) > 120:
        return True

    if text in GENERIC_NAME_PATTERNS:
        return True

    return False


def clean_business_name_candidate(
    value: str,
) -> str:
    value = clean_text(value)

    if not value:
        return ""

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

    return value


def title_candidate_quality(
    candidate: str,
) -> float:
    candidate = clean_text(candidate)

    if not candidate:
        return 0

    lowered = candidate.lower()

    if looks_generic_business_name(candidate):
        return 0

    score = 50

    words = lowered.split()

    if 1 <= len(words) <= 6:
        score += 15

    if len(words) <= 3:
        score += 10

    if any(
        word in lowered
        for word in DESCRIPTIVE_TITLE_WORDS
    ):
        score -= 20

    if re.search(
        r"\b(india|usa|uk|canada|australia|"
        r"singapore|dubai|uae|germany|france)\b",
        lowered,
    ):
        score -= 15

    if len(candidate) > 70:
        score -= 20

    return max(0, min(100, score))


# =========================================================
# BUSINESS NAME EXTRACTION
# =========================================================

def iter_jsonld_objects(
    soup: BeautifulSoup,
) -> list[dict]:
    objects: list[dict] = []

    for script in soup.find_all(
        "script",
        attrs={"type": re.compile(
            r"application/ld\+json",
            re.I,
        )},
    ):
        raw = script.string or script.get_text()

        if not raw:
            continue

        try:
            parsed = json.loads(raw)
        except Exception:
            continue

        if isinstance(parsed, dict):
            objects.append(parsed)

            graph = parsed.get("@graph")

            if isinstance(graph, list):
                objects.extend(
                    item
                    for item in graph
                    if isinstance(item, dict)
                )

        elif isinstance(parsed, list):
            objects.extend(
                item
                for item in parsed
                if isinstance(item, dict)
            )

    return objects


def extract_business_name(
    soup: BeautifulSoup,
) -> tuple[str, str, int]:

    # -----------------------------------------------------
    # 1. JSON-LD
    # -----------------------------------------------------

    schema_candidates: list[str] = []

    for item in iter_jsonld_objects(soup):
        schema_type = item.get("@type")

        if isinstance(schema_type, str):
            types = [schema_type]
        elif isinstance(schema_type, list):
            types = [
                str(value)
                for value in schema_type
            ]
        else:
            types = []

        if not any(
            item_type in BUSINESS_SCHEMA_TYPES
            for item_type in types
        ):
            continue

        for field in [
            "name",
            "legalName",
        ]:
            value = item.get(field)

            if isinstance(value, str):
                cleaned = clean_business_name_candidate(
                    value
                )

                if (
                    cleaned
                    and not looks_generic_business_name(
                        cleaned
                    )
                ):
                    schema_candidates.append(
                        cleaned
                    )

        # Nested brand
        brand = item.get("brand")

        if isinstance(brand, dict):
            brand_name = brand.get("name")

            if isinstance(brand_name, str):
                cleaned = clean_business_name_candidate(
                    brand_name
                )

                if cleaned:
                    schema_candidates.append(
                        cleaned
                    )

    if schema_candidates:
        return (
            schema_candidates[0],
            "json_ld",
            95,
        )

    # -----------------------------------------------------
    # 2. OpenGraph site name
    # -----------------------------------------------------

    og_site_name = soup.find(
        "meta",
        attrs={
            "property": "og:site_name"
        },
    )

    if og_site_name:
        value = og_site_name.get("content")

        if isinstance(value, str):
            cleaned = clean_business_name_candidate(
                value
            )

            if cleaned and not looks_generic_business_name(
                cleaned
            ):
                return (
                    cleaned,
                    "og_site_name",
                    90,
                )

    # -----------------------------------------------------
    # 3. Logo / brand metadata
    # -----------------------------------------------------

    logo_selectors = [
        '[itemprop="name"]',
        '[itemprop="brand"]',
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
        element = soup.select_one(selector)

        if not element:
            continue

        text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        text = clean_business_name_candidate(
            text
        )

        if (
            text
            and not looks_generic_business_name(text)
            and len(text) <= 100
        ):
            return (
                text,
                "logo_or_brand",
                82,
            )

    # -----------------------------------------------------
    # 4. Meta publisher / application name
    # -----------------------------------------------------

    for attr_name in [
        "application-name",
        "publisher",
    ]:
        tag = soup.find(
            "meta",
            attrs={"name": attr_name},
        )

        if not tag:
            continue

        value = tag.get("content")

        if isinstance(value, str):
            cleaned = clean_business_name_candidate(
                value
            )

            if cleaned and not looks_generic_business_name(
                cleaned
            ):
                return (
                    cleaned,
                    f"meta_{attr_name}",
                    75,
                )

    # -----------------------------------------------------
    # 5. Footer company name
    # -----------------------------------------------------

    for selector in [
        "footer",
        "[class*='footer']",
    ]:
        footer = soup.select_one(selector)

        if not footer:
            continue

        text = clean_text(
            footer.get_text(
                " ",
                strip=True,
            )
        )

        patterns = [
            r"(?:©|copyright)\s*(?:\d{4}\s*)?([A-Za-z0-9&.,'’\- ]{2,100})",
            r"(?:owned by|operated by|a division of)\s+([A-Za-z0-9&.,'’\- ]{2,100})",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.I,
            )

            if match:
                candidate = clean_text(
                    match.group(1)
                )

                candidate = re.sub(
                    r"\s*[|•·].*$",
                    "",
                    candidate,
                ).strip()

                if candidate:
                    return (
                        candidate,
                        "footer",
                        65,
                    )

    # -----------------------------------------------------
    # 6. Title intelligence
    # -----------------------------------------------------

    title = ""

    if soup.title:
        title = clean_text(
            soup.title.get_text()
        )

    title_candidates: list[tuple[str, float]] = []

    if title:
        separators = [
            " | ",
            " - ",
            " — ",
            " – ",
            " :: ",
        ]

        for separator in separators:
            parts = [
                clean_text(part)
                for part in title.split(separator)
                if clean_text(part)
            ]

            if len(parts) >= 2:
                for part in parts:
                    quality = title_candidate_quality(
                        part
                    )

                    if quality > 0:
                        title_candidates.append(
                            (part, quality)
                        )

    if title_candidates:
        title_candidates.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        candidate, quality = title_candidates[0]

        # Do not use a purely descriptive title
        if quality >= 45:
            return (
                candidate,
                "title_inference",
                int(min(60, quality)),
            )

    # -----------------------------------------------------
    # 7. Final domain fallback
    # -----------------------------------------------------

    return (
        "",
        "unknown",
        0,
    )


# =========================================================
# COUNTRY / LOCALIZATION
# =========================================================

def get_phone_country(
    phone: str,
) -> Optional[str]:
    digits = re.sub(r"\D", "", phone)

    if not digits:
        return None

    for length in [3, 2, 1]:
        prefix = digits[:length]

        if prefix in PHONE_COUNTRY_CODES:
            return PHONE_COUNTRY_CODES[prefix]

    return None


def extract_country_names(
    text: str,
) -> list[str]:
    lowered = clean_text(text).lower()
    found: list[str] = []

    for name, code in COUNTRY_NAMES.items():
        if re.search(
            rf"\b{re.escape(name)}\b",
            lowered,
        ):
            found.append(code)

    return list(dict.fromkeys(found))


def detect_locale_signals(
    soup: BeautifulSoup,
    url: str,
    phones: Optional[list[str]] = None,
) -> dict:

    html_tag = soup.find("html")

    language = None

    if html_tag:
        raw_lang = html_tag.get("lang")

        if raw_lang:
            language = clean_text(
                raw_lang
            ).lower()

    # -----------------------------------------------------
    # Important:
    # `en-us` is LANGUAGE metadata, not proof that
    # the company itself is in the US.
    # -----------------------------------------------------

    language_country = None

    if language and "-" in language:
        possible = language.rsplit(
            "-",
            1,
        )[1].upper()

        if (
            len(possible) == 2
            and possible in set(
                TLD_COUNTRY_MAP.values()
            )
        ):
            language_country = possible

    currency_hints: list[str] = []

    text = soup.get_text(
        " ",
        strip=True,
    )

    currency_patterns = {
        "USD": [
            "$",
            "USD",
            "US$",
        ],
        "EUR": [
            "€",
            "EUR",
        ],
        "GBP": [
            "£",
            "GBP",
        ],
        "INR": [
            "₹",
            "INR",
            "Rs.",
            "Rs ",
        ],
        "CAD": [
            "C$",
            "CAD",
        ],
        "AUD": [
            "A$",
            "AUD",
        ],
        "JPY": [
            "¥",
            "JPY",
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
            "S$",
            "SGD",
        ],
        "NZD": [
            "NZ$",
            "NZD",
        ],
        "MYR": [
            "MYR",
            "RM ",
        ],
        "BRL": [
            "R$",
            "BRL",
        ],
        "ZAR": [
            "ZAR",
            "R ",
        ],
    }

    for currency, patterns in currency_patterns.items():
        if any(
            pattern in text
            for pattern in patterns
        ):
            currency_hints.append(
                currency
            )

    # -----------------------------------------------------
    # TLD
    # -----------------------------------------------------

    tld = ""

    try:
        hostname = get_domain(url)

        if "." in hostname:
            tld = hostname.rsplit(
                ".",
                1,
            )[1].lower()
    except Exception:
        pass

    tld_country = TLD_COUNTRY_MAP.get(
        tld
    )

    # -----------------------------------------------------
    # Explicit country mentions
    # -----------------------------------------------------

    explicit_countries = extract_country_names(
        text[:30000]
    )

    explicit_country = (
        explicit_countries[0]
        if explicit_countries
        else None
    )

    # -----------------------------------------------------
    # Phone country
    # -----------------------------------------------------

    phone_country = None

    if phones:
        phone_votes: dict[str, int] = {}

        for phone in phones:
            country = get_phone_country(
                phone
            )

            if country:
                phone_votes[country] = (
                    phone_votes.get(country, 0) + 1
                )

        if phone_votes:
            phone_country = max(
                phone_votes,
                key=phone_votes.get,
            )

    # -----------------------------------------------------
    # Evidence scoring
    #
    # Phone > explicit address/country > currency
    # > TLD > hreflang > language
    # -----------------------------------------------------

    evidence: dict[str, int] = {}

    def add_evidence(
        country: Optional[str],
        weight: int,
    ) -> None:
        if not country:
            return

        evidence[country] = (
            evidence.get(country, 0)
            + weight
        )

    add_evidence(phone_country, 100)
    add_evidence(explicit_country, 80)

    # Currency-to-country hints
    currency_country_map = {
        "USD": "US",
        "EUR": "EU",
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
    }

    for currency in currency_hints:
        add_evidence(
            currency_country_map.get(
                currency
            ),
            35,
        )

    add_evidence(tld_country, 25)

    # hreflang
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
            country = hreflang.rsplit(
                "-",
                1,
            )[1].upper()

            if len(country) == 2:
                hreflang_countries.append(
                    country
                )

    if hreflang_countries:
        for country in set(
            hreflang_countries
        ):
            add_evidence(
                country,
                18,
            )

    add_evidence(
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

        winning_score = evidence[
            country_hint
        ]

        if winning_score >= 100:
            country_confidence = "High"
        elif winning_score >= 70:
            country_confidence = "High"
        elif winning_score >= 35:
            country_confidence = "Medium"
        else:
            country_confidence = "Low"

        # EU is a currency-region hint,
        # not an actual country.
        if country_hint == "EU":
            country_hint = None
            country_confidence = "Unknown"

    return {
        "language": language,
        "country_hint": country_hint,
        "country_confidence": country_confidence,
        "country_evidence": {
            "phone_country": phone_country,
            "explicit_country": explicit_country,
            "tld_country": tld_country,
            "language_country": language_country,
        },
        "currency_hints": currency_hints[:8],
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
            "google-analytics.com" in html_lower
            or "googletagmanager.com/gtag" in html_lower
            or "gtag(" in html_lower
            or "gtag.js" in html_lower
            or "google-analytics" in html_lower
        ),
        "facebook_pixel": (
            "connect.facebook.net" in html_lower
            or "fbevents.js" in html_lower
            or "fbq(" in html_lower
        ),
        "google_tag_manager": (
            "googletagmanager.com" in html_lower
            or "gtm-" in html_lower
        ),
        "linkedin_insight": (
            "snap.licdn.com" in html_lower
            or "lintrk" in html_lower
            or "linkedininsighttag" in html_lower
        ),
        "hubspot": (
            "js.hs-scripts.com" in html_lower
            or "_hsq" in html_lower
            or "hubspotutk" in html_lower
        ),
    }


# =========================================================
# PHONE NORMALIZATION
# =========================================================

def normalize_phone_candidate(
    candidate: str,
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

    if not (8 <= len(digits) <= 15):
        return None

    # Obvious junk
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

    # Reject numbers that are clearly dates
    if len(digits) == 8 and re.match(
        r"^(19|20)\d{6}$",
        digits,
    ):
        return None

    has_plus = value.startswith("+")
    separators = len(
        re.findall(
            r"[\s().\-]",
            value,
        )
    )

    # A bare 10-digit number can be legitimate,
    # but only accept it when the surrounding text
    # strongly looks like a phone.
    if (
        not has_plus
        and separators == 0
        and len(digits) == 10
    ):
        if digits.startswith(
            (
                "000",
                "111",
                "123",
                "999",
            )
        ):
            return None

    if has_plus:
        return f"+{digits}"

    return digits


def extract_phone_numbers(
    soup: BeautifulSoup,
) -> list[str]:

    phones: list[str] = []
    seen_digits: set[str] = set()

    # -----------------------------------------------------
    # 1. tel: links
    # -----------------------------------------------------

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        href = clean_text(
            anchor.get("href", "")
        )

        if href.lower().startswith("tel:"):
            raw = urllib.parse.unquote(
                href[4:]
            ).strip()

            normalized = normalize_phone_candidate(
                raw
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
    # 2. Visible text
    # -----------------------------------------------------

    visible_text = soup.get_text(
        " ",
        strip=True,
    )

    for candidate in PHONE_CANDIDATE_REGEX.findall(
        visible_text
    ):
        normalized = normalize_phone_candidate(
            candidate
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

    return phones[:8]


# =========================================================
# CONTACTS / SOCIALS
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
            anchor.get("href", "")
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

        emails.append(clean)
        seen.add(clean)

    return emails[:8]


# =========================================================
# CONVERSION SIGNALS
# =========================================================

def extract_conversion_signals(
    soup: BeautifulSoup,
    html_lower: str,
) -> dict:

    form_count = len(
        soup.find_all("form")
    )

    has_form = form_count > 0

    has_whatsapp = (
        "wa.me/" in html_lower
        or "api.whatsapp.com" in html_lower
        or "whatsapp.com/" in html_lower
    )

    has_tel_link = any(
        str(
            anchor.get("href", "")
        ).lower().startswith("tel:")
        for anchor in soup.find_all(
            "a",
            href=True,
        )
    )

    has_mailto = any(
        str(
            anchor.get("href", "")
        ).lower().startswith("mailto:")
        for anchor in soup.find_all(
            "a",
            href=True,
        )
    )

    has_booking = False
    has_cta = False

    cta_examples: list[str] = []

    for tag in soup.find_all(
        ["a", "button", "input"],
    ):
        text = (
            tag.get_text(
                " ",
                strip=True,
            )
            or tag.get("value", "")
            or tag.get("aria-label", "")
            or tag.get("title", "")
        )

        text = clean_text(
            text
        ).lower()

        if not text:
            continue

        matched = [
            keyword
            for keyword in CTA_KEYWORDS
            if keyword in text
        ]

        if matched:
            has_cta = True

            if len(cta_examples) < 6:
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
            anchor.get("href", "")
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
# TECHNICAL SIGNALS
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

    html_tag = soup.find("html")

    html_language = None

    if html_tag:
        raw_lang = html_tag.get("lang")

        if raw_lang:
            html_language = clean_text(
                raw_lang
            ).lower()

    has_ssl = final_url.lower().startswith(
        "https://"
    )

    return {
        "has_viewport": bool(viewport),
        "has_favicon": bool(favicon),
        "has_canonical": bool(canonical),
        "has_robots_meta": bool(robots),
        "html_language": html_language,
        "has_ssl": has_ssl,
    }


# =========================================================
# BUSINESS / COMMERCIAL SIGNALS
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

    pages_with_commercial_intent = 0

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
            ]
        ):
            pages_with_commercial_intent += 1

    return {
        "commercial_keyword_count": len(
            set(commercial_matches)
        ),
        "commercial_keywords": list(
            dict.fromkeys(
                commercial_matches
            )
        )[:20],
        "commercial_navigation_signals": (
            pages_with_commercial_intent
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
        data.get("title", "")
    )

    meta_description = clean_text(
        data.get(
            "meta_description",
            "",
        )
    )

    h1_count = int(
        data.get(
            "h1_count",
            0,
        )
    )

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

    # =====================================================
    # WEBSITE HEALTH
    # =====================================================

    # -----------------------------
    # SEO 35
    # -----------------------------

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

    # -----------------------------
    # CONVERSION 40
    # -----------------------------

    conversion_score = 40

    has_contact_path = (
        bool(data.get("phones"))
        or bool(data.get("emails"))
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

    # -----------------------------
    # TECHNICAL / MARKETING 25
    # -----------------------------

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

    has_any_tracking = any(
        bool(value)
        for value in trackers.values()
    )

    if not has_any_tracking:
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
    # SALES OPPORTUNITY
    #
    # This is deliberately independent from
    # Website Health.
    # =====================================================

    opportunity_score = 0

    # -----------------------------
    # Conversion opportunity
    # -----------------------------

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

    # -----------------------------
    # SEO opportunity
    # -----------------------------

    if not meta_description:
        opportunity_score += 5
        opportunity_reasons.append(
            "Missing meta description"
        )
        recommendations.append(
            "Rewrite the meta title and meta description for search and conversion"
        )
    elif len(meta_description) < 50:
        opportunity_score += 3
        opportunity_reasons.append(
            "Weak meta description"
        )
        recommendations.append(
            "Improve the meta description to better communicate the offer"
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

    # -----------------------------
    # Marketing maturity
    # -----------------------------

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

    # -----------------------------
    # Commercial intent
    # -----------------------------

    business_signals = data.get(
        "business_signals",
        {},
    )

    commercial_keyword_count = int(
        business_signals.get(
            "commercial_keyword_count",
            0,
        )
    )

    navigation_signals = int(
        business_signals.get(
            "commercial_navigation_signals",
            0,
        )
    )

    if commercial_keyword_count >= 10:
        opportunity_score += 9
        opportunity_reasons.append(
            "Strong commercial intent detected"
        )
    elif commercial_keyword_count >= 6:
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

    # -----------------------------
    # Health contribution
    # -----------------------------

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

    # -----------------------------
    # Strong business contact evidence
    # -----------------------------

    if data.get("emails"):
        opportunity_score += 2

    if data.get("phones"):
        opportunity_score += 2

    if (
        conversion.get("has_whatsapp")
    ):
        opportunity_score += 2

    # -----------------------------
    # Clamp
    # -----------------------------

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
    # SERVICE RECOMMENDATION
    # =====================================================

    has_major_conversion_gap = (
        not conversion.get("has_form")
        or not conversion.get("has_cta")
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
        }

        service_reason = (
            "The website has measurable marketing and "
            "conversion improvements available."
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
        }

        service_reason = (
            "The website has smaller but "
            "commercially relevant improvement opportunities."
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
        }

        service_reason = (
            "Only limited commercial opportunities "
            "were detected."
        )

    # =====================================================
    # OUTREACH
    # =====================================================

    business_name = clean_text(
        data.get(
            "business_name",
            "",
        )
    )

    if not business_name:
        business_name = "your business"

    display_reason = (
        opportunity_reasons[0]
        if opportunity_reasons
        else "a few opportunities to improve the website"
    )

    pitch = (
        f"Hi, I was reviewing {business_name}'s website "
        f"and noticed {display_reason.lower()}. "
        f"For a business with a commercial website, "
        f"that can create unnecessary friction for people "
        f"who are ready to enquire or buy. "
        f"I put together a few ideas for improving the "
        f"customer journey and conversion flow. "
        f"Would you be open to seeing a quick preview?"
    )

    return {
        "website_score": website_score,
        "seo_score": seo_score,
        "conversion_score": conversion_score,
        "technical_score": technical_score,
        "opportunity_score": opportunity_score,
        "opportunity_level": opportunity_level,
        "opportunity_reasons": opportunity_reasons,
        "recommendations": recommendations,
        "service_reason": service_reason,
        "suggested_offer": suggested_offer,
        "suggested_price": suggested_price,
        "project_value": project_value,
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

        # -------------------------------------------------
        # Final resolved URL
        # -------------------------------------------------

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

        (
            business_name,
            business_name_source,
            business_name_confidence,
        ) = extract_business_name(
            soup
        )

        # -------------------------------------------------
        # Meta description
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

            if isinstance(content, str):
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

            if isinstance(content, str):
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
        # Signals
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

        locale_signals = (
            detect_locale_signals(
                soup,
                final_url,
                phones,
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
            "h1_count": len(h1_tags),
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

        # -------------------------------------------------
        # Intelligence
        # -------------------------------------------------

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
                    result.get("error")
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

    semaphore = asyncio.Semaphore(8)

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

    title = (
        payload.get("business_name")
        or payload.get("title")
        or "Your Business"
    )

    business_name = (
        payload.get("business_name")
        or payload.get("title")
        or "Your Business"
    )

    title = html_lib.escape(
        str(title)
    )

    business_name = html_lib.escape(
        str(business_name)
    )

    page_description = (
        payload.get(
            "meta_description"
        )
        or (
            f"Discover what "
            f"{html_lib.unescape(business_name)} "
            f"can do for you."
        )
    )

    page_description = html_lib.escape(
        str(page_description)
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
        else (
            payload.get(
                "business_name"
            )
            or payload.get(
                "title"
            )
            or "Your Business"
        )
    )

    hero_title = html_lib.escape(
        str(hero_title)
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

    # -----------------------------------------------------
    # Image
    # -----------------------------------------------------

    image_html = ""

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

        contact_items += f"""
        <a
            href="tel:{html_lib.escape(phone_href, quote=True)}"
            class="button button-dark"
        >
            Call Us
        </a>
        """

    if emails:
        email_value = str(
            emails[0]
        )

        contact_items += f"""
        <a
            href="mailto:{html_lib.escape(email_value, quote=True)}"
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
            socials_html += f"""
            <a
                href="{html_lib.escape(
                    str(social_url),
                    quote=True,
                )}"
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
    --surface-soft: #f8fafc;
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
    width: min(1160px, calc(100% - 40px));
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
    font-size: clamp(48px, 7vw, 84px);
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
        rgba(15, 23, 42, 0.12);
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
    font-size: clamp(36px, 5vw, 58px);
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
        repeat(3, minmax(0, 1fr));
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
    font-size: clamp(40px, 5vw, 60px);
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
        "version": "4.0.0",
        "message": (
            "Global Sales Intelligence Engine"
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