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

from models import (
    UserCreate, UserResponse, UpdateCredits,
    RuleCreate, RuleResponse,
    CommandExecutionRequest, CommandExecutionResponse, 
    CommandHistoryResponse, InsufficientCreditsResponse
)
from auth import get_current_user, get_admin_user
from database import (
    init_db, users_collection, rules_collection, 
    commands_collection
)

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

@api_router.post("/auth/verify", response_model=UserResponse)
async def verify_api_key(user: dict = Depends(get_current_user)):
    """Verify API key and return user details"""
    return UserResponse(
        user_id=user['user_id'],
        api_key=user['api_key'],
        name=user['name'],
        role=user['role'],
        credits=user['credits']
    )

# ============ User Management Endpoints ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(admin: dict = Depends(get_admin_user)):
    """Get all users (Admin only)"""
    users = await users_collection.find().to_list(1000)
    return [
        UserResponse(
            user_id=u['user_id'],
            api_key=u['api_key'],
            name=u['name'],
            role=u['role'],
            credits=u['credits']
        ) for u in users
    ]

@api_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    admin: dict = Depends(get_admin_user)
):
    """Create new user (Admin only)"""
    from models import User
    
    new_user = User(
        name=user_data.name,
        role=user_data.role,
        credits=10
    )
    
    user_dict = new_user.dict()
    user_dict['created_at'] = user_dict['created_at'].isoformat() if user_dict['created_at'] else None
    
    await users_collection.insert_one(user_dict)
    
    logger.info(f"Admin {admin['user_id']} created user {new_user.user_id}")
    
    return UserResponse(
        user_id=new_user.user_id,
        api_key=new_user.api_key,
        name=new_user.name,
        role=new_user.role,
        credits=new_user.credits
    )

@api_router.put("/users/{user_id}/credits")
async def update_user_credits(
    user_id: str,
    update_data: UpdateCredits,
    admin: dict = Depends(get_admin_user)
):
    """Update user credits (Admin only)"""
    result = await users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'credits': update_data.credits}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Admin {admin['user_id']} updated {user_id} credits to {update_data.credits}")
    
    return {
        "success": True,
        "user_id": user_id,
        "credits": update_data.credits
    }

# ============ Rules Management Endpoints ============

@api_router.get("/rules", response_model=List[RuleResponse])
async def get_rules(user: dict = Depends(get_current_user)):
    """Get all configured rules"""
    rules = await rules_collection.find().sort('order', 1).to_list(1000)
    return [
        RuleResponse(
            id=r['id'],
            pattern=r['pattern'],
            action=r['action'],
            description=r['description'],
            created_at=r['created_at']
        ) for r in rules
    ]

@api_router.post("/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    admin: dict = Depends(get_admin_user)
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
    
    from models import Rule
    
    # Get current max order
    max_order_rule = await rules_collection.find_one(sort=[('order', -1)])
    next_order = (max_order_rule['order'] + 1) if max_order_rule else 1
    
    new_rule = Rule(
        pattern=rule_data.pattern,
        action=rule_data.action,
        description=rule_data.description,
        order=next_order
    )
    
    rule_dict = new_rule.dict()
    rule_dict['created_at'] = rule_dict['created_at'].isoformat() if rule_dict['created_at'] else None
    
    await rules_collection.insert_one(rule_dict)
    
    logger.info(f"Admin {admin['user_id']} created rule {new_rule.id}")
    
    return RuleResponse(
        id=new_rule.id,
        pattern=new_rule.pattern,
        action=new_rule.action,
        description=new_rule.description,
        created_at=rule_dict['created_at']
    )

@api_router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    admin: dict = Depends(get_admin_user)
):
    """Delete a rule (Admin only)"""
    result = await rules_collection.delete_one({'id': rule_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    
    logger.info(f"Admin {admin['user_id']} deleted rule {rule_id}")
    
    return {"success": True, "message": "Rule deleted"}

# ============ Command Execution Endpoints ============

@api_router.post("/commands/execute")
async def execute_command(
    request: CommandExecutionRequest,
    user: dict = Depends(get_current_user)
):
    """Execute a command with rule matching and credit management"""
    start_time = time.time()
    
    # Check if user has credits
    if user['credits'] <= 0:
        return InsufficientCreditsResponse(remaining_credits=0)
    
    # Get all rules sorted by order
    rules = await rules_collection.find().sort('order', 1).to_list(1000)
    
    # Match command against rules (first match wins)
    matched_rule_id = None
    command_status = "NO_MATCH"
    credits_to_deduct = 0
    
    for rule in rules:
        try:
            pattern = re.compile(rule['pattern'])
            if pattern.search(request.command_text):
                matched_rule_id = rule['id']
                command_status = "EXECUTED" if rule['action'] == "AUTO_ACCEPT" else "BLOCKED"
                
                # Only deduct credits if command is executed
                if command_status == "EXECUTED":
                    credits_to_deduct = 1
                
                break
        except re.error as e:
            logger.error(f"Invalid regex in rule {rule['id']}: {e}")
            continue
    
    # Update user credits if needed (transactional)
    new_credits = user['credits']
    if credits_to_deduct > 0:
        result = await users_collection.update_one(
            {'user_id': user['user_id']},
            {'$inc': {'credits': -credits_to_deduct}}
        )
        if result.modified_count > 0:
            new_credits = user['credits'] - credits_to_deduct
    
    # Log command execution
    execution_time = (time.time() - start_time) * 1000  # Convert to ms
    
    from models import CommandExecution
    
    command_log = CommandExecution(
        user_id=user['user_id'],
        command_text=request.command_text,
        status=command_status,
        matched_rule=matched_rule_id,
        credits_used=credits_to_deduct,
        execution_time_ms=execution_time
    )
    
    log_dict = command_log.dict()
    log_dict['timestamp'] = log_dict['timestamp'].isoformat() if log_dict['timestamp'] else None
    
    await commands_collection.insert_one(log_dict)
    
    logger.info(
        f"User {user['user_id']} executed command: '{request.command_text}' "
        f"-> {command_status} (Rule: {matched_rule_id})"
    )
    
    return CommandExecutionResponse(
        status=command_status,
        command_text=request.command_text,
        matched_rule=matched_rule_id,
        credits_used=credits_to_deduct,
        remaining_credits=new_credits,
        timestamp=log_dict['timestamp']
    )

@api_router.get("/commands/history", response_model=List[CommandHistoryResponse])
async def get_command_history(
    admin_view: bool = False,
    user: dict = Depends(get_current_user)
):
    """Get command execution history"""
    # If admin_view is true and user is admin, show all commands
    # Otherwise, show only user's own commands
    query = {}
    if not admin_view or user['role'] != 'admin':
        query = {'user_id': user['user_id']}
    
    commands = await commands_collection.find(query).sort('timestamp', -1).limit(100).to_list(100)
    
    # Get user names for each command
    result = []
    for cmd in commands:
        # Fetch user name
        cmd_user = await users_collection.find_one({'user_id': cmd['user_id']})
        user_name = cmd_user['name'] if cmd_user else 'Unknown User'
        
        result.append(CommandHistoryResponse(
            id=cmd['id'],
            user_id=cmd['user_id'],
            user_name=user_name,
            command_text=cmd['command_text'],
            status=cmd['status'],
            matched_rule=cmd.get('matched_rule'),
            credits_used=cmd['credits_used'],
            timestamp=cmd['timestamp']
        ))
    
    return result

# Include the router in the main app
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    from database import client
    client.close()
