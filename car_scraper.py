import os
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api._generated import ElementHandle as pw_element
import time

class UsedCarsScraper:

    def __init__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=False)
        self._page = self._browser.new_page()

    def add_trims_to_url(self, url: str, trim_codes_dicts: dict) -> str:
        for model in trim_codes_dicts.keys():
            for trim_code in trim_codes_dicts[model]:
                trim_code = trim_code.replace(' ', '%20')
                url += f"trimCode={model.upper()}%7C{trim_code}&"
        return url[:-1]  # remove the last '&'

    def construct_url(self, search_results_preference: dict) -> str:
        url = "https://www.autotrader.com/cars-for-sale/"
        url += f"{search_results_preference['body_type']}/"
        url += f"{search_results_preference['make']}/"
        url += f"{search_results_preference['model']}/"
        url += f"{search_results_preference['city_state']}?"
        url += f"dealType={search_results_preference['deal_type']}&"
        url += f"marketExtension={search_results_preference['inlude_delivery_options']}&"
        url += f"searchRadius={search_results_preference['search_radius']}&"
        url += f"sortBy={search_results_preference['sort_type']}&"
        url += f"startYear={search_results_preference['min_year']}&"
        constructed_url = self.add_trims_to_url(url, search_results_preference["trim_codes"])
        return constructed_url

    def extract_car_info(self, car_info_tile:pw_element, i:int) -> dict | None:
        try:
            title = car_info_tile.query_selector("h2[data-cmp='subheading']").inner_text().strip()
            car_img_src = car_info_tile.query_selector("img[data-cmp='inventoryImage']").get_attribute("src")
            car_mileage = car_info_tile.query_selector("div[data-cmp='mileageSpecification']").inner_text().strip()
            car_price = car_info_tile.query_selector("div[data-cmp='pricing']").inner_text().split("\n")[0].strip()
            owner_name = car_info_tile.query_selector("span.padding-left-1.ellipsis-truncated").inner_text().strip()
            owner_distance = car_info_tile.query_selector("div[data-cmp='ownerDistance']").inner_text().strip()
            owner_phone_number = car_info_tile.query_selector("span[data-cmp='phoneNumber']").inner_text().strip()
        except Exception as e:
            print(f"Failed to extract car info at the index {i}: {e}")
            return None

        return {
            "title": title,
            "car_img_src": car_img_src,
            "car_mileage": car_mileage,
            "car_price": car_price,
            "owner_name": owner_name,
            "owner_distance": owner_distance,
            "owner_phone_number": owner_phone_number,
        }

    def get_car_list(self, list_length: int = 3) -> list | None:
        cars_info = []
        try:
            # Wait for item cards to appear, timeout 30s
            self._page.wait_for_selector("div[data-cmp='inventoryListing'] > div > div[data-cmp='itemCard']", timeout=30000)
            items_list = self._page.query_selector_all("div[data-cmp='inventoryListing'] > div > div[data-cmp='itemCard']")
        except PlaywrightTimeoutError:
            self._page.screenshot(path="headless_debug.png", full_page=True)
            print("Failed to load the results page")
            html = self._page.content()
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            return None

        num_items_to_extract = min(list_length, len(items_list))
        # The first car is displayed by a sponsor, which I am not interested
        for i in range(1, num_items_to_extract+1):
            extracted_info = self.extract_car_info(items_list[i], i)
            if extracted_info is None:
                return None
            print(extracted_info)
            cars_info.append(extracted_info)

        return cars_info

    def send_telegram_image_url(self, image_url: str, caption: str):
        telegram_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN_1')}/sendPhoto"
        payload = {
            'chat_id': os.getenv("TELEGRAM_CHAT_ID"),
            'photo': image_url,
            'caption': caption,
            'parse_mode': 'HTML'  # optional, for formatting
        }
        response = requests.post(telegram_url, data=payload)
        return response.status_code == 200

    def main(self, search_results_preference: dict):
        results_page_url = self.construct_url(search_results_preference)
        self._page.goto(results_page_url)
        time.sleep(10)  # allow page to load fully
        results = self.get_car_list()
        if results is None:
            print("An error occurred")
            return

        # Uncomment to send Telegram messages
        for car in results:
            caption = (
                f"🚗 <b>{car['title']}</b>\n"
                f"👨🏻‍💼 <b>Owner/Dealership:</b> {car['owner_name']}\n"
                f"📍 <b>Distance:</b> {car['owner_distance']}\n"
                f"📞 <b>Phone:</b> {car['owner_phone_number']}\n"
                f"💰 <b>Price:</b> {car['car_price']}\n"
                f"🛣️ <b>Mileage:</b> {car['car_mileage']}"
            )
            if not self.send_telegram_image_url(car['car_img_src'], caption):
                print("Failed to send a result!")
                return 

    def end(self) -> None:
        self._browser.close()
        self._playwright.stop()


if __name__ == "__main__":
    search_results_preference = {
        "body_type": "hatchback",
        "make": "honda",
        "model": "civic",
        "min_year": "2022",
        "city_state": os.getenv("LOCAL_PLACE_NAME"),  # <city_name>-<state_abbreviation_code> with lower case
        "deal_type": "greatprice",
        "inlude_delivery_options": "off",
        "search_radius": "200",
        "sort_type": "derivedpriceASC",
        "trim_codes": {"CIVIC": ["EX-L", "LX", "Sport", "Sport Touring"]},
    }

    scraper = UsedCarsScraper()
    scraper.main(search_results_preference)
    scraper.end()