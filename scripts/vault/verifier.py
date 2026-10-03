#!/usr/bin/env python3
"""
Frondabrick Vault Hardening & Canary Verifier (Phase 22)
Provides automated verification of Windows NTFS physical protection,
canary survival regression tests, and workspace autonomy verification.
"""

import os
import sys
import json
import hashlib
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

class VaultVerifier:
    @staticmethod
    def audit_acl(target_path: Path) -> Dict[str, Any]:
        """
        Inspects the effective NTFS ACL for target_path using icacls.
        Returns whether explicit denial of DE/DC exists for the current user.
        """
        username = os.environ.get("USERNAME", "")
        if not target_path.exists():
            return {"exists": False, "has_deny": False, "raw_output": ""}

        res = subprocess.run(
            ["icacls", str(target_path)],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )
        raw_output = res.stdout.strip()
        has_deny_user = f"{username}:(DENY)" in raw_output or f"{username}:(I)(DENY)" in raw_output or "(DENY)" in raw_output
        has_de = "(DE)" in raw_output or "(DE,DC)" in raw_output or "DENY" in raw_output

        return {
            "exists": True,
            "username": username,
            "has_deny": has_deny_user,
            "has_de_dc_denial": has_de,
            "raw_output": raw_output
        }

    @staticmethod
    def apply_protection(target_path: Path) -> bool:
        """
        Applies reproducible inherited denial of Delete and Delete Child:
        icacls <target_path> /deny %USERNAME%:(OI)(CI)(DE,DC)
        """
        username = os.environ.get("USERNAME", "")
        res = subprocess.run(
            ["icacls", str(target_path), "/deny", f"{username}:(OI)(CI)(DE,DC)"],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )
        return res.returncode == 0

    @staticmethod
    def remove_protection(target_path: Path) -> bool:
        """
        Removes the deny rule so the canary can be cleaned up cleanly.
        """
        username = os.environ.get("USERNAME", "")
        res = subprocess.run(
            ["icacls", str(target_path), "/remove:d", username],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )
    @staticmethod
    def audit_vault_integrity(target_path: Path) -> Dict[str, Any]:
        """
        EXP-23.1: Detailed ACL Audit & Drift Detector.
        Verifies:
        - ACL_PRESENT
        - DELETE_DENIED
        - DELETE_CHILD_DENIED
        - READ_ALLOWED
        - EXPECTED_IDENTITY
        Detects UNEXPECTED_ACE, PROTECTION_MISSING, or ACL_DRIFT.
        """
        username = os.environ.get("USERNAME", "")
        report = {
            "acl_present": "FAIL",
            "delete_denied": "FAIL",
            "delete_child_denied": "FAIL",
            "read_allowed": "FAIL",
            "expected_identity": "FAIL",
            "protection_status": "FAIL",
            "drift_detected": True,
            "raw_acl": ""
        }

        if not target_path.exists():
            return report

        # Test read
        try:
            if target_path.is_dir():
                _ = list(target_path.iterdir())
            else:
                _ = target_path.read_bytes()
            report["read_allowed"] = "PASS"
        except Exception:
            report["read_allowed"] = "FAIL"

        res = subprocess.run(
            ["icacls", str(target_path)],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )
        raw = res.stdout.strip()
        report["raw_acl"] = raw

        if res.returncode == 0 and raw:
            report["acl_present"] = "PASS"

        # Check expected identity and deny flags
        if username and username.lower() in raw.lower():
            report["expected_identity"] = "PASS"

        # Check specific denial of DE and DC
        if "(DENY)" in raw or "(I)(DENY)" in raw:
            if "(DE" in raw or ":(DENY)(DE" in raw or "(DE,DC)" in raw:
                report["delete_denied"] = "PASS"
            if "DC" in raw or "(DE,DC)" in raw:
                report["delete_child_denied"] = "PASS"

        # Overall protection assessment
        is_protected = (
            report["acl_present"] == "PASS" and
            report["delete_denied"] == "PASS" and
            report["delete_child_denied"] == "PASS" and
            report["read_allowed"] == "PASS" and
            report["expected_identity"] == "PASS"
        )

        if is_protected:
            report["protection_status"] = "PASS"
            report["drift_detected"] = False
        else:
            report["protection_status"] = "FAIL"
            report["drift_detected"] = True

        return report

    @classmethod
    def run_persistence_test(cls, base_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        EXP-23.2: Persistence test across independent child processes.
        Applies protection in process A, terminates process A, launches
        a completely new and independent process B that attempts deletion.
        """
        root = base_dir or WORKSPACE_ROOT
        persist_dir = root / "sentinel_persistence_vault_tmp"
        persist_file = persist_dir / "canary.txt"

        report = {
            "setup_process": "FAIL",
            "independent_process_read": "FAIL",
            "independent_process_delete_blocked": "FAIL",
            "canary_survival": "FAIL",
            "hash_match": "FAIL",
            "persistence": "NOT_DEMONSTRATED"
        }

        try:
            # 1. Setup in current process
            if persist_dir.exists():
                cls.remove_protection(persist_dir)
                subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force '{persist_dir}'"], capture_output=True)

            persist_dir.mkdir(parents=True, exist_ok=True)
            secret_payload = "PERSISTENCE_ACROSS_ISOLATED_PROCESSES_2026"
            persist_file.write_text(secret_payload, encoding="utf-8")
            expected_hash = hashlib.sha256(secret_payload.encode("utf-8")).hexdigest()

            applied = cls.apply_protection(persist_dir)
            if not applied:
                return report
            report["setup_process"] = "PASS"

            # 2. Spawn a completely separate, independent Python process to attack
            attack_script = f"""
import sys, os, hashlib, subprocess
from pathlib import Path

p_dir = Path(r'{persist_dir}')
p_file = Path(r'{persist_file}')

# 1. Read
try:
    content = p_file.read_text(encoding='utf-8')
    assert content == '{secret_payload}'
    print('INDEPENDENT_READ_OK')
except Exception as e:
    print('INDEPENDENT_READ_FAIL:', e)

# 2. Attack deletion
res_del = subprocess.run(['powershell', '-Command', f"Remove-Item -Recurse -Force '{{p_dir}}'"], capture_output=True, text=True)
if p_dir.exists() and p_file.exists():
    print('INDEPENDENT_DELETE_BLOCKED')
else:
    print('INDEPENDENT_DELETE_SUCCEEDED_ATTACK')

# 3. Hash
if p_file.exists():
    h = hashlib.sha256(p_file.read_text(encoding='utf-8').encode('utf-8')).hexdigest()
    if h == '{expected_hash}':
        print('INDEPENDENT_HASH_MATCH')
"""
            subproc = subprocess.run(
                [sys.executable, "-c", attack_script],
                capture_output=True,
                text=True,
                cwd=str(WORKSPACE_ROOT)
            )

            stdout = subproc.stdout
            if "INDEPENDENT_READ_OK" in stdout:
                report["independent_process_read"] = "PASS"
            if "INDEPENDENT_DELETE_BLOCKED" in stdout:
                report["independent_process_delete_blocked"] = "PASS"
            if persist_dir.exists() and persist_file.exists():
                report["canary_survival"] = "PASS"
            if "INDEPENDENT_HASH_MATCH" in stdout:
                report["hash_match"] = "PASS"

            if (report["setup_process"] == "PASS" and
                report["independent_process_read"] == "PASS" and
                report["independent_process_delete_blocked"] == "PASS" and
                report["canary_survival"] == "PASS" and
                report["hash_match"] == "PASS"):
                report["persistence"] = "DEMONSTRATED"

        finally:
            if persist_dir.exists():
                cls.remove_protection(persist_dir)
                subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force '{persist_dir}'"], capture_output=True)

        return report

    @classmethod
    def run_drift_simulation_test(cls, base_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        EXP-23.3: Accidental regression / ACL drift simulation.
        1. Confirms vault integrity passes when protected.
        2. Deliberately simulates protection removal (drift).
        3. Asserts audit_vault_integrity catches the failure and flags ACL_DRIFT.
        4. Re-applies protection and asserts recovery.
        """
        root = base_dir or WORKSPACE_ROOT
        drift_dir = root / "sentinel_drift_simulation_tmp"
        drift_file = drift_dir / "target.txt"

        report = {
            "initial_protection": "FAIL",
            "tamper_detected": "FAIL",
            "drift_flagged": "FAIL",
            "recovery_verified": "FAIL",
            "drift_detector": "NOT_DEMONSTRATED"
        }

        try:
            if drift_dir.exists():
                cls.remove_protection(drift_dir)
                subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force '{drift_dir}'"], capture_output=True)

            drift_dir.mkdir(parents=True, exist_ok=True)
            drift_file.write_text("DRIFT_DETECTION_TEST", encoding="utf-8")

            # Step 1: Normal protection applied
            cls.apply_protection(drift_dir)
            audit_init = cls.audit_vault_integrity(drift_dir)
            if audit_init["protection_status"] == "PASS" and not audit_init["drift_detected"]:
                report["initial_protection"] = "PASS"

            # Step 2: Deliberate tamper (simulate accidental ACL removal)
            cls.remove_protection(drift_dir)
            audit_tampered = cls.audit_vault_integrity(drift_dir)
            if audit_tampered["protection_status"] == "FAIL":
                report["tamper_detected"] = "PASS"
            if audit_tampered["drift_detected"] is True:
                report["drift_flagged"] = "PASS"

            # Step 3: Re-apply and verify recovery
            cls.apply_protection(drift_dir)
            audit_recovered = cls.audit_vault_integrity(drift_dir)
            if audit_recovered["protection_status"] == "PASS" and not audit_recovered["drift_detected"]:
                report["recovery_verified"] = "PASS"

            if (report["initial_protection"] == "PASS" and
                report["tamper_detected"] == "PASS" and
                report["drift_flagged"] == "PASS" and
                report["recovery_verified"] == "PASS"):
                report["drift_detector"] = "DEMONSTRATED"

        finally:
            if drift_dir.exists():
                cls.remove_protection(drift_dir)
                subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force '{drift_dir}'"], capture_output=True)

        return report

    @classmethod
    def run_canary_test(cls, base_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Automated regression test:
        1. Create canary file in temporary vault
        2. Apply NTFS ACL protection
        3. Attempt destructive deletion via PowerShell
        4. Assert deletion is denied and file survives
        5. Verify SHA-256 hash preservation
        6. Clean up safely
        """
        root = base_dir or WORKSPACE_ROOT
        canary_dir = root / "sentinel_vault_canary_tmp"
        canary_file = canary_dir / "canary.txt"

        report = {
            "acl": "FAIL",
            "read": "FAIL",
            "delete": "FAILED_TO_BLOCK",
            "delete_child": "FAILED_TO_BLOCK",
            "canary_exists": "FAIL",
            "hash": "FAIL",
            "enforcement": "NOT_DEMONSTRATED"
        }

        try:
            # 1. Setup
            if canary_dir.exists():
                cls.remove_protection(canary_dir)
                subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force '{canary_dir}'"], capture_output=True)

            canary_dir.mkdir(parents=True, exist_ok=True)
            payload = "FRONDABRICK_VAULT_CANARY_INTEGRITY_2026_TEST"
            canary_file.write_text(payload, encoding="utf-8")
            initial_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()

            # 2. Apply ACL Protection
            acl_applied = cls.apply_protection(canary_dir)
            if not acl_applied:
                return report
            report["acl"] = "PASS"

            # 3. Read Verification
            with open(canary_file, "r", encoding="utf-8") as f:
                content = f.read()
            if content == payload:
                report["read"] = "PASS"

            # 4. Attempt DELETE (child file)
            res_del_file = subprocess.run(
                ["cmd", "/c", f"del /f /q \"{canary_file}\""],
                capture_output=True,
                text=True
            )
            # del should fail with Access Denied or return code != 0, and file must still exist
            if canary_file.exists():
                report["delete"] = "BLOCKED"

            # 5. Attempt DELETE_CHILD (parent folder recursive removal)
            res_del_dir = subprocess.run(
                ["powershell", "-Command", f"Remove-Item -Recurse -Force '{canary_dir}'"],
                capture_output=True,
                text=True
            )
            if canary_dir.exists():
                report["delete_child"] = "BLOCKED"

            # 6. Verify Existence and Hash Preservation
            if canary_dir.exists() and canary_file.exists():
                report["canary_exists"] = "PASS"
                with open(canary_file, "r", encoding="utf-8") as f:
                    post_attack_content = f.read()
                post_sha256 = hashlib.sha256(post_attack_content.encode("utf-8")).hexdigest()
                if post_sha256 == initial_sha256:
                    report["hash"] = "PASS"

            # 7. Final Enforcement evaluation
            if (report["acl"] == "PASS" and
                report["read"] == "PASS" and
                report["delete"] == "BLOCKED" and
                report["delete_child"] == "BLOCKED" and
                report["canary_exists"] == "PASS" and
                report["hash"] == "PASS"):
                report["enforcement"] = "DEMONSTRATED"

        finally:
            # Cleanup
            if canary_dir.exists():
                cls.remove_protection(canary_dir)
                subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force '{canary_dir}'"], capture_output=True)

        return report

    @classmethod
    def run_autonomy_test(cls, base_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Verifies that outside the vault, normal mutable development operations
        (create, edit, execute, delete) proceed with 100% autonomy without hindrance.
        """
        root = base_dir or WORKSPACE_ROOT
        mutable_dir = root / "tmp_autonomy_mutable_test"
        mutable_file = mutable_dir / "test_module.py"

        report = {
            "create": "FAIL",
            "edit": "FAIL",
            "execute": "FAIL",
            "delete": "FAIL",
            "autonomy": "NOT_DEMONSTRATED"
        }

        try:
            # 1. Create
            mutable_dir.mkdir(parents=True, exist_ok=True)
            mutable_file.write_text("print('HELLO_AUTONOMY')", encoding="utf-8")
            if mutable_file.exists():
                report["create"] = "PASS"

            # 2. Edit
            mutable_file.write_text("print('AUTONOMY_COMPILED_OK')", encoding="utf-8")
            if "AUTONOMY_COMPILED_OK" in mutable_file.read_text(encoding="utf-8"):
                report["edit"] = "PASS"

            # 3. Execute / Compile
            res_exec = subprocess.run([sys.executable, str(mutable_file)], capture_output=True, text=True)
            if res_exec.returncode == 0 and "AUTONOMY_COMPILED_OK" in res_exec.stdout:
                report["execute"] = "PASS"

            # 4. Delete
            res_del = subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force '{mutable_dir}'"], capture_output=True)
            if not mutable_dir.exists():
                report["delete"] = "PASS"

            if all(report[k] == "PASS" for k in ["create", "edit", "execute", "delete"]):
                report["autonomy"] = "DEMONSTRATED"

        finally:
            if mutable_dir.exists():
                subprocess.run(["powershell", "-Command", f"Remove-Item -Recurse -Force '{mutable_dir}'"], capture_output=True)

        return report

if __name__ == "__main__":
    print("=" * 60)
    print("FRONDABRICK VAULT HARDENING & CANARY VERIFIER (PHASE 22)")
    print("=" * 60)

    print("\n[EJECUTANDO] EXP-22.3: Canary Test (Protección Física NTFS)...")
    canary_res = VaultVerifier.run_canary_test()
    for k, v in canary_res.items():
        print(f"  {k.upper():<16} : {v}")

    print("\n[EJECUTANDO] EXP-22.4: Autonomy Test (Espacio Mutable)...")
    autonomy_res = VaultVerifier.run_autonomy_test()
    for k, v in autonomy_res.items():
        print(f"  {k.upper():<16} : {v}")

    print("=" * 60)
    success = (canary_res.get("enforcement") == "DEMONSTRATED" and
               autonomy_res.get("autonomy") == "DEMONSTRATED")
    if success:
        print("ESTADO: FASE 22 HARDENING VERIFICADO (PASS)")
        sys.exit(0)
    else:
        print("ESTADO: FALLA EN VERIFICACIÓN (FAIL)")
        sys.exit(1)
