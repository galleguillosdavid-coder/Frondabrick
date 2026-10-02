#!/usr/bin/env python3
"""
Frondabrick Evidence Recorder
Enforces the 7 Mandatory Evidence Questions:
1. what: ¿Qué se hizo?
2. why: ¿Por qué?
3. files_changed: ¿Qué archivos cambió?
4. command_executed: ¿Qué comando se ejecutó?
5. result: ¿Qué resultado produjo?
6. tests_passed: ¿Qué pruebas pasaron?
7. tests_failed: ¿Qué pruebas fallaron?
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_ROOT = WORKSPACE_ROOT / "evidence"

MANDATORY_EVIDENCE_FIELDS = [
    "what",
    "why",
    "files_changed",
    "command_executed",
    "result",
    "tests_passed",
    "tests_failed"
]

CATEGORIES = {"session", "security", "tests", "architecture"}

class EvidenceRecorder:
    def __init__(self, root_dir: Path = EVIDENCE_ROOT):
        self.root_dir = root_dir
        for cat in CATEGORIES:
            (self.root_dir / cat).mkdir(parents=True, exist_ok=True)

    def record(self, category: str, data: Dict[str, Any], title: str = "") -> Path:
        if category not in CATEGORIES:
            raise ValueError(f"Categoría inválida '{category}'. Debe ser una de: {CATEGORIES}")

        # Validate the 7 mandatory fields
        missing = [f for f in MANDATORY_EVIDENCE_FIELDS if f not in data]
        if missing:
            raise ValueError(f"Registro de evidencia inválido. Faltan los campos obligatorios: {missing}")

        timestamp = datetime.now(timezone.utc).isoformat()
        slug = title.strip().lower().replace(" ", "_").replace("/", "_") if title else "event"
        filename = f"{int(time.time())}_{slug}.json"
        target_path = self.root_dir / category / filename

        record_payload = {
            "timestamp": timestamp,
            "category": category,
            "title": title or "Acción Registrada",
            "evidence": {
                "what": data["what"],
                "why": data["why"],
                "files_changed": data["files_changed"],
                "command_executed": data["command_executed"],
                "result": data["result"],
                "tests_passed": data["tests_passed"],
                "tests_failed": data["tests_failed"]
            },
            "metadata": data.get("metadata", {})
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(record_payload, f, indent=2, ensure_ascii=False)

        # Also append to a category summary log
        summary_log = self.root_dir / category / "summary.jsonl"
        with open(summary_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": timestamp,
                "file": filename,
                "title": title,
                "result": data["result"]
            }) + "\n")

        return target_path

    def list_records(self, category: str) -> List[Path]:
        cat_dir = self.root_dir / category
        if not cat_dir.exists():
            return []
        return sorted([p for p in cat_dir.glob("*.json") if p.name != "summary.json"])
