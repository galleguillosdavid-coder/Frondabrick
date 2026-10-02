#!/usr/bin/env python3
"""
Harness Validator for EXP-001
Tests Antigravity Customization Specifications:
- Plugin manifest validation
- Skill YAML frontmatter validation
- Hook PreToolUse contract and F-Shield policy logic
- Role-based write prevention (Reviewer / Planner isolation)
- Hook parameter overwrite simulation
"""

import os
import sys
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
EVIDENCE_DIR = BASE_DIR / "evidence"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

class AntigravitySpecValidator:
    DANGEROUS_COMMAND_PATTERNS = [
        (r"\brm\s+-[rRfF]{1,3}\b", "Recursive forced deletion detected"),
        (r"\bdel\s+/[sS]\b", "Recursive deletion command detected"),
        (r"\bformat\s+[a-zA-Z]:", "Disk format attempt detected"),
        (r"\bDROP\s+(DATABASE|SCHEMA|TABLE)\b", "Destructive SQL DROP detected"),
        (r"\bgit\s+reset\s+--hard\b", "Destructive git hard reset detected"),
        (r"\bgit\s+clean\s+-[fF]{1,2}[dD]?\b", "Destructive git clean detected"),
        (r"\bgit\s+push\s+.*--force\b", "Destructive git push force detected"),
    ]

    RESTRICTED_WRITE_TOOLS = {
        "write_to_file",
        "replace_file_content",
        "multi_replace_file_content",
    }

    READ_ONLY_ROLES = {"reviewer", "planner"}

    @staticmethod
    def validate_plugin_manifest(manifest_path: Path) -> dict:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "name" in data, "Plugin manifest must have a 'name' field"
        assert isinstance(data["name"], str) and data["name"].strip() != "", "Plugin name must be non-empty string"
        return {"valid": True, "name": data["name"]}

    @staticmethod
    def validate_skill_file(skill_path: Path) -> dict:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
        assert match is not None, "Skill file must contain valid YAML frontmatter delimiters (---)"
        frontmatter_text = match.group(1)
        name_match = re.search(r"^name:\s*([a-zA-Z0-9_-]+)", frontmatter_text, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(.+)", frontmatter_text, re.MULTILINE)
        assert name_match is not None, "Skill frontmatter must declare 'name'"
        assert desc_match is not None, "Skill frontmatter must declare 'description'"
        return {
            "valid": True,
            "name": name_match.group(1),
            "description": desc_match.group(1).strip()
        }

    @classmethod
    def evaluate_pretooluse_hook(cls, payload: dict) -> dict:
        """
        Simulates the PreToolUse hook engine conforming to Antigravity's contract:
        Input: JSON with toolCall, activeRole, etc.
        Output: JSON with decision, reason, optional permissionOverrides or overwrite.
        """
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        active_role = payload.get("activeRole", "default").lower()

        # Rule 1: Role permission isolation
        if active_role in cls.READ_ONLY_ROLES and tool_name in cls.RESTRICTED_WRITE_TOOLS:
            return {
                "decision": "deny",
                "reason": f"Role '{active_role}' is strictly read-only and prohibited from executing write tool '{tool_name}'."
            }

        # Rule 2: Dangerous command blocking
        if tool_name == "run_command":
            cmd = tool_args.get("CommandLine", "")
            for pattern, reason in cls.DANGEROUS_COMMAND_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    return {
                        "decision": "deny",
                        "reason": f"Security policy triggered: {reason} (pattern: {pattern})"
                    }

        # Rule 3: Parameter overwrite verification (if requested in payload)
        if payload.get("testOverwrite", False):
            return {
                "decision": "allow",
                "reason": "Parameter overwrite policy applied",
                "overwrite": {"CommandLine": "git status --short"}
            }

        return {
            "decision": "allow",
            "reason": "Tool call verified against security policies."
        }


def main():
    print("[EXP-001] Iniciando validación experimental...")
    results = {}
    evidence = []

    # 1. Validar Manifiesto de Plugin
    manifest_file = INPUT_DIR / "mock_plugin_manifest.json"
    plugin_res = AntigravitySpecValidator.validate_plugin_manifest(manifest_file)
    results["plugin_manifest"] = plugin_res
    evidence.append(f"Plugin manifest validado correctamente: {plugin_res['name']}")

    # 2. Validar Skill YAML Frontmatter
    skill_file = INPUT_DIR / "mock_skill.md"
    skill_res = AntigravitySpecValidator.validate_skill_file(skill_file)
    results["skill_frontmatter"] = skill_res
    evidence.append(f"Skill validado: {skill_res['name']} con descripción '{skill_res['description']}'")

    # 3. Hook PreToolUse - Comando destructivo (rm -rf /)
    with open(INPUT_DIR / "mock_pretooluse_dangerous.json", "r", encoding="utf-8") as f:
        dangerous_input = json.load(f)
    dangerous_out = AntigravitySpecValidator.evaluate_pretooluse_hook(dangerous_input)
    results["pretooluse_dangerous"] = dangerous_out
    assert dangerous_out["decision"] == "deny", "Dangerous command must be DENIED!"
    evidence.append(f"Comando destructivo denegado exitosamente: {dangerous_out['reason']}")

    # 4. Hook PreToolUse - Rol Reviewer intentando escribir
    with open(INPUT_DIR / "mock_pretooluse_reviewer_write.json", "r", encoding="utf-8") as f:
        reviewer_input = json.load(f)
    reviewer_out = AntigravitySpecValidator.evaluate_pretooluse_hook(reviewer_input)
    results["pretooluse_reviewer_write"] = reviewer_out
    assert reviewer_out["decision"] == "deny", "Reviewer write must be DENIED!"
    evidence.append(f"Escritura en rol reviewer bloqueada exitosamente: {reviewer_out['reason']}")

    # 5. Hook PreToolUse - Comando seguro (git status)
    with open(INPUT_DIR / "mock_pretooluse_safe.json", "r", encoding="utf-8") as f:
        safe_input = json.load(f)
    safe_out = AntigravitySpecValidator.evaluate_pretooluse_hook(safe_input)
    results["pretooluse_safe"] = safe_out
    assert safe_out["decision"] == "allow", "Safe command must be ALLOWED!"
    evidence.append(f"Comando seguro permitido correctamente: {safe_out['reason']}")

    # 6. Hook PreToolUse - Prueba de Overwrite
    overwrite_input = {
        "toolCall": {"name": "run_command", "args": {"CommandLine": "git status"}},
        "testOverwrite": True
    }
    overwrite_out = AntigravitySpecValidator.evaluate_pretooluse_hook(overwrite_input)
    results["pretooluse_overwrite"] = overwrite_out
    assert "overwrite" in overwrite_out and overwrite_out["overwrite"]["CommandLine"] == "git status --short"
    evidence.append("Mecanismo de overwrite verificado en contrato de salida")

    # Guardar resultados y evidencia
    with open(OUTPUT_DIR / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(EVIDENCE_DIR / "trace.log", "w", encoding="utf-8") as f:
        f.write("\n".join(evidence) + "\n")

    print("[EXP-001] Todas las aserciones pasaron satisfactoriamente (PASS).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
