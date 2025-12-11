import logging
import re
from typing import Dict, Any

from database import supabase
from guard import CommandGuard
from ai_judge import judge_command

logger = logging.getLogger(__name__)

class CommandOrchestrator:
    """
    The Controller that coordinates the 3-layer defense system.
    """
    
    @staticmethod
    async def process_command(command_text: str) -> Dict[str, Any]:
        """
        Process a command through the 3 layers.
        Returns:
        {
            "status": "EXECUTED" | "BLOCKED",
            "layer": "1_RULES" | "2_GUARD" | "3_AI",
            "score": int,
            "reason": str,
            "matched_rule": str (optional)
        }
        """
        logger.info(f"Orchestrating command: {command_text}")
        
        # =================================================
        # LAYER 1: The Constitution (Admin Rules)
        # =================================================
        try:
            # Fetch ALL ACTIVE rules from Supabase, sorted by created_at (FIFO)
            # Note: In a real high-perf app, we'd cache this.
            response = supabase.table("rules").select("*").eq("is_active", True).order("created_at").execute()
            rules = response.data
            
            logger.info(f"Layer 1: Checking command '{command_text}' against {len(rules)} active rules")
            
            l1_decision = "NO_MATCH"
            matched_rule_id = None
            
            # Check EVERY rule for a match
            for rule in rules:
                logger.debug(f"Layer 1: Testing pattern '{rule['pattern']}' against '{command_text}'")
                try:
                    # Use re.search to check if pattern matches the command
                    if re.search(rule['pattern'], command_text):
                        matched_rule_id = rule['id']
                        logger.info(f"Layer 1 MATCH FOUND: Pattern '{rule['pattern']}' matched command '{command_text}' - Action: {rule['action']}")
                        
                        if rule['action'] == "AUTO_REJECT":
                            # 🛑 FINAL BLOCK - Admin explicitly forbidden
                            logger.info(f"Layer 1 BLOCK: Rule {matched_rule_id} ('{rule['pattern']}') - AUTO_REJECT")
                            return {
                                "status": "BLOCKED",
                                "layer": "1_RULES",
                                "score": 0,
                                "reason": f"Admin Explicitly Forbidden: {rule.get('description', 'No description')}",
                                "matched_rule": matched_rule_id
                            }
                        elif rule['action'] == "AUTO_ACCEPT":
                            # Proceed to Layer 2 for verification (Do not trust blindly)
                            l1_decision = "AUTO_ACCEPT"
                            logger.info(f"Layer 1 AUTO_ACCEPT: Rule {matched_rule_id} ('{rule['pattern']}') matched - proceeding to Layer 2 verification")
                            break # First matching AUTO_ACCEPT rule wins
                            
                except re.error as regex_err:
                    logger.error(f"Invalid regex in rule {rule['id']}: {regex_err}")
                    continue
                    
        except Exception as e:
            logger.error(f"Layer 1 Error: {e}")
            # Fail safe: If DB fails, proceed to Layer 2 but log error
            l1_decision = "NO_MATCH"
        
        if l1_decision == "NO_MATCH":
            logger.info(f"Layer 1: NO rules matched command '{command_text}' - proceeding to Layer 2")

        # =================================================
        # LAYER 2: The Watchdog (Risk Scoring)
        # =================================================
        l2_decision, score, l2_reason = CommandGuard.analyze(command_text)
        
        logger.info(f"Layer 2 Analysis: {l2_decision} (Score: {score}) - {l2_reason}")

        # =================================================
        # CONFLICT RESOLUTION LOGIC (The Decision Tree)
        # =================================================
        # Safe: 0 (verified safe)
        # Ambiguous Range: 1-99 (needs AI context)
        # Critical: 100+ (high risk)
        
        # Case 1: Score >= 100 (High Risk - Critical)
        if score >= 100:
            if l1_decision == "AUTO_ACCEPT":
                # 🚨 CONFLICT! Admin said OK, but Guard says CRITICAL DANGER
                # Escalate to Layer 3 (AI) to break the tie
                logger.warning(f"🚨 CONFLICT DETECTED: L1 AUTO_ACCEPT vs L2 High Risk ({score}). Escalating to AI Judge.")
                pass # Fall through to Layer 3
            else:
                # L1 was NO_MATCH, Guard says HIGH RISK -> FINAL BLOCK
                logger.info(f"Layer 2 BLOCK: High Risk Score ({score})")
                return {
                    "status": "BLOCKED",
                    "layer": "2_GUARD",
                    "score": score,
                    "reason": f"Heuristic Risk too high ({score}): {l2_reason}",
                    "matched_rule": matched_rule_id
                }
                
        # Case 2: Score == 0 (Safe)
        elif score == 0:
            # ✅ FINAL EXECUTE - Verified Safe
            logger.info("Layer 2 SAFE: Verified Safe")
            return {
                "status": "EXECUTED",
                "layer": "2_GUARD",
                "score": score,
                "reason": "Verified Safe",
                "matched_rule": matched_rule_id
            }
            
        # Case 3: Score 1-99 (Ambiguous)
        else:
            # 🟡 ESCALATE to Layer 3 - Needs AI Context
            logger.info(f"Layer 2 AMBIGUOUS: Score {score} (1-99 range) - Escalating to AI")
            pass # Fall through to Layer 3
            
        # =================================================
        # LAYER 3: "The Judge" (AI)
        # =================================================
        logger.info("Escalating to Layer 3 (AI Judge)...")
        
        ai_result = await judge_command(command_text)
        
        logger.info(f"Layer 3 AI Response: {ai_result}")
        logger.info(f"Layer 3 Decision: {ai_result['status']} - Reason: {ai_result['reason']}")
        
        return {
            "status": ai_result["status"],
            "layer": "3_AI",
            "score": score,
            "reason": f"AI Verdict: {ai_result['reason']} (Risk Score: {score})",
            "matched_rule": matched_rule_id
        }
