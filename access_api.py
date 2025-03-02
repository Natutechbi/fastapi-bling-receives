import requests
from threading import Lock
from time import time, sleep
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_TOKEN_BLING = os.getenv("API_TOKEN_BLING")

token_cache = {} # loja: (token: str, expiry: float)

lock = Lock()
o_get = requests.get
def get(*args, **kwargs):
    with lock:
        sleep(4)
        return o_get(*args, **kwargs)

def fetch_access_token(loja=None):
    """
    Try to fetch and return access token for lajaodositio, with cache
    with token expiry 5 hours.

    Answer:
       -It's the token-fetching logic that checks a cache for a valid access token and, 
       if necessary, makes an HTTP GET request to retrieve and cache a new token.

    Reasons:
       -It first verifies if a valid token exists in the cache.
       -If the token is missing or expired, it requests a new one from an external URL.
       -On success, it stores the token with its expiry time for future use.
    """
    # Use environment variable if loja is not provided
    if loja is None:
        loja = os.getenv("LOJA")
        
    if loja in token_cache:
        token, expiry = token_cache[loja]
        if time() < expiry:
            return token
    url = f"{API_TOKEN_BLING}/{loja}"
    headers = {
        'Authorization': 'Bearer 0123456789',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("GET", url, headers=headers, data={})
        if response.status_code == 200:
            logging.info(f"Successfully fetched access token for {loja}")
            access_token = response.json().get("access_token")
            if access_token:
                token_cache[loja] = (access_token, time() + 5 * 60 * 60)
                return access_token
            else:
                logging.error("Failed to fetch access token.")
                return None
        else:
            logging.error(f"Failed to fetch access token: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching access token: {e}")
        return None

def get_headers(loja=None) -> dict:
    """
    Return headers for the store with access token
    """
    # Use environment variable if loja is not provided
    if loja is None:
        loja = os.getenv("LOJA")
        
    token = fetch_access_token(loja)
    if not token:
        logging.error("token not available in headers")
    else:
        logging.info("Successfully added token to headers")

    headers = {
        'Accept': 'application/json',
        'Authorization': f"Bearer {token}"
    }

    return headers
