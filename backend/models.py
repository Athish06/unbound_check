from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

# ============ User Models ============

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:8]}")
    api_key: str = Field(default_factory=lambda: f"{uuid.uuid4().hex}")
    name: str
    role: Literal["admin", "member"]
    credits: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    name: str
    role: Literal["admin", "member"] = "member"

class UserResponse(BaseModel):
    user_id: str
    api_key: str
    name: str
    role: str
    credits: int

class UpdateCredits(BaseModel):
    credits: int = Field(ge=0)

# ============ Rule Models ============

class Rule(BaseModel):
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    pattern: str
    action: Literal["AUTO_ACCEPT", "AUTO_REJECT"]
    description: str = ""
    order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RuleCreate(BaseModel):
    pattern: str
    action: Literal["AUTO_ACCEPT", "AUTO_REJECT"]
    description: str = ""

class RuleResponse(BaseModel):
    id: str
    pattern: str
    action: str
    description: str
    created_at: str

# ============ Command Execution Models ============

class CommandExecutionRequest(BaseModel):
    command_text: str

class CommandExecution(BaseModel):
    id: str = Field(default_factory=lambda: f"cmd_{uuid.uuid4().hex[:8]}")
    user_id: str
    command_text: str
    status: Literal["EXECUTED", "BLOCKED", "NO_MATCH", "INSUFFICIENT_CREDITS"]
    matched_rule: Optional[str] = None
    credits_used: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0

class CommandExecutionResponse(BaseModel):
    status: str
    command_text: str
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
    matched_rule: Optional[str]
    credits_used: int
    timestamp: str

class InsufficientCreditsResponse(BaseModel):
    status: str = "INSUFFICIENT_CREDITS"
    message: str = "No credits available"
    remaining_credits: int = 0
