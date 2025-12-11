from supabase import create_client, Client
from typing import Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Supabase connection
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")

supabase: Client = create_client(supabase_url, supabase_key)

async def init_db():
    """Initialize database with seed data"""
    
    # Check if admin user exists
    try:
        response = supabase.table("app_users").select("*").eq("api_key", "admin_key_2025").execute()
        
        if not response.data:
            # Seed initial admin user
            admin_user = {
                'name': 'Admin User',
                'role': 'admin',
                'credits': 1000,
                'api_key': 'admin_key_2025'
            }
            supabase.table("app_users").insert(admin_user).execute()
            logger.info("✓ Admin user seeded: admin_key_2025")
        else:
            logger.info("✓ Admin user already exists")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
