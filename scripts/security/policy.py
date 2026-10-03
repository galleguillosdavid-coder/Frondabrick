#!/usr/bin/env python3
"""
F-Shield Policy Engine
Implements the 5 Defense Levels:
1. Detect
2. Warn
3. Ask Confirmation
4. Block (Hard Deny - Policy rejection & audit verdict)
5. Overwrite (Parameter Rewrite)
And role isolation policies.

NOTE: F-Shield operates as a normative policy validator and audit barrier.
The 'deny' verdict flags violations in hooks and audit logs. It is not an
OS-level kernel sandbox.
"""

from typing import Dict, Any, Tuple, Optional
from scripts.security.detector import SecurityDetector

WRITE_TOOLS = {
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
}

READ_ONLY_ROLES = {"reviewer", "planner"}

class ShieldPolicyEngine:
    @classmethod
    def evaluate(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        active_role = payload.get("activeRole", "builder").lower()

        # 1. Role-based isolation policy
        if active_role in READ_ONLY_ROLES and tool_name in WRITE_TOOLS:
            return {
                "decision": "deny",
                "reason": f"F-Shield Aislamiento de Rol: El rol '{active_role}' es estrictamente de lectura y no puede ejecutar '{tool_name}'.",
                "level": 4
            }

        # 2. Command inspections
        if tool_name == "run_command":
            cmd = args.get("CommandLine", "")
            rule = SecurityDetector.inspect_command(cmd)
            if rule:
                return cls._apply_rule(rule, payload, tool_call)

        # 3. File write and content inspections
        if tool_name in WRITE_TOOLS:
            target_file = args.get("TargetFile", "")
            code_content = args.get("CodeContent", "") or args.get("ReplacementContent", "")

            # Check target file (.env)
            file_rule = SecurityDetector.inspect_target_file(target_file)
            if file_rule:
                return cls._apply_rule(file_rule, payload, tool_call)

            # Check leaked secrets
            content_rule = SecurityDetector.inspect_content(code_content)
            if content_rule:
                return cls._apply_rule(content_rule, payload, tool_call)

        # Default safe
        return {
            "decision": "allow",
            "reason": "Operación verificada por F-Shield.",
            "level": 1
        }

    @classmethod
    def _apply_rule(cls, rule: Dict[str, Any], payload: Dict[str, Any], tool_call: Dict[str, Any]) -> Dict[str, Any]:
        level = rule.get("level", 4)
        action = rule.get("action", "BLOCK")
        reason = f"[F-Shield {rule['risk']}] {rule['name']}: {rule['reason']}"

        # Level 5: Overwrite parameter (if enabled / specified)
        if level == 5 or rule.get("overwrite_spec"):
            new_args = dict(tool_call.get("args", {}))
            new_args.update(rule.get("overwrite_spec", {}))
            return {
                "decision": "allow",
                "reason": f"{reason} - Parámetro reescrito de forma segura (Nivel 5).",
                "level": 5,
                "overwrite": new_args
            }

        # Level 4: Block
        if level == 4 or action == "BLOCK":
            return {
                "decision": "deny",
                "reason": f"{reason} (Operación bloqueada por Nivel 4).",
                "level": 4
            }

        # Level 3: Ask confirmation
        if level == 3 or action == "ASK":
            return {
                "decision": "ask",
                "reason": f"{reason} (Requiere confirmación explícita del usuario - Nivel 3).",
                "level": 3
            }

        # Level 2: Warn
        if level == 2 or action == "WARN":
            return {
                "decision": "allow",
                "reason": f"[ADVERTENCIA] {reason}",
                "level": 2
            }

        # Level 1: Detect
        return {
            "decision": "allow",
            "reason": f"[DETECTADO] {reason}",
            "level": 1
        }
