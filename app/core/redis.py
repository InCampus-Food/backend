import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def blacklist_token(jti: str, expires_in: int):
    """Add token JTI to blacklist with expiry"""
    await redis_client.setex(f"blacklist:{jti}", expires_in, "1")

async def is_token_blacklisted(jti: str) -> bool:
    """Check if token is blacklisted"""
    return await redis_client.exists(f"blacklist:{jti}") > 0

async def store_refresh_token(user_id: str, jti: str, expires_in: int):
    """Store refresh token JTI for user"""
    await redis_client.setex(f"refresh:{user_id}:{jti}", expires_in, "1")

async def revoke_refresh_token(user_id: str, jti: str):
    """Revoke a specific refresh token"""
    await redis_client.delete(f"refresh:{user_id}:{jti}")

async def revoke_all_refresh_tokens(user_id: str):
    """Revoke all refresh tokens for a user (logout all devices)"""
    keys = await redis_client.keys(f"refresh:{user_id}:*")
    if keys:
        await redis_client.delete(*keys)

async def is_refresh_token_valid(user_id: str, jti: str) -> bool:
    """Check if refresh token is valid"""
    return await redis_client.exists(f"refresh:{user_id}:{jti}") > 0
