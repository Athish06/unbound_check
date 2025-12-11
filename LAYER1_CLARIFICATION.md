# Layer 1 Clarification - Pattern Matching (NOT Conflict Detection)

## ❌ WRONG Understanding (My Initial Mistake)
Layer 1 = Conflict detection between rules

## ✅ CORRECT Understanding
**Layer 1 = Admin Pattern Matching**
- Admin creates rules with regex patterns
- When a command arrives, check ALL active rules
- If ANY pattern matches:
  - AUTO_REJECT → Block immediately (don't go to Layer 2)
  - AUTO_ACCEPT → Continue to Layer 2 for verification
- If NO pattern matches → Continue to Layer 2

**Conflict Detection = Separate process**
- Happens when CREATING or EDITING rules
- Uses Finite Automata Theory (greenery library)
- Prevents overlapping patterns in the rules database
- NOT part of command execution flow

## The Corrected Flow

```
Command arrives
    ↓
Layer 1: Pattern Matching
    ├─ Fetch all ACTIVE rules from DB
    ├─ For each rule: re.search(pattern, command)
    ├─ If match found:
    │   ├─ AUTO_REJECT → 🛑 BLOCK (Final, don't continue)
    │   └─ AUTO_ACCEPT → Continue to Layer 2
    └─ No match → Continue to Layer 2
    ↓
Layer 2: Risk Scoring
    ├─ Parse command tokens
    ├─ Calculate risk score (0-200+)
    ├─ Score >= 100 (High Risk):
    │   ├─ L1 was AUTO_ACCEPT → 🚨 CONFLICT → Layer 3
    │   └─ L1 was NO_MATCH → 🛑 BLOCK
    ├─ Score == 0 (Safe) → ✅ EXECUTE
    └─ Score 1-99 (Ambiguous) → Layer 3
    ↓
Layer 3: AI Judge
    └─ Contextual analysis → ✅ EXECUTE or 🛑 BLOCK
```

## Examples

### Example 1: AUTO_REJECT (Immediate Block)
```
Rule in DB: ^rm -rf /  → AUTO_REJECT
Command: rm -rf /
Layer 1: Pattern matches → 🛑 BLOCKED (Never reaches Layer 2)
```

### Example 2: AUTO_ACCEPT (Verify in Layer 2)
```
Rule in DB: ^git .*  → AUTO_ACCEPT
Command: git push
Layer 1: Pattern matches → AUTO_ACCEPT → Continue to Layer 2
Layer 2: Score 0 (Safe) → ✅ EXECUTED
```

### Example 3: AUTO_ACCEPT with Conflict
```
Rule in DB: ^dd .*  → AUTO_ACCEPT
Command: dd if=/dev/zero of=/dev/sda
Layer 1: Pattern matches → AUTO_ACCEPT → Continue to Layer 2
Layer 2: Score 200 (Critical) → 🚨 CONFLICT detected
Layer 3: AI analyzes → 🛑 BLOCKED
```

### Example 4: No Match (Layer 2 decides)
```
No matching rules
Command: python script.py
Layer 1: No match → Continue to Layer 2
Layer 2: Score 50 (Ambiguous) → Escalate to Layer 3
Layer 3: AI analyzes → Decision
```

## Pattern Matching Tips

### Good Patterns
- `^git .*` - Matches "git " followed by anything (git push, git commit, etc.)
- `^git($| .*)` - Better: Matches "git" alone OR "git " + arguments
- `^rm -rf /.*` - Matches rm -rf with root path
- `^sudo .*` - Matches all sudo commands

### Bad Patterns (Will Fail)
- `git` - Will match "legit" or "digit" (no anchor)
- `^git.*` - Will match "gitalive" (no space)
- `^git .*` - Will NOT match "git" alone (requires space + args)

### Testing Your Pattern
```python
import re
pattern = r"^git .*"
re.search(pattern, "git push")  # ✅ Match
re.search(pattern, "git")        # ❌ No match (no space + args)
re.search(pattern, "legit push") # ❌ No match (doesn't start with git)
```

## Fixed Implementation

The orchestrator.py now correctly:
1. ✅ Fetches ALL active rules from database
2. ✅ Uses re.search() for pattern matching
3. ✅ AUTO_REJECT → Immediate block (never reaches Layer 2)
4. ✅ AUTO_ACCEPT → Proceeds to Layer 2 for verification
5. ✅ NO_MATCH → Proceeds to Layer 2 for heuristic analysis

Conflict detection happens separately in:
- `POST /api/rules` - Before creating a new rule
- `PUT /api/rules/{id}` - Before updating an existing rule
