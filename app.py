import asyncio
import re
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

app = FastAPI()

# Data model for incoming requests from n8n
class BusinessData(BaseModel):
    PharmacyName: str
    Map: str
    Website: Optional[str] = ""

async def extract_website_from_gmb(map_url: str):
    if not map_url or "google.com/maps" not in map_url and "maps.app.goo.gl" not in map_url:
        return None

    browser_cfg = BrowserConfig(headless=True)
    run_cfg = CrawlerRunConfig(
        wait_until="networkidle",
        cache_mode="bypass"
    )

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=map_url, config=run_cfg)
            if result.success:
                # Logic 1: Search links
                links = result.media.get('links', [])
                for link in links:
                    href = str(link.get('href', ''))
                    if href.startswith('http') and not any(x in href.lower() for x in [
                        'google.com', 'gstatic.com', 'apple.com', 'facebook.com', 
                        'instagram.com', 'twitter.com', 'schema.org'
                    ]):
                        return href
                
                # Logic 2: Regex fallback
                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', result.markdown)
                for url in urls:
                    clean_url = url.strip(').,')
                    if not any(x in clean_url.lower() for x in ['google.com', 'gstatic', 'maps.app']):
                        return clean_url
    except Exception as e:
        print(f"Error crawling {map_url}: {e}")
    return None

@app.post("/process-maps")
async def process_maps(data: List[BusinessData]):
    results = []
    
    # Process rows (Note: For high volume, you might want to use asyncio.gather)
    for item in data:
        discovered_url = await extract_website_from_gmb(item.Map)
        
        results.append({
            "PharmacyName": item.PharmacyName,
            "Map": item.Map,
            "gmb link": item.Map,
            "Website": discovered_url if discovered_url else item.Website,
            "Status": "Found" if discovered_url else "Not Found"
        })
        
    return results

@app.get("/")
def home():
    return {"status": "Crawl4AI API is running"}
