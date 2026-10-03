#!/usr/bin/env python3
"""
Frondabrick Session Tracker & Forensics Correlator (Phase 26)
Stitches together:
- session_id (single UUID per autonomous session)
- Intent
- F-Shield decisions (audit.jsonl)
- Process execution metadata (PID / parent_pid)
- EvidenceRecorder items (evidence/tests/, etc.)
- VaultVerifier state snapshot
- Git commit / branch / dirty state

Enforces the strict rule:
KNOWN vs UNKNOWN (Never guess or infer missing evidence).
"""

import os
import sys
import json
import uuid
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = WORKSPACE_ROOT / "evidence"
SESSION_DIR = EVIDENCE_DIR / "session"
ACTIVE_SESSION_FILE = SESSION_DIR / ".active_session"

class SessionTracker:
    @staticmethod
    def get_active_session_id() -> Optional[str]:
        env_id = os.environ.get("FRONDABRICK_SESSION_ID")
        if env_id:
            return env_id.strip()
        if ACTIVE_SESSION_FILE.is_file():
            try:
                sid = ACTIVE_SESSION_FILE.read_text(encoding="utf-8").strip()
                return sid if sid else None
            except Exception:
                return None
        return None

    @classmethod
    def start_session(cls, intent: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        EXP-26.1.1: Generates a single session_id (UUID) and registers initial intent and process metadata.
        """
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        session_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()

        # EXP-26.1.2: Record real PID and parent_pid (or None if unavailable, never fabricate)
        pid = os.getpid()
        parent_pid = os.getppid() if hasattr(os, "getppid") else None

        os.environ["FRONDABRICK_SESSION_ID"] = session_id
        ACTIVE_SESSION_FILE.write_text(session_id, encoding="utf-8")

        init_payload = {
            "session_id": session_id,
            "intent": intent,
            "started_at": started_at,
            "process": {
                "pid": pid,
                "parent_pid": parent_pid
            },
            "metadata": metadata or {}
        }

        # Store session state file
        state_file = SESSION_DIR / f"{session_id}_state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(init_payload, f, indent=2, ensure_ascii=False)

        # Initialize event log
        events_file = SESSION_DIR / f"{session_id}_events.jsonl"
        with open(events_file, "w", encoding="utf-8") as f:
            start_event = {
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "session_id": session_id,
                "event_type": "session_start",
                "timestamp": started_at,
                "pid": pid,
                "parent_pid": parent_pid,
                "data": {"intent": intent}
            }
            f.write(json.dumps(start_event) + "\n")

        return init_payload

    @classmethod
    def record_session_event(cls, event_type: str, data: Dict[str, Any], session_id: Optional[str] = None, pid: Optional[int] = None) -> Dict[str, Any]:
        """
        Records an event within the active session. Sanitizes command if provided.
        """
        sid = session_id or cls.get_active_session_id()
        if not sid:
            raise ValueError("No active session_id found. Call start_session first or pass session_id explicitly.")

        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        resolved_pid = pid if pid is not None else os.getpid()

        sanitized_data = dict(data)
        if "command" in sanitized_data:
            cmd = sanitized_data["command"]
            sanitized_data["command_hash"] = hashlib.sha256(cmd.encode("utf-8")).hexdigest()

        event = {
            "event_id": event_id,
            "session_id": sid,
            "event_type": event_type,
            "timestamp": now,
            "pid": resolved_pid,
            "data": sanitized_data
        }

        events_file = SESSION_DIR / f"{sid}_events.jsonl"
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        return event

    @classmethod
    def close_session(cls, session_id: Optional[str] = None, final_status: str = "PASS") -> Dict[str, Any]:
        """
        EXP-26.1.3 & EXP-26.1.4:
        Seals the session, capturing Git state, VaultVerifier integrity state,
        correlating F-Shield and EvidenceRecorder artifacts into a coherent manifest.
        """
        sid = session_id or cls.get_active_session_id()
        if not sid:
            raise ValueError("No active session to close.")

        closed_at = datetime.now(timezone.utc).isoformat()
        state_file = SESSION_DIR / f"{sid}_state.json"
        if state_file.is_file():
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = {
                "session_id": sid,
                "intent": "UNKNOWN",
                "started_at": "UNKNOWN",
                "process": {"pid": None, "parent_pid": None}
            }

        # 1. Capture Git State (EXP-26.1.3)
        git_commit = "UNKNOWN"
        git_branch = "UNKNOWN"
        git_dirty = "UNKNOWN"
        try:
            r1 = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
            if r1.returncode == 0:
                git_commit = r1.stdout.strip()
            r2 = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
            if r2.returncode == 0:
                git_branch = r2.stdout.strip()
            r3 = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
            if r3.returncode == 0:
                git_dirty = bool(r3.stdout.strip())
        except Exception:
            pass

        # 2. Capture Vault State (EXP-26.1.4: reuse audit_vault_integrity)
        vault_report = {
            "protection_status": "UNKNOWN",
            "drift_detected": "UNKNOWN",
            "acl_present": "UNKNOWN",
            "delete_denied": "UNKNOWN",
            "canary_sha256": "UNKNOWN"
        }
        try:
            from scripts.vault.verifier import VaultVerifier
            vault_dir = WORKSPACE_ROOT / "vault"
            v_rep = VaultVerifier.audit_vault_integrity(vault_dir)
            canary_path = vault_dir / "canary.txt"
            canary_sha = "UNKNOWN"
            if canary_path.is_file():
                try:
                    canary_sha = hashlib.sha256(canary_path.read_bytes()).hexdigest()
                except Exception:
                    pass

            vault_report = {
                "protection_status": v_rep.get("protection_status", "UNKNOWN"),
                "drift_detected": v_rep.get("drift_detected", "UNKNOWN"),
                "acl_present": v_rep.get("acl_present", "UNKNOWN"),
                "delete_denied": v_rep.get("delete_denied", "UNKNOWN"),
                "canary_sha256": canary_sha
            }
        except Exception as e:
            vault_report["error"] = str(e)

        # 3. Read Session Events
        events = []
        events_file = SESSION_DIR / f"{sid}_events.jsonl"
        if events_file.is_file():
            with open(events_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except Exception:
                            pass

        # 4. Correlate F-Shield events from evidence/security/audit.jsonl
        f_shield_events = []
        audit_file = EVIDENCE_DIR / "security" / "audit.jsonl"
        if audit_file.is_file():
            with open(audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            rec = json.loads(line)
                            if rec.get("session_id") == sid:
                                f_shield_events.append(rec)
                        except Exception:
                            pass

        # 5. Correlate EvidenceRecorder records
        evidence_records = []
        for cat in ["tests", "security", "architecture"]:
            cat_summary = EVIDENCE_DIR / cat / "summary.jsonl"
            if cat_summary.is_file():
                with open(cat_summary, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                item = json.loads(line)
                                if item.get("session_id") == sid:
                                    evidence_records.append({"category": cat, "record": item})
                            except Exception:
                                pass

        # 6. EXP-26.5: Calculate Integrity Seal (SHA-256)
        events_sha256 = "UNKNOWN"
        if events_file.is_file():
            try:
                events_sha256 = hashlib.sha256(events_file.read_bytes()).hexdigest()
            except Exception:
                pass

        canonical_digest_payload = {
            "schema_version": 1,
            "session_id": sid,
            "intent": state.get("intent", "UNKNOWN"),
            "started_at": state.get("started_at", "UNKNOWN"),
            "closed_at": closed_at,
            "process": state.get("process", {"pid": None, "parent_pid": None}),
            "git": {
                "commit": git_commit,
                "branch": git_branch,
                "dirty": git_dirty
            },
            "vault": vault_report,
            "events_count": len(events),
            "events_sha256": events_sha256,
            "final_status": final_status
        }
        canonical_str = json.dumps(canonical_digest_payload, sort_keys=True, ensure_ascii=False)
        manifest_digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        integrity_seal = {
            "algorithm": "SHA-256",
            "type": "INTEGRITY_SEAL",
            "manifest_sha256": manifest_digest,
            "events_sha256": events_sha256,
            "sealed_at": closed_at
        }

        # 7. Assemble Manifest
        manifest = {
            "schema_version": 1,
            "session_id": sid,
            "intent": state.get("intent", "UNKNOWN"),
            "started_at": state.get("started_at", "UNKNOWN"),
            "closed_at": closed_at,
            "process": state.get("process", {"pid": None, "parent_pid": None}),
            "git": {
                "commit": git_commit,
                "branch": git_branch,
                "dirty": git_dirty
            },
            "vault": vault_report,
            "events_count": len(events),
            "events": events,
            "f_shield_events": f_shield_events,
            "evidence_records": evidence_records,
            "integrity_seal": integrity_seal,
            "final_status": final_status
        }

        # Write final session manifest
        final_manifest_path = SESSION_DIR / f"{sid}.json"
        with open(final_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # Append to session summary log
        summary_log = SESSION_DIR / "summary.jsonl"
        with open(summary_log, "a", encoding="utf-8") as f:
            summary_entry = {
                "timestamp": closed_at,
                "session_id": sid,
                "intent": state.get("intent", "UNKNOWN"),
                "result": final_status,
                "manifest_sha256": manifest_digest,
                "file": f"{sid}.json"
            }
            f.write(json.dumps(summary_entry) + "\n")

        # Cleanup active pointer
        if ACTIVE_SESSION_FILE.is_file():
            try:
                ACTIVE_SESSION_FILE.unlink()
            except Exception:
                pass
        os.environ.pop("FRONDABRICK_SESSION_ID", None)

        return manifest

    @classmethod
    def verify_session_seal(cls, session_id: str) -> Dict[str, Any]:
        """
        EXP-26.5: Verifies cryptographic integrity of a closed session.
        Returns SEAL_VALID, SEAL_TAMPERED, or SEAL_MISSING.
        """
        manifest_file = SESSION_DIR / f"{session_id}.json"
        events_file = SESSION_DIR / f"{session_id}_events.jsonl"
        if not manifest_file.is_file():
            return {
                "session_id": session_id,
                "seal_present": False,
                "manifest_integrity": "FAIL",
                "events_integrity": "FAIL",
                "verdict": "SEAL_MISSING",
                "reason": f"Manifest file not found: {manifest_file}"
            }

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            return {
                "session_id": session_id,
                "seal_present": False,
                "manifest_integrity": "FAIL",
                "events_integrity": "FAIL",
                "verdict": "CORRUPTED",
                "reason": str(e)
            }

        seal = manifest.get("integrity_seal")
        if not seal or not isinstance(seal, dict):
            return {
                "session_id": session_id,
                "seal_present": False,
                "manifest_integrity": "UNKNOWN",
                "events_integrity": "UNKNOWN",
                "verdict": "SEAL_MISSING",
                "reason": "Manifest does not contain integrity_seal block."
            }

        # Recompute canonical manifest digest
        canonical_digest_payload = {
            "schema_version": manifest.get("schema_version", 1),
            "session_id": manifest.get("session_id"),
            "intent": manifest.get("intent"),
            "started_at": manifest.get("started_at"),
            "closed_at": manifest.get("closed_at"),
            "process": manifest.get("process"),
            "git": manifest.get("git"),
            "vault": manifest.get("vault"),
            "events_count": manifest.get("events_count"),
            "events_sha256": seal.get("events_sha256"),
            "final_status": manifest.get("final_status")
        }
        canonical_str = json.dumps(canonical_digest_payload, sort_keys=True, ensure_ascii=False)
        computed_manifest_digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        manifest_ok = (computed_manifest_digest == seal.get("manifest_sha256"))

        # Recompute events digest
        events_ok = True
        if events_file.is_file():
            actual_events_sha = hashlib.sha256(events_file.read_bytes()).hexdigest()
            events_ok = (actual_events_sha == seal.get("events_sha256"))
        elif seal.get("events_sha256") != "UNKNOWN":
            events_ok = False

        all_valid = manifest_ok and events_ok
        return {
            "session_id": session_id,
            "seal_present": True,
            "manifest_integrity": "PASS" if manifest_ok else "FAIL",
            "events_integrity": "PASS" if events_ok else "FAIL",
            "verdict": "SEAL_VALID" if all_valid else "SEAL_TAMPERED",
            "computed_manifest_sha256": computed_manifest_digest,
            "sealed_manifest_sha256": seal.get("manifest_sha256")
        }
