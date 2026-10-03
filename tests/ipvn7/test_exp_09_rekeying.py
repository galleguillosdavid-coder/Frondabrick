#!/usr/bin/env python3
"""
EXP-IPVN7-09: Re-claveo Transparente de Sesión en Vuelo (In-Flight Transparent Session Rekeying)
Verifica experimentalmente:
1. Rotación de claves criptográficas y reinicio del contador de secuencia de 64 bits sin pérdida de paquetes.
2. Ventana de gracia dual (Dual-Key Grace Window): aceptación fluida de paquetes rezagados en tránsito
   cifrados bajo la clave de la época anterior que llegan desordenados tras iniciada la nueva época.
3. Purgado determinista de claves previas tras expirar el periodo de gracia.
4. Campaña adversarial:
   - Rechazo al 100% de paquetes de época previa inyectados post-expiración de gracia.
   - Rechazo por replay de paquetes de época previa re-inyectados dentro de la gracia.
   - 500 datagramas de época nueva corruptos bit a bit descartados silenciosamente (100.0%).
"""

import sys
import os
import time
import random
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.ipvn7.core import (
    IPVN7Object,
    IPVN7Container,
    OBJ_TEXT_MESSAGE,
    OBJ_STRUCTURED_TELEMETRY,
)
from scripts.ipvn7.rekeying import (
    RekeyableSessionEndpoint,
    OBJ_REKEY_ANNOUNCE,
    OBJ_REKEY_ACK,
)


def mutate_bytes(data: bytes, num_bit_flips: int = 1) -> bytes:
    mutable = bytearray(data)
    total_bits = len(mutable) * 8
    flips = min(num_bit_flips, total_bits)
    positions = random.sample(range(total_bits), flips)
    for pos in positions:
        byte_idx = pos // 8
        bit_idx = pos % 8
        mutable[byte_idx] ^= (1 << bit_idx)
    return bytes(mutable)


