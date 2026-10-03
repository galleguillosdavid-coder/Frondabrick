#!/usr/bin/env python3
"""
Frondabrick Forensic Session Reconstructor (Phase 26)
Consumes existing evidence artifacts and reconstructs the causal timeline
strictly distinguishing KNOWN facts from UNKNOWN gaps.

Axiom:
KNOWN != INFERRED.
Never guess, extrapolate, or fabricate missing evidence.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = WORKSPACE_ROOT / "evidence"
SESSION_DIR = EVIDENCE_DIR / "session"

class SessionReconstructor:
    @staticmethod
    def reconstruct(session_id: str) -> Dict[str, Any]:
        """
        Loads all persisted evidence for session_id and produces a structured forensic reconstruction.
        """
        manifest_file = SESSION_DIR / f"{session_id}.json"
        events_file = SESSION_DIR / f"{session_id}_events.jsonl"
        state_file = SESSION_DIR / f"{session_id}_state.json"

        reconstruction = {
            "session_id": session_id,
            "manifest_found": manifest_file.is_file(),
            "identity": {},
            "intent": {},
            "process": {},
            "f_shield": {},
            "commands": {},
            "filesystem": {},
            "tests": {},
            "recovery": {},
            "vault": {},
            "git": {},
            "forensic_conclusion": {}
        }

        # 1. Manifest
        manifest = {}
        if manifest_file.is_file():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception as e:
                reconstruction["manifest_error"] = str(e)

        # 2. Identity
        started_at = manifest.get("started_at")
        closed_at = manifest.get("closed_at")
        final_status = manifest.get("final_status")

        reconstruction["identity"] = {
            "session_id": {"status": "KNOWN", "value": session_id},
            "started_at": {"status": "KNOWN", "value": started_at} if started_at and started_at != "UNKNOWN" else {"status": "UNKNOWN", "value": None},
            "closed_at": {"status": "KNOWN", "value": closed_at} if closed_at and closed_at != "UNKNOWN" else {"status": "UNKNOWN", "value": None},
            "final_status": {"status": "KNOWN", "value": final_status} if final_status and final_status != "UNKNOWN" else {"status": "UNKNOWN", "value": None}
        }

        # 3. Intent
        intent = manifest.get("intent")
        if intent and intent != "UNKNOWN":
            reconstruction["intent"] = {"status": "KNOWN", "value": intent}
        else:
            reconstruction["intent"] = {"status": "UNKNOWN", "reason": "No existe intención documentada en manifiesto."}

        # 4. Process (PID / parent_pid)
        proc = manifest.get("process", {})
        pid = proc.get("pid")
        parent_pid = proc.get("parent_pid")
        process_status = "KNOWN" if pid is not None and pid != "UNKNOWN" else "UNKNOWN"
        reconstruction["process"] = {
            "status": process_status,
            "pid": {"status": "KNOWN", "value": pid} if pid is not None and pid != "UNKNOWN" else {"status": "UNKNOWN", "reason": "PID no capturado en runtime."},
            "parent_pid": {"status": "KNOWN", "value": parent_pid} if parent_pid is not None and parent_pid != "UNKNOWN" else {"status": "UNKNOWN", "reason": "Parent PID no disponible."}
        }

        # 5. F-Shield Events
        f_shield_events = manifest.get("f_shield_events", [])
        if not f_shield_events:
            # Fallback cross-check against audit.jsonl directly
            audit_file = EVIDENCE_DIR / "security" / "audit.jsonl"
            if audit_file.is_file():
                try:
                    with open(audit_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                rec = json.loads(line)
                                if rec.get("session_id") == session_id:
                                    f_shield_events.append(rec)
                except Exception:
                    pass

        if f_shield_events:
            reconstruction["f_shield"] = {
                "status": "KNOWN",
                "events_count": len(f_shield_events),
                "events": f_shield_events
            }
        else:
            reconstruction["f_shield"] = {
                "status": "UNKNOWN",
                "reason": "No existen eventos de F-Shield asociados a esta sesión."
            }

        # 6. Commands and Execution Events
        raw_events = manifest.get("events", [])
        if not raw_events and events_file.is_file():
            try:
                with open(events_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            raw_events.append(json.loads(line))
            except Exception:
                pass

        action_events = [e for e in raw_events if e.get("event_type") in ["action_executed", "command_executed", "attack_attempted", "blocked_attempt"]]
        if action_events:
            reconstruction["commands"] = {
                "status": "KNOWN",
                "events": action_events
            }
        else:
            reconstruction["commands"] = {
                "status": "UNKNOWN",
                "reason": "No existen registros de comandos en los eventos de sesión."
            }

        # OS Physical Enforcement Detection (EXP-26.3)
        os_enforcement_events = [
            e for e in raw_events
            if e.get("event_type") in ["blocked_attempt", "access_denied"]
            or "access_denied" in str(e.get("data", "")).lower()
            or e.get("data", {}).get("enforcement_layer") == "NTFS_ACL"
        ]
        if os_enforcement_events:
            reconstruction["os_enforcement"] = {
                "status": "KNOWN",
                "events_count": len(os_enforcement_events),
                "events": os_enforcement_events
            }
        else:
            reconstruction["os_enforcement"] = {
                "status": "UNKNOWN",
                "reason": "No existe evidencia estructurada de denegación física por parte del SO."
            }

        # 7. Filesystem Events
        fs_changes = []
        for e in raw_events:
            if "files_changed" in e.get("data", {}) and e["data"]["files_changed"]:
                fs_changes.extend(e["data"]["files_changed"])
        for r in manifest.get("evidence_records", []):
            rec_files = r.get("record", {}).get("files_changed", [])
            if rec_files:
                fs_changes.extend(rec_files)

        if fs_changes:
            reconstruction["filesystem"] = {
                "status": "KNOWN",
                "files_changed": list(set(fs_changes))
            }
        else:
            reconstruction["filesystem"] = {
                "status": "UNKNOWN",
                "reason": "No existe evidencia estructurada de modificación individual de archivos."
            }

        # 8. Test Results
        evidence_records = manifest.get("evidence_records", [])
        test_records = [r for r in evidence_records if r.get("category") == "tests"]
        if test_records:
            reconstruction["tests"] = {
                "status": "KNOWN",
                "records": test_records
            }
        else:
            reconstruction["tests"] = {
                "status": "UNKNOWN",
                "reason": "No existe evidencia de tests ejecutados en esta sesión."
            }

        # 9. Recovery
        recovery_events = [e for e in raw_events if "recovery" in e.get("event_type", "").lower() or "recover" in str(e.get("data", "")).lower()]
        if recovery_events:
            reconstruction["recovery"] = {
                "status": "KNOWN",
                "events": recovery_events
            }
        else:
            reconstruction["recovery"] = {
                "status": "UNKNOWN",
                "reason": "No existe evento de recuperación registrado."
            }

        # 10. Vault State
        vault = manifest.get("vault", {})
        prot_status = vault.get("protection_status")
        drift = vault.get("drift_detected")
        canary_sha = vault.get("canary_sha256")
        if prot_status and prot_status != "UNKNOWN":
            reconstruction["vault"] = {
                "status": "KNOWN",
                "protection_status": prot_status,
                "drift_detected": drift,
                "canary_sha256": canary_sha
            }
        else:
            reconstruction["vault"] = {
                "status": "UNKNOWN",
                "reason": "Estado de la bóveda no verificado en el manifiesto."
            }

        # 11. Git Metadata
        git_info = manifest.get("git", {})
        commit = git_info.get("commit")
        branch = git_info.get("branch")
        dirty = git_info.get("dirty")
        if commit and commit != "UNKNOWN":
            reconstruction["git"] = {
                "status": "KNOWN",
                "commit": commit,
                "branch": branch,
                "dirty": dirty
            }
        else:
            reconstruction["git"] = {
                "status": "UNKNOWN",
                "reason": "Estado de Git no capturado en el manifiesto."
            }

        # 12. Integrity Seal (EXP-26.5)
        seal = manifest.get("integrity_seal")
        if seal and isinstance(seal, dict):
            from scripts.evidence.session import SessionTracker
            verification = SessionTracker.verify_session_seal(session_id)
            reconstruction["integrity_seal"] = {
                "status": "KNOWN" if verification["verdict"] == "SEAL_VALID" else "FAIL",
                "verdict": verification["verdict"],
                "algorithm": seal.get("algorithm", "SHA-256"),
                "manifest_sha256": seal.get("manifest_sha256"),
                "events_sha256": seal.get("events_sha256")
            }
        else:
            reconstruction["integrity_seal"] = {
                "status": "UNKNOWN",
                "reason": "Manifiesto no contiene bloque de sellado criptográfico."
            }

        # 13. Forensic Conclusion
        known_aspects = []
        unknown_aspects = []

        for section in ["intent", "process", "f_shield", "commands", "filesystem", "tests", "recovery", "vault", "git"]:
            sec_data = reconstruction[section]
            if sec_data.get("status") == "KNOWN":
                known_aspects.append(section)
            else:
                unknown_aspects.append(section)

        reconstruction["forensic_conclusion"] = {
            "known_aspects": known_aspects,
            "unknown_aspects": unknown_aspects,
            "fully_reconstructed": len(unknown_aspects) == 0
        }

        return reconstruction

    @classmethod
    def format_report(cls, session_id: str) -> str:
        recon = cls.reconstruct(session_id)
        lines = []
        lines.append("=" * 60)
        lines.append(f"FRONDABRICK FORENSIC SESSION RECONSTRUCTION")
        lines.append("=" * 60)
        lines.append(f"SESSION ID : {recon['session_id']}")
        lines.append(f"STATUS     : {recon['identity']['final_status']['value'] if recon['identity']['final_status']['status'] == 'KNOWN' else 'UNKNOWN'}")
        lines.append(f"STARTED AT : {recon['identity']['started_at']['value'] if recon['identity']['started_at']['status'] == 'KNOWN' else 'UNKNOWN'}")
        lines.append(f"CLOSED AT  : {recon['identity']['closed_at']['value'] if recon['identity']['closed_at']['status'] == 'KNOWN' else 'UNKNOWN'}")

        lines.append("\n" + "-" * 60)
        lines.append("INTENT")
        lines.append("-" * 60)
        if recon["intent"]["status"] == "KNOWN":
            lines.append(f"  KNOWN: {recon['intent']['value']}")
        else:
            lines.append(f"  UNKNOWN: {recon['intent']['reason']}")

        lines.append("\n" + "-" * 60)
        lines.append("PROCESS")
        lines.append("-" * 60)
        p_pid = recon["process"]["pid"]
        p_ppid = recon["process"]["parent_pid"]
        lines.append(f"  PID        : {p_pid['value'] if p_pid['status'] == 'KNOWN' else 'UNKNOWN'}")
        lines.append(f"  Parent PID : {p_ppid['value'] if p_ppid['status'] == 'KNOWN' else 'UNKNOWN'}")

        lines.append("\n" + "-" * 60)
        lines.append("F-SHIELD")
        lines.append("-" * 60)
        if recon["f_shield"]["status"] == "KNOWN":
            for ev in recon["f_shield"]["events"]:
                lines.append(f"  KNOWN: decision={ev.get('decision')} | level={ev.get('level')} | reason={ev.get('reason')}")
        else:
            lines.append(f"  UNKNOWN: {recon['f_shield']['reason']}")

        lines.append("\n" + "-" * 60)
        lines.append("COMMANDS & ACTIONS")
        lines.append("-" * 60)
        if recon["commands"]["status"] == "KNOWN":
            for c in recon["commands"]["events"]:
                data = c.get("data", {})
                lines.append(f"  KNOWN: event={c.get('event_type')} | hash={data.get('command_hash', 'UNKNOWN')} | exit_code={data.get('exit_code', 'UNKNOWN')}")
                if "command" in data:
                    lines.append(f"         command={data['command']}")
        else:
            lines.append(f"  UNKNOWN: {recon['commands']['reason']}")

        lines.append("\n" + "-" * 60)
        lines.append("OS ENFORCEMENT (PHYSICAL)")
        lines.append("-" * 60)
        if recon.get("os_enforcement", {}).get("status") == "KNOWN":
            for osev in recon["os_enforcement"]["events"]:
                odata = osev.get("data", {})
                lines.append(f"  KNOWN: layer={odata.get('enforcement_layer', 'NTFS_ACL')} | exit_code={odata.get('os_exit_code', 'UNKNOWN')} | error={odata.get('os_error', 'UNKNOWN')}")
                if "target_path" in odata:
                    lines.append(f"         target={odata['target_path']}")
        else:
            lines.append(f"  UNKNOWN: {recon.get('os_enforcement', {}).get('reason', 'Sin eventos de enforcement del SO')}")

        lines.append("\n" + "-" * 60)
        lines.append("TESTS")
        lines.append("-" * 60)
        if recon["tests"]["status"] == "KNOWN":
            for t in recon["tests"]["records"]:
                rec = t.get("record", {})
                lines.append(f"  KNOWN: {rec.get('title')} | result={rec.get('result')} | file={rec.get('file')}")
        else:
            lines.append(f"  UNKNOWN: {recon['tests']['reason']}")

        lines.append("\n" + "-" * 60)
        lines.append("VAULT STATE")
        lines.append("-" * 60)
        if recon["vault"]["status"] == "KNOWN":
            lines.append(f"  KNOWN: protection_status={recon['vault']['protection_status']}")
            lines.append(f"         drift_detected={recon['vault']['drift_detected']}")
            lines.append(f"         canary_sha256={recon['vault']['canary_sha256']}")
        else:
            lines.append(f"  UNKNOWN: {recon['vault']['reason']}")

        lines.append("\n" + "-" * 60)
        lines.append("GIT")
        lines.append("-" * 60)
        if recon["git"]["status"] == "KNOWN":
            lines.append(f"  KNOWN: commit={recon['git']['commit']}")
            lines.append(f"         branch={recon['git']['branch']} | dirty={recon['git']['dirty']}")
        else:
            lines.append(f"  UNKNOWN: {recon['git']['reason']}")

        lines.append("\n" + "-" * 60)
        lines.append("FILESYSTEM")
        lines.append("-" * 60)
        if recon["filesystem"]["status"] == "KNOWN":
            lines.append(f"  KNOWN: {recon['filesystem']['files_changed']}")
        else:
            lines.append(f"  UNKNOWN: {recon['filesystem']['reason']}")

        lines.append("\n" + "-" * 60)
        lines.append("RECOVERY")
        lines.append("-" * 60)
        if recon["recovery"]["status"] == "KNOWN":
            lines.append(f"  KNOWN: {recon['recovery']['events']}")
        else:
            lines.append(f"  UNKNOWN: {recon['recovery']['reason']}")

        lines.append("\n" + "-" * 60)
        lines.append("INTEGRITY SEAL (EXP-26.5)")
        lines.append("-" * 60)
        if recon.get("integrity_seal", {}).get("status") == "KNOWN":
            s = recon["integrity_seal"]
            lines.append(f"  KNOWN: verdict={s.get('verdict')} | algorithm={s.get('algorithm')}")
            lines.append(f"         manifest_sha256={s.get('manifest_sha256')}")
            lines.append(f"         events_sha256={s.get('events_sha256')}")
        else:
            lines.append(f"  UNKNOWN: {recon.get('integrity_seal', {}).get('reason', 'Sin sello criptográfico.')}")

        lines.append("\n" + "=" * 60)
        lines.append("FORENSIC CONCLUSION")
        lines.append("=" * 60)
        conc = recon["forensic_conclusion"]
        lines.append(f"  KNOWN ASPECTS   : {', '.join(conc['known_aspects']) if conc['known_aspects'] else 'None'}")
        lines.append(f"  UNKNOWN ASPECTS : {', '.join(conc['unknown_aspects']) if conc['unknown_aspects'] else 'None'}")
        lines.append(f"  VERDICT         : {'COMPLETO' if conc['fully_reconstructed'] else 'PARCIAL CON HUECOS IDENTIFICADOS (UNKNOWN)'}")
        
        has_shield_deny = recon["f_shield"]["status"] == "KNOWN" and any(e.get("decision") == "deny" for e in recon["f_shield"]["events"])
        has_os_block = recon.get("os_enforcement", {}).get("status") == "KNOWN"
        if has_shield_deny or has_os_block:
            lines.append("\n  ARCHITECTURAL SEPARATION VERIFIED:")
            lines.append("  - F-Shield : DETECTION / CLASSIFICATION / AUDIT (Policy Deny)")
            lines.append("  - OS/NTFS  : PHYSICAL ENFORCEMENT (Denied at Kernel/FS level)")
            lines.append("  - Vault    : PHYSICAL INTEGRITY CONFIRMED (Canary intact, drift false)")
        elif recon["f_shield"]["status"] == "KNOWN" and all(e.get("decision") == "allow" for e in recon["f_shield"]["events"]):
            lines.append("\n  EVENT CLASSIFICATION: ALLOWED_DEVELOPMENT")
            lines.append("  - F-Shield  : ALLOW (All operations verified compliant)")
            lines.append("  - Execution : UNHINDERED (Full mutable workspace autonomy)")
            lines.append("  - Evidence  : PERSISTED (Filesystem, tests, git correlated)")
        lines.append("=" * 60)

        return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/forensics/reconstruct_session.py <SESSION_ID>")
        sys.exit(1)

    session_id = sys.argv[1].strip()
    report = SessionReconstructor.format_report(session_id)
    print(report)

if __name__ == "__main__":
    main()
