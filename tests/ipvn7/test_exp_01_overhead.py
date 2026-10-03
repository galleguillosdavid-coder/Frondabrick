#!/usr/bin/env python3
"""
EXP-IPVN7-01: Evaluación Cuantitativa de Sobrecarga de Encabezados (Framing Tax Benchmark)
Ejecuta la medición física y matemática de la eficiencia en el cable para payloads de:
16, 32, 64, 128, 512, 1024 bytes.
Compara IPVN7 frente a:
- Datagrama UDP plano
- WireGuard VPN (con encapsulamiento de socket interno L3)
- HTTP/2 sobre TLS 1.3 sobre TCP (régimen estacionario con HPACK)
"""

import sys
import os
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.ipvn7.core import (
    IPVN7Object,
    IPVN7Container,
    OBJ_STRUCTURED_TELEMETRY,
    CONTAINER_HEADER_SIZE,
    AEAD_TAG_SIZE,
    OBJECT_HEADER_SIZE,
)

# Clave simétrica de 32 bytes para la prueba
TEST_KEY = b"\x01" * 32

PAYLOAD_SIZES = [16, 32, 64, 128, 512, 1024]

def run_exp_01_framing_benchmark():
    print("=" * 75)
    print("EJECUCIÓN EXPERIMENTAL: EXP-IPVN7-01 (FRAMING TAX BENCHMARK)")
    print("=" * 75)

    results = []

    for payload_size in PAYLOAD_SIZES:
        payload_data = b"X" * payload_size
        obj = IPVN7Object(object_type=OBJ_STRUCTURED_TELEMETRY, payload=payload_data, object_id=101)
        container = IPVN7Container(receiver_index=42, sequence_number=1, objects=[obj])

        # 1. Empaquetar datagrama real IPVN7
        wire_ipvn7_payload = container.pack(TEST_KEY)
        ipvn7_udp_wire = 20 + 8 + len(wire_ipvn7_payload)  # 20B IPv4 + 8B UDP + Container (Header + Encrypted(Obj) + Tag)

        # 2. Baseline UDP plano
        udp_wire = 20 + 8 + payload_size

        # 3. Baseline WireGuard transportando un datagrama UDP de aplicación
        # WireGuard transporta paquetes IP: IPv4 (20B) + UDP (8B) + WG Data Header (16B) + IP_inner (20B) + UDP_inner (8B) + Payload + Tag (16B)
        wireguard_app_wire = 20 + 8 + 16 + 20 + 8 + payload_size + 16

        # 4. Baseline HTTP/2 sobre TLS 1.3 sobre TCP (régimen estacionario con headers HPACK mínimos comprimidos)
        # IPv4 (20B) + TCP (20B) + TLS Record Header (5B) + TLS Tag (16B) + H2 Frame Header (9B) + HPACK Headers (~20B) + Payload
        http2_tls_wire = 20 + 20 + 5 + 16 + 9 + 20 + payload_size

        # Calcular ratios de eficiencia: Payload / Wire * 100%
        eff_ipvn7 = (payload_size / ipvn7_udp_wire) * 100.0
        eff_http2 = (payload_size / http2_tls_wire) * 100.0
        eff_wg = (payload_size / wireguard_app_wire) * 100.0

        improvement_vs_http2 = ((eff_ipvn7 - eff_http2) / eff_http2) * 100.0

        results.append({
            "payload_size": payload_size,
            "ipvn7_bytes": ipvn7_udp_wire,
            "http2_bytes": http2_tls_wire,
            "wg_bytes": wireguard_app_wire,
            "eff_ipvn7": eff_ipvn7,
            "eff_http2": eff_http2,
            "improvement": improvement_vs_http2,
        })

    # Imprimir tabla comparativa
    print(f"{'Payload':<10} | {'IPVN7 (Wire)':<12} | {'HTTP/2+TLS':<12} | {'WireGuard':<12} | {'Eficiencia IPVN7':<16} | {'Eficiencia H2':<14} | {'Mejora vs H2'}")
    print("-" * 100)
    for r in results:
        print(f"{r['payload_size']:<8} B | {r['ipvn7_bytes']:<10} B | {r['http2_bytes']:<10} B | {r['wg_bytes']:<10} B | {r['eff_ipvn7']:>14.2f} % | {r['eff_http2']:>12.2f} % | +{r['improvement']:.1f}%")

    # Aserciones científicas del Plan Experimental
    # 1. El encabezado base total no debe superar 32 bytes (16B header + 16B tag)
    assert CONTAINER_HEADER_SIZE + AEAD_TAG_SIZE == 32, f"Encabezado de contenedor excede 32B: {CONTAINER_HEADER_SIZE + AEAD_TAG_SIZE}"
    assert OBJECT_HEADER_SIZE == 8, f"Encabezado de objeto excede 8B: {OBJECT_HEADER_SIZE}"

    # 2. Comprobar mejoras relativas frente a HTTP/2+TLS:
    res_16 = next(r for r in results if r["payload_size"] == 16)
    res_64 = next(r for r in results if r["payload_size"] == 64)

    # Para 16 bytes (telemetría ultra-corta): debe superar el 25% de mejora relativa
    assert res_16["improvement"] >= 25.0, f"Mejora a 16B ({res_16['improvement']:.1f}%) inferior a 25%"

    # Para 64 bytes: debe superar el umbral crítico del 15% establecido en el plan experimental
    assert res_64["improvement"] >= 15.0, f"Mejora frente a HTTP/2 a 64B ({res_64['improvement']:.1f}%) inferior al 15% de umbral mínimo!"

    # 3. La eficiencia absoluta de IPVN7 para 64 bytes debe superar el 45%
    assert res_64["eff_ipvn7"] >= 45.0, f"Eficiencia de IPVN7 ({res_64['eff_ipvn7']:.1f}%) demasiado baja"

    print("\n[RESULTADO EXPERIMENTAL]")
    print(f"  Container Overhead Fijo : {CONTAINER_HEADER_SIZE + AEAD_TAG_SIZE} bytes (16B Header + 16B Tag Poly1305)")
    print(f"  Object Overhead Fijo    : {OBJECT_HEADER_SIZE} bytes")
    print(f"  Total Overhead IPVN7    : 40 bytes por mensaje")
    print(f"  Ventaja relativa a 16B  : +{res_16['improvement']:.1f}% frente a HTTP/2+TLS")
    print(f"  Ventaja relativa a 64B  : +{res_64['improvement']:.1f}% frente a HTTP/2+TLS")
    print("  DICTAMEN EXP-IPVN7-01   : PASS (Demostrado dentro del rango esperado)")

if __name__ == "__main__":
    run_exp_01_framing_benchmark()
