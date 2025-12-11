# Unbound Command Gateway - API Contracts & Integration Plan

## 1. API Endpoints Overview

### Base URL
- **Development**: `http://localhost:8001/api`
- **Environment Variable**: `REACT_APP_BACKEND_URL`

### Authentication
- **Method**: API Key in headers
- **Header**: `X-API-Key: <api_key>`

---

## 2. API Contracts

### 2.1 Authentication & User Management

#### `POST /api/auth/verify`
**Description**: Verify API key and return user details
**Request Headers**:
```
X-API-Key: admin_key_123
```
**Response**:
```json
{
  "api_key": "admin_key_123",
  "user_id": "admin_001",
  "name": "Admin User",
  "role": "admin",
  "credits": 100
}
```

#### `GET /api/users`
**Description**: Get all users (Admin only)
**Auth**: Admin only
**Response**:
```json
[
  {
    "user_id": "admin_001",
    "api_key": "admin_key_123",
    "name": "Admin User",
    "role": "admin",
    "credits": 100
  }
]
```

#### `POST /api/users`
**Description**: Create new user (Admin only)
**Request**:
```json
{
  "name": "John Smith",
  "role": "member"
}
```
**Response**:
```json
{
  "user_id": "member_003",
  "api_key": "member_key_abc123",
  "name": "John Smith",
  "role": "member",
  "credits": 10
}
```

#### `PUT /api/users/{user_id}/credits`
**Description**: Update user credits (Admin only)
**Request**:
```json
{
  "credits": 50
}
```
**Response**:
```json
{
  "success": true,
  "user_id": "member_001",
  "credits": 50
}
```

---

### 2.2 Rules Management

#### `GET /api/rules`
**Description**: Get all configured rules
**Response**:
```json
[
  {
    "id": "rule_001",
    "pattern": "^git (pull|fetch|status)",
    "action": "AUTO_ACCEPT",
    "description": "Safe git read operations",
    "created_at": "2024-07-15T10:30:00Z"
  }
]
```

#### `POST /api/rules`
**Description**: Create new rule (Admin only)
**Request**:
```json
{
  "pattern": "^npm install",
  "action": "AUTO_ACCEPT",
  "description": "Safe npm package installation"
}
```
**Response**:
```json
{
  "id": "rule_005",
  "pattern": "^npm install",
  "action": "AUTO_ACCEPT",
  "description": "Safe npm package installation",
  "created_at": "2024-07-15T11:00:00Z"
}
```

#### `DELETE /api/rules/{rule_id}`
**Description**: Delete a rule (Admin only)
**Response**:
```json
{
  "success": true,
  "message": "Rule deleted"
}
```

---

### 2.3 Command Execution

#### `POST /api/commands/execute`
**Description**: Execute a command
**Request**:
```json
{
  "command_text": "git status"
}
```
**Response (Success)**:
```json
{
  "status": "EXECUTED",
  "command_text": "git status",
  "matched_rule": "rule_001",
  "credits_used": 1,
  "remaining_credits": 9,
  "timestamp": "2024-07-15T14:30:00Z"
}
```
**Response (Blocked)**:
```json
{
  "status": "BLOCKED",
  "command_text": "rm -rf /",
  "matched_rule": "rule_002",
  "credits_used": 0,
  "remaining_credits": 10,
  "timestamp": "2024-07-15T14:31:00Z"
}
```
**Response (No Match)**:
```json
{
  "status": "NO_MATCH",
  "command_text": "unknown command",
  "matched_rule": null,
  "credits_used": 0,
  "remaining_credits": 10,
  "timestamp": "2024-07-15T14:32:00Z"
}
```
**Response (Insufficient Credits)**:
```json
{
  "status": "INSUFFICIENT_CREDITS",
  "message": "No credits available",
  "remaining_credits": 0
}
```

