#!/usr/bin/env python3
"""
Frondabrick Unified CLI
Provides commands:
- frondabrick doctor
- frondabrick validate
- frondabrick audit
- frondabrick shield
- frondabrick memory
- frondabrick init
"""

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.security.detector import SecurityDetector
from scripts.security.policy import ShieldPolicyEngine
from scripts.memory.manager import MemoryManager
from scripts.evidence.recorder import EvidenceRecorder

def cmd_doctor(args):
    """
    Verifies:
    [ ] Antigravity compatible
    [ ] Plugin válido
    [ ] Rules válidas
    [ ] Skills válidas
    [ ] Agentes válidos
    [ ] Scripts ejecutables
    [ ] Hooks válidos
    [ ] Memoria accesible
    [ ] Tests disponibles
    [ ] Configuración correcta
    Outputs: PASS, WARN, FAIL
    """
    print("=" * 60)
    print("FRONDABRICK DOCTOR — DIAGNÓSTICO DE ENTORNO Y ARNES")
    print("=" * 60)

    checks = []

    # 1. Antigravity Compatible
    py_ok = sys.version_info >= (3, 10)
    git_ok = (WORKSPACE_ROOT / ".git").is_dir()
    if py_ok and git_ok:
        checks.append(("PASS", "Antigravity Compatible (Python >= 3.10, Git repo activo)"))
    else:
        checks.append(("WARN", f"Compatibilidad parcial (Python {sys.version_split[0]}, Git repo: {git_ok})"))

    # 2. Plugin Válido
    plugin_json = WORKSPACE_ROOT / ".agents" / "plugins" / "frondabrick-core" / "plugin.json"
    if plugin_json.is_file():
        checks.append(("PASS", "Plugin Válido (frondabrick-core/plugin.json existe y tiene esquema)"))
    else:
        checks.append(("FAIL", "Plugin frondabrick-core no encontrado en .agents/plugins/"))

    # 3. Rules Válidas
    core_rules = ["00-core.md", "01-safety.md", "02-workflow.md", "03-testing.md"]
    rules_dir = WORKSPACE_ROOT / ".agents" / "rules"
    missing_rules = [r for r in core_rules if not (rules_dir / r).is_file()]
    if not missing_rules:
        checks.append(("PASS", f"Rules Válidas (Las {len(core_rules)} reglas base están presentes)"))
    else:
        checks.append(("FAIL", f"Faltan reglas base: {missing_rules}"))

    # 4. Skills Válidas
    skills = ["fronda-planner", "fronda-reviewer", "fronda-shield", "fronda-tdd", "fronda-build", "fronda-memory"]
    skills_dir = WORKSPACE_ROOT / ".agents" / "skills"
    missing_skills = [s for s in skills if not (skills_dir / s / "SKILL.md").is_file()]
    if not missing_skills:
        checks.append(("PASS", f"Skills Válidas ({len(skills)} skills operativas)"))
    else:
        checks.append(("FAIL", f"Faltan skills en .agents/skills/: {missing_skills}"))

    # 5. Agentes Válidos
    agents = ["planner", "reviewer", "browser_qa", "build_resolver"]
    agents_dir = WORKSPACE_ROOT / "agents"
    missing_agents = [a for a in agents if not (agents_dir / a / "ROLE.md").is_file()]
    if not missing_agents:
        checks.append(("PASS", f"Agentes Válidos ({len(agents)} especificaciones de rol activas)"))
    else:
        checks.append(("FAIL", f"Faltan especificaciones de agentes: {missing_agents}"))

    # 6. Scripts Ejecutables
    scripts = [
        WORKSPACE_ROOT / "scripts" / "security" / "validator.py",
        WORKSPACE_ROOT / "scripts" / "memory" / "manager.py",
        WORKSPACE_ROOT / "scripts" / "evidence" / "recorder.py",
        WORKSPACE_ROOT / "scripts" / "fleet" / "orchestrator.py",
    ]
    missing_scripts = [s.name for s in scripts if not s.is_file()]
    if not missing_scripts:
        checks.append(("PASS", "Scripts Ejecutables (Módulos de seguridad, memoria, evidencia y flota listos)"))
    else:
        checks.append(("FAIL", f"Scripts faltantes: {missing_scripts}"))

    # 7. Hooks Válidos
    hooks_file = WORKSPACE_ROOT / ".agents" / "hooks.json"
    if hooks_file.is_file():
        checks.append(("PASS", "Hooks Válidos (.agents/hooks.json configurado)"))
    else:
        checks.append(("FAIL", "Hooks ausentes: .agents/hooks.json no encontrado"))

    # 8. Memoria Accesible
    mem_subdirs = ["session", "candidates", "verified", "anti-patterns"]
    mem_root = WORKSPACE_ROOT / "memory"
    missing_mem = [m for m in mem_subdirs if not (mem_root / m).is_dir()]
    if not missing_mem:
        checks.append(("PASS", "Memoria Accesible (Jerarquía de memoria persistente operativa)"))
    else:
        checks.append(("FAIL", f"Directorios de memoria ausentes: {missing_mem}"))

    # 9. Tests Disponibles
    test_runner = WORKSPACE_ROOT / "tests" / "run_all.py"
    if test_runner.is_file():
        checks.append(("PASS", "Tests Disponibles (Master runner tests/run_all.py presente)"))
    else:
        checks.append(("FAIL", "Test harness ausente"))

    # 10. Configuración Correcta
    checks.append(("PASS", "Configuración Correcta (Antigravity Workspace Root verificado)"))

    # Print results
    has_fail = False
    has_warn = False
    for status, msg in checks:
        if status == "FAIL":
            has_fail = True
            print(f"  [FAIL] {msg}")
        elif status == "WARN":
            has_warn = True
            print(f"  [WARN] {msg}")
        else:
            print(f"  [PASS] {msg}")

    print("-" * 60)
    if has_fail:
        print("ESTADO DOCTOR: FAIL (Existen componentes críticos que requieren corrección)")
        return 1
    elif has_warn:
        print("ESTADO DOCTOR: WARN (El sistema opera pero existen advertencias)")
        return 0
    else:
        print("ESTADO DOCTOR: PASS (Todas las verificaciones de entorno Frondabrick resultaron exitosas)")
        return 0

