from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import re
from datetime import datetime
from typing import List, Optional
import time
import uuid

from models import (
    UserCreate, UserResponse, UserResponseWithKey, UserVerifyResponse, UpdateCredits,
    RuleCreate, RuleResponse,
    CommandExecutionRequest, CommandExecutionResponse, 
    CommandHistoryResponse, InsufficientCreditsResponse
)
from auth import get_current_user, get_admin_user, UserPayload
from database import init_db, supabase
from orchestrator import CommandOrchestrator
from conflict import ConflictDetector

# Setup
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app without a prefix
app = FastAPI(title="Unbound Command Gateway API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ Startup Event ============

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    logger.info("✓ Database initialized")

# ============ Health Check ============

@api_router.get("/")
async def root():
    return {"message": "Unbound Command Gateway API", "status": "online"}

# ============ Authentication Endpoints ============

@api_router.post("/auth/verify")
async def verify_api_key(user: UserPayload = Depends(get_current_user)):
    """Verify API key and return user details"""
    return {
        "status": "authenticated",
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "credits": user.credits
        }
    }

# ============ User Management Endpoints ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin: UserPayload = Depends(get_admin_user)):
    """Get all users (Admin only) - NEVER returns api_key for security"""
    try:
        response = supabase.table("app_users").select("id, name, role, credits, created_at").execute()
        return [
            UserResponse(
                id=u['id'],
                name=u['name'],
                role=u['role'],
                credits=u['credits'],
                created_at=u.get('created_at')
            ) for u in response.data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@api_router.post("/users", response_model=UserResponseWithKey, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    admin: UserPayload = Depends(get_admin_user)
):
    """Create new user (Admin only) - Returns API key ONCE"""
    
    # 1. Generate unique API key with 'uk_' prefix
    # Note: User schema has a default for api_key, but we can override or let DB handle it.
    # The schema uses encoding random bytes. 
    # But our auth system expects to verify it. 
    # Let's generate it here to show it to the user once.
    new_api_key = f"uk_{uuid.uuid4().hex}"
    
    # 2. Insert into Supabase
    user_payload = {
        "name": user_data.name,
        "role": user_data.role,
        "credits": 10,
        "api_key": new_api_key
    }
    
    try:
        response = supabase.table("app_users").insert(user_payload).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        new_user = response.data[0]
        
        logger.info(f"Admin {admin.id} created user {new_user['id']}")
        
        # 3. Return the key (This is the "Once" part)
        return UserResponseWithKey(
            id=new_user['id'],
            name=new_user['name'],
            role=new_user['role'],
            credits=new_user['credits'],
            api_key=new_user['api_key']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@api_router.put("/users/{user_id}/credits")
async def update_user_credits(
    user_id: str,
    update_data: UpdateCredits,
    admin: UserPayload = Depends(get_admin_user)
):
    """Update user credits (Admin only)"""
    try:
        response = supabase.table("app_users").update(
            {"credits": update_data.credits}
        ).eq("id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"Admin {admin.id} updated {user_id} credits to {update_data.credits}")
        
        return {
            "success": True,
            "user_id": user_id,
            "credits": update_data.credits
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: UserPayload = Depends(get_admin_user)
):
    """Delete user (Admin only)"""
    try:
        # Prevent admin from deleting themselves
        if user_id == admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        response = supabase.table("app_users").delete().eq("id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"Admin {admin.id} deleted user {user_id}")
        
        return {
            "success": True,
            "message": "User deleted successfully",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ============ Rules Management Endpoints ============

@api_router.get("/rules", response_model=List[RuleResponse])
async def get_rules(user: UserPayload = Depends(get_current_user)):
    """Get all configured rules"""
    try:
        # No 'order' column in user schema, so sort by created_at
        response = supabase.table("rules").select("*").order("created_at").execute()
        return [
            RuleResponse(
                id=r['id'],
                pattern=r['pattern'],
                action=r['action'],
                description=r.get('description', ''),
                is_active=r.get('is_active', True),
                created_at=r['created_at']
            ) for r in response.data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@api_router.post("/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    admin: UserPayload = Depends(get_admin_user)
):
    """Create new rule (Admin only)"""
    # Validate regex pattern
    try:
        re.compile(rule_data.pattern)
    except re.error as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid regex pattern: {str(e)}"
        )
    
    # Check for conflicts
    try:
        existing_rules_res = supabase.table("rules").select("id, pattern").execute()
        existing_rules = existing_rules_res.data
        
        has_conflict, reason = ConflictDetector.check_overlap(rule_data.pattern, existing_rules)
        
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Rule Conflict: {reason}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conflict check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify rule safety: {str(e)}"
        )
    
    try:
        # No 'order' column
        new_rule_payload = {
            "pattern": rule_data.pattern,
            "action": rule_data.action,
            "description": rule_data.description,
            "is_active": rule_data.is_active
        }
        
        response = supabase.table("rules").insert(new_rule_payload).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create rule")
            
        new_rule = response.data[0]
        
        logger.info(f"Admin {admin.id} created rule {new_rule['id']}")
        
        return RuleResponse(
            id=new_rule['id'],
            pattern=new_rule['pattern'],
            action=new_rule['action'],
            description=new_rule.get('description', ''),
            is_active=new_rule.get('is_active', True),
            created_at=new_rule['created_at']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@api_router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    admin: UserPayload = Depends(get_admin_user)
):
    """Delete a rule (Admin only)"""
    try:
        response = supabase.table("rules").delete().eq("id", rule_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        
        logger.info(f"Admin {admin.id} deleted rule {rule_id}")
        
        return {"success": True, "message": "Rule deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@api_router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    rule_data: RuleCreate,
    admin: UserPayload = Depends(get_admin_user)
):
    """Update a rule (Admin only)"""
    # Validate regex pattern
    try:
        re.compile(rule_data.pattern)
    except re.error as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid regex pattern: {str(e)}"
        )
    
    # Check for conflicts
    try:
        existing_rules_res = supabase.table("rules").select("id, pattern").neq("id", rule_id).execute()
        existing_rules = existing_rules_res.data
        
        has_conflict, reason = ConflictDetector.check_overlap(rule_data.pattern, existing_rules)
        
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Rule Conflict: {reason}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conflict check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify rule safety: {str(e)}"
        )
    
    try:
        update_payload = {
            "pattern": rule_data.pattern,
            "action": rule_data.action,
            "description": rule_data.description,
            "is_active": rule_data.is_active
        }
        
        response = supabase.table("rules").update(update_payload).eq("id", rule_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
            
        updated_rule = response.data[0]
        
        logger.info(f"Admin {admin.id} updated rule {rule_id}")
        
        return RuleResponse(
            id=updated_rule['id'],
            pattern=updated_rule['pattern'],
            action=updated_rule['action'],
            description=updated_rule.get('description', ''),
            is_active=updated_rule.get('is_active', True),
            created_at=updated_rule['created_at']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ============ Command Execution Endpoints ============

@api_router.post("/commands/execute")
async def execute_command(
    request: CommandExecutionRequest,
    user: UserPayload = Depends(get_current_user)
):
    """Execute a command with rule matching and credit management"""
    start_time = time.time()
    
    # Check if user has credits
    if user.credits <= 0:
        return InsufficientCreditsResponse(remaining_credits=0)
    
    # Process Command through Orchestrator
    result = await CommandOrchestrator.process_command(request.command_text)
    
    command_status = result["status"]
    credits_to_deduct = 0
    
    # Only deduct credits if command is executed
    if command_status == "EXECUTED":
        credits_to_deduct = 1
    
    # Update user credits if needed
    new_credits = user.credits
    if credits_to_deduct > 0:
        try:
            update_res = supabase.table("app_users").update(
                {"credits": user.credits - credits_to_deduct}
            ).eq("id", user.id).execute()
            
            if update_res.data:
                new_credits = update_res.data[0]['credits']
        except Exception as e:
            logger.error(f"Failed to update credits: {e}")
            raise HTTPException(status_code=500, detail="Credit transaction failed")
    
    # Log command execution
    execution_time = (time.time() - start_time) * 1000  # Convert to ms
    
    log_payload = {
        "user_id": user.id,
        "command_text": request.command_text,
        "status": command_status,
        "verdict_source": result.get("layer"), # Mapped from 'layer'
        "risk_score": result.get("score", 0),  # Mapped from 'score'
        # 'reason' and 'matched_rule' are NOT in DB schema, so we omit them
    }
    
    try:
        supabase.table("command_logs").insert(log_payload).execute()
    except Exception as e:
        logger.error(f"Failed to log command: {e}")
    
    logger.info(
        f"User {user.id} executed: '{request.command_text}' "
        f"-> {command_status} (Source: {result.get('layer')})"
    )
    
    return CommandExecutionResponse(
        status=command_status,
        command_text=request.command_text,
        verdict_source=result.get("layer"),
        risk_score=result.get("score", 0),
        reason=result.get("reason"), # Returned to UI but not saved to DB
        matched_rule=result.get("matched_rule"), # Returned to UI but not saved to DB
        credits_used=credits_to_deduct,
        remaining_credits=new_credits,
        timestamp=datetime.utcnow().isoformat()
    )

@api_router.get("/commands/history", response_model=List[CommandHistoryResponse])
async def get_command_history(
    admin_view: bool = False,
    user: UserPayload = Depends(get_current_user)
):
    """Get command execution history"""
    try:
        # Fetch logs
        query = supabase.table("command_logs").select("*")
        
        # If not admin or not requesting admin view, filter by user
        if not (admin_view and user.role == 'admin'):
            query = query.eq("user_id", user.id)
            
        response = query.order("created_at", desc=True).limit(100).execute()
        logs = response.data
        
        # Manually fetch user names if needed
        user_ids = list(set(log['user_id'] for log in logs if log.get('user_id')))
        user_map = {}
        
        if user_ids:
            users_res = supabase.table("app_users").select("id, name").in_("id", user_ids).execute()
            for u in users_res.data:
                user_map[u['id']] = u['name']
        
        result = []
        for cmd in logs:
            user_name = user_map.get(cmd.get('user_id'), 'Unknown')
            
            result.append(CommandHistoryResponse(
                id=str(cmd['id']),
                user_id=cmd['user_id'] or "",
                user_name=user_name,
                command_text=cmd['command_text'],
                status=cmd['status'],
                verdict_source=cmd.get('verdict_source'),
                risk_score=cmd.get('risk_score', 0),
                timestamp=cmd['created_at']
            ))
        
        return result
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)