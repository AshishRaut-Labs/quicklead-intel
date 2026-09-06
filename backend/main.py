# QuickLead Intel V2 - Sales Engine

import asyncio
import re
import urllib.parse

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from html import escape

app = FastAPI(title="QuickLead Intel V2 - Sales Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

PHONE_REGEX = re.compile(
    r"(?<![\d.])(?:\+?\d{1,3}[-.\s]?)?"
    r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?![\d.])"
)

CTA_KEYWORDS = [
    "book",
    "demo",
    "contact",
    "quote",
    "get started",
    "buy now",
    "schedule",
    "call",
    "learn more",
    "request",
    "enquire",
    "inquire",
]


# ---------------------------------------------------------
# TECH STACK DETECTION
# ---------------------------------------------------------

def detect_tech_stack(html_lower: str) -> dict:
    return {
        "wordpress": (
            "wp-content" in html_lower
            or "wp-includes" in html_lower
        ),
        "shopify": (
            "cdn.shopify.com" in html_lower
            or "myshopify.com" in html_lower
        ),
        "nextjs": (
            "__next_data__" in html_lower
            or "/_next/static/" in html_lower
        ),
    }


# ---------------------------------------------------------
# TRACKER DETECTION
# ---------------------------------------------------------

def detect_trackers(html_lower: str) -> dict:
    return {
        "google_analytics": (
            "google-analytics.com" in html_lower
            or "gtag(" in html_lower
            or "ua-" in html_lower
            or "g-" in html_lower
        ),
        "facebook_pixel": (
            "fbevents.js" in html_lower
            or "fbq(" in html_lower
        ),
        "google_tag_manager": (
            "googletagmanager.com/gtm.js" in html_lower
        ),
        "linkedin_insight": (
            "snap.licdn.com" in html_lower
            or "lintrk" in html_lower
        ),
        "hubspot": (
            "js.hs-scripts.com" in html_lower
            or "_hsq" in html_lower
        ),
    }


# ---------------------------------------------------------
# CONVERSION SIGNALS
# ---------------------------------------------------------

def extract_conversion_signals(
    soup: BeautifulSoup,
    html_lower: str
) -> dict:

    has_form = len(soup.find_all("form")) > 0

    has_whatsapp = (
        "wa.me/" in html_lower
        or "api.whatsapp.com" in html_lower
    )

    has_cta = False

    for tag in soup.find_all(["a", "button"]):
        text = tag.get_text(" ", strip=True).lower()

        if text and any(
            keyword in text
            for keyword in CTA_KEYWORDS
        ):
            has_cta = True
            break

    return {
        "has_form": has_form,
        "has_whatsapp": has_whatsapp,
        "has_cta": has_cta,
    }


# ---------------------------------------------------------
# TECHNICAL SIGNALS
# ---------------------------------------------------------

def extract_technical_signals(
    soup: BeautifulSoup
) -> dict:

    has_viewport = bool(
        soup.find(
            "meta",
            attrs={"name": "viewport"}
        )
    )

    has_favicon = bool(
        soup.find(
            "link",
            rel=lambda x: (
                x and "icon" in str(x).lower()
            )
        )
    )

    has_canonical = bool(
        soup.find(
            "link",
            rel="canonical"
        )
    )

    return {
        "has_viewport": has_viewport,
        "has_favicon": has_favicon,
        "has_canonical": has_canonical,
    }


# ---------------------------------------------------------
# SALES INTELLIGENCE ENGINE
# ---------------------------------------------------------

