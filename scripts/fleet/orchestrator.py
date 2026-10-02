#!/usr/bin/env python3
"""
Frondabrick Fleet Orchestrator
Manages role delegation and enforces the agent permissions matrix.
Never grants blanket permissions for convenience.
"""

from typing import Dict, Any, List, Optional, Tuple

FLEET_ROLES = {
    "planner": {
        "description": "Descomposición y especificación de tareas previas al desarrollo.",
        "allowed_tools": {"view_file", "list_dir", "grep_search"},
        "restricted_write": True
    },
    "reviewer": {
        "description": "Auditoría de calidad, diffs y seguridad en modo sólo lectura.",
        "allowed_tools": {"view_file", "list_dir", "grep_search"},
        "restricted_write": True
    },
    "builder": {
        "description": "Implementación de código bajo la regla de cambio mínimo.",
        "allowed_tools": {"view_file", "list_dir", "grep_search", "run_command", "write_to_file", "replace_file_content", "multi_replace_file_content"},
        "restricted_write": False
    },
    "shield": {
        "description": "Evaluación de políticas de seguridad y guardarraíles.",
        "allowed_tools": {"view_file", "list_dir", "grep_search"},
        "restricted_write": True
    },
    "build_resolver": {
        "description": "Diagnóstico y corrección quirúrgica de fallos de compilador y tests.",
        "allowed_tools": {"view_file", "list_dir", "grep_search", "run_command", "write_to_file", "replace_file_content", "multi_replace_file_content"},
        "restricted_write": False
    },
    "memory": {
        "description": "Gestión del aprendizaje persistente y anti-patrones.",
        "allowed_tools": {"view_file", "list_dir", "grep_search"},
        "restricted_write": True
    },
    "browser_qa": {
        "description": "Validación funcional y visual en navegador para aplicaciones web.",
        "allowed_tools": {"view_file", "list_dir", "grep_search", "browser_subagent"},
        "restricted_write": True
    }
}

class FleetOrchestrator:
    @staticmethod
    def authorize_tool_for_role(role: str, tool_name: str, target_file: str = "") -> Tuple[bool, str]:
        role_key = role.lower().strip()
        if role_key not in FLEET_ROLES:
            return (False, f"Rol desconocido '{role}'. Rechazado por principio de mínimo privilegio.")

        spec = FLEET_ROLES[role_key]

        # Check special write exemptions (e.g. planner writing only plan docs)
        if role_key == "planner" and tool_name == "write_to_file":
            if "docs" in target_file or "plan" in target_file.lower():
                return (True, "Escritura de plan/documentación autorizada para Planner.")
            return (False, "F-Planner tiene prohibido escribir código fuente de producción.")

        if role_key == "memory" and tool_name == "write_to_file":
            if "memory" in target_file:
                return (True, "Escritura autorizada exclusivamente en directorio memory/.")
            return (False, "F-Memory sólo puede escribir en el directorio de memoria persistente.")

        if tool_name not in spec["allowed_tools"]:
            return (False, f"Herramienta '{tool_name}' no autorizada para el rol '{role_key}'. Permisos delimitados.")

        return (True, f"Herramienta '{tool_name}' autorizada para '{role_key}'.")
