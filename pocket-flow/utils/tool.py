
import requests
from .settings import BRAVE_API_KEY


def search_web_brave(query) -> str:

    url = "https://api.search.brave.com/res/v1/web/search"
    api_key = BRAVE_API_KEY
    if not api_key:
        raise ValueError("BRAVE_API_KEY is not set")

    headers = {
        "accept": "application/json",
        "Accept-Encoding": "gzip",
        "x-subscription-token": api_key
    }

    params = {
        "q": query
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data['web']['results']
        return "\n\n".join([f"Title: {r['title']}\nURL: {r['url']}\nDescription: {r['description']}" for r in results])
    return f"Request failed with status code: {response.status_code}"