def generate_sales_intel(data: dict) -> dict:
    """
    Generates:

    - Website Health Score
    - Sales Opportunity Score
    - Opportunity Level
    - Opportunity Reasons
    - Problems Found
    - Recommended Offer
    - Suggested Price
    - Estimated Project Value
    - Personalized Outreach
    """

    problems = []

    # =====================================================
    # WEBSITE HEALTH SCORE
    # =====================================================

    # SEO = 35 points
    seo_score = 35

    if not data.get("title") or len(data["title"]) < 10:
        seo_score -= 15
        problems.append(
            "Missing or weak page title"
        )

    if (
        not data.get("meta_description")
        or len(data["meta_description"]) < 50
    ):
        seo_score -= 10
        problems.append(
            "Missing or weak meta description"
        )

    h1_count = data.get("h1_count", 0)

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

    # Conversion = 40 points
    conv_score = 40

    conv_signals = data.get(
        "conversion_signals",
        {}
    )

    if not conv_signals.get("has_cta"):
        conv_score -= 20
        problems.append(
            "No clear Call-to-Action (CTA)"
        )

    if not conv_signals.get("has_form"):
        conv_score -= 10
        problems.append(
            "No lead capture form"
        )

    if (
        not data.get("phones")
        and not data.get("emails")
    ):
        conv_score -= 10
        problems.append(
            "No visible contact information"
        )

    # Technical / Marketing = 25 points
    tech_score = 25

    tech_signals = data.get(
        "technical_signals",
        {}
    )

    trackers = data.get(
        "trackers",
        {}
    )

    if not tech_signals.get("has_viewport"):
        tech_score -= 15
        problems.append(
            "Missing mobile viewport configuration"
        )

    if (
        not trackers.get("google_analytics")
        and not trackers.get("facebook_pixel")
    ):
        tech_score -= 10
        problems.append(
            "No marketing tracking detected"
        )

    website_score = max(
        0,
        min(
            100,
            seo_score + conv_score + tech_score
        )
    )

    # =====================================================
    # SALES OPPORTUNITY SCORE
    # =====================================================

    opportunity_score = 0
    opportunity_reasons = []

    # Major sales opportunities
    if not conv_signals.get("has_cta"):
        opportunity_score += 20
        opportunity_reasons.append(
            "Weak or missing CTA"
        )

    if not conv_signals.get("has_form"):
        opportunity_score += 15
        opportunity_reasons.append(
            "No lead capture form"
        )

    if (
        not data.get("phones")
        and not data.get("emails")
    ):
        opportunity_score += 10
        opportunity_reasons.append(
            "Weak contact accessibility"
        )

    if not conv_signals.get("has_whatsapp"):
        opportunity_score += 5
        opportunity_reasons.append(
            "No WhatsApp conversion path"
        )

    if not trackers.get("google_analytics"):
        opportunity_score += 5
        opportunity_reasons.append(
            "Google Analytics not detected"
        )

    if not trackers.get("facebook_pixel"):
        opportunity_score += 5
        opportunity_reasons.append(
            "Facebook Pixel not detected"
        )

    if not tech_signals.get("has_viewport"):
        opportunity_score += 10
        opportunity_reasons.append(
            "Mobile optimization concern"
        )

    if not data.get("title") or len(data["title"]) < 10:
        opportunity_score += 5
        opportunity_reasons.append(
            "Weak page title"
        )

    if (
        not data.get("meta_description")
        or len(data["meta_description"]) < 50
    ):
        opportunity_score += 5
        opportunity_reasons.append(
            "Weak meta description"
        )

    if h1_count == 0:
        opportunity_score += 5
        opportunity_reasons.append(
            "Missing H1 structure"
        )

    if not data.get("og_image"):
        opportunity_score += 3
        opportunity_reasons.append(
            "No social/OG image detected"
        )

    # Website health contributes to opportunity
    if website_score < 50:
        opportunity_score += 12
    elif website_score < 70:
        opportunity_score += 7
    elif website_score < 85:
        opportunity_score += 3

    opportunity_score = max(
        0,
        min(
            100,
            opportunity_score
        )
    )

    # =====================================================
    # OPPORTUNITY LEVEL
    # =====================================================

    if opportunity_score >= 80:
        opportunity_level = "HOT"
    elif opportunity_score >= 60:
        opportunity_level = "HIGH"
    elif opportunity_score >= 40:
        opportunity_level = "MEDIUM"
    else:
        opportunity_level = "LOW"

    # =====================================================
    # RECOMMENDED OFFER
    # =====================================================

    if opportunity_score >= 80:
        suggested_offer = (
            "Full Website Redesign & "
            "Conversion System"
        )

        suggested_price = "$1,200 - $2,500"

        project_value = {
            "min": 1200,
            "max": 2500,
        }

    elif opportunity_score >= 60:
        suggested_offer = (
            "Website Redesign + "
            "Lead Capture Improvements"
        )

        suggested_price = "$750 - $1,500"

        project_value = {
            "min": 750,
            "max": 1500,
        }

    elif opportunity_score >= 40:
        suggested_offer = (
            "Conversion Optimization & "
            "SEO Improvements"
        )

        suggested_price = "$500 - $900"

        project_value = {
            "min": 500,
            "max": 900,
        }

    else:
        suggested_offer = (
            "Website Growth Optimization"
        )

        suggested_price = "$250 - $500"

        project_value = {
            "min": 250,
            "max": 500,
        }

    # =====================================================
    # PERSONALIZED OUTREACH
    # =====================================================

    if opportunity_reasons:

        top_reason = (
            opportunity_reasons[0]
        )

        pitch = (
            f"Hi there, I reviewed your website "
            f"and noticed {top_reason.lower()}. "
            f"That may be creating unnecessary "
            f"friction for potential customers. "
            f"I put together a few improvements "
            f"that could make the site generate "
            f"more enquiries. Would you be open "
            f"to seeing a quick preview?"
        )

    else:

        pitch = (
            "I reviewed your website and found "
            "a few opportunities to improve "
            "lead generation and conversion. "
            "I'd be happy to show you a quick "
            "preview."
        )

    return {
        "website_score": website_score,
        "seo_score": seo_score,
        "conversion_score": conv_score,

        "opportunity_score": opportunity_score,
        "opportunity_level": opportunity_level,
        "opportunity_reasons": opportunity_reasons,

        "suggested_offer": suggested_offer,
        "suggested_price": suggested_price,

        "project_value": project_value,

        "problems_found": problems,

        "personalized_pitch": pitch,
    }


