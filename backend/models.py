from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

# ============ User Models ============

class UserCreate(BaseModel):
    name: str
    role: Literal["admin", "member"] = "member"

class UserResponseWithKey(BaseModel):
    """Used ONLY when creating a user - returns the API key once"""
    id: str
    name: str
    role: str
    credits: int
    api_key: str
    message: str = "User created successfully"
    warning: str = "SAVE THIS KEY NOW. It will never be shown again."

class UserResponse(BaseModel):
    """Used for listing users - NEVER includes api_key"""
    id: str
    name: str
    role: str
    credits: int
    created_at: Optional[str] = None

class UserVerifyResponse(BaseModel):
    """Used for auth/verify endpoint"""
    status: str = "authenticated"
    user: dict

class UpdateCredits(BaseModel):
    credits: int = Field(ge=0)

# ============ Rule Models ============

class Rule(BaseModel):
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    pattern: str
    action: Literal["AUTO_ACCEPT", "AUTO_REJECT"]
    description: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RuleCreate(BaseModel):
    pattern: str
    action: Literal["AUTO_ACCEPT", "AUTO_REJECT"]
    description: str = ""
    is_active: bool = True

class RuleResponse(BaseModel):
    id: str
    pattern: str
    action: str
    description: str
    is_active: bool
    created_at: str

# ============ Command Execution Models ============

class CommandExecutionRequest(BaseModel):
    command_text: str

class CommandExecution(BaseModel):
    id: str = Field(default_factory=lambda: f"cmd_{uuid.uuid4().hex[:8]}")
    user_id: str
    command_text: str
    status: Literal["EXECUTED", "BLOCKED", "NO_MATCH", "INSUFFICIENT_CREDITS"]
    verdict_source: Optional[str] = None # Was 'layer'
    risk_score: int = 0 # Was 'score'
    reason: Optional[str] = None # Not in DB schema but useful for response? User didn't include it in DB.
    # User schema: id, user_id, command_text, status, verdict_source, risk_score, created_at.
    # 'reason' and 'matched_rule' are NOT in the DB schema provided.
    # We will return them in API response but NOT save them to DB unless we add columns.
    # User said "i have only three tables... and i will provide the schema".
    # So we must NOT try to insert 'reason' or 'matched_rule' into DB.
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0

class CommandExecutionResponse(BaseModel):
    status: str
    command_text: str
    verdict_source: Optional[str] = None
    risk_score: int = 0
    reason: Optional[str] = None # We can still return it to frontend if we calculate it
    matched_rule: Optional[str] = None
    credits_used: int
    remaining_credits: int
    timestamp: str

class CommandHistoryResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    command_text: str
    status: str
    verdict_source: Optional[str]
    risk_score: int
    # reason and matched_rule removed from history response as they aren't in DB
    timestamp: str

class InsufficientCreditsResponse(BaseModel):
    status: str = "INSUFFICIENT_CREDITS"
    message: str = "No credits available"
    remaining_credits: int = 0
