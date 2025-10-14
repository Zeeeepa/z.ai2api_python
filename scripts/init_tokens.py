#!/usr/bin/env python3
"""
Token initialization script
Logs in with credentials and stores tokens in the database
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.zai_provider import ZAIProvider
from app.services.token_dao import TokenDAO
from app.core.config import settings
from app.utils.logger import logger


async def initialize_tokens():
    """Initialize tokens by logging in and storing them"""
    
    logger.info("🔑 Starting token initialization...")
    
    # Check credentials
    if not settings.ZAI_EMAIL or not settings.ZAI_PASSWORD:
        logger.error("❌ ZAI_EMAIL or ZAI_PASSWORD not configured!")
        logger.error("   Please set environment variables:")
        logger.error("   export ZAI_EMAIL='your@email.com'")
        logger.error("   export ZAI_PASSWORD='your_password'")
        return False
    
    # Initialize database
    token_dao = TokenDAO()
    await token_dao.init_database()
    logger.info("✅ Database initialized")
    
    # Login to get token
    provider = ZAIProvider()
    logger.info(f"🔐 Attempting login with email: {settings.ZAI_EMAIL}")
    
    token = await provider.login_with_credentials()
    
    if not token:
        logger.error("❌ Login failed! Could not retrieve token")
        logger.error("   Please check:")
        logger.error("   1. Email and password are correct")
        logger.error("   2. Network connection is available")
        logger.error("   3. Z.AI service is accessible")
        return False
    
    logger.info(f"✅ Login successful! Token retrieved: {token[:30]}...")
    
    # Store token in database
    logger.info("💾 Storing token in database...")
    token_id = await token_dao.add_token(
        provider="zai",
        token=token,
        token_type="user",
        priority=10,
        validate=False  # Already validated by login
    )
    
    if token_id:
        logger.info(f"✅ Token stored successfully! Token ID: {token_id}")
        logger.info("")
        logger.info("🎉 Token initialization complete!")
        logger.info("   You can now start the server with: bash scripts/start.sh")
        return True
    else:
        logger.error("❌ Failed to store token in database")
        return False


async def main():
    """Main entry point"""
    success = await initialize_tokens()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

