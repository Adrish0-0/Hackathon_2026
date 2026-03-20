import hashlib
import hmac
import requests
import time


API_KEY = "9eoh9Mb0vdGOaIgFauoB5BsuNDlxPDixJOZUee5vwEgjMqcyevIAyBmWRsCL285X"
API_SECRET = "FPvzVFsVfBxLX8OSnOiIVxbc2VkDhkkeUYf4wIOcU7VAqhx1VXJzWNCYv0Z1UkeT"

BASE_URL = "https://mock-api.roostoo.com"


def generate_signature(parameters):
    query_string = "&".join([f"{i}={parameters[i]}" for i in sorted(parameters.keys())])
    secret_byte = API_SECRET.encode("utf-8")
    query_byte = query_string.encode("utf-8")
    
    signature = hmac.new(secret_byte, query_byte, hashlib.sha256).hexdigest()
    
    return signature


def get_server_time():
    url = BASE_URL + "/v3/serverTime"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get server time: {e}")
        return None


def get_exchange_info():
    url = BASE_URL + "/v3/exchangeInfo"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get exchange info: {e}")
        return None


def get_ticker(pair = None):
    url = BASE_URL + "/v3/ticker"
    payload = {"timestamp": int(time.time()) * 1000}
    if pair:
        payload["pair"] = pair
    try:
        response = requests.get(url, params = payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get ticker: {e}")
        return None


def get_balance():
    url = BASE_URL + "/v3/balance"
    payload = {"timestamp": int(time.time()) * 1000}
    headers = {
        "RST-API-KEY": API_KEY,
        "MSG-SIGNATURE": generate_signature(payload)
    }
    try:
        response = requests.get(url, params = payload, headers = headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get balance: {e}")
        print(f"[ERROR] Response text: {e.response.text if e.response else 'N/A'}")
        return None


def get_pending_count():
    url = BASE_URL + "/v3/pending_count"
    payload = {"timestamp": int(time.time()) * 1000}
    headers = {
        "RST-API-KEY": API_KEY,
        "MSG-SIGNATURE": generate_signature(payload)
    }
    try:
        response = requests.get(url, params = payload, headers = headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get pending count: {e}")
        print(f"[ERROR] Response text: {e.response.text if e.response else "N/A"}")
        return None


def place_order(coin, side, quantity, price = None):
    url = BASE_URL + "/v3/place_order"
    payload = {
        "timestamp": int(time.time()) * 1000,
        "pair": coin + "/USD",
        "side": side,
        "quantity": quantity
    }
    if not price:
        payload["type"] = "MARKET"
    else:
        payload["type"] = "LIMIT"
        payload["price"] = price
    headers = {
        "RST-API-KEY": API_KEY,
        "MSG-SIGNATURE": generate_signature(payload)
    }
    try:
        response = requests.post(url, data = payload, headers = headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to place order: {e}")
        print(f"Response text: {e.response.text if e.response else "N/A"}")
        return None


def cancel_order():
    url = BASE_URL + "/v3/cancel_order"
    payload = {
        "timestamp": int(time.time()) * 1000,
        "pair": "BTC/USD"
    }
    headers = {
        "RST-API-KEY": API_KEY,
        "MSG-SIGNATURE": generate_signature(payload)
    }
    try:
        response = requests.post(url, data = payload, headers = headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to cancel order: {e}")
        print(f"Response text: {e.response.text if e.response else "N/A"}")
        return None



def query_order():
    url = BASE_URL + "/v3/query_order"
    payload = {"timestamp": int(time.time()) * 1000}
    headers = {
        "RST-API-KEY": API_KEY,
        "MSG-SIGNATURE": generate_signature(payload)
    }
    try:
        response = requests.post(url, data = payload, headers = headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to query order: {e}")
        print(f"Response text: {e.response.text if e.response else "N/A"}")
        return None





