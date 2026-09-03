import os

PORT = int(os.getenv("PORT", "8080"))
HOST = os.getenv("HOST", "0.0.0.0")

BASE_URL = os.getenv("ABHI_BASE_URL", "https://abhilinks.site")
REST_API_URL = f"{BASE_URL}/wp-json/wp/v2"

MOVIESHUNT_BASE_URL = os.getenv("MOVIESHUNT_BASE_URL", "https://movieshunt.casa")

USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "12.0"))
MAX_PER_PAGE = int(os.getenv("MAX_PER_PAGE", "50"))
