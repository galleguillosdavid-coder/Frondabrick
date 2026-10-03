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
        return res.returncode == 0

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