# ---------------------------------------------------------
# CONTACT EXTRACTION
# ---------------------------------------------------------

def extract_contacts(
    html_content: str,
    soup: BeautifulSoup
) -> tuple[list, dict]:

    phones = []

    # tel: links
    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"]

        if href.startswith("tel:"):

            raw_tel = (
                href.replace(
                    "tel:",
                    ""
                ).strip()
            )

            decoded_tel = (
                urllib.parse.unquote(
                    raw_tel
                )
            )

            if decoded_tel not in phones:
                phones.append(
                    decoded_tel
                )

    # Regex phone detection
    raw_phones = PHONE_REGEX.findall(
        html_content
    )

    for phone in raw_phones:

        cleaned = phone.strip()

        digits = re.sub(
            r"\D",
            "",
            cleaned
        )

        if (
            10 <= len(digits) <= 15
            and cleaned not in phones
        ):
            phones.append(cleaned)

    socials = {
        "linkedin": None,
        "twitter": None,
        "instagram": None,
        "facebook": None,
    }

    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"].lower()

        if (
            "linkedin.com/company" in href
            or "linkedin.com/in" in href
        ):
            socials["linkedin"] = (
                socials.get("linkedin")
                or a["href"]
            )

        elif (
            (
                "twitter.com/" in href
                or "x.com/" in href
            )
            and "status" not in href
        ):
            socials["twitter"] = (
                socials.get("twitter")
                or a["href"]
            )

        elif "instagram.com/" in href:
            socials["instagram"] = (
                socials.get("instagram")
                or a["href"]
            )

        elif "facebook.com/" in href:
            socials["facebook"] = (
                socials.get("facebook")
                or a["href"]
            )

    return phones[:3], socials


# ---------------------------------------------------------
# SINGLE URL PROCESSOR
# ---------------------------------------------------------

