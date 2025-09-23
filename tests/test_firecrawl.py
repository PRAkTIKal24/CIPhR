
import os
from firecrawl import FirecrawlApp
from config.config import FIRECRAWL_API_KEY
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_firecrawl_arxiv_scrape(url: str):
    if not FIRECRAWL_API_KEY:
        logging.error("FIRECRAWL_API_KEY not found.")
        return

    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    logging.info(f"Attempting to scrape: {url}")
    try:
        scraped_data = app.scrape(url)
        if scraped_data and isinstance(scraped_data, list) and len(scraped_data) > 0:
            content = scraped_data[0].get("content")
            if content:
                logging.info(f"Successfully scraped content (first 500 chars):\n{content[:500]}...")
            else:
                logging.warning(f"Scraped data found, but 'content' key is empty for {url}.")
        else:
            logging.warning(f"No data returned by Firecrawl for {url}.")
    except Exception as e:
        logging.error(f"Error scraping {url} with Firecrawl: {e}")

if __name__ == "__main__":
    # Use a known arXiv abstract page URL
    test_url = "https://arxiv.org/abs/2301.00001"
    test_firecrawl_arxiv_scrape(test_url)


