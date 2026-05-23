# System Architecture & Logic Specification: SolaX Cloud API Extractor

## 1. Project Objective
Build a modular, robust Python application that authenticates with the SolaX Cloud web portal, bypasses their custom AES frontend encryption, and extracts daily inverter energy data into a structured format (JSON) for local ingestion.

## 2. Core Cryptographic Constants & Rules
The SolaX portal uses custom encryption to mask payloads.

* **Encryption Algorithm:** AES-128-CBC
* **Padding:** PKCS7
* **Secret Key:** `b"hj7x22H$yuBI0456"` (Load from `SOLAX_AES_KEY`)
* **Initialization Vector (IV):** `b"NIfb&74GUY86Gfgh"` (Load from `SOLAX_AES_IV`)
* **Password Hashing:** Raw MD5 (32-character hex digest)

### Payload Transformation Flow
1. **Redundant Security Pattern:** **Every** POST request requires encrypted data in **both** the URL and the Body.
2. **URL Data (`?data=`):** Encrypted raw string: `timeStamp=<ms_timestamp>&requestId=<8_char_uuid_fragment>`.
3. **Body Data (`{"data": "..."}`):** Encrypted compact JSON (no spaces).
4. **Encryption Step:** `Text` -> `PKCS7 Pad` -> `AES-CBC Encrypt` -> `Base64 Encode` -> `URL Encode` (for Query Param only).

## 3. API Endpoints & Mandatory Headers

**Base URL:** `https://euapi.solaxcloud.com`

### Mandatory Headers (Global)
These headers are required to avoid `407`, `408`, and `501` errors:
* `Content-Type: application/json`
* `User-Agent: Mozilla/5.0 ...` (Browser string)
* `crytoVer: 1`
* `deviceId: 84737d0a`
* `deviceType: 3`
* `Lang: en_US`
* `source: 0`
* `websiteType: 0`
* `x-request-source: 3`
* `platform: 1`
* `version: blue`
* `Permission-Version: v7.2.0`

### A. Authentication (Login)
* **Endpoint:** POST `/unionUser/web/v2/public/login`
* **Plaintext JSON Schema (for Body):**
    ```json
    {
      "loginName": "<USER_ID_OR_NAME>",
      "password": "<MD5_HASHED_PASSWORD>",
      "service": ""
    }
    ```
* **Action:** Decrypt the response and extract the JWT `token` from `result.token`. Pass this as a `token` header in all subsequent requests.

### B. Daily Data Extraction (Report)
* **Endpoint:** POST `/zeus/v1/inverterEnergy/report`
* **Additional Header:** `token: <JWT_TOKEN_FROM_LOGIN>`
* **Plaintext JSON Schema (for Body):**
    ```json
    {
      "pageSize": 500,
      "pageNo": 1,
      "time": "YYYY-MM-DD", 
      "sn": "<INVERTER_SN>",
      "siteId": "<PLANT_ID>",
      "dimension": 1
    }
    ```

## 4. Application Logic
* **Smart Sync:** 
    * Always refresh the current day.
    * Re-fetch historical days if the local JSON is missing, marked as `"empty": true`, or has fewer than **180** records.
* **Anti-Bot Measures:**
    * Implement random delays (e.g., 2-5 seconds) between API requests to mimic human behavior and avoid rate-limiting or 501/timeout errors.
* **Storage:** 
    * JSON: `data/<SN>/<SN>_<yyyy_mm_dd>.json` acts as the primary source of truth.
    * PostgreSQL: Aggregates records into a persistent database managed by **Alembic**.
    * **Descriptive Schema**: Maps raw API keys (e.g., `vdc1`, `pac1`) to human-readable columns (e.g., `mppt1_voltage_volts`, `ac_power_watts`).
