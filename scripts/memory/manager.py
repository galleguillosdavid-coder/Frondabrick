#!/usr/bin/env python3
"""
F-Memory Manager
Manages the controlled lifecycle of persistent memories:
observation -> repetition -> confirmation -> confidence -> promotion.
Enforces the mandatory 8-field memory schema:
id, content, origin, created_at, last_verified, confidence, domain, status
"""

import sys
import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_ROOT = WORKSPACE_ROOT / "memory"

REQUIRED_MEMORY_FIELDS = [
    "id",
    "content",
    "origin",
    "created_at",
    "last_verified",
    "confidence",
    "domain",
    "status"
]

class MemoryManager:
    def __init__(self, root_dir: Path = MEMORY_ROOT):
        self.root_dir = root_dir
        self.session_dir = self.root_dir / "session"
        self.candidates_dir = self.root_dir / "candidates"
        self.verified_dir = self.root_dir / "verified"
        self.antipatterns_dir = self.root_dir / "anti-patterns"

        for d in [self.session_dir, self.candidates_dir, self.verified_dir, self.antipatterns_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def observe(self, content: str, origin: str, domain: str = "general", initial_confidence: float = 0.3) -> Dict[str, Any]:
        """Registers a candidate memory item. Will not promote immediately."""
        memory_id = f"MEM-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        item = {
            "id": memory_id,
            "content": content,
            "origin": origin,
            "created_at": now,
            "last_verified": now,
            "confidence": round(min(max(initial_confidence, 0.0), 0.5), 2),  # Initial confidence capped at 0.5
            "domain": domain,
            "status": "candidate"
        }

        self._save_item(self.candidates_dir, item)
        return item

    def reinforce(self, memory_id: str, delta: float = 0.2) -> Optional[Dict[str, Any]]:
        """Increases confidence upon repeated observation or verification."""
        item, path = self._find_item(memory_id)
        if not item or not path:
            return None

        now = datetime.now(timezone.utc).isoformat()
        item["last_verified"] = now
        item["confidence"] = round(min(item["confidence"] + delta, 1.0), 2)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(item, f, indent=2, ensure_ascii=False)

        return item

    def promote(self, memory_id: str, threshold: float = 0.7) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Promotes a candidate to verified status only if confidence >= threshold.
        Prevents isolated corrections from becoming permanent rules automatically.
        """
        item, path = self._find_item(memory_id)
        if not item or not path:
            return (False, f"Memoria {memory_id} no encontrada.", None)

        if item["confidence"] < threshold:
            return (False, f"Confianza insuficiente ({item['confidence']} < {threshold}). No autorizada la promoción.", item)

        # Move to verified
        item["status"] = "verified"
        item["last_verified"] = datetime.now(timezone.utc).isoformat()

        target_path = self.verified_dir / f"{item['id']}.json"
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(item, f, indent=2, ensure_ascii=False)

        # Remove from candidates
        if path.exists() and path != target_path:
            path.unlink()

        return (True, f"Memoria {memory_id} promovida exitosamente a verificada.", item)

    def flag_anti_pattern(self, content: str, origin: str, domain: str = "general") -> Dict[str, Any]:
        """Registers a documented harmful pattern to avoid."""
        memory_id = f"ANTI-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        item = {
            "id": memory_id,
            "content": content,
            "origin": origin,
            "created_at": now,
            "last_verified": now,
            "confidence": 1.0,
            "domain": domain,
            "status": "anti-pattern"
        }

        self._save_item(self.antipatterns_dir, item)
        return item

    def get_verified(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for file in self.verified_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                item = json.load(f)
            if domain is None or item.get("domain") == domain:
                results.append(item)
        return sorted(results, key=lambda x: x.get("confidence", 0), reverse=True)

    def _save_item(self, directory: Path, item: Dict[str, Any]) -> Path:
        target = directory / f"{item['id']}.json"
        with open(target, "w", encoding="utf-8") as f:
            json.dump(item, f, indent=2, ensure_ascii=False)
        return target

    def _find_item(self, memory_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
        for d in [self.candidates_dir, self.verified_dir, self.antipatterns_dir, self.session_dir]:
            target = d / f"{memory_id}.json"
            if target.is_file():
                with open(target, "r", encoding="utf-8") as f:
                    return (json.load(f), target)
        return (None, None)
