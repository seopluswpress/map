import asyncio
import re
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

app = FastAPI()

class PharmacyRecord(BaseModel):
    PharmacyName: str
    Map: str
    Website: Optional[str] = None

async def extract_website_from_gmb(map_url: str):
    if not map_url or "google.com/maps" not in map_url and "maps.app.goo.gl" not in map_url:
        return None

    browser_cfg = BrowserConfig(headless=True)
    run_cfg = CrawlerRunConfig(wait_until="networkidle", cache_mode="bypass")

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=map_url, config=run_cfg)
            if result.success:
                # 1. Search meta links
                links = result.media.get('links', [])
                for link in links:
                    href = str(link.get('href', ''))
                    if href.startswith('http') and not any(x in href.lower() for x in ['google.com', 'gstatic.com', 'facebook.com', 'instagram.com']):
                        return href
                # 2. Regex fallback
                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', result.markdown)
                for url in urls:
                    clean_url = url.strip(').,')
                    if not any(x in clean_url.lower() for x in ['google.com', 'gstatic', 'maps.app']):
                        return clean_url
    except:
        pass
    return None

@app.post("/process-maps")
async def process_single_map(item: PharmacyRecord):
    discovered_url = await extract_website_from_gmb(item.Map)
    return {
        "PharmacyName": item.PharmacyName,
        "gmb link": item.Map,
        "Website": discovered_url if discovered_url else item.Website,
        "Status": "Success" if discovered_url else "Website Not Found"
    }

@app.get("/")
def health_check():
    return {"status": "Crawl4AI is alive"}
