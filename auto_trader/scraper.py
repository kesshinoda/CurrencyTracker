# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

import asyncio
import os
import requests
import json
import csv
from bs4 import BeautifulSoup
import traceback
import zendriver as ZenDriver

class UsedCarsScraper():
        
    def __init__(self):
        # Initialize something here
        return 
    
    def get_cars(
    make="BMW", 
    model="5 SERIES", 
    postcode="SW1A 0AA", 
    radius=1500, 
    min_year=1995, 
    max_year=1995, 
    include_writeoff="include", 
    max_attempts_per_page=5, 
    verbose=False):

        # To bypass Cloudflare protection
        scraper = cloudscraper.create_scraper()

        # Basic variables
        results = []
        n_this_year_results = 0

        url = "https://www.autotrader.co.uk/results-car-search"

        keywords = {}
        keywords["mileage"] = ["miles"]
        keywords["BHP"] = ["BHP"]
        keywords["transmission"] = ["Automatic", "Manual"]
        keywords["fuel"] = [
        "Petrol", 
        "Diesel", 
        "Electric", 
        "Hybrid – Diesel/Electric Plug-in", 
        "Hybrid – Petrol/Electric", 
        "Hybrid – Petrol/Electric Plug-in"
        ]
        keywords["owners"] = ["owners"]
        keywords["body"] = [
        "Coupe", 
        "Convertible", 
        "Estate", 
        "Hatchback", 
        "MPV", 
        "Pickup", 
        "SUV", 
        "Saloon"
        ]
        keywords["ULEZ"] = ["ULEZ"]
        keywords["year"] = [" reg)"]
        keywords["engine"] = ["engine"]

        # Set up parameters for query to autotrader.co.uk
        params = {
            "sort": "relevance",
            "postcode": postcode,
            "radius": radius,
            "make": make,
            "model": model,
            "search-results-price-type": "total-price",
            "search-results-year": "select-year",
        }

        if (include_writeoff == "include"):
            params["writeoff-categories"] = "on"
        elif (include_writeoff == "exclude"):
            params["exclude-writeoff-categories"] = "on"
        elif (include_writeoff == "writeoff-only"):
            params["only-writeoff-categories"] = "on"
            
        year = min_year
        page = 1
        attempt = 1

        try:
            while year <= max_year:
                params["year-from"] = year
                params["year-to"] = year
                params["page"] = page

                r = scraper.get(url, params=params)
                if verbose:
                    print("Year:     ", year)
                    print("Page:     ", page)
                    print("Response: ", r)

                try:
                    if r.status_code != 200:   # If not successful (e.g. due to bot protection)
                        attempt = attempt + 1  # Log as an attempt
                        if attempt <= max_attempts_per_page:
                            if verbose:
                                print("Exception. Starting attempt #", attempt, "and keeping at page #", page)
                        else:
                            page = page + 1
                            attempt = 1
                            if verbose:
                                print("Exception. All attempts exhausted for this page. Skipping to next page #", page)

                    else:

                        j = r.json()
                        s = BeautifulSoup(j["html"], features="html.parser")

                        articles = s.find_all("article", attrs={"data-standout-type":""})

                        # If no results or reached end of results...
                        if len(articles) == 0 or r.url[r.url.find("page=")+5:] != str(page):
                            if verbose:
                                print("Found total", n_this_year_results, "results for year", year, "across", page-1, "pages")
                                if year+1 <= max_year:
                                    print("Moving on to year", year + 1)
                                    print("---------------------------------")

                            # Increment year and reset relevant variables
                            year = year + 1
                            page = 1
                            attempt = 1
                            n_this_year_results = 0
                        else:
                            for article in articles:
                                car = {}
                                car["name"] = article.find("h3", {"class": "product-card-details__title"}).text.strip()             
                                car["link"] = "https://www.autotrader.co.uk" + \
                                    article.find("a", {"class": "listing-fpa-link"})["href"][: article.find("a", {"class": "listing-fpa-link"})["href"] \
                                    .find("?")]
                                car["price"] = article.find("div", {"class": "product-card-pricing__price"}).text.strip()

                                seller_info = article.find("ul", {"class": "product-card-seller-info__specs"}).text.strip()
                                car["seller"] = " ".join(seller_info.split())

                                key_specs_bs_list = article.find("ul", {"class": "listing-key-specs"}).find_all("li")
                                
                                for key_spec_bs_li in key_specs_bs_list:

                                    key_spec_bs = key_spec_bs_li.text

                                    if any(keyword in key_spec_bs for keyword in keywords["mileage"]):
                                        car["mileage"] = int(key_spec_bs[:key_spec_bs.find(" miles")].replace(",",""))
                                    elif any(keyword in key_spec_bs for keyword in keywords["BHP"]):
                                        car["BHP"] = int(key_spec_bs[:key_spec_bs.find("BHP")])
                                    elif any(keyword in key_spec_bs for keyword in keywords["transmission"]):
                                        car["transmission"] = key_spec_bs
                                    elif any(keyword in key_spec_bs for keyword in keywords["fuel"]):
                                        car["fuel"] = key_spec_bs
                                    elif any(keyword in key_spec_bs for keyword in keywords["owners"]):
                                        car["owners"] = int(key_spec_bs[:key_spec_bs.find(" owners")])
                                    elif any(keyword in key_spec_bs for keyword in keywords["body"]):
                                        car["body"] = key_spec_bs
                                    elif any(keyword in key_spec_bs for keyword in keywords["ULEZ"]):
                                        car["ULEZ"] = key_spec_bs
                                    elif any(keyword in key_spec_bs for keyword in keywords["year"]):
                                        car["year"] = key_spec_bs
                                    elif key_spec_bs[1] == "." and key_spec_bs[3] == "L":
                                        car["engine"] = key_spec_bs

                                results.append(car)
                                n_this_year_results = n_this_year_results + 1

                            page = page + 1
                            attempt = 1

                            if verbose:
                                print("Car count: ", len(results))
                                print("---------------------------------")

                except KeyboardInterrupt:
                    break

                except:
                    traceback.print_exc()
                    attempt = attempt + 1
                    if attempt <= max_attempts_per_page:
                        if verbose:
                            print("Exception. Starting attempt #", attempt, "and keeping at page #", page)
                    else:
                        page = page + 1
                        attempt = 1
                        if verbose:
                            print("Exception. All attempts exhausted for this page. Skipping to next page #", page)

        except KeyboardInterrupt:
            pass

        return results

    async def add_trims_to_url(self, url:str, trim_codes_dicts:list) -> str:
        for model in trim_codes_dicts.keys():
            for trim_code in trim_codes_dicts[model]:
                trim_code = trim_code.replace(' ', '%20')
                url+=f"trimCode={model.upper()}%7C{trim_code}&"
        return url[:len(url)-1] # remove the last '&'

    async def construct_url(self, search_results_preference:dict) -> str:
        url = "https://www.autotrader.com/cars-for-sale/"
        url += f"{search_results_preference["body_type"]}/"
        url += f"{search_results_preference["make"]}/"
        url += f"{search_results_preference["model"]}/"
        url += f"{search_results_preference["city_state"]}?"
        url += f"dealType={search_results_preference["deal_type"]}&"
        url += f"marketExtension={search_results_preference["inlude_delivery_options"]}&"
        url += f"searchRadius={search_results_preference["search_radius"]}&"
        url += f"sortBy={search_results_preference["sort_type"]}&"
        url += f"startYear={search_results_preference["min_year"]}&"
        constructed_url = await self.add_trims_to_url(url, search_results_preference["trim_codes"])
        return constructed_url
    
    async def get_car_list(self) -> list:
        return []

    async def main(self, search_results_preference:dict):
        self._browser = await ZenDriver.start()
        self._page = self._browser.main_tab
        await self._page.maximize()
        results_page_url = await self.construct_url(search_results_preference)
        print(results_page_url)
        await self._page.get(results_page_url)

        await asyncio.sleep(1000)

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
    asyncio.run(class_instance.main(search_results_preference))