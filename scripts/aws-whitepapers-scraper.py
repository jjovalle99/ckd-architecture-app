import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict

from dotenv import load_dotenv
from playwright.async_api import ElementHandle, async_playwright

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# HTML classes and selectors
HTML_SELECTORS = {
    "cards": ".m-card",
    "category": ".m-category",
    "headline": ".m-headline",
    "description": ".m-desc > p:first-child",
    "date": ".m-info-txt",
    "pdf_link": ".m-desc a[href*='.pdf']",
}


async def extract_whitepaper_data(card_element: ElementHandle) -> Dict[str, str]:
    """
    Extracts the whitepaper data from a card element.

    Args:
        card_element: The card element from which to extract the data.

    Returns:
        A dictionary with the whitepaper name, category, description, date, and PDF link.
    """
    category = await card_element.query_selector(HTML_SELECTORS["category"])
    headline = await card_element.query_selector(HTML_SELECTORS["headline"])
    description = await card_element.query_selector(HTML_SELECTORS["description"])
    date = await card_element.query_selector(HTML_SELECTORS["date"])
    pdf_link_element = await card_element.query_selector(HTML_SELECTORS["pdf_link"])

    category_text = await category.inner_text() if category else "No Category"
    headline_text = await headline.inner_text() if headline else "No Headline"
    description_text = await description.inner_text() if description else "No Description"
    date_text = await date.inner_text() if date else "No Date"
    pdf_link = await pdf_link_element.get_attribute("href") if pdf_link_element else "No PDF Link"

    return {
        "name": headline_text,
        "category": category_text,
        "description": description_text,
        "date": date_text,
        "pdf_link": pdf_link,
    }


async def scrape_page(page_url: str) -> Dict[str, str]:
    """
    Scrapes a single page for whitepapers data.

    Args:
        page_url: The URL of the page to scrape.

    Returns:
        A list of dictionaries, each containing data about a single whitepaper.
    """
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(
            endpoint_url=f"wss://chrome.browserless.io?token={os.getenv('BROWSERLESS_API_KEY')}"
        )
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(page_url, wait_until="networkidle")

        card_elements = await page.query_selector_all(HTML_SELECTORS["cards"])
        whitepaper_data_futures = [extract_whitepaper_data(card) for card in card_elements]
        whitepapers_data = await asyncio.gather(*whitepaper_data_futures)

        await browser.close()

    return whitepapers_data


def clean_and_update_data(data):
    cleaned_data = []
    for item in data:
        if all(item.values()):
            date_str = item["date"]
            try:
                date_obj = datetime.strptime(date_str, "%B %Y")
                item["year"] = date_obj.year
                item["month"] = date_obj.month
                cleaned_data.append(item)
            except ValueError:
                print(f"Warning: Invalid date format '{date_str}' in item: {item}")
    return cleaned_data


async def main():
    """
    Main function to orchestrate the scraping process.
    """
    all_whitepapers_data = []

    for i in range(19):
        page_url = f"https://aws.amazon.com/whitepapers/?whitepapers-main.sort-by=item.additionalFields.sortDate&whitepapers-main.sort-order=desc&awsf.whitepapers-content-type=*all&awsf.whitepapers-global-methodology=*all&awsf.whitepapers-tech-category=*all&awsf.whitepapers-industries=*all&awsf.whitepapers-business-category=*all&awsm.page-whitepapers-main={i+1}"
        logging.info(f"Scraping page {i + 1}/20")
        whitepapers_data = await scrape_page(page_url)
        all_whitepapers_data.extend(whitepapers_data)

    cleaned_data = clean_and_update_data(all_whitepapers_data)

    with open("whitepapers_data.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
    logging.info("Data saved to whitepapers_data.json")


if __name__ == "__main__":
    asyncio.run(main())
