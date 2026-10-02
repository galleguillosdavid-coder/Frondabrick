#!/usr/bin/env python3
"""
Test Suite for Phase 1: F-Core
Validates plugin manifest, rule presence, and required normative clauses.
"""

import sys
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGIN_DIR = WORKSPACE_ROOT / ".agents" / "plugins" / "frondabrick-core"
RULES_DIR = PLUGIN_DIR / "rules"
WORKSPACE_RULES_DIR = WORKSPACE_ROOT / ".agents" / "rules"

REQUIRED_RULES = [
    "00-core.md",
    "01-safety.md",
    "02-workflow.md",
    "03-testing.md",
]

def test_plugin_manifest():
    manifest_path = PLUGIN_DIR / "plugin.json"
    assert manifest_path.is_file(), f"plugin.json missing at {manifest_path}"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("name") == "frondabrick-core", "Plugin name must be 'frondabrick-core'"
    assert "version" in data, "Plugin must have a version field"
    print("[PASS] Plugin manifest valid.")

def test_rules_presence():
    for rule in REQUIRED_RULES:
        plugin_rule = RULES_DIR / rule
        ws_rule = WORKSPACE_RULES_DIR / rule
        assert plugin_rule.is_file(), f"Rule missing in plugin: {plugin_rule}"
        assert ws_rule.is_file(), f"Rule missing in workspace: {ws_rule}"
    print(f"[PASS] All {len(REQUIRED_RULES)} core rules are present in plugin and workspace directories.")

def test_rules_content():
    # 00-core
    core_text = (RULES_DIR / "00-core.md").read_text(encoding="utf-8")
    assert "Realidad > Diseño" in core_text, "00-core.md missing 'Realidad > Diseño'"
    assert "Anti-Alucinación" in core_text or "anti-alucinación" in core_text.lower(), "00-core.md missing anti-hallucination clause"
    assert "Mínimo Privilegio" in core_text, "00-core.md missing 'Mínimo Privilegio'"
    assert "Evidencia Obligatoria" in core_text, "00-core.md missing 'Evidencia Obligatoria'"

    # 01-safety
    safety_text = (RULES_DIR / "01-safety.md").read_text(encoding="utf-8")
    assert "rm -rf" in safety_text, "01-safety.md missing 'rm -rf'"
    assert "DROP DATABASE" in safety_text, "01-safety.md missing 'DROP DATABASE'"
    assert "BEGIN RSA PRIVATE KEY" in safety_text or "credenciales" in safety_text.lower(), "01-safety.md missing secrets protection"
    assert "Rollback" in safety_text or "rollback" in safety_text.lower(), "01-safety.md missing rollback strategy"

    # 02-workflow
    wf_text = (RULES_DIR / "02-workflow.md").read_text(encoding="utf-8")
    assert "INSPECCIONAR" in wf_text, "02-workflow.md missing INSPECCIONAR"
    assert "PLANIFICAR" in wf_text, "02-workflow.md missing PLANIFICAR"
    assert "IMPLEMENTAR" in wf_text, "02-workflow.md missing IMPLEMENTAR"
    assert "TESTEAR" in wf_text, "02-workflow.md missing TESTEAR"
    assert "AUDITAR" in wf_text, "02-workflow.md missing AUDITAR"
    assert "DOCUMENTAR" in wf_text, "02-workflow.md missing DOCUMENTAR"

    # 03-testing
    test_rule_text = (RULES_DIR / "03-testing.md").read_text(encoding="utf-8")
    assert "No Test = No Finalizado" in test_rule_text, "03-testing.md missing 'No Test = No Finalizado'"
    for status in ["PASS", "FAIL", "INCONCLUSIVE", "NOT_SUPPORTED"]:
        assert status in test_rule_text, f"03-testing.md missing status '{status}'"

    print("[PASS] Core rules content semantics fully verified.")

if __name__ == "__main__":
    try:
        test_plugin_manifest()
        test_rules_presence()
        test_rules_content()
        print("\n=== FASE 1: F-CORE TESTS PASSED (100%) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Test failure in F-Core: {e}")
        sys.exit(1)
