from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from database import supabase
from pydantic import BaseModel

# Define the Header Scheme
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

class UserPayload(BaseModel):
    id: str
    name: str
    role: str
    credits: int
    api_key: str

async def get_current_user(api_key: str = Security(api_key_header)):
    """
    Authenticates user by checking the x-api-key header against the DB.
    """
    if not api_key:
        raise HTTPException(
            status_code=401, 
            detail="Missing API Key. Use header 'x-api-key'"
        )

    # 1. Direct Lookup
    try:
        response = supabase.table("app_users").select("*").eq("api_key", api_key).execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    
    # 2. Handle Invalid Key
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=401, 
            detail="Invalid API Key"
        )

    user = response.data[0]
    
    return UserPayload(
        id=user['id'],
        name=user['name'],
        role=user['role'],
        credits=user['credits'],
        api_key=user['api_key']
    )

async def get_admin_user(user: UserPayload = Security(get_current_user)):
    """Guard for Admin Routes"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin Access Required")
    return user
