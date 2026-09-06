import asyncio
import re
import urllib.parse
import httpx
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

app = FastAPI(title="QuickLead Intel V2 - Sales Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?<![\d.])(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?![\d.])")
CTA_KEYWORDS = ["book", "demo", "contact", "quote", "get started", "buy now", "schedule", "call"]


def detect_tech_stack(html_lower: str) -> dict:
    return {
        "wordpress": "wp-content" in html_lower or "wp-includes" in html_lower,
        "shopify": "cdn.shopify.com" in html_lower or "myshopify.com" in html_lower,
        "nextjs": "__next_data__" in html_lower or "/_next/static/" in html_lower,
    }

def detect_trackers(html_lower: str) -> dict:
    return {
        "google_analytics": "google-analytics.com" in html_lower or "gtag(" in html_lower or "ua-" in html_lower or "g-" in html_lower,
        "facebook_pixel": "fbevents.js" in html_lower or "fbq(" in html_lower,
        "google_tag_manager": "googletagmanager.com/gtm.js" in html_lower,
        "linkedin_insight": "snap.licdn.com" in html_lower or "lintrk" in html_lower,
        "hubspot": "js.hs-scripts.com" in html_lower or "_hsq" in html_lower,
    }

def extract_conversion_signals(soup: BeautifulSoup, html_lower: str) -> dict:
    # Check for forms
    has_form = len(soup.find_all("form")) > 0
    # Check for WhatsApp links
    has_whatsapp = "wa.me/" in html_lower or "api.whatsapp.com" in html_lower
    # Check for visible CTAs in buttons or links
    has_cta = False
    for tag in soup.find_all(["a", "button"]):
        if tag.string and any(keyword in tag.string.lower() for keyword in CTA_KEYWORDS):
            has_cta = True
            break

    return {
        "has_form": has_form,
        "has_whatsapp": has_whatsapp,
        "has_cta": has_cta,
    }

def extract_technical_signals(soup: BeautifulSoup) -> dict:
    has_viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
    has_favicon = bool(soup.find("link", rel=lambda x: x and "icon" in x.lower()))
    has_canonical = bool(soup.find("link", rel="canonical"))
    return {
        "has_viewport": has_viewport,
        "has_favicon": has_favicon,
        "has_canonical": has_canonical
    }

def generate_sales_intel(data: dict) -> dict:
    """
    The Brain: Analyzes raw signals to generate scores, problems, pricing, and a personalized pitch.
    """
    problems = []
    
    # 1. SEO Scoring (Max 35 points)
    seo_score = 35
    if not data.get("title") or len(data["title"]) < 10:
        seo_score -= 15
        problems.append("Missing or weak page title")
    if not data.get("meta_description") or len(data["meta_description"]) < 50:
        seo_score -= 10
        problems.append("Missing or weak meta description")
    if data.get("h1_count", 0) == 0:
        seo_score -= 10
        problems.append("No H1 heading detected")
    elif data.get("h1_count", 0) > 1:
        seo_score -= 5
        problems.append("Multiple H1 headings (confuses SEO)")

    # 2. Conversion Scoring (Max 40 points)
    conv_score = 40
    conv_signals = data.get("conversion_signals", {})
    if not conv_signals.get("has_cta"):
        conv_score -= 20
        problems.append("No clear Call-to-Action (CTA)")
    if not conv_signals.get("has_form"):
        conv_score -= 10
        problems.append("No lead capture form")
    if not data.get("phones") and not data.get("emails"):
        conv_score -= 10
        problems.append("No visible contact information")

    # 3. Technical & Marketing Scoring (Max 25 points)
    tech_score = 25
    tech_signals = data.get("technical_signals", {})
    trackers = data.get("trackers", {})
    if not tech_signals.get("has_viewport"):
        tech_score -= 15
        problems.append("Not optimized for mobile (Missing Viewport)")
    if not trackers.get("google_analytics") and not trackers.get("facebook_pixel"):
        tech_score -= 10
        problems.append("No marketing trackers (GA/Pixel) installed")

    # Total Score Calculations
    overall_score = seo_score + conv_score + tech_score
    
    # Opportunity logic (Worse score = Better opportunity for you to sell)
    if overall_score < 40:
        opportunity = "HIGH"
        suggested_offer = "Full Website Redesign & Conversion Setup"
        suggested_price = "$1,200 - $2,500"
    elif overall_score < 75:
        opportunity = "MEDIUM"
        suggested_offer = "Conversion Optimization & SEO Fixes"
        suggested_price = "$500 - $900"
    else:
        opportunity = "LOW"
        suggested_offer = "Retainer / Minor Tweaks"
        suggested_price = "$200 - $400"

    # Generate Pitch
    if len(problems) > 0:
        top_problem = problems[0]
        pitch = f"Hi there, I reviewed your site and noticed a critical issue: {top_problem.lower()}. This is likely costing you leads. I can fix this and upgrade your overall conversion system. Open to a quick chat?"
    else:
        pitch = "Your website looks solid, but I have a few advanced strategies to increase your lead volume. Open to a chat?"

    return {
        "website_score": overall_score,
        "seo_score": seo_score,
        "conversion_score": conv_score,
        "opportunity_score": opportunity,
        "problems_found": problems,
        "suggested_offer": suggested_offer,
        "suggested_price": suggested_price,
        "personalized_pitch": pitch
    }