async def process_single_url(
    client: httpx.AsyncClient,
    raw_url: str
) -> dict:

    target_url = raw_url.strip()

    if not target_url:
        return None

    if not target_url.startswith(
        ("http://", "https://")
    ):
        target_url = (
            f"https://{target_url}"
        )

    try:

        response = await client.get(
            target_url,
            headers=HEADERS
        )

        response.raise_for_status()

        html_content = response.text
        html_lower = html_content.lower()

        soup = BeautifulSoup(
            html_content,
            "html.parser"
        )

        # Page title
        title = ""

        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Meta description
        meta_tag = (
            soup.find(
                "meta",
                attrs={
                    "name": re.compile(
                        r"^description$",
                        re.I
                    )
                }
            )
            or soup.find(
                "meta",
                attrs={
                    "property": re.compile(
                        r"^og:description$",
                        re.I
                    )
                }
            )
        )

        meta_desc = ""

        if (
            meta_tag
            and meta_tag.get("content")
        ):
            meta_desc = (
                meta_tag["content"].strip()
            )

        # H1s
        h1_tags = soup.find_all("h1")

        # OG image
        og_image_tag = soup.find(
            "meta",
            attrs={
                "property": "og:image"
            }
        )

        # Contacts
        phones, socials = extract_contacts(
            html_content,
            soup
        )

        # Emails
        emails = list({
            email
            for email in EMAIL_REGEX.findall(
                html_content
            )
            if not email.lower().endswith(
                (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".webp",
                    ".gif",
                    ".svg",
                )
            )
        })[:3]

        raw_data = {
            "url": target_url,

            "title": title,

            "meta_description": meta_desc,

            "h1_count": len(h1_tags),

            "h1_tags": [
                h1.get_text(
                    " ",
                    strip=True
                )
                for h1 in h1_tags
            ][:5],

            "og_image": (
                og_image_tag["content"]
                if (
                    og_image_tag
                    and og_image_tag.get("content")
                )
                else None
            ),

            "phones": phones,

            "emails": emails,

            "socials": socials,

            "tech_stack": detect_tech_stack(
                html_lower
            ),

            "trackers": detect_trackers(
                html_lower
            ),

            "conversion_signals":
                extract_conversion_signals(
                    soup,
                    html_lower
                ),

            "technical_signals":
                extract_technical_signals(
                    soup
                ),
        }

        # Sales intelligence
        intel = generate_sales_intel(
            raw_data
        )

        return {
            **raw_data,
            "status": "Success",
            "intelligence": intel,
        }

    except Exception as e:

        return {
            "url": target_url,
            "status": "Failed",
            "error": str(e),
        }


# ---------------------------------------------------------
# SINGLE SCAN API
# ---------------------------------------------------------

@app.get("/api/scan")
async def scan_target(
    url: str = Query(
        ...,
        description="Target URL to scan"
    )
):

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True
    ) as client:

        result = await process_single_url(
            client,
            url
        )

        if (
            not result
            or result.get("status") == "Failed"
        ):
            raise HTTPException(
                status_code=500,
                detail=(
                    result.get("error")
                    if result
                    else "Unable to scan URL."
                )
            )

        return result


# ---------------------------------------------------------
# BULK SCAN API
# ---------------------------------------------------------

