"""
Token compression and decompression utilities for Qwen authentication
"""

import base64
import gzip
from typing import Dict, Optional

from loguru import logger


def compress_token(credentials: str) -> str:
    """
    Compress credentials string using gzip and base64 encode
    
    Args:
        credentials: String in format "qwen_token|ssxmod_itna_cookie"
        
    Returns:
        Base64 encoded compressed string
        
    Raises:
        ValueError: If credentials is empty
        
    Example:
        >>> credentials = "abc123|xyz789"
        >>> compressed = compress_token(credentials)
        >>> isinstance(compressed, str)
        True
    """
    if not credentials or not credentials.strip():
        raise ValueError("Credentials cannot be empty")
        
    try:
        # Compress with gzip
        compressed = gzip.compress(credentials.encode('utf-8'))
        # Base64 encode
        encoded = base64.b64encode(compressed).decode('utf-8')
        logger.debug(f"✅ Compressed token: {len(credentials)} -> {len(encoded)} bytes")
        return encoded
    except Exception as e:
        logger.error(f"❌ Token compression error: {e}")
        raise


def decompress_token(compressed: str) -> str:
    """
    Decompress base64 encoded gzip compressed token
    
    Args:
        compressed: Base64 encoded compressed string
        
    Returns:
        Original credentials string
        
    Example:
        >>> credentials = "abc123|xyz789"
        >>> compressed = compress_token(credentials)
        >>> decompress_token(compressed) == credentials
        True
    """
    try:
        # Base64 decode
        decoded = base64.b64decode(compressed)
        # Decompress gzip
        decompressed = gzip.decompress(decoded)
        credentials = decompressed.decode('utf-8')
        logger.debug(
            f"✅ Decompressed token: {len(compressed)} -> "
            f"{len(credentials)} bytes"
        )
        return credentials
    except Exception as e:
        logger.error(f"❌ Token decompression error: {e}")
        raise


def parse_credentials(credentials: str) -> Optional[Dict[str, str]]:
    """
    Parse credentials string into components
    
    Args:
        credentials: String in format "qwen_token|ssxmod_itna_cookie"
        
    Returns:
        Dictionary with 'qwen_token' and 'ssxmod_itna' keys, or None if invalid
        
    Example:
        >>> creds = parse_credentials("abc123|xyz789")
        >>> creds['qwen_token']
        'abc123'
        >>> creds['ssxmod_itna']
        'xyz789'
    """
    try:
        parts = credentials.split('|')
        if len(parts) < 2:
            logger.warning("⚠️ Invalid credentials format: missing pipe separator")
            return None
        
        return {
            'qwen_token': parts[0].strip(),
            'ssxmod_itna': parts[1].strip()
        }
    except Exception as e:
        logger.error(f"❌ Credentials parsing error: {e}")
        return None


def validate_token_format(token: str) -> bool:
    """
    Validate token format without decompressing
    
    Args:
        token: Compressed token string
        
    Returns:
        True if format is valid, False otherwise
    """
    if not token or not token.strip():
        return False
        
    try:
        # Check if it's valid base64
        decoded = base64.b64decode(token)
        # Check if it's valid gzip
        gzip.decompress(decoded)
        return True
    except Exception:
        return False