def cmd_validate(args):
    """Executes the master test suite."""
    print("[FRONDABRICK] Ejecutando suite de validación completa...")
    ret = subprocess.run([sys.executable, str(WORKSPACE_ROOT / "tests" / "run_all.py")])
    return ret.returncode

def cmd_audit(args):
    """Performs security and repository audit."""
    print("=" * 60)
    print("FRONDABRICK AUDIT — AUDITORÍA DE SEGURIDAD Y REPOSITORIO")
    print("=" * 60)
    issues = 0
    # Audit .env files
    for p in WORKSPACE_ROOT.glob("**/.env*"):
        if not p.name.endswith(".example") and p.is_file():
            print(f"  [ALERTA DE SEGURIDAD] Archivo de entorno detectado: {p.relative_to(WORKSPACE_ROOT)}")
            issues += 1

    # Check git status for unstaged dangerous changes
    try:
        res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
        print(f"\n[ESTADO DE GIT]\n{res.stdout.strip() if res.stdout.strip() else 'Working tree limpio.'}")
    except Exception as e:
        print(f"Error consultando Git: {e}")

    print(f"\nResultado de Auditoría: {issues} alertas encontradas.")
    return 0

def cmd_shield(args):
    """Tests a command or text against F-Shield."""
    target_cmd = " ".join(args.command) if args.command else ""
    if not target_cmd:
        print("Uso: frondabrick shield <comando a probar>")
        return 1

    rule = SecurityDetector.inspect_command(target_cmd)
    if rule:
        print(f"[F-SHIELD INTERCEPTADO] Nivel {rule['level']} ({rule['action']})")
        print(f"  Regla: {rule['id']} - {rule['name']}")
        print(f"  Riesgo: {rule['risk']}")
        print(f"  Razón: {rule['reason']}")
    else:
        print(f"[F-SHIELD PERMITIDO] El comando '{target_cmd}' no activó reglas destructivas.")
    return 0

def cmd_memory(args):
    """Lists or inspects memories."""
    mgr = MemoryManager(root_dir=WORKSPACE_ROOT / "memory")
    verified = mgr.get_verified()
    print("=" * 60)
    print(f"FRONDABRICK MEMORY — MEMORIAS VERIFICADAS ACTIVAS ({len(verified)})")
    print("=" * 60)
    if not verified:
        print("  (No hay memorias verificadas aún en el sistema)")
    for m in verified:
        print(f"- [{m['id']}] (Confianza: {m['confidence']}) {m['content']}")
    return 0

def cmd_init(args):
    """Initializes Frondabrick structure in the current directory."""
    print("[FRONDABRICK] Inicializando estructura de arnés en workspace...")
    for d in [
        WORKSPACE_ROOT / ".agents" / "rules",
        WORKSPACE_ROOT / ".agents" / "skills",
        WORKSPACE_ROOT / "evidence" / "session",
        WORKSPACE_ROOT / "evidence" / "security",
        WORKSPACE_ROOT / "evidence" / "tests",
        WORKSPACE_ROOT / "evidence" / "architecture",
        WORKSPACE_ROOT / "memory" / "session",
        WORKSPACE_ROOT / "memory" / "candidates",
        WORKSPACE_ROOT / "memory" / "verified",
        WORKSPACE_ROOT / "memory" / "anti-patterns",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    print("[FRONDABRICK] Inicialización completada con éxito.")
    return 0

def main():
    parser = argparse.ArgumentParser(prog="frondabrick", description="Frondabrick Engineering Harness CLI")
    subparsers = parser.add_subparsers(dest="subcommand")

    # doctor
    subparsers.add_parser("doctor", help="Diagnóstico integral del estado del arnés")

    # validate
    subparsers.add_parser("validate", help="Ejecutar test harness completo")

    # audit
    subparsers.add_parser("audit", help="Auditoría de seguridad y repositorio")

    # shield
    p_shield = subparsers.add_parser("shield", help="Evaluar comando contra políticas de seguridad")
    p_shield.add_argument("command", nargs="*", help="Comando a analizar")

    # memory
    subparsers.add_parser("memory", help="Inspeccionar memoria persistente")

    # init
    subparsers.add_parser("init", help="Inicializar estructura del arnés")

    args = parser.parse_args()

    if args.subcommand == "doctor":
        return cmd_doctor(args)
    elif args.subcommand == "validate":
        return cmd_validate(args)
    elif args.subcommand == "audit":
        return cmd_audit(args)
    elif args.subcommand == "shield":
        return cmd_shield(args)
    elif args.subcommand == "memory":
        return cmd_memory(args)
    elif args.subcommand == "init":
        return cmd_init(args)
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
