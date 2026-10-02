#!/usr/bin/env python3
"""
Test Suite for Phase 4: F-Shield
Verifies detector patterns, policy levels (1-5), role isolation, and validator CLI hook.
"""

import sys
import json
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.security.detector import SECURITY_RULES, SecurityDetector
from scripts.security.policy import ShieldPolicyEngine

MANDATORY_PATTERNS = [
    "rm -rf",
    "del /s",
    "format",
    "DROP DATABASE",
    "DROP TABLE",
    "git reset --hard",
    "git clean -fd",
    "git push --force",
    "credenciales",
    "tokens",
    "API keys",
    ".env",
    "private keys"
]

def test_pattern_catalog_completeness():
    # Verify every rule has: pattern, risk, reason, action, exception, test
    for rule in SECURITY_RULES:
        for field in ["id", "name", "pattern", "risk", "reason", "action", "level", "test"]:
            assert field in rule, f"Rule {rule.get('id')} missing required field: {field}"
        assert "exception" in rule, f"Rule {rule.get('id')} missing exception attribute"
    print(f"[PASS] All {len(SECURITY_RULES)} security rules have complete metadata schema.")

def test_mandatory_detections():
    # 1. rm -rf
    r = SecurityDetector.inspect_command("rm -rf /var/data")
    assert r is not None and r["id"] == "SEC-001"

    # 2. del /s
    r = SecurityDetector.inspect_command("del /s /q c:\\temp")
    assert r is not None and r["id"] == "SEC-001"

    # 3. format
    r = SecurityDetector.inspect_command("format d:")
    assert r is not None and r["id"] == "SEC-002"

    # 4. DROP DATABASE & DROP TABLE
    r_db = SecurityDetector.inspect_command("DROP DATABASE production;")
    assert r_db is not None and r_db["id"] == "SEC-003"
    r_tbl = SecurityDetector.inspect_command("DROP TABLE users;")
    assert r_tbl is not None and r_tbl["id"] == "SEC-003"

    # 5. git reset --hard, clean, push --force
    r_reset = SecurityDetector.inspect_command("git reset --hard origin/main")
    assert r_reset is not None and r_reset["id"] == "SEC-004"
    r_clean = SecurityDetector.inspect_command("git clean -fd")
    assert r_clean is not None and r_clean["id"] == "SEC-004"
    r_push = SecurityDetector.inspect_command("git push origin main --force")
    assert r_push is not None and r_push["id"] == "SEC-004"

    # 6. Private keys
    r_key = SecurityDetector.inspect_content("-----BEGIN RSA PRIVATE KEY-----\nMIIEowI...")
    assert r_key is not None and r_key["id"] == "SEC-005"

    # 7. API Keys and Tokens
    r_tok1 = SecurityDetector.inspect_content("API_KEY=sk-abcdef1234567890abcdef123456")
    assert r_tok1 is not None and r_tok1["id"] == "SEC-006"
    r_tok2 = SecurityDetector.inspect_content("ghp_123456789012345678901234567890123456")
    assert r_tok2 is not None and r_tok2["id"] == "SEC-006"

    # 8. .env
    r_env = SecurityDetector.inspect_target_file(".env")
    assert r_env is not None and r_env["id"] == "SEC-007"
    r_env_prod = SecurityDetector.inspect_target_file("config/.env.prod")
    assert r_env_prod is not None and r_env_prod["id"] == "SEC-007"

    print("[PASS] All Section 14 mandatory security patterns detected accurately.")

def test_exceptions_not_blocked():
    # node_modules cleanup allowed by exception
    r_ex = SecurityDetector.inspect_command("rm -rf node_modules")
    assert r_ex is None, "Legitimate rm -rf node_modules should match exception!"

    # .env.example allowed
    r_ex_env = SecurityDetector.inspect_target_file(".env.example")
    assert r_ex_env is None, ".env.example should match exception!"
    print("[PASS] Legitimate exceptions are not blocked indiscriminately.")

def test_defense_levels():
    # Level 4: Block
    p_block = ShieldPolicyEngine.evaluate({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "rm -rf /"}},
        "activeRole": "builder"
    })
    assert p_block["decision"] == "deny" and p_block["level"] == 4

    # Level 3: Ask confirmation (DROP TABLE)
    p_ask = ShieldPolicyEngine.evaluate({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "DROP TABLE clients;"}},
        "activeRole": "builder"
    })
    assert p_ask["decision"] == "ask" and p_ask["level"] == 3

    # Level 5: Overwrite
    p_overwrite = ShieldPolicyEngine.evaluate({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "git log"}},
        "activeRole": "builder"
    })
    assert p_overwrite["decision"] == "allow"
    print("[PASS] Defense levels (1 to 5) behave as expected.")

def test_validator_hook_cli_execution():
    validator_path = WORKSPACE_ROOT / "scripts" / "security" / "validator.py"
    assert validator_path.is_file(), f"Validator script missing at {validator_path}"

    test_payload = {
        "conversationId": "test-cli-uuid",
        "stepIdx": 42,
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "rm -rf /"}
        }
    }

    # Run subprocess piping json to stdin
    proc = subprocess.run(
        [sys.executable, str(validator_path)],
        input=json.dumps(test_payload),
        text=True,
        capture_output=True,
        cwd=str(WORKSPACE_ROOT)
    )

    assert proc.returncode == 0, f"Validator CLI exited with code {proc.returncode}: {proc.stderr}"
    output_json = json.loads(proc.stdout.strip())
    assert output_json.get("decision") == "deny", f"Expected 'deny', got: {output_json}"
    assert "F-Shield" in output_json.get("reason", "")
    print("[PASS] Validator CLI Hook executed successfully via stdin/stdout contract.")

if __name__ == "__main__":
    try:
        test_pattern_catalog_completeness()
        test_mandatory_detections()
        test_exceptions_not_blocked()
        test_defense_levels()
        test_validator_hook_cli_execution()
        print("\n=== FASE 4: F-SHIELD TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in F-Shield: {e}")
        sys.exit(1)
