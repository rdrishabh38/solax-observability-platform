import os
import requests
import urllib.parse
import time
import uuid
from typing import Optional, Dict, Any
from .crypto import SolaXCrypto

class SolaXClient:
    BASE_URL = "https://euapi.solaxcloud.com"

    def __init__(self, username=None, password=None):
        self.username = username or os.getenv("SOLAX_USERNAME")
        self.password = password or os.getenv("SOLAX_PASSWORD")
        self.crypto = SolaXCrypto()
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "crytoVer": "1",
            "deviceId": "84737d0a",
            "deviceType": "3",
            "Lang": "en_US",
            "source": "0",
            "websiteType": "0",
            "x-request-source": "3",
            "platform": "1",
            "version": "blue",
            "Permission-Version": "v7.2.0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        })

    def login(self) -> bool:
        """Authenticates and extracts the tokenId."""
        if not self.username or not self.password:
            return False

        # Use the username exactly as provided (user confirmed rdrishabh38 in .env)
        login_name = self.username

        payload = {
            "loginName": login_name,
            "password": self.crypto.md5_hash(self.password),
            "service": ""
        }
        
        # Encrypted credentials for the body
        encrypted_body = self.crypto.encrypt(payload)
        
        # Encrypted metadata for the query parameter
        timestamp = int(time.time() * 1000)
        request_id = str(uuid.uuid4())[:8]
        query_text = f"timeStamp={timestamp}&requestId={request_id}"
        encrypted_query = self.crypto.encrypt_string(query_text)
        
        url_encoded_data = urllib.parse.quote(encrypted_query)
        
        url = f"{self.BASE_URL}/unionUser/web/v2/public/login?data={url_encoded_data}"
        
        try:
            response = self.session.post(url, json={"data": encrypted_body}, timeout=10)
            print(f"Login Response Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Login Result Keys: {result.keys()}")
                if "data" in result:
                    decrypted = self.crypto.decrypt(result["data"])
                    
                    # Token is inside the 'result' object under the key 'token'
                    auth_result = decrypted.get("result", {})
                    self.token = auth_result.get("token")
                    
                    if self.token:
                        self.session.headers.update({"token": self.token})
                        return True
                    else:
                        print(f"Token key not found in result. Keys: {list(auth_result.keys())}")
                else:
                    print(f"Login failed: 'data' not in response: {result}")
        except Exception as e:
            print(f"Login error: {e}")
        return False

    def get_daily_report(self, sn: str, site_id: str, date_str: str) -> Optional[Dict[str, Any]]:
        """
        Fetches daily energy data for a specific inverter.
        date_str format: YYYY-MM-DD
        """
        if not self.token:
            if not self.login():
                return None

        payload = {
            "pageSize": 500,
            "pageNo": 1,
            "time": date_str,
            "sn": sn,
            "siteId": site_id,
            "dimension": 1
        }
        
        # Encrypted payload for the body
        encrypted_body = self.crypto.encrypt(payload)
        
        # Encrypted metadata for the query parameter
        timestamp = int(time.time() * 1000)
        request_id = str(uuid.uuid4())[:8]
        query_text = f"timeStamp={timestamp}&requestId={request_id}"
        encrypted_query = self.crypto.encrypt_string(query_text)
        url_encoded_data = urllib.parse.quote(encrypted_query)
        
        url = f"{self.BASE_URL}/zeus/v1/inverterEnergy/report?data={url_encoded_data}"
        
        try:
            response = self.session.post(url, json={"data": encrypted_body}, timeout=10)
            print(f"Report Response Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if "data" in result:
                    return self.crypto.decrypt(result["data"])
                else:
                    print(f"Report failed: 'data' not in response: {result}")
        except Exception as e:
            print(f"API Error: {e}")
        return None
