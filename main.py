import requests

def get_usd_to_jpy():
    URL = "https://api.frankfurter.app/latest?from=USD&to=JPY"
    try:
        res = requests.get(URL)
        data = res.json()
        rate = data["rates"]["JPY"]
        print(f"1 USD = {rate} JPY")
    except Exception as e:
        print("Exception thrown while fetching rate: {e}")

if __name__ == "__main__":
    get_usd_to_jpy()