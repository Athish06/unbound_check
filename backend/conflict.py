from greenery import parse
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ConflictDetector:
    @staticmethod
    def check_overlap(new_pattern_str: str, existing_patterns: List[dict]) -> Tuple[bool, Optional[str]]:
        """
        Brutally verifies if 'new_pattern' overlaps with ANY existing pattern.
        Returns: (has_conflict, reason)
        """
        try:
            # 1. Parse the new regex into a Finite Automate (LEGO)
            # Note: Greenery is strict. We might need to sanitize input (e.g., ensure anchors)
            # We'll try to parse as is.
            new_regex = parse(new_pattern_str)
        except Exception as e:
            # If the regex is invalid/unsupported, we can't mathematically prove overlap.
            # Fail safe or let the user know their regex is too complex for verification.
            return True, f"Invalid or too complex regex structure for verification: {str(e)}"

        for rule in existing_patterns:
            existing_str = rule['pattern']
            rule_id = rule['id']
            
            try:
                existing_regex = parse(existing_str)
                
                # 2. Calculate Intersection (A & B)
                # This creates a new FSM accepting ONLY strings that match BOTH patterns
                intersection = new_regex & existing_regex
                
                # 3. If Intersection is NOT empty, there is an overlap
                if not intersection.empty():
                    # We found a conflict!
                    # Get an example string that triggers both to show the user
                    example_collision = intersection.strings()
                    try:
                        example = next(example_collision)
                    except StopIteration:
                        example = "[Infinite possibilities]"
                    
                    return True, (
                        f"Conflict detected with Rule {rule_id} ('{existing_str}'). "
                        f"Both rules would match the command: '{example}'"
                    )
            
            except Exception as e:
                # If an existing rule is broken, skip it (or flag it)
                logger.warning(f"Skipping conflict check for malformed existing rule {rule_id}: {e}")
                continue

        # No overlaps found
        return False, None
