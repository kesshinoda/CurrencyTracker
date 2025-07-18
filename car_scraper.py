# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

import asyncio
import os
import requests
import selenium
import time
import zendriver as ZenDriver

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from zendriver.core.connection import ProtocolException
from zendriver.core.element import Element as ZenElement


class UsedCarsScraper():
        
    def __init__(self, headless:bool):
        chrome_options = Options()
        if(headless):
            chrome_options.add_argument("--headless")
        self._driver = webdriver.Chrome(options=chrome_options)
        return 

    def add_trims_to_url(self, url:str, trim_codes_dicts:list) -> str:
        for model in trim_codes_dicts.keys():
            for trim_code in trim_codes_dicts[model]:
                trim_code = trim_code.replace(' ', '%20')
                url+=f"trimCode={model.upper()}%7C{trim_code}&"
        return url[:len(url)-1] # remove the last '&'

    def construct_url(self, search_results_preference:dict) -> str:
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
    
    def extract_car_info(self, car_info_tile:WebElement) -> dict | None:
        try:
            title = car_info_tile.find_element(By.XPATH, ".//h2[@data-cmp='subheading']").text
            car_img_src = car_info_tile.find_element(By.XPATH, ".//img[@data-cmp='inventoryImage']").get_attribute("src")            
            car_mileage = car_info_tile.find_element(By.XPATH, ".//div[@data-cmp='mileageSpecification']").text
            car_price = car_info_tile.find_element(By.XPATH, ".//div[@data-cmp='pricing']").text
            owner_distance = car_info_tile.find_element(By.XPATH, ".//div[@data-cmp='ownerDistance']").text
            owner_phone_number = car_info_tile.find_element(By.XPATH, ".//span[@data-cmp='phoneNumber']").text
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
    
    def get_car_list(self, list_length:int=3) -> list | None:
        cars_info = []
        try :
            items_list = WebDriverWait(self._driver, 30).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div[data-cmp='inventoryListing'] > div > div[data-cmp='itemCard']")
                )  
            )
        except TimeoutException:
            print("Failed to load the results page")
            return None
        num_items_to_extract = min(list_length, len(items_list))
        for item_index in range(1, num_items_to_extract+1):
            extracted_info = self.extract_car_info(items_list[item_index])
            if(extracted_info is None):
                return None
            print(extracted_info)
            cars_info.append(extracted_info)
        return cars_info
    
    def send_telegram_image_url(self, image_url:str, caption:str):
        telegram_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN_1')}/sendPhoto"
        payload = {
            'chat_id': os.getenv("TELEGRAM_CHAT_ID"),
            'photo': image_url,
            'caption': caption,
            'parse_mode': 'HTML'  # optional, for formatting
        }
        response = requests.post(telegram_url, data=payload)
        return response.status_code == 200
    
    def main(self, search_results_preference:dict):
        
        results_page_url = self.construct_url(search_results_preference)
        self._driver.get(results_page_url)
        time.sleep(10)
        results = self.get_car_list()
        if(results is None):
            return print("An error occurred")
        # for car in results:
        #     caption = (
        #         f"🚗 <b>{car['title']}</b>\n"
        #         f"📍 <b>Distance:</b> {car['owner_distance']}\n"
        #         f"📞 <b>Phone:</b> {car['owner_phone_number']}\n"
        #         f"💰 <b>Price:</b> {car['car_price']}\n"
        #         f"🛣️ <b>Mileage:</b> {car['car_mileage']}"
        #     )
        #     if(self.send_telegram_image_url(car['car_img_src'], caption) == False):
        #         print("Failed to send a result!")
        
    def end(self) -> None:
        self._driver.quit()

if __name__ == "__main__":
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
    }

    class_instance = UsedCarsScraper(headless=False)
    class_instance.main(search_results_preference)