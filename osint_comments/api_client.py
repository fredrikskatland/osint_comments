# api_client.py
import random
import requests
from config import API_BASE_URL, COMMENTS_ENDPOINT_TEMPLATE, DEFAULT_LIMIT, DEFAULT_OFFSET, DEFAULT_ORDER, DEFAULT_REPLIES

# A list of example User-Agent strings.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.90 Safari/537.36"
    # ... add more user agents as needed
]

# A list of proxies. Format: "http://ip:port" or "https://ip:port".
# Leave the list empty if you are not using proxies.
PROXIES = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    # ... add more proxies if you have them
]

class APIClient:
    def __init__(self):
        self.base_url = API_BASE_URL

    def get_random_headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS)
        }

    def get_random_proxy(self):
        # If you have proxies defined, choose one at random.
        if PROXIES:
            proxy = random.choice(PROXIES)
            # Both HTTP and HTTPS can use the same proxy.
            return {
                "http": proxy,
                "https": proxy
            }
        return None

    def fetch_comments(self, article_identifier: str, limit: int = DEFAULT_LIMIT, offset: int = DEFAULT_OFFSET,
                       order: str = DEFAULT_ORDER, replies: str = DEFAULT_REPLIES) -> dict:
        endpoint = COMMENTS_ENDPOINT_TEMPLATE.format(article_identifier=article_identifier)
        url = f"{self.base_url}{endpoint}?limit={limit}&offset={offset}&order={order}&replies={replies}"

        headers = self.get_random_headers()
        proxies = self.get_random_proxy()

        # You might also consider adding retry logic or timeouts.
        response = requests.get(url, headers=headers, timeout=10) # , proxies=proxies,
        response.raise_for_status()
        return response.json()
