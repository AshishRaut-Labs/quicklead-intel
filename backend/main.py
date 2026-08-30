import re
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

app = FastAPI(title="Tech Stack Scanner API")

# Allow requests from localhost and deployed production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom User-Agent to mimic a standard browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def detect_tech_stack(html: str) -> dict:
    """
    Detect presence of common tech stacks based on HTML content.
    Returns a dictionary with boolean flags.
    """
    html_lower = html.lower()

    # WordPress: check wp paths and generator meta tag
    wordpress = (
        "wp-content" in html_lower
        or "wp-includes" in html_lower
        or 'name="generator" content="wordpress' in html_lower
    )

    # Shopify: check CDN and theme markers
    shopify = "cdn.shopify.com" in html_lower or "shopify.theme" in html_lower

    # Next.js: check runtime data markers
    nextjs = "__next_data__" in html_lower or 'id="__next"' in html_lower

    # Google Analytics: check common scripts and ID patterns
    google_analytics = (
        "google-analytics.com/analytics.js" in html_lower
        or "googletagmanager.com/gtag/js" in html_lower
        or "gtag(" in html_lower
        or "ua-" in html_lower
        or "g-" in html_lower
    )

    return {
        "wordpress": wordpress,
        "shopify": shopify,
        "nextjs": nextjs,
        "google_analytics": google_analytics,
    }


@app.get("/api/scan")
async def scan_target(url: str = Query(..., description="Target URL to scan")):
    """
    Scan a target URL and extract metadata, emails, and tech stack.
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
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

    # Extract title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Extract meta description
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    # Extract email addresses
    emails = list(set(EMAIL_REGEX.findall(html_content)))

    # Detect tech stack
    tech_stack = detect_tech_stack(html_content)

    return {
        "title": title,
        "meta_description": meta_desc,
        "emails": emails,
        "tech_stack": tech_stack,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)