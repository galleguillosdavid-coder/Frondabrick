#!/usr/bin/env python3
"""
F-Shield Detector Module
Detects destructive commands, credentials, sensitive file access, and role violations.
Each rule implements: pattern, risk, reason, action, exception, test.
"""

import re
from typing import Dict, Any, List, Optional

SECURITY_RULES = [
    {
        "id": "SEC-001",
        "name": "Recursive Forced Deletion",
        "pattern": r"(\brm\s+-[rRfF]{1,3}\b|\bdel\b(?=.*\/[sS])|\b(?:rmdir|rd)\b(?=.*\/[sS])|\b(?:Remove-Item|ri)\b(?=.*-(?:r\b|rec\w*)))",
        "risk": "CRITICAL",
        "reason": "Intento de eliminación recursiva forzada en el sistema de archivos.",
        "action": "BLOCK",
        "level": 4,
        "exception": r"\brm\s+-[rRfF]+\s+(?:node_modules|\.cache|tmp|temp)\b",
        "test": "rm -rf /"
    },
    {
        "id": "SEC-002",
        "name": "Storage Format / Partition Destruction",
        "pattern": r"\b(format\s+[a-zA-Z]:|mkfs\b|fdisk\b|diskpart\b)",
        "risk": "CRITICAL",
        "reason": "Comando destructivo de formateo o partición de almacenamiento.",
        "action": "BLOCK",
        "level": 4,
        "exception": None,
        "test": "format c:"
    },
    {
        "id": "SEC-003",
        "name": "Database Table / Schema Drop",
        "pattern": r"\bDROP\s+(?:DATABASE|SCHEMA|TABLE)\b",
        "risk": "HIGH",
        "reason": "Sentencia SQL destructiva de eliminación de bases de datos o tablas.",
        "action": "ASK",
        "level": 3,
        "exception": r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:temp_|test_)\w+\b",
        "test": "DROP TABLE users;"
    },
    {
        "id": "SEC-004",
        "name": "Git Destructive History Operations",
        "pattern": r"\bgit\s+(?:reset\s+--hard|clean\s+-[fF]{1,2}[dD]?|push\s+.*(?:--force|-f\b))",
        "risk": "HIGH",
        "reason": "Operación destructiva en el historial de control de versiones.",
        "action": "BLOCK",
        "level": 4,
        "exception": None,
        "test": "git reset --hard HEAD~1"
    },
    {
        "id": "SEC-005",
        "name": "Private Key Exposure",
        "pattern": r"-----BEGIN\s+(?:RSA|OPENSSH|EC|DSA)?\s*PRIVATE\s+KEY-----",
        "risk": "CRITICAL",
        "reason": "Detección de clave privada en contenido o argumentos.",
        "action": "BLOCK",
        "level": 4,
        "exception": None,
        "test": "-----BEGIN RSA PRIVATE KEY-----"
    },
    {
        "id": "SEC-006",
        "name": "API Key / Token Leakage",
        "pattern": r"\b(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{30,}|AKIA[0-9A-Z]{16})\b",
        "risk": "HIGH",
        "reason": "Detección de token de API o credencial en texto claro.",
        "action": "BLOCK",
        "level": 4,
        "exception": None,
        "test": "sk-123456789012345678901234"
    },
    {
        "id": "SEC-007",
        "name": "Sensitive File Alteration (.env)",
        "pattern": r"(?:^|[\\/])\.env(?:\.(?:local|prod|production))?$",
        "risk": "MEDIUM",
        "reason": "Modificación o lectura directa de archivo de variables sensibles (.env).",
        "action": "ASK",
        "level": 3,
        "exception": r"\.env\.example$",
        "test": ".env"
    },
    {
        "id": "SEC-008",
        "name": "Encoded PowerShell Execution",
        "pattern": r"\b(?:powershell|pwsh)\b(?=.*-(?:e|enc|encodedcommand)\b)",
        "risk": "HIGH",
        "reason": "Ejecución de comando PowerShell codificado u ofuscado.",
        "action": "ASK",
        "level": 3,
        "exception": None,
        "test": "powershell -enc Y21k"
    }
]

class SecurityDetector:
    @staticmethod
    def inspect_command(command: str) -> Optional[Dict[str, Any]]:
        # Filtro de falsos positivos: comandos inocuos de inspección o impresión sin ejecución encadenada
        is_inspection = re.match(r"^\s*(?:git\s+grep|rg|grep|findstr|echo|cat|type|Select-String)\b", command, re.IGNORECASE)
        has_exec_pipe = re.search(r"\|\s*(?:sh|bash|cmd|powershell|pwsh|iex|Invoke-Expression)\b", command, re.IGNORECASE)
        if is_inspection and not has_exec_pipe:
            return None

        for rule in SECURITY_RULES:
            if re.search(rule["pattern"], command, re.IGNORECASE):
                if rule["exception"] and re.search(rule["exception"], command, re.IGNORECASE):
                    continue
                return rule
        return None

    @staticmethod
    def inspect_content(content: str) -> Optional[Dict[str, Any]]:
        for rule in [r for r in SECURITY_RULES if r["id"] in ["SEC-005", "SEC-006"]]:
            if re.search(rule["pattern"], content):
                return rule
        return None

    @staticmethod
    def inspect_target_file(target_file: str) -> Optional[Dict[str, Any]]:
        rule = next((r for r in SECURITY_RULES if r["id"] == "SEC-007"), None)
        if rule and re.search(rule["pattern"], target_file, re.IGNORECASE):
            if not (rule["exception"] and re.search(rule["exception"], target_file, re.IGNORECASE)):
                return rule
        return None
