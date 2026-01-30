import asyncio
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

app = FastAPI()

# This model matches the fields n8n will send
class PharmacyRecord(BaseModel):
    PharmacyName: str
    Map: str
    Website: Optional[str] = None

async def extract_website_from_gmb(map_url: str):
    if not map_url or "google.com/maps" not in map_url and "maps.app.goo.gl" not in map_url:
        return None

    # GMB is heavy, we need a clean browser for every request
    browser_cfg = BrowserConfig(headless=True)
    run_cfg = CrawlerRunConfig(
        wait_until="networkidle", # Correct parameter for recent Crawl4AI versions
        cache_mode="bypass"
    )

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=map_url, config=run_cfg)
            if result.success:
                # Logic 1: Look for the 'Website' link in the metadata/media links
                links = result.media.get('links', [])
                for link in links:
                    href = str(link.get('href', ''))
                    if href.startswith('http') and not any(x in href.lower() for x in [
                        'google.com', 'gstatic.com', 'apple.com', 'facebook.com', 
                        'instagram.com', 'twitter.com', 'schema.org'
                    ]):
                        return href
                
                # Logic 2: Regex fallback (if the link is hidden in text)
                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', result.markdown)
                for url in urls:
                    clean_url = url.strip(').,')
                    if not any(x in clean_url.lower() for x in ['google.com', 'gstatic', 'maps.app']):
                        return clean_url
    except Exception as e:
        print(f"Error crawling {map_url}: {e}")
    return None

@app.post("/process-maps")
async def process_single_map(item: PharmacyRecord):
    # This matches n8n sending one record at a time
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
