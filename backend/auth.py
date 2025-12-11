from fastapi import Header, HTTPException, status
from typing import Optional
from database import users_collection

async def get_current_user(x_api_key: Optional[str] = Header(None)):
    """Authenticate user via API key"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required. Include X-API-Key header."
        )
    
    user = await users_collection.find_one({'api_key': x_api_key})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    # Remove MongoDB _id for cleaner response
    user.pop('_id', None)
    return user

async def get_admin_user(x_api_key: Optional[str] = Header(None)):
    """Authenticate and verify admin role"""
    user = await get_current_user(x_api_key)
    
    if user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user
