#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Session Store - Encrypted storage for authentication cookies and tokens
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from app.utils.logger import get_logger

logger = get_logger()


class SessionStore:
    """Encrypted session storage for cookies and tokens"""
    
    def __init__(self, provider_name: str, storage_dir: str = ".sessions"):
        """
        Initialize session store
        
        Args:
            provider_name: Name of the provider (zai, k2think, qwen)
            storage_dir: Directory to store session files
        """
        self.provider_name = provider_name
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Session file path
        self.session_file = self.storage_dir / f"{provider_name}_session.json"
        
        # Encryption key (derived from environment variable or default)
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key"""
        # Try to get key from environment
        key_env = os.getenv("SESSION_ENCRYPTION_KEY")
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env)
            except Exception:
                logger.warning("Invalid SESSION_ENCRYPTION_KEY, generating new key")
        
        # Generate key from machine-specific data
        machine_id = os.getenv("HOSTNAME", "default-machine")
        salt = b"z.ai2api_python_session_salt"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return key
    
    def save_session(
        self, 
        cookies: Dict[str, str], 
        token: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save session data with encryption
        
        Args:
            cookies: Dictionary of cookies
            token: Optional authentication token
            extra_data: Optional extra data to store
            
        Returns:
            bool: True if successful
        """
        try:
            session_data = {
                "provider": self.provider_name,
                "cookies": cookies,
                "token": token,
                "timestamp": int(time.time()),
                "extra": extra_data or {}
            }
            
            # Serialize and encrypt
            json_data = json.dumps(session_data)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            # Save to file
            with open(self.session_file, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info(f"✅ {self.provider_name} session saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save {self.provider_name} session: {e}")
            return False
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt session data
        
        Returns:
            Optional[Dict]: Session data if valid, None otherwise
        """
        try:
            if not self.session_file.exists():
                logger.debug(f"No session file found for {self.provider_name}")
                return None
            
            # Read and decrypt
            with open(self.session_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            session_data = json.loads(decrypted_data.decode())
            
            logger.debug(f"✅ {self.provider_name} session loaded successfully")
            return session_data
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load {self.provider_name} session: {e}")
            return None
    
    def is_valid(self, max_age: int = 86400) -> bool:
        """
        Check if session is still valid
        
        Args:
            max_age: Maximum age in seconds (default: 24 hours)
            
        Returns:
            bool: True if valid
        """
        session = self.load_session()
        if not session:
            return False
        
        timestamp = session.get("timestamp", 0)
        age = int(time.time()) - timestamp
        
        is_valid = age < max_age
        if not is_valid:
            logger.info(f"⏰ {self.provider_name} session expired (age: {age}s)")
        
        return is_valid
    
    def get_cookies(self) -> Optional[Dict[str, str]]:
        """Get cookies from stored session"""
        session = self.load_session()
        return session.get("cookies") if session else None
    
    def get_token(self) -> Optional[str]:
        """Get token from stored session"""
        session = self.load_session()
        return session.get("token") if session else None
    
    def clear_session(self) -> bool:
        """Delete session file"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info(f"🗑️ {self.provider_name} session cleared")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear {self.provider_name} session: {e}")
            return False
    
    def update_timestamp(self) -> bool:
        """Update session timestamp to keep it fresh"""
        session = self.load_session()
        if session:
            session["timestamp"] = int(time.time())
            return self.save_session(
                session.get("cookies", {}),
                session.get("token"),
                session.get("extra")
            )
        return False
