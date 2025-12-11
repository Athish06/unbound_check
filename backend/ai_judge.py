import os
import logging
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not found. AI Judge will default to BLOCK.")

async def judge_command(command_text: str) -> dict:
    """
    Layer 3: AI Contextual Analysis
    Uses Gemini to decide if a command is safe.
    Returns: {'status': 'EXECUTED'|'BLOCKED', 'reason': '...'}
    """
    if not GEMINI_API_KEY:
        return {
            "status": "BLOCKED", 
            "reason": "AI Judge unavailable (Missing API Key)"
        }
        
    try:
        # Use gemini-2.5-flash (current stable model)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a Linux Security Officer. Analyze this command: '{command_text}'. 
        Is it safe to execute on a production server? 
        
        Rules:
        1. harmless commands (ls, pwd, echo, cat) -> SAFE
        2. destructive commands (rm -rf /, mkfs, dd) -> DANGEROUS
        3. system modification (chmod, chown, useradd) -> DANGEROUS unless clearly benign
        4. data exfiltration (curl, wget, nc) -> DANGEROUS if suspicious URL/IP
        
        Reply with valid JSON only: {{"status": "EXECUTED"|"BLOCKED", "reason": "short explanation"}}
        """
        
        # Use sync API in async wrapper
        import asyncio
        response = await asyncio.to_thread(model.generate_content, prompt)
        response_text = response.text
        
        # Clean up code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        result = json.loads(response_text.strip())
        
        # Validate structure
        if "status" not in result or result["status"] not in ["EXECUTED", "BLOCKED"]:
            logger.error(f"Invalid AI response format: {result}")
            return {"status": "BLOCKED", "reason": "AI returned invalid format"}
            
        return result
        
    except Exception as e:
        logger.error(f"AI Judge error: {str(e)}")
        return {
            "status": "BLOCKED",
            "reason": f"AI Judge failed: {str(e)}"
        }
