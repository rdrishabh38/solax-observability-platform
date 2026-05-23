import os
import hashlib
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from dotenv import load_dotenv

load_dotenv()

class SolaXCrypto:
    def __init__(self):
        # Load from env with defaults as fallback (though they should be in .env)
        self.key = os.getenv("SOLAX_AES_KEY", "hj7x22H$yuBI0456").encode("utf-8")
        self.iv = os.getenv("SOLAX_AES_IV", "NIfb&74GUY86Gfgh").encode("utf-8")
        self.block_size = AES.block_size

    def md5_hash(self, text: str) -> str:
        """Raw MD5 32-character hex digest."""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def encrypt_string(self, text: str) -> str:
        """
        Encrypts a raw string: String -> PKCS7 Pad -> AES-CBC Encrypt -> Base64.
        """
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_data = pad(text.encode("utf-8"), self.block_size)
        encrypted_bytes = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_bytes).decode("utf-8")

    def encrypt(self, data: dict) -> str:
        """
        Encrypts a dictionary: Dict -> JSON String -> PKCS7 Pad -> AES-CBC Encrypt -> Base64.
        """
        json_str = json.dumps(data, separators=(",", ":"))
        return self.encrypt_string(json_str)

    def decrypt(self, encrypted_base64: str) -> dict:
        """
        Decrypts a Base64 string: Base64 Decode -> AES-CBC Decrypt -> Unpad -> Parse JSON.
        """
        encrypted_bytes = base64.b64decode(encrypted_base64)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        unpadded_data = unpad(decrypted_bytes, self.block_size)
        return json.loads(unpadded_data.decode("utf-8"))