def extract_contacts(html_content: str, soup: BeautifulSoup) -> tuple[list, dict]:
    phones = []
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("tel:"):
            raw_tel = a["href"].replace("tel:", "").strip()
            decoded_tel = urllib.parse.unquote(raw_tel)
            if decoded_tel not in phones:
                phones.append(decoded_tel)

    raw_phones = PHONE_REGEX.findall(html_content)
    for p in raw_phones:
        cleaned = p.strip()
        digits = re.sub(r"\D", "", cleaned)
        if 10 <= len(digits) <= 15 and cleaned not in phones:
            phones.append(cleaned)

    socials = {"linkedin": None, "twitter": None, "instagram": None, "facebook": None}
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "linkedin.com/company" in href or "linkedin.com/in" in href:
            socials["linkedin"] = socials.get("linkedin") or a["href"]
        elif ("twitter.com/" in href or "x.com/" in href) and "status" not in href:
            socials["twitter"] = socials.get("twitter") or a["href"]
        elif "instagram.com/" in href:
            socials["instagram"] = socials.get("instagram") or a["href"]
        elif "facebook.com/" in href:
            socials["facebook"] = socials.get("facebook") or a["href"]

    return phones[:3], socials

async def process_single_url(client: httpx.AsyncClient, raw_url: str) -> dict:
    target_url = raw_url.strip()
    if not target_url: return None
    if not target_url.startswith(("http://", "https://")):
        target_url = f"https://{target_url}"

    try:
        response = await client.get(target_url, headers=HEADERS)
        html_content = response.text
        html_lower = html_content.lower()
        soup = BeautifulSoup(html_content, "html.parser")

        title = soup.title.string.strip() if (soup.title and soup.title.string) else ""
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)}) or soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
        meta_desc = meta_tag["content"].strip() if (meta_tag and meta_tag.get("content")) else ""
        
        h1_tags = soup.find_all("h1")
        og_image_tag = soup.find("meta", attrs={"property": "og:image"})
        
        phones, socials = extract_contacts(html_content, soup)
        
        raw_data = {
            "url": target_url,
            "title": title,
            "meta_description": meta_desc,
            "h1_count": len(h1_tags),
            "h1_tags": [h1.get_text(strip=True) for h1 in h1_tags][:2],
            "og_image": og_image_tag["content"] if og_image_tag and og_image_tag.get("content") else None,
            "phones": phones,
            "emails": list({e for e in EMAIL_REGEX.findall(html_content) if not e.endswith(('.png', '.jpg', '.webp'))})[:3],
            "socials": socials,
            "tech_stack": detect_tech_stack(html_lower),
            "trackers": detect_trackers(html_lower),
            "conversion_signals": extract_conversion_signals(soup, html_lower),
            "technical_signals": extract_technical_signals(soup)
        }

        # Pass raw data to the Brain to generate Sales Intel
        intel = generate_sales_intel(raw_data)
        
        # Merge raw data and generated intelligence
        return {**raw_data, "status": "Success", "intelligence": intel}

    except Exception as e:
        return {"url": target_url, "status": "Failed", "error": str(e)}

@app.get("/api/scan")
async def scan_target(url: str = Query(..., description="Target URL to scan")):
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        result = await process_single_url(client, url)
        if result.get("status") == "Failed":
            raise HTTPException(status_code=500, detail=result.get("error"))
        return result

@app.post("/api/bulk-scan")
async def bulk_scan_targets(urls: list[str] = Body(..., description="List of URLs to scan in bulk")):
    cleaned_urls = [u for u in urls[:50] if u.strip()]
    if not cleaned_urls:
        return {"results": []}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        tasks = [process_single_url(client, u) for u in cleaned_urls]
        results = await asyncio.gather(*tasks)

    return {"results": [r for r in results if r is not None]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)