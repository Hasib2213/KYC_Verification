import hmac
import hashlib
import json
import time
from typing import Dict, Any

def generate_signature(method: str, path: str, body: str, timestamp: int, secret: str) -> str:
    """Generate HMAC SHA256 signature for Sumsub API"""
    message = f"{method}{path}{body}{timestamp}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def prepare_headers(method: str, path: str, body: str = "", api_key: str = "", api_secret: str = "") -> Dict[str, str]:
    """Prepare headers with signature for official Sumsub API
    
    Uses X-App-Token and request signature headers.
    Signature format: METHOD + path + body + timestamp
    """
    timestamp = int(time.time())
    signature = generate_signature(method, path, body, timestamp, api_secret)
    
    headers = {
        "X-App-Token": api_key,
        "X-App-Access-Ts": str(timestamp),
        "X-App-Access-Sig": signature,
        "Content-Type": "application/json"
    }
    return headers

def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify Sumsub webhook signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
