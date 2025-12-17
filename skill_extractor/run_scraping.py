#!/usr/bin/env python3
"""
Pipeline 1: Web Scraping & Raw Data Saving
Scrapes real job data from ReKrute and LinkedIn, saves to data/raw/
Filtering is done in scraper.py functions.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import logging

# Setup paths
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from scrapping.scraper import scrape_all_sources


def run_scraping_pipeline():
    """Execute web scraping pipeline."""
    
    logger.info("🌐 Starting real job scraping from ReKrute and LinkedIn...")
    
    # Use scrape_all_sources which handles filtering internally
    offers = scrape_all_sources(test_mode=False, min_offers=50)
    
    if not offers:
        logger.error("❌ No offers scraped")
        return []
    
    # Create output directory
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = raw_dir / f"raw_offers_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PIPELINE 1: WEB SCRAPING & RAW DATA SAVING")
    print("="*60)
    
    offers = run_scraping_pipeline()
    
    print(f"\n✓ Pipeline completed: {len(offers)} offers saved to data/raw/")
    print("="*60 + "\n")
