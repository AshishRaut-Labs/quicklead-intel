# QuickLead Intel V3 - Global Sales Intelligence Engine

import asyncio
import html as html_lib
import re
import urllib.parse
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from html import escape


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="QuickLead Intel - Global Sales Intelligence Engine",
    version="3.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HTTP HEADERS
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
    "Accept-Language": (
        "en-US,en;q=0.9"
    ),
}


# =========================================================
# REGEX / KEYWORDS
# =========================================================

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+\-]+"
    r"@"
    r"[a-zA-Z0-9\-]+"
    r"(?:\.[a-zA-Z0-9\-]+)+"
)

# Broad enough for international websites, but validated
# afterwards so random 10-digit numbers are less likely
# to become fake phone numbers.
PHONE_CANDIDATE_REGEX = re.compile(
    r"""
    (?<![\d])
    (?:
        \+\d{1,3}[\s.\-()]*
    )?
    (?:\d[\s.\-()]*){7,15}
    (?![\d])
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
]

BUSINESS_SCHEMA_TYPES = {
    "Organization",
    "Corporation",
    "LocalBusiness",
    "ProfessionalService",
    "Service",
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
}


# =========================================================
# URL HELPERS
# =========================================================

def normalize_url(raw_url: str) -> str:
    value = (raw_url or "").strip()

    if not value:
        return ""

    if value.startswith(
        ("http://", "https://")
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
            .removeprefix("www.")
        )
    except Exception:
        return ""


# =========================================================
# BUSINESS NAME EXTRACTION
# =========================================================

def extract_business_name(
    soup: BeautifulSoup,
) -> str:
    """
    Attempts to find the actual organization/business name
    before falling back to the page title.
    """

    # -----------------------------------------------------
    # JSON-LD
    # -----------------------------------------------------

    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        raw = script.string or script.get_text()

        if not raw:
            continue

        try:
            import json

            parsed = json.loads(raw)

            candidates = []

            if isinstance(parsed, dict):
                candidates.append(parsed)

                graph = parsed.get("@graph")

                if isinstance(graph, list):
                    candidates.extend(
                        item
                        for item in graph
                        if isinstance(item, dict)
                    )

            elif isinstance(parsed, list):
                candidates.extend(
                    item
                    for item in parsed
                    if isinstance(item, dict)
                )

            for item in candidates:

                schema_type = item.get("@type")

                types = []

                if isinstance(schema_type, str):
                    types = [schema_type]

                elif isinstance(schema_type, list):
                    types = schema_type

                if any(
                    str(item_type)
                    in BUSINESS_SCHEMA_TYPES
                    for item_type in types
                ):
                    name = item.get("name")

                    if isinstance(name, str):
                        name = name.strip()

                        if 2 <= len(name) <= 150:
                            return name

        except Exception:
            continue

    # -----------------------------------------------------
    # OpenGraph site_name
    # -----------------------------------------------------

    og_site_name = soup.find(
        "meta",
        attrs={
            "property": "og:site_name"
        },
    )

    if (
        og_site_name
        and og_site_name.get("content")
    ):
        value = og_site_name["content"].strip()

        if 2 <= len(value) <= 150:
            return value

    # -----------------------------------------------------
    # Application / publisher meta
    # -----------------------------------------------------

    for attr_name in [
        "application-name",
        "author",
        "publisher",
    ]:
        tag = soup.find(
            "meta",
            attrs={"name": attr_name},
        )

        if tag and tag.get("content"):
            value = tag["content"].strip()

            if 2 <= len(value) <= 150:
                return value

    # -----------------------------------------------------
    # Header / logo text
    # -----------------------------------------------------

    selectors = [
        "header .logo",
        "header .brand",
        "header [class*='logo']",
        "header [class*='brand']",
        "nav .logo",
        "nav .brand",
    ]

    for selector in selectors:
        element = soup.select_one(selector)

        if element:
            text = element.get_text(
                " ",
                strip=True,
            )

            if 2 <= len(text) <= 100:
                return text

    # -----------------------------------------------------
    # Title fallback
    # -----------------------------------------------------

    if soup.title and soup.title.string:
        title = soup.title.string.strip()

        separators = [
            " | ",
            " - ",
            " — ",
            " – ",
            " :: ",
        ]

        for separator in separators:
            parts = [
                p.strip()
                for p in title.split(
                    separator
                )
                if p.strip()
            ]

            if len(parts) >= 2:
                # The shorter side is often the company
                # but we avoid making overly aggressive guesses.
                candidates = sorted(
                    parts,
                    key=len,
                )

                candidate = candidates[0]

                if (
                    2 <= len(candidate) <= 100
                    and len(candidate.split()) <= 12
                ):
                    return candidate

        if 2 <= len(title) <= 150:
            return title

    return ""


# =========================================================
# LOCALIZATION / COUNTRY HINTS
# =========================================================

def detect_locale_signals(
    soup: BeautifulSoup,
    url: str,
) -> dict:
    """
    Returns hints only. These are NOT used to assume
    the business is from one particular country.
    """

    language = None
    country_hint = None
    currency_hints = []

    html_tag = soup.find("html")

    if html_tag:
        lang = html_tag.get("lang")

        if lang:
            language = lang.strip().lower()

            if "-" in language:
                country_hint = (
                    language.split("-", 1)[1].upper()
                )

    # hreflang
    for link in soup.find_all(
        "link",
        href=True,
    ):
        if link.get("rel") == ["alternate"] or (
            "alternate" in link.get(
                "rel",
                [],
            )
        ):
            hreflang = link.get("hreflang")

            if hreflang:
                if "-" in hreflang:
                    possible_country = (
                        hreflang.split(
                            "-",
                            1,
                        )[1]
                        .upper()
                    )

                    if (
                        not country_hint
                        and 2
                        <= len(possible_country)
                        <= 3
                    ):
                        country_hint = possible_country

    text = soup.get_text(
        " ",
        strip=True,
    )

    currency_patterns = {
        "USD": ["$", "USD", "US$"],
        "EUR": ["€", "EUR"],
        "GBP": ["£", "GBP"],
        "INR": ["₹", "INR", "Rs."],
        "CAD": ["C$", "CAD"],
        "AUD": ["A$", "AUD"],
        "JPY": ["¥", "JPY"],
        "CNY": ["¥", "CNY", "RMB"],
        "AED": ["AED"],
        "SAR": ["SAR"],
        "SGD": ["S$", "SGD"],
        "NZD": ["NZ$", "NZD"],
    }

    for currency, patterns in currency_patterns.items():
        if any(
            pattern in text
            for pattern in patterns
        ):
            currency_hints.append(currency)

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

    tld_country_map = {
        "uk": "GB",
        "de": "DE",
        "fr": "FR",
        "it": "IT",
        "es": "ES",
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
    }

    if not country_hint:
        country_hint = tld_country_map.get(tld)

    return {
        "language": language,
        "country_hint": country_hint,
        "currency_hints": currency_hints[:5],
    }


# =========================================================
# TECH STACK
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
# TRACKER DETECTION
# =========================================================

def detect_trackers(
    html_lower: str,
) -> dict:

    return {
        "google_analytics": (
            "google-analytics.com"
            in html_lower
            or "googletagmanager.com/gtag"
            in html_lower
            or "gtag("
            in html_lower
            or "gtag.js"
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
# PHONE VALIDATION
# =========================================================

def normalize_phone_candidate(
    candidate: str,
) -> Optional[str]:

    if not candidate:
        return None

    value = candidate.strip()

    # Remove HTML artifacts / excessive punctuation
    value = value.replace(
        "\u00a0",
        " ",
    )

    digits = re.sub(
        r"\D",
        "",
        value,
    )

    # Reasonable global phone length
    if not (8 <= len(digits) <= 15):
        return None

    # Reject values consisting almost entirely of one digit
    if len(set(digits)) == 1:
        return None

    # Reject obvious date-like / ID-like fragments
    if (
        len(digits) == 10
        and digits.startswith("000")
    ):
        return None

    # Require either an explicit international prefix
    # or a reasonably formatted phone candidate.
    has_plus = value.startswith("+")

    separator_count = len(
        re.findall(
            r"[\s().\-]",
            value,
        )
    )

    # A raw contiguous number without a country code is
    # more likely to be junk in scraped HTML.
    if (
        not has_plus
        and separator_count == 0
        and len(digits) == 10
    ):
        # Still allow it if it looks like a normal phone
        # rather than an obvious technical identifier.
        if digits.startswith(
            (
                "000",
                "111",
                "123",
                "999",
            )
        ):
            return None

    return "+" + digits if has_plus else digits


def extract_phone_numbers(
    html_content: str,
    soup: BeautifulSoup,
) -> list:

    phones = []
    seen_digits = set()

    # -----------------------------------------------------
    # tel: links are highest-confidence
    # -----------------------------------------------------

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        href = anchor.get("href", "")

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
                    phones.append(normalized)
                    seen_digits.add(digits)

    # -----------------------------------------------------
    # Visible page text
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
            phones.append(normalized)
            seen_digits.add(digits)

    return phones[:5]


# =========================================================
# CONTACTS / SOCIALS
# =========================================================

def extract_contacts(
    html_content: str,
    soup: BeautifulSoup,
) -> tuple[list, dict]:

    phones = extract_phone_numbers(
        html_content,
        soup,
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

        original_href = (
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
# CONVERSION SIGNALS
# =========================================================

def extract_conversion_signals(
    soup: BeautifulSoup,
    html_lower: str,
) -> dict:

    # Forms
    form_count = len(
        soup.find_all("form")
    )

    has_form = form_count > 0

    # WhatsApp
    has_whatsapp = (
        "wa.me/" in html_lower
        or "api.whatsapp.com" in html_lower
        or "whatsapp.com/" in html_lower
    )

    # Phone links
    has_tel_link = any(
        a.get("href", "").lower().startswith(
            "tel:"
        )
        for a in soup.find_all(
            "a",
            href=True,
        )
    )

    # Email links
    has_mailto = any(
        a.get("href", "").lower().startswith(
            "mailto:"
        )
        for a in soup.find_all(
            "a",
            href=True,
        )
    )

    # Booking / appointment
    has_booking = False

    # CTA
    has_cta = False
    cta_examples = []

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

            if len(cta_examples) < 5:
                cta_examples.append(
                    text[:80]
                )

        if any(
            keyword in text
            for keyword in [
                "book",
                "appointment",
                "schedule",
                "booking",
                "reserve",
            ]
        ):
            has_booking = True

    # Conversion links
    has_conversion_link = False

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        anchor_text = anchor.get_text(
            " ",
            strip=True,
        ).lower()

        href = anchor.get(
            "href",
            "",
        ).lower()

        combined = f"{anchor_text} {href}"

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
    html_content: str,
) -> dict:

    viewport = soup.find(
        "meta",
        attrs={"name": re.compile(
            r"^viewport$",
            re.I,
        )},
    )

    canonical = soup.find(
        "link",
        rel=lambda value: (
            value
            and (
                "canonical"
                in str(value).lower()
            )
        ),
    )

    favicon = soup.find(
        "link",
        rel=lambda value: (
            value
            and (
                "icon"
                in str(value).lower()
            )
        ),
    )

    robots = soup.find(
        "meta",
        attrs={"name": re.compile(
            r"^robots$",
            re.I,
        )},
    )

    lang = soup.find("html")

    has_ssl = False

    return {
        "has_viewport": bool(viewport),
        "has_favicon": bool(favicon),
        "has_canonical": bool(canonical),
        "has_robots_meta": bool(robots),
        "html_language": (
            lang.get("lang")
            if lang
            else None
        ),
        "has_ssl": has_ssl,
    }


# =========================================================
# CONTENT / COMMERCIAL SIGNALS
# =========================================================

def extract_business_signals(
    soup: BeautifulSoup,
    business_name: str,
    title: str,
) -> dict:

    visible_text = soup.get_text(
        " ",
        strip=True,
    ).lower()

    combined = (
        f"{business_name} "
        f"{title} "
        f"{visible_text[:20000]}"
    ).lower()

    commercial_matches = []

    for keyword in COMMERCIAL_KEYWORDS:
        if keyword in combined:
            commercial_matches.append(
                keyword
            )

    # Product / service architecture
    internal_links = []

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        text = anchor.get_text(
            " ",
            strip=True,
        )

        if text:
            internal_links.append(
                text.lower()
            )

    pages_with_commercial_intent = 0

    for link_text in internal_links[:200]:
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
        )[:15],
        "commercial_navigation_signals":
            pages_with_commercial_intent,
    }


# =========================================================
# SALES INTELLIGENCE ENGINE
# =========================================================

def generate_sales_intel(
    data: dict,
) -> dict:

    problems = []
    opportunity_reasons = []
    recommendations = []

    # =====================================================
    # WEBSITE HEALTH
    # =====================================================

    # -----------------------------------------------------
    # SEO = 35
    # -----------------------------------------------------

    seo_score = 35

    title = (
        data.get("title")
        or ""
    ).strip()

    meta_description = (
        data.get("meta_description")
        or ""
    ).strip()

    h1_count = data.get(
        "h1_count",
        0,
    )

    if not title:
        seo_score -= 15
        problems.append(
            "Missing page title"
        )

    elif len(title) < 10:
        seo_score -= 10
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

    # -----------------------------------------------------
    # CONVERSION = 40
    # -----------------------------------------------------

    conversion_score = 40

    conversion = data.get(
        "conversion_signals",
        {},
    )

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
    )

    if not conversion.get(
        "has_cta"
    ):
        conversion_score -= 15
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

    # -----------------------------------------------------
    # TECHNICAL / MARKETING = 25
    # -----------------------------------------------------

    technical_score = 25

    technical = data.get(
        "technical_signals",
        {},
    )

    trackers = data.get(
        "trackers",
        {},
    )

    if not technical.get(
        "has_viewport"
    ):
        technical_score -= 12
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
        technical_score -= 3
        problems.append(
            "Favicon not detected"
        )

    has_any_marketing_tracking = any(
        trackers.values()
    )

    if not has_any_marketing_tracking:
        technical_score -= 5
        problems.append(
            "No marketing or analytics tracking detected"
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
    # This is NOT simply the inverse of website health.
    # It combines website improvement potential with
    # commercial intent.
    # =====================================================

    opportunity_score = 0

    # -----------------------------------------------------
    # WEBSITE IMPROVEMENT POTENTIAL
    # -----------------------------------------------------

    if not conversion.get(
        "has_cta"
    ):
        opportunity_score += 16
        opportunity_reasons.append(
            "No clear conversion CTA"
        )
        recommendations.append(
            "Add a strong primary CTA"
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
        opportunity_score += 8
        opportunity_reasons.append(
            "Weak contact accessibility"
        )
        recommendations.append(
            "Make contact options more prominent"
        )

    if not conversion.get(
        "has_conversion_link"
    ) and not conversion.get(
        "has_booking"
    ):
        opportunity_score += 8
        opportunity_reasons.append(
            "No clear enquiry or booking path"
        )

    if not technical.get(
        "has_viewport"
    ):
        opportunity_score += 8
        opportunity_reasons.append(
            "Mobile optimization concern"
        )

    if not meta_description:
        opportunity_score += 5
        opportunity_reasons.append(
            "Missing meta description"
        )

    elif len(meta_description) < 50:
        opportunity_score += 3
        opportunity_reasons.append(
            "Weak meta description"
        )

    if h1_count == 0:
        opportunity_score += 6
        opportunity_reasons.append(
            "Missing H1 structure"
        )

    if not technical.get(
        "has_canonical"
    ):
        opportunity_score += 3
        opportunity_reasons.append(
            "Canonical URL not detected"
        )

    if not data.get(
        "og_image"
    ):
        opportunity_score += 3
        opportunity_reasons.append(
            "No social sharing image detected"
        )

    # -----------------------------------------------------
    # MARKETING MATURITY
    # -----------------------------------------------------

    if not trackers.get(
        "google_analytics"
    ):
        opportunity_score += 3

        opportunity_reasons.append(
            "Google Analytics not detected"
        )

    if not trackers.get(
        "facebook_pixel"
    ):
        opportunity_score += 2

        opportunity_reasons.append(
            "Meta/Facebook Pixel not detected"
        )

    # -----------------------------------------------------
    # COMMERCIAL INTENT
    # -----------------------------------------------------

    business_signals = data.get(
        "business_signals",
        {},
    )

    commercial_keyword_count = (
        business_signals.get(
            "commercial_keyword_count",
            0,
        )
    )

    navigation_signals = (
        business_signals.get(
            "commercial_navigation_signals",
            0,
        )
    )

    # These are positive sales-value signals,
    # not "website is bad" signals.
    if commercial_keyword_count >= 8:
        opportunity_score += 8

    elif commercial_keyword_count >= 4:
        opportunity_score += 5

    elif commercial_keyword_count >= 2:
        opportunity_score += 3

    if navigation_signals >= 4:
        opportunity_score += 5

    elif navigation_signals >= 2:
        opportunity_score += 3

    # -----------------------------------------------------
    # HEALTH CONTRIBUTION
    # -----------------------------------------------------

    if website_score < 50:
        opportunity_score += 12

    elif website_score < 65:
        opportunity_score += 9

    elif website_score < 80:
        opportunity_score += 5

    elif website_score < 90:
        opportunity_score += 2

    # -----------------------------------------------------
    # Clamp
    # -----------------------------------------------------

    opportunity_score = max(
        0,
        min(
            100,
            opportunity_score,
        ),
    )

    # Remove duplicate reasons
    opportunity_reasons = list(
        dict.fromkeys(
            opportunity_reasons
        )
    )[:10]

    recommendations = list(
        dict.fromkeys(
            recommendations
        )
    )[:8]

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
        not conversion.get(
            "has_form"
        )
        or not conversion.get(
            "has_cta"
        )
        or not conversion.get(
            "has_conversion_link"
        )
    )

    has_major_seo_gap = (
        not meta_description
        or h1_count == 0
        or not title
    )

    if (
        opportunity_score >= 75
        and has_major_conversion_gap
    ):

        suggested_offer = (
            "Website Redesign + "
            "Lead Generation System"
        )

        suggested_price = (
            "$1,000 - $2,500"
        )

        project_value = {
            "min": 1000,
            "max": 2500,
        }

        service_reason = (
            "Strong website and conversion "
            "improvement opportunity."
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
            "The site has identifiable "
            "conversion friction."
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
            "commercially relevant improvements."
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
            "Only limited opportunities "
            "were detected."
        )

    # =====================================================
    # OUTREACH
    # =====================================================

    business_name = (
        data.get("business_name")
        or data.get("title")
        or "your business"
    )

    business_name = business_name.strip()

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

    # =====================================================
    # RETURN
    # =====================================================

    return {
        # Website
        "website_score": website_score,
        "seo_score": max(
            0,
            seo_score,
        ),
        "conversion_score": max(
            0,
            conversion_score,
        ),
        "technical_score": max(
            0,
            technical_score,
        ),

        # Sales
        "opportunity_score": opportunity_score,
        "opportunity_level": opportunity_level,

        "opportunity_reasons": opportunity_reasons,

        "recommendations": recommendations,

        "service_reason": service_reason,

        # Offer
        "suggested_offer": suggested_offer,
        "suggested_price": suggested_price,
        "project_value": project_value,

        # Problems
        "problems_found": list(
            dict.fromkeys(
                problems
            )
        ),

        # Outreach
        "personalized_pitch": pitch,
    }


# =========================================================
# EMAIL EXTRACTION
# =========================================================

def extract_emails(
    html_content: str,
) -> list:

    candidates = EMAIL_REGEX.findall(
        html_content
    )

    emails = []
    seen = set()

    for email in candidates:

        clean = email.strip().lower()

        if clean in seen:
            continue

        # Ignore obvious asset/path artifacts
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

        # Ignore obvious placeholder examples
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

    return emails[:5]


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
        # Title
        # -------------------------------------------------

        title = ""

        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # -------------------------------------------------
        # Business Name
        # -------------------------------------------------

        business_name = extract_business_name(
            soup
        )

        # -------------------------------------------------
        # Meta Description
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

        if (
            meta_tag
            and meta_tag.get("content")
        ):
            meta_description = (
                meta_tag["content"].strip()
            )

        # -------------------------------------------------
        # H1
        # -------------------------------------------------

        h1_tags = soup.find_all(
            "h1"
        )

        h1_text = [
            h1.get_text(
                " ",
                strip=True,
            )
            for h1 in h1_tags
        ]

        # -------------------------------------------------
        # OG Image
        # -------------------------------------------------

        og_image_tag = soup.find(
            "meta",
            attrs={
                "property": "og:image"
            },
        )

        og_image = None

        if (
            og_image_tag
            and og_image_tag.get("content")
        ):
            og_image = (
                og_image_tag["content"].strip()
            )

        # -------------------------------------------------
        # Contacts
        # -------------------------------------------------

        phones, socials = extract_contacts(
            html_content,
            soup,
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
                html_content,
            )
        )

        locale_signals = (
            detect_locale_signals(
                soup,
                target_url,
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
            "url": target_url,

            "domain": get_domain(
                target_url
            ),

            "business_name": (
                business_name
            ),

            "title": title,

            "meta_description":
                meta_description,

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

            "conversion_signals":
                conversion_signals,

            "technical_signals":
                technical_signals,

            "locale_signals":
                locale_signals,

            "business_signals":
                business_signals,
        }

        # -------------------------------------------------
        # Sales intelligence
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
        timeout=20.0,
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
                    else
                    "Unable to scan URL."
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

    # A concurrency limit prevents one batch from
    # hammering many websites at the same time.
    semaphore = asyncio.Semaphore(8)

    async with httpx.AsyncClient(
        timeout=20.0,
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
            href="tel:{html_lib.escape(phone_href)}"
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
            href="mailto:{html_lib.escape(email_value)}"
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
        "version": "3.0.0",
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