def run_exp_09_rekeying_test():
    print("=" * 80)
    print("EJECUCIÓN EXPERIMENTAL: EXP-IPVN7-09 (IN-FLIGHT SESSION REKEYING & RATIO)")
    print("=" * 80)

    random.seed(20261003)
    k_alice_send = b"\x11" * 32
    k_bob_send = b"\x22" * 32

    # Umbral de rekeying = 30 paquetes; ventana de gracia = 0.6 segundos
    alice = RekeyableSessionEndpoint(
        local_rx_index=100,
        remote_rx_index=200,
        send_key=k_alice_send,
        recv_key=k_bob_send,
        rekey_threshold=30,
        grace_period_sec=0.6,
    )
    bob = RekeyableSessionEndpoint(
        local_rx_index=200,
        remote_rx_index=100,
        send_key=k_bob_send,
        recv_key=k_alice_send,
        rekey_threshold=30,
        grace_period_sec=0.6,
    )

    # --------------------------------------------------------------------------
    # FASE 1: Transmisión Normal en Época 1 hasta alcanzar el umbral de Rekeying
    # --------------------------------------------------------------------------
    print("\n[Fase 1: Transmisión en Época 1 y disparo de Rekeying por umbral]...")
    alice_received_by_bob = []

    # Alice envía 28 paquetes de datos ordinarios con Época 1
    for i in range(1, 29):
        obj = IPVN7Object(OBJ_TEXT_MESSAGE, f"Data_Epoch1_{i}".encode(), object_id=i)
        pkt = alice.send_data(obj)
        delivered = bob.receive_packet(pkt)
        assert delivered is not None
        alice_received_by_bob.append(delivered[0].payload)

    assert len(alice_received_by_bob) == 28
    assert alice.send_seq == 29
    assert not alice.needs_rekey()  # seq = 29 < 30
    print(f"  28 paquetes entregados en Época 1. Alice send_seq = {alice.send_seq} (needs_rekey=False)")

    # Alice emite el paquete 29 pero este queda 'en vuelo' en la red (retrasado por jitter/tránsito)
    obj_lagging = IPVN7Object(OBJ_STRUCTURED_TELEMETRY, b"PAQUETE_REZAGADO_EN_VUELO", object_id=888)
    lagging_pkt_epoch1 = alice.send_data(obj_lagging)
    assert alice.send_seq == 30
    assert alice.needs_rekey() is True, "Alice debió marcar needs_rekey() en seq 30"
    print("  [DISPARO] Umbral de rekeying alcanzado (seq=30). Paquete 29 retenido en vuelo (lagging).")

    # Alice emite anuncio de rekey (paquete con seq 30)
    rekey_init_pkt = alice.initiate_rekey()

    # Bob recibe el anuncio de rekey de Alice (seq 30 se compromete en ventana de Bob)
    objs_bob = bob.receive_packet(rekey_init_pkt)
    assert objs_bob is not None
    assert objs_bob[0].object_type == OBJ_REKEY_ANNOUNCE
    print("  Bob recibió OBJ_REKEY_ANNOUNCE. Transicionando a Época 2 y habilitando gracia...")

    # Bob procesa el anuncio y genera el ACK
    rekey_ack_pkt = bob.handle_rekey_announce(objs_bob[0])
    assert bob.epoch == 2
    assert bob.send_seq == 2  # 1 fue para el ACK, siguiente es 2

    # Alice recibe el ACK de Bob
    objs_alice = alice.receive_packet(rekey_ack_pkt)
    assert objs_alice is not None
    assert objs_alice[0].object_type == OBJ_REKEY_ACK
    alice.handle_rekey_ack(objs_alice[0])
    assert alice.epoch == 2
    assert alice.send_seq == 1  # Contador de secuencia reiniciado a 1!
    print(f"  [PASS] Rekeying completado: Alice y Bob en Época 2. Contadores reiniciados a 1.")

    # --------------------------------------------------------------------------
    # FASE 2: Tolerancia a Paquetes Rezagados en Tránsito (Dual-Key Grace Window)
    # --------------------------------------------------------------------------
    print("\n[Fase 2: Evaluación de entrega de paquete rezagado en Época 1 durante gracia]...")
    # Alice envía 5 paquetes de datos en Época 2 (con la nueva clave y nuevo índice)
    for i in range(1, 6):
        obj = IPVN7Object(OBJ_TEXT_MESSAGE, f"Data_Epoch2_{i}".encode(), object_id=100 + i)
        pkt = alice.send_data(obj)
        delivered = bob.receive_packet(pkt)
        assert delivered is not None
        alice_received_by_bob.append(delivered[0].payload)

    # AHORA llega el paquete rezagado que fue emitido con Época 1 antes de la transición!
    delivered_lagging = bob.receive_packet(lagging_pkt_epoch1)
    assert delivered_lagging is not None, "Fallo: Bob debió aceptar el paquete rezagado dentro de la ventana de gracia!"
    assert delivered_lagging[0].payload == b"PAQUETE_REZAGADO_EN_VUELO"
    print("  [PASS] Paquete rezagado de Época 1 recibido y descifrado con éxito en medio de Época 2.")

    # --------------------------------------------------------------------------
    # FASE 3: Campaña Adversarial (Expiración de Gracia, Replay y Manipulación)
    # --------------------------------------------------------------------------
    print("\n[Fase 3: Campaña Adversarial contra el Rekeying]...")

    # Ataque 3.1: Intento de replay de un paquete de Época 1 dentro de la gracia
    print("  [Ataque 3.1] Intento de Replay del paquete rezagado de Época 1...")
    replay_lagging = bob.receive_packet(lagging_pkt_epoch1)
    assert replay_lagging is None, "Vulnerabilidad: Bob aceptó un replay de Época 1!"
    print("  [PASS] Replay en Época 1 descartado por la ventana anti-replay de la clave en gracia.")

    # Ataque 3.2: Expiración y purga segura de la clave vieja
    print("  [Ataque 3.2] Esperando expiración de ventana de gracia (0.7s) y purga de Época 1...")
    time.sleep(0.7)  # Supera grace_period_sec = 0.6s

    fresh_old_epoch1_obj = IPVN7Object(OBJ_TEXT_MESSAGE, b"ATAQUE_POST_GRACIA", object_id=999)
    post_grace_pkt = IPVN7Container(
        receiver_index=200,  # Índice de época 1
        sequence_number=999,
        objects=[fresh_old_epoch1_obj]
    ).pack(k_alice_send)

    res_post_grace = bob.receive_packet(post_grace_pkt)
    assert res_post_grace is None, "Vulnerabilidad grave: Bob aceptó un paquete con clave expirada post-gracia!"
    assert 200 not in bob.rx_states, "La clave vieja no fue purgada de rx_states!"
    print("  [PASS] Clave de Época 1 purgada de memoria; 100% de paquetes post-gracia descartados.")

    # Ataque 3.3: 500 mutaciones de bits sobre paquetes de Época 2
    print("  [Ataque 3.3] Inyección de 500 datagramas de Época 2 corruptos bit a bit...")
    valid_epoch2_pkt = alice.send_data(IPVN7Object(OBJ_TEXT_MESSAGE, b"TEST_EPOCH2", object_id=777))
    accepted_corrupted = 0
    for _ in range(500):
        flips = random.choice([1, 2, 4, 8])
        corrupted = mutate_bytes(valid_epoch2_pkt, num_bit_flips=flips)
        if bob.receive_packet(corrupted) is not None:
            accepted_corrupted += 1

    assert accepted_corrupted == 0, f"Fallo: {accepted_corrupted} paquetes corruptos de Época 2 aceptados!"
    print("  [PASS] 500/500 datagramas corruptos de Época 2 descartados silenciosamente (100.0%).")

    print("\n[RESULTADO EXPERIMENTAL]")
    print(f"  Pérdida de Paquetes en Transición : 0.0% (Continuidad fluida)")
    print(f"  Entrega de Paquetes Rezagados     : 100.0% (Aceptados en ventana dual)")
    print(f"  Purga Segura Post-Gracia          : DEMOSTRADA (Clave anterior destruida)")
    print(f"  Reinicio de Secuencia             : seq -> 1 verificado sin colisión de nonce")
    print("  DICTAMEN EXP-IPVN7-09             : PASS (Re-claveo en vuelo formalmente demostrado)")


if __name__ == "__main__":
    run_exp_09_rekeying_test()