#### `GET /api/commands/history`
**Description**: Get command history
**Query Parameters**:
- `admin_view`: true/false (if true, shows all users' history)
**Response**:
```json
[
  {
    "id": "cmd_001",
    "user_id": "member_001",
    "user_name": "John Doe",
    "command_text": "git status",
    "status": "EXECUTED",
    "matched_rule": "rule_001",
    "credits_used": 1,
    "timestamp": "2024-07-15T14:22:10Z"
  }
]
```

---

## 3. MongoDB Collections Schema

### Collection: `users`
```javascript
{
  _id: ObjectId,
  user_id: String (unique),
  api_key: String (unique, indexed),
  name: String,
  role: String ("admin" | "member"),
  credits: Number,
  created_at: Date
}
```

### Collection: `rules`
```javascript
{
  _id: ObjectId,
  id: String (unique),
  pattern: String (regex pattern),
  action: String ("AUTO_ACCEPT" | "AUTO_REJECT"),
  description: String,
  created_at: Date,
  order: Number (for priority)
}
```

### Collection: `command_executions`
```javascript
{
  _id: ObjectId,
  id: String (unique),
  user_id: String,
  command_text: String,
  status: String ("EXECUTED" | "BLOCKED" | "NO_MATCH" | "INSUFFICIENT_CREDITS"),
  matched_rule: String (rule_id or null),
  credits_used: Number,
  timestamp: Date,
  execution_time_ms: Number
}
```

---

## 4. Backend Implementation Plan

### Phase 1: Models & Database Setup
- Define Pydantic models for User, Rule, CommandExecution
- Setup MongoDB collections with indexes
- Seed initial data (admin user, basic rules)

### Phase 2: Authentication Middleware
- API key validation middleware
- Extract user from API key
- Role-based authorization (admin/member)

### Phase 3: Core Endpoints
- User management endpoints
- Rules management endpoints
- Command execution logic with rule matching
- Command history retrieval

### Phase 4: Business Logic
- Rule matching engine (first-match-wins)
- Credit deduction (transactional)
- Audit trail logging
- Regex validation

---

## 5. Frontend Integration Changes

### Files to Update:
1. **Remove mock.js**: Delete `/app/frontend/src/mockData.js`
2. **Create API service**: `/app/frontend/src/services/api.js`
3. **Update components**: Replace `mockAPI` calls with real API calls

### API Service Structure (`/app/frontend/src/services/api.js`):
```javascript
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

export const api = {
  // Auth
  verifyApiKey: (apiKey) => { ... },
  
  // Users
  getAllUsers: (apiKey) => { ... },
  createUser: (apiKey, userData) => { ... },
  updateUserCredits: (apiKey, userId, credits) => { ... },
  
  // Rules
  getRules: (apiKey) => { ... },
  createRule: (apiKey, ruleData) => { ... },
  deleteRule: (apiKey, ruleId) => { ... },
  
  // Commands
  executeCommand: (apiKey, commandText) => { ... },
  getCommandHistory: (apiKey, isAdmin) => { ... }
};
```

### Components to Update:
- `Login.jsx`: Replace `mockAPI.authenticateUser()` with `api.verifyApiKey()`
- `Dashboard.jsx`: Replace `mockAPI.executeCommand()` and `mockAPI.getCommandHistory()`
- `RuleManager.jsx`: Replace `mockAPI.getRules()`, `mockAPI.addRule()`, `mockAPI.deleteRule()`
- `UserManager.jsx`: Replace `mockAPI.getAllUsers()`, `mockAPI.createUser()`, `mockAPI.updateUserCredits()`

---

## 6. Error Handling

### HTTP Status Codes:
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Invalid/missing API key
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Regex validation failed
- `500 Internal Server Error`: Server error

### Error Response Format:
```json
{
  "detail": "Error message"
}
```

---

## 7. Testing Checklist

### Backend Testing:
- [ ] API key authentication works
- [ ] Admin can access admin endpoints
- [ ] Members cannot access admin endpoints
- [ ] Rule matching engine works correctly (first-match-wins)
- [ ] Credits deduct only on EXECUTED commands
- [ ] Credits check before execution
- [ ] Invalid regex patterns are rejected
- [ ] Command history filtering works (user vs admin view)
- [ ] Transactional operations work (credits + audit log)

### Integration Testing:
- [ ] Login with admin key
- [ ] Login with member key
- [ ] Execute safe command (credit deduction)
- [ ] Execute blocked command (no credit deduction)
- [ ] Execute command with no matching rule
- [ ] Execute with 0 credits
- [ ] Admin: Create rule
- [ ] Admin: Delete rule
- [ ] Admin: Create user (receives API key)
- [ ] Admin: Update user credits
- [ ] View command history (member view)
- [ ] View audit log (admin view)

---

## 8. Deployment Notes

### Environment Variables:
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `REACT_APP_BACKEND_URL`: Backend URL for frontend

### CORS Configuration:
- Allow all origins for development
- Restrict in production

### Database Indexes:
- `users.api_key`: Unique index for fast lookup
- `users.user_id`: Unique index
- `rules.id`: Unique index
- `rules.order`: Index for sorting
- `command_executions.user_id`: Index for user history
- `command_executions.timestamp`: Index for sorting

---

## Summary

This document serves as the complete contract between frontend and backend. The backend will implement all these endpoints exactly as specified, and the frontend will be updated to call these real APIs instead of the mock functions.
