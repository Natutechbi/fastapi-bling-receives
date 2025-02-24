import requests
from threading import Lock
from time import time, sleep

API_BASE_URL = "https://www.bling.com.br/Api/v3"

token_cache = {} # loja: (token: str, expiry: float)

"""
loja="lojaodositio" is not indented to be change,
this functnality will be extended for othel stores, but for now
only for the lojaodositio, so this is for future versions
"""      

"""
Block code lines 22-27: It's a thread-safe, throttled wrapper around requests.get 
that enforces a 1-second delay before executing the call. This ensures 
that multiple threads don't make simultaneous requests and that each 
request has a slight pause.He lock enforces thread safety and the sleep call 
introduces the delay before making each HTTP call.
"""
lock = Lock()
o_get = requests.get
def get(*args, **kwargs):
    with lock:
        sleep(4)
        return o_get(*args, **kwargs)

def fetch_access_token(loja="lojaodositio"):
    """
    Try to fetch and return access token for lajaodositio, with cache
    with token expiry 5 hours.

    Answer:
       -It’s the token-fetching logic that checks a cache for a valid access token and, 
       if necessary, makes an HTTP GET request to retrieve and cache a new token.

    Reasons:
       -It first verifies if a valid token exists in the cache.
       -If the token is missing or expired, it requests a new one from an external URL.
       -On success, it stores the token with its expiry time for future use.
    """
    if loja in token_cache:
        token, expiry = token_cache[loja]
        if time() < expiry:
            return token

    url = f"http://85.209.93.197:8080/code_bling/{loja}"
    headers = {
        'Authorization': 'Bearer 0123456789',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("GET", url, headers=headers, data={})
        access_token = response.json().get("access_token")
        if access_token:
            token_cache[loja] = (access_token, time() + 5 * 60 * 60)
            return access_token
        else:
            print("Failed to fetch access token.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching access token: {e}")
        return None

def get_headers(loja="lojaodositio") -> dict:
    """
    Return headers for lojaodasito with access token
    """

    token = fetch_access_token()
    if not token:
        print("token now available in headers")

    headers = {
        'Accept': 'application/json',
        'Authorization': f"Bearer {token}"
    }

    return headers