@app.post("/api/bulk-scan")
async def bulk_scan_targets(
    urls: list[str] = Body(
        ...,
        description="List of URLs to scan in bulk"
    )
):

    cleaned_urls = [
        u.strip()
        for u in urls[:50]
        if u and u.strip()
    ]

    if not cleaned_urls:
        return {
            "results": []
        }

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True
    ) as client:

        tasks = [
            process_single_url(
                client,
                url
            )
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


# ---------------------------------------------------------
# GENERATED WEBSITE PREVIEW
# ---------------------------------------------------------

@app.post("/api/generate-website")
async def generate_website(
    payload: dict = Body(...)
):
    """
    Generates a real HTML website preview
    using the scraped business information.
    """

    title = escape(
        payload.get("title")
        or "Your Business"
    )

    meta_description = escape(
        payload.get("meta_description")
        or (
            "A modern website designed to "
            "turn visitors into customers."
        )
    )

    h1_tags = (
        payload.get("h1_tags")
        or []
    )

    hero_title = escape(
        h1_tags[0]
        if h1_tags
        else (
            payload.get("title")
            or "Your Business"
        )
    )

    phones = (
        payload.get("phones")
        or []
    )

    emails = (
        payload.get("emails")
        or []
    )

    phone = (
        escape(phones[0])
        if phones
        else ""
    )

    email = (
        escape(emails[0])
        if emails
        else ""
    )

    socials = (
        payload.get("socials")
        or {}
    )

    linkedin = escape(
        socials.get("linkedin")
        or ""
    )

    instagram = escape(
        socials.get("instagram")
        or ""
    )

    facebook = escape(
        socials.get("facebook")
        or ""
    )

    og_image = (
        payload.get("og_image")
        or ""
    )

    # Hero image
    image_html = ""

    if og_image:

        image_html = f"""
        <img
            src="{escape(og_image)}"
            alt="{hero_title}"
            style="
                width:100%;
                height:420px;
                object-fit:cover;
                border-radius:24px;
                margin-top:40px;
                box-shadow:
                    0 20px 60px
                    rgba(0,0,0,0.15);
            "
        />
        """

    # Contact buttons
    contact_items = ""

    if phone:

        contact_items += f"""
        <a
            href="tel:{phone}"
            style="
                display:inline-block;
                margin:8px 8px 8px 0;
                padding:14px 20px;
                background:#111827;
                color:white;
                border-radius:10px;
                text-decoration:none;
                font-weight:600;
            "
        >
            Call {phone}
        </a>
        """

    if email:

        contact_items += f"""
        <a
            href="mailto:{email}"
            style="
                display:inline-block;
                margin:8px 8px 8px 0;
                padding:14px 20px;
                background:#2563eb;
                color:white;
                border-radius:10px;
                text-decoration:none;
                font-weight:600;
            "
        >
            Contact Us
        </a>
        """

    # Social links
    socials_html = ""

    social_links = [
        ("LinkedIn", linkedin),
        ("Instagram", instagram),
        ("Facebook", facebook),
    ]

    for label, social_url in social_links:

        if social_url:

            socials_html += f"""
            <a
                href="{social_url}"
                target="_blank"
                rel="noopener noreferrer"
                style="
                    margin-right:18px;
                    color:#6b7280;
                    text-decoration:none;
                "
            >
                {label}
            </a>
            """

    html = f"""
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
    content="{meta_description}"
>

<style>

* {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    margin: 0;
    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    color: #111827;

    background: #f9fafb;
}}

a {{
    transition:
        opacity 0.2s ease,
        transform 0.2s ease;
}}

a:hover {{
    opacity: 0.85;
}}

.container {{
    max-width: 1100px;
    margin: auto;
    padding: 0 24px;
}}

nav {{
    padding: 22px 0;

    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.03em;
}}

.hero {{
    padding: 80px 0 90px;
}}

.hero-grid {{
    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        minmax(0, 1fr);

    gap: 50px;

    align-items: center;
}}

.badge {{
    display: inline-block;

    padding: 8px 12px;

    background: #eef2ff;

    color: #4338ca;

    border-radius: 999px;

    font-size: 13px;

    font-weight: 700;

    margin-bottom: 20px;
}}

h1 {{
    font-size:
        clamp(46px, 6vw, 76px);

    line-height: 1.02;

    letter-spacing: -0.05em;

    margin: 0 0 24px;
}}

.subtitle {{
    font-size: 20px;

    line-height: 1.6;

    color: #6b7280;

    max-width: 600px;
}}

.cta {{
    display: inline-block;

    margin-top: 30px;

    padding: 16px 26px;

    border-radius: 12px;

    background: #111827;

    color: white;

    text-decoration: none;

    font-weight: 700;
}}

.section {{
    padding: 90px 0;
}}

.section-heading {{
    max-width: 700px;

    margin-bottom: 40px;
}}

.section-label {{
    color: #4f46e5;

    font-weight: 700;

    margin-bottom: 12px;
}}

.section-title {{
    font-size: 42px;

    letter-spacing: -0.04em;

    margin: 0 0 16px;
}}

.section-text {{
    color: #6b7280;

    font-size: 18px;

    line-height: 1.7;
}}

.cards {{
    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 22px;
}}

.card {{
    padding: 30px;

    background: white;

    border:
        1px solid #e5e7eb;

    border-radius: 18px;

    box-shadow:
        0 10px 30px
        rgba(0,0,0,0.03);
}}

.card h3 {{
    margin-top: 0;
}}

.card p {{
    color: #6b7280;

    line-height: 1.7;
}}

.contact {{
    text-align: center;

    background: #111827;

    color: white;

    border-radius: 28px;

    margin-bottom: 60px;

    padding: 70px 30px;
}}

.contact h2 {{
    font-size: 48px;

    letter-spacing: -0.04em;

    margin: 0 0 16px;
}}

.contact p {{
    color: #d1d5db;

    font-size: 18px;
}}

footer {{
    padding: 40px 0;

    border-top:
        1px solid #e5e7eb;
}}

@media (max-width: 800px) {{

    .hero-grid {{
        grid-template-columns: 1fr;
    }}

    .cards {{
        grid-template-columns: 1fr;
    }}

    .hero {{
        padding-top: 50px;
    }}

    h1 {{
        font-size: 48px;
    }}

    .section-title {{
        font-size: 34px;
    }}

    .contact h2 {{
        font-size: 38px;
    }}
}}

</style>

</head>

<body>

<div class="container">

    <nav>

        <div class="logo">
            {title}
        </div>

        <div>

            <a
                href="#contact"
                style="
                    text-decoration:none;
                    color:#111827;
                    font-weight:600;
                "
            >
                Contact
            </a>

        </div>

    </nav>


    <section class="hero">

        <div class="hero-grid">

            <div>

                <div class="badge">
                    Trusted Local Business
                </div>

                <h1>
                    {hero_title}
                </h1>

                <p class="subtitle">
                    {meta_description}
                </p>

                <a
                    href="#contact"
                    class="cta"
                >
                    Get Started
                </a>

            </div>

            <div>

                {image_html}

            </div>

        </div>

    </section>


    <section class="section">

        <div class="section-heading">

            <div class="section-label">
                WHY CHOOSE US
            </div>

            <h2 class="section-title">
                A better experience
                for your customers.
            </h2>

            <p class="section-text">
                Clear messaging, strong
                calls-to-action and an
                easier customer journey
                designed to turn more
                visitors into enquiries.
            </p>

        </div>


        <div class="cards">

            <div class="card">

                <h3>
                    Professional Experience
                </h3>

                <p>
                    Make a stronger first
                    impression with a modern,
                    professional digital presence.
                </p>

            </div>


            <div class="card">

                <h3>
                    Easy to Contact
                </h3>

                <p>
                    Give customers a simple
                    path to call, message or
                    request more information.
                </p>

            </div>


            <div class="card">

                <h3>
                    Built for Growth
                </h3>

                <p>
                    A flexible foundation that
                    can grow alongside your
                    business and marketing.
                </p>

            </div>

        </div>

    </section>


    <section
        id="contact"
        class="contact"
    >

        <h2>
            Ready to get started?
        </h2>

        <p>
            Let's make it easy for customers
            to choose you.
        </p>

        <div style="margin-top:20px;">
            {contact_items}
        </div>

    </section>


    <footer>

        <div style="margin-bottom:18px;">
            {socials_html}
        </div>

        <div
            style="
                color:#9ca3af;
                font-size:14px;
            "
        >
            © {title}
        </div>

    </footer>

</div>

</body>

</html>
"""

    return {
        "status": "success",
        "html": html,
        "title": title,
    }


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )