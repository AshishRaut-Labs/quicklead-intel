import re
import httpx
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

app = FastAPI(title="Tech Stack Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


def detect_tech_stack(html: str) -> dict:
    html_lower = html.lower()

    wordpress = (
        "wp-content" in html_lower
        or "wp-includes" in html_lower
        or 'name="generator" content="wordpress' in html_lower
    )

    shopify = (
        "cdn.shopify.com" in html_lower 
        or "shopify.theme" in html_lower 
        or "myshopify.com" in html_lower
    )

    nextjs = (
        "__next_data__" in html_lower 
        or 'id="__next"' in html_lower
        or "/_next/static/" in html_lower
    )

    google_analytics = (
        "google-analytics.com/analytics.js" in html_lower
        or "googletagmanager.com/gtag/js" in html_lower
        or "gtag(" in html_lower
        or bool(re.search(r"ua-\d+-\d+", html_lower))
        or bool(re.search(r"g-[a-z0-9]{8,}", html_lower))
    )

    return {
        "wordpress": wordpress,
        "shopify": shopify,
        "nextjs": nextjs,
        "google_analytics": google_analytics,
    }


def detect_trackers(html: str) -> dict:
    html_lower = html.lower()

    return {
        "facebook_pixel": "fbevents.js" in html_lower or "fbq(" in html_lower,
        "google_tag_manager": "googletagmanager.com/gtm.js" in html_lower or "gtm(" in html_lower,
        "tiktok_pixel": "analytics.tiktok.com" in html_lower or "ttq." in html_lower,
        "hubspot": "js.hs-scripts.com" in html_lower or "js.hsscripts.com" in html_lower or "_hsq" in html_lower,
        "klaviyo": "klaviyo.com/onsite" in html_lower or "_learnq" in html_lower,
    }


def extract_contacts(html_content: str, soup: BeautifulSoup) -> tuple[list, dict]:
    phones = []
    
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("tel:"):
            raw_tel = a["href"].replace("tel:", "").strip()
            if raw_tel not in phones:
                phones.append(raw_tel)

    raw_phones = PHONE_REGEX.findall(html_content)
    for p in raw_phones:
        cleaned = p.strip()
        if len(re.sub(r"\D", "", cleaned)) >= 10 and cleaned not in phones:
            phones.append(cleaned)

    socials = {
        "linkedin": None,
        "twitter": None,
        "instagram": None,
        "facebook": None,
    }

    for a in soup.find_all("a", href=True):
        href = a["href"]
        href_lower = href.lower()
        if "linkedin.com/company" in href_lower or "linkedin.com/in" in href_lower:
            if not socials["linkedin"]:
                socials["linkedin"] = href
        elif ("twitter.com/" in href_lower or "x.com/" in href_lower) and not socials["twitter"]:
            if "status" not in href_lower:
                socials["twitter"] = href
        elif "instagram.com/" in href_lower and not socials["instagram"]:
            socials["instagram"] = href
        elif "facebook.com/" in href_lower and not socials["facebook"]:
            socials["facebook"] = href

    return phones[:5], socials


@app.get("/api/scan")
async def scan_target(url: str = Query(..., description="Target URL to scan")):
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"HTTP error: {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")

    title = soup.title.string.strip() if (soup.title and soup.title.string) else ""

    meta_desc = ""
    meta_tag = (
        soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        or soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
    )
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all("h1") if h1.get_text(strip=True)]
    og_image_tag = soup.find("meta", attrs={"property": "og:image"})
    og_image = og_image_tag["content"] if (og_image_tag and og_image_tag.get("content")) else None

    raw_emails = EMAIL_REGEX.findall(html_content)
    emails = list({e for e in raw_emails if not e.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'))})

    phones, socials = extract_contacts(html_content, soup)
    tech_stack = detect_tech_stack(html_content)
    trackers = detect_trackers(html_content)

    return {
        "title": title,
        "meta_description": meta_desc,
        "h1_tags": h1_tags[:3],
        "og_image": og_image,
        "emails": emails[:5],
        "phones": phones,
        "socials": socials,
        "tech_stack": tech_stack,
        "trackers": trackers,
    }


@app.post("/api/bulk-scan")
async def bulk_scan_targets(urls: list[str] = Body(..., description="List of URLs to scan in bulk")):
    """
    Asynchronously scan multiple URLs and return aggregated intelligence reports for CSV export.
    """
    results = []
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for raw_url in urls[:50]:  # Cap at 50 URLs per request
            target_url = raw_url.strip()
            if not target_url:
                continue
            if not target_url.startswith(("http://", "https://")):
                target_url = f"https://{target_url}"
                
            try:
                response = await client.get(target_url, headers=HEADERS)
                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")
                
                title = soup.title.string.strip() if (soup.title and soup.title.string) else ""
                meta_tag = (
                    soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
                    or soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
                )
                meta_desc = meta_tag["content"].strip() if (meta_tag and meta_tag.get("content")) else ""
                
                phones, socials = extract_contacts(html_content, soup)
                tech_stack = detect_tech_stack(html_content)
                trackers = detect_trackers(html_content)
                
                results.append({
                    "url": target_url,
                    "status": "Success",
                    "title": title,
                    "meta_description": meta_desc,
                    "phones": phones[:2],
                    "socials": socials,
                    "tech_stack": tech_stack,
                    "trackers": trackers
                })
            except Exception as e:
                results.append({
                    "url": target_url,
                    "status": "Failed",
                    "error": str(e)
                })
                
    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)