"""Master runner for IPVN7 experimental suite (EXP-01 to EXP-05)."""

import sys
import subprocess
import time

EXPERIMENTS = [
    ("EXP-IPVN7-01", "Overhead & Wire Tax Analysis", "tests/ipvn7/test_exp_01_overhead.py"),
    ("EXP-IPVN7-02", "Tampering & Replay Resistance", "tests/ipvn7/test_exp_02_tampering.py"),
    ("EXP-IPVN7-03", "Connection Migration / Roaming", "tests/ipvn7/test_exp_03_migration.py"),
    ("EXP-IPVN7-04", "Silent Discovery Quiescence", "tests/ipvn7/test_exp_04_discovery.py"),
    ("EXP-IPVN7-05", "Object Fragmentation & Interleaving", "tests/ipvn7/test_exp_05_fragmentation.py"),
    ("EXP-IPVN7-06", "Noise_IK Handshake & PFS", "tests/ipvn7/test_exp_06_handshake.py"),
    ("EXP-IPVN7-07", "Path Validation & Anti-Reflection", "tests/ipvn7/test_exp_07_path_validation.py"),
    ("EXP-IPVN7-08", "Egress Priority & Anti-HoL", "tests/ipvn7/test_exp_08_egress_scheduling.py"),
    ("EXP-IPVN7-09", "In-Flight Rekeying & Grace Window", "tests/ipvn7/test_exp_09_rekeying.py"),
    ("EXP-IPVN7-10", "NAT Hole-Punching & Quiescence", "tests/ipvn7/test_exp_10_nat.py"),
]

def main():
    print("=" * 80)
    print("EJECUTOR MAESTRO DE EXPERIMENTOS IPVN7 (LABORATORIO EMPÍRICO)")
    print("=" * 80)
    t0 = time.time()
    results = []

    for exp_id, title, script_path in EXPERIMENTS:
        print(f"\n>>> Ejecutando {exp_id}: {title}...")
        sub_t0 = time.time()
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        elapsed = time.time() - sub_t0
        status = "PASS" if res.returncode == 0 else "FAIL"
        results.append((exp_id, title, status, elapsed, res.stdout, res.stderr))
        print(f"    Resultado: {status} ({elapsed:.2f}s)")
        if res.returncode != 0:
            print(f"    ERROR STDERR:\n{res.stderr}")
            print(f"    STDOUT:\n{res.stdout}")

    total_time = time.time() - t0
    print("\n" + "=" * 80)
    print("TABLA RESUMEN DE LA BATERÍA EXPERIMENTAL IPVN7-0")
    print("=" * 80)
    print(f"{'ID':<14} | {'Descripción':<38} | {'Estado':<8} | {'Tiempo':<8}")
    print("-" * 80)
    all_pass = True
    for exp_id, title, status, elapsed, _, _ in results:
        print(f"{exp_id:<14} | {title:<38} | {status:<8} | {elapsed:.2f}s")
        if status != "PASS":
            all_pass = False
    print("-" * 80)
    print(f"Total Suites : {len(results)} | Superadas: {sum(1 for r in results if r[2] == 'PASS')} | Tiempo Total: {total_time:.2f}s")
    print("=" * 80)

    passed_count = sum(1 for r in results if r[2] == 'PASS')
    if all_pass:
        print(f"\nDICTAMEN FINAL: {passed_count}/{len(results)} SUITES EXPERIMENTALES SUPERADAS (PASS)\n")
        return 0
    else:
        print(f"\nDICTAMEN FINAL: {len(results) - passed_count}/{len(results)} SUITES FALLARON\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
