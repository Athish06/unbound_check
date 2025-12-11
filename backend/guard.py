import shlex
import logging

logger = logging.getLogger(__name__)

class CommandGuard:
    """
    Layer 2: Heuristic Risk Scoring
    Analyzes command tokens to assign a risk score.
    """
    
    # Risk scores for known binaries
    BINARY_RISK = {
        'rm': 60,
        'dd': 100,
        'mkfs': 100,
        'wget': 40,
        'curl': 40,
        'mv': 30,
        'chmod': 40,
        'chown': 40,
        'sudo': 50,
        'nc': 50,
        'netcat': 50,
        'ssh': 30,
        'scp': 30,
        'ftp': 30,
        'python': 50,
        'python3': 50,
        'perl': 50,
        'ruby': 50,
        'bash': 50,
        'sh': 50,
        'zsh': 50,
        'ls': 0,
        'pwd': 0,
        'echo': 0,
        'cat': 0,
        'grep': 0,
        'find': 10,
        'whoami': 0,
        'id': 0,
    }
    
    DEFAULT_BINARY_RISK = 20
    
    # High risk flags
    RISKY_FLAGS = ['-f', '--force', '-r', '--recursive']
    
    # Critical targets
    CRITICAL_TARGETS = ['/', '/etc', '/var', '/boot', '/bin', '/sbin', '/usr/bin', '/usr/sbin']

    @classmethod
    def analyze(cls, command_text: str):
        """
        Analyze a command and return (decision, score, reason)
        """
        score = 0
        reasons = []
        
        # Check for piping/redirection
        if '|' in command_text or '>' in command_text:
            score += 30
            reasons.append("Piping/Redirection detected (+30)")
            
        try:
            # Split command safely
            tokens = shlex.split(command_text)
        except ValueError:
            # If shlex fails, it's likely a complex or malformed command -> High Risk
            return "BLOCK", 100, "Malformed command syntax"
            
        if not tokens:
            return "ALLOW", 0, "Empty command"
            
        binary = tokens[0]
        
        # 1. Binary Risk
        bin_score = cls.BINARY_RISK.get(binary, cls.DEFAULT_BINARY_RISK)
        score += bin_score
        if bin_score > 0:
            reasons.append(f"Binary '{binary}' risk (+{bin_score})")
            
        # 2. Flag Analysis
        has_force = False
        has_recursive = False
        
        for token in tokens[1:]:
            if token in cls.RISKY_FLAGS:
                score += 20
                reasons.append(f"Risky flag '{token}' (+20)")
                
            if token in ['-f', '--force']:
                has_force = True
            if token in ['-r', '-R', '--recursive']:
                has_recursive = True
                
            # 3. Target Analysis
            # Check if token looks like a critical path
            # Simple check: exact match or starts with critical path
            for critical in cls.CRITICAL_TARGETS:
                if token == critical or (token.startswith(critical + '/') and len(token) > len(critical)):
                    score += 100
                    reasons.append(f"Critical target '{token}' (+100)")
                    break
        
        # Bonus Risk: rm -rf
        if binary == 'rm' and has_force and has_recursive:
            score += 50
            reasons.append("Destructive combination 'rm -rf' (+50)")
            
        # Determine Decision
        if score >= 100:
            decision = "BLOCK"
        elif score == 0:
            decision = "ALLOW"
        else:
            decision = "ESCALATE"
            
        reason_str = "; ".join(reasons) if reasons else "Safe command"
        
        return decision, score, reason_str
