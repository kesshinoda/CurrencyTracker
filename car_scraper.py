# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

import asyncio
import os
import requests
import zendriver as ZenDriver

from zendriver.core.connection import ProtocolException
from zendriver.core.element import Element as ZenElement


class UsedCarsScraper():
        
    def __init__(self):
        # Initialize something here
        return 

    async def add_trims_to_url(self, url:str, trim_codes_dicts:list) -> str:
        for model in trim_codes_dicts.keys():
            for trim_code in trim_codes_dicts[model]:
                trim_code = trim_code.replace(' ', '%20')
                url+=f"trimCode={model.upper()}%7C{trim_code}&"
        return url[:len(url)-1] # remove the last '&'

    async def construct_url(self, search_results_preference:dict) -> str:
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
        constructed_url = await self.add_trims_to_url(url, search_results_preference["trim_codes"])
        return constructed_url
    
    async def extract_car_info(self, car_info_tile:ZenElement) -> dict | None:
        try:
            title = (await self._page.query_selector("h2[data-cmp='subheading']", car_info_tile)).text
            car_img_src = (await self._page.query_selector("img[data-cmp='inventoryImage']", car_info_tile))["src"]
            car_mileage = (await self._page.query_selector("div[data-cmp='mileageSpecification']", car_info_tile)).text
            car_price = (await self._page.query_selector("div[data-cmp='pricing']", car_info_tile)).text
            owner_distance = (await self._page.query_selector("div[data-cmp='ownerDistance']", car_info_tile)).text
            owner_phone_number = (await self._page.query_selector("span[data-cmp='phoneNumber']", car_info_tile)).text
        except Exception as e:
            print(f"Failed to extract car info: {e}")
            return None
        car_info_dict = {
            "title": title,
            "car_img_src": car_img_src,
            "car_mileage": car_mileage,
            "car_price": car_price, 
            "owner_distance": owner_distance,
            "owner_phone_number": owner_phone_number,
        }
        return car_info_dict
    
    async def get_car_list(self, list_length:int=3) -> list | None:
        cars_info = []
        try :
            await self._page.wait_for_ready_state("complete")
            await asyncio.sleep(3)
            items_list = await self._page.query_selector_all("div[data-cmp='inventoryListing'] > div > div[data-cmp='itemCard']")
        except (TimeoutError, ProtocolException):
            print("Failed to load the results page")
            return None
        for item_index in range(1, list_length+1):
            extracted_info = await self.extract_car_info(items_list[item_index])
            if(extracted_info is None):
                return None
            cars_info.append(extracted_info)
        return cars_info
    
    async def send_telegram_image_url(self, image_url:str, caption:str):
        telegram_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN_1')}/sendPhoto"
        payload = {
            'chat_id': os.getenv("TELEGRAM_CHAT_ID"),
            'photo': image_url,
            'caption': caption,
            'parse_mode': 'HTML'  # optional, for formatting
        }
        response = requests.post(telegram_url, data=payload)
        return response.status_code == 200
    
    async def main(self, search_results_preference:dict, headless:bool):
        self._browser = await ZenDriver.start(headless=headless, no_sandbox=True)
        self._page = self._browser.main_tab
        await self._page.maximize()
        results_page_url = await self.construct_url(search_results_preference)
        await self._page.get(results_page_url)
        await asyncio.sleep(2)
        results = await self.get_car_list()
        # if(results is None):
        #     return print("An error occurred")
        # for car in results:
        #     caption = (
        #         f"🚗 <b>{car['title']}</b>\n"
        #         f"📍 <b>Distance:</b> {car['owner_distance']}\n"
        #         f"📞 <b>Phone:</b> {car['owner_phone_number']}\n"
        #         f"💰 <b>Price:</b> {car['car_price']}\n"
        #         f"🛣️ <b>Mileage:</b> {car['car_mileage']}"
        #     )
        #     if(await self.send_telegram_image_url(car['car_img_src'], caption) == False):
        #         print("Failed to send a result!")
        print("code executed successfully!!")
        print(results)

if __name__ == "__main__":
    # car_info = {
    #     "make": "honda",
    #     "model": "civic",
    #     "min_year": "2022",
    # }
    search_results_preference = {
        "body_type": "hatchback",
        "make": "honda",
        "model": "civic",
        "min_year": "2022",
        "city_state": os.getenv("LOCAL_PLACE_NAME"),# <city_name>-<state_abbreviation_code> with lower case
        "deal_type": "greatprice",
        "inlude_delivery_options": "off",
        "search_radius": "200",
        "sort_type": "derivedpriceASC", 
        "trim_codes": {"CIVIC": ["EX-L", "LX", "Sport", "Sport Touring"]},
        # "zip_code": os.getenv("LOCAL_ZIP_CODE"),
    }

    class_instance = UsedCarsScraper()
    asyncio.run(class_instance.main(search_results_preference, headless=True))