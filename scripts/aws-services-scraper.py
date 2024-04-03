import asyncio
import json
import logging
import os
from typing import Dict, List

from dotenv import load_dotenv
from playwright.async_api import ElementHandle, Page, async_playwright

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# HTML classes
HTML_CLASSES = {
    "button_class": ".awsui_button_fvjdu_1n7pg_136",
    "card_class": ".awsui_card_p8a6i_wx573_97",
    "service_name_class": ".awsui_root_18wu0_1lqen_93 a",
    "description_class": (".awsui_root_18wu0_1lqen_93.awsui_box_18wu0_1lqen_207.awsui_d-block_18wu0_1lqen_991"),
    "category_class": ".awsui_badge_1yjyg_1jkj8_93",
}


async def extract_service_data(card_element: ElementHandle) -> Dict[str, List[str]]:
    """
    Extracts the service data from a card element.

    Args:
        card_element: The card element from which to extract the data.

    Returns:
        A dictionary with the service name, description, and categories.
    """
    service_name = await (await card_element.query_selector(HTML_CLASSES["service_name_class"])).inner_text()
    description = await (await card_element.query_selector(HTML_CLASSES["description_class"])).inner_text()
    category_elements = await card_element.query_selector_all(HTML_CLASSES["category_class"])
    service_categories = [await category.inner_text() for category in category_elements]

    return {
        "service_name": service_name,
        "description": description,
        "service_categories": service_categories,
    }


async def scrape_page(page: Page) -> List[Dict[str, List[str]]]:
    """
    Scrapes a single page for services data.

    Args:
        page: The page to scrape.

    Returns:
        A list of dictionaries, each containing data about a single AWS service.
    """
    card_elements = await page.query_selector_all(HTML_CLASSES["card_class"])
    service_data_futures = [extract_service_data(card) for card in card_elements]
    services_data = await asyncio.gather(*service_data_futures)
    return services_data


async def main():
    """
    Main function to orchestrate the scraping process.
    """
    all_services_data = []

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(
            endpoint_url=f"wss://chrome.browserless.io?token={os.getenv('BROWSERLESS_API_KEY')}"
        )
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://docs.aws.amazon.com/", wait_until="domcontentloaded")

        for i in range(17):
            logging.info(f"Scraping page {i + 1}/17")
            services_data = await scrape_page(page)
            all_services_data.extend(services_data)
            pagination_buttons = await page.query_selector_all(HTML_CLASSES["button_class"])
            if i == 16:
                break
            await pagination_buttons[-1].click()

        with open("services_data_sc.json", "w", encoding="utf-8") as f:
            json.dump(all_services_data, f, ensure_ascii=False, indent=4)
        logging.info("Data saved to services_data_sc.json")


if __name__ == "__main__":
    asyncio.run(main())
