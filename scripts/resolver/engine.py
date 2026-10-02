#!/usr/bin/env python3
"""
F-Build-Resolver Engine
Implements the 7-step error diagnosis and resolution pipeline:
1. Reproduce
2. Locate
3. Explain
4. Propose
5. Fix
6. Rerun
7. Prove
Enforces: Never hide errors to achieve a fake PASS.
"""

import sys
import re
from typing import Dict, Any, Optional

RESOLVER_STEPS = [
    "reproduce",
    "locate",
    "explain",
    "propose",
    "fix",
    "rerun",
    "proof"
]

class BuildResolverEngine:
    @staticmethod
    def parse_error_trace(trace: str) -> Dict[str, Any]:
        """Extracts file, line number, and error type from stack traces or compiler output."""
        location = {"file": None, "line": None, "error_type": "UnknownError", "message": ""}

        # Python traceback pattern: File "...", line X, in ...
        py_match = re.search(r'File\s+"([^"]+)",\s+line\s+(\d+)(?:,\s+in\s+(\w+))?', trace)
        if py_match:
            location["file"] = py_match.group(1)
            location["line"] = int(py_match.group(2))
            if py_match.group(3):
                location["scope"] = py_match.group(3)

        # Extract last error line
        lines = [line.strip() for line in trace.strip().splitlines() if line.strip()]
        if lines:
            last_line = lines[-1]
            err_match = re.match(r"^([a-zA-Z_]\w*(?:Error|Exception|Failure)):\s*(.*)$", last_line)
            if err_match:
                location["error_type"] = err_match.group(1)
                location["message"] = err_match.group(2)
            else:
                location["message"] = last_line

        return location

    @classmethod
    def evaluate_resolution_cycle(cls, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates that all 7 steps were executed legitimately.
        Fails if rerun indicates non-zero exit code or if proof is omitted.
        """
        missing_steps = [s for s in RESOLVER_STEPS if s not in report]
        if missing_steps:
            return {
                "status": "FAIL",
                "reason": f"Proceso de resolución incompleto. Faltan los pasos: {missing_steps}"
            }

        rerun_info = report.get("rerun", {})
        exit_code = rerun_info.get("exit_code", 1)
        if exit_code != 0:
            return {
                "status": "FAIL",
                "reason": f"El paso de re-ejecución (Paso 6) falló con código {exit_code}. Error no resuelto."
            }

        proof_text = report.get("proof", "")
        if not proof_text or len(proof_text.strip()) < 10:
            return {
                "status": "FAIL",
                "reason": "El paso de demostración (Paso 7) carece de evidencia suficiente."
            }

        return {
            "status": "RESOLVED",
            "message": "Error diagnosticado, corregido y demostrado con éxito (100% PASS).",
            "details": report
        }
