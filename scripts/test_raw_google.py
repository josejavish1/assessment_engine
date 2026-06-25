import os

import requests


def test_raw_google():
    key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_CSE_ID", "02ec5ea2411d24516")
    if not key:
        print("❌ Error: GOOGLE_SEARCH_API_KEY no configurada.")
        return

    url = f"https://www.googleapis.com/customsearch/v1?q=Redeia&key={key}&cx={cx}"

    print(f"Testing URL: {url.replace(key, '***')}")
    r = requests.get(url)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")


if __name__ == "__main__":
    test_raw_google()
