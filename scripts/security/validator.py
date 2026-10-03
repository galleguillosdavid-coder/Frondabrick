#!/usr/bin/env python3
"""
F-Shield Validator CLI Hook
Conforms to Antigravity PreToolUse hook contract:
- Reads JSON payload from stdin
- Evaluates against ShieldPolicyEngine
- Emits JSON response to stdout
"""

import sys
import os
import json
from pathlib import Path

# Ensure workspace root is in python path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.security.policy import ShieldPolicyEngine

def main():
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            # If called without stdin, return safe allow
            result = {
                "decision": "allow",
                "reason": "F-Shield: Sin payload de herramienta recibido."
            }
        else:
            payload = json.loads(raw_input)
            result = ShieldPolicyEngine.evaluate(payload)

            # Record audit trace to evidence/security if directory exists
            evidence_dir = WORKSPACE_ROOT / "evidence" / "security"
            if evidence_dir.exists():
                trace_file = evidence_dir / "audit.jsonl"
                
                # Correlate session_id if active
                session_id = payload.get("sessionId") or os.environ.get("FRONDABRICK_SESSION_ID")
                if not session_id:
                    active_session_file = WORKSPACE_ROOT / "evidence" / "session" / ".active_session"
                    if active_session_file.is_file():
                        try:
                            session_id = active_session_file.read_text(encoding="utf-8").strip()
                        except Exception:
                            session_id = None

                record = {
                    "session_id": session_id,
                    "stepIdx": payload.get("stepIdx"),
                    "tool": payload.get("toolCall", {}).get("name"),
                    "decision": result.get("decision"),
                    "level": result.get("level"),
                    "reason": result.get("reason")
                }
                with open(trace_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")

    except Exception as e:
        # Fail-safe posture: if an unexpected exception occurs, ask user or deny
        result = {
            "decision": "ask",
            "reason": f"F-Shield Error interno de evaluación: {str(e)}"
        }

    # Emit standard json output on stdout
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())
