"""Z.AI API Signature Generation"""

import hashlib
import time
from typing import Tuple


def generate_signature_headers(chat_id: str) -> Tuple[str, str]:
    """
    Generate Z.AI API signature headers.
    
    Args:
        chat_id: Chat session ID
        
    Returns:
        Tuple of (signature, timestamp)
    """
    timestamp = int(time.time() * 1000)
    raw = f"{chat_id}{timestamp}"
    signature = hashlib.sha256(raw.encode()).hexdigest()
    return signature, str(timestamp)


def add_signature_to_headers(headers: dict, chat_id: str) -> dict:
    """
    Add Z.AI signature headers to existing headers dict.
    
    Args:
        headers: Existing headers dictionary
        chat_id: Chat session ID
        
    Returns:
        Updated headers dictionary
    """
    signature, timestamp = generate_signature_headers(chat_id)
    headers["X-Signature"] = signature
    headers["X-Timestamp"] = timestamp
    return headers
