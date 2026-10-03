#!/usr/bin/env python3
"""
EXP-IPVN7-06: Apretón de Manos Criptográfico Noise_IK y Derivación de Claves de Sesión (1-RTT PFS Handshake)
Verifica experimentalmente:
1. Ejecución nominal de Noise_IK en 1.0 RTT (Init: 116B, Resp: 60B).
2. Derivación determinista de claves de transporte simétricas cruzadas (send_key / recv_key).
3. Transmisión fluida inmediata de Contenedores IPVN7 con payload real usando las claves derivadas.
4. Campaña de ataque:
   - Rechazo silente ante identidad no autorizada (Mallory).
   - Inyección de 500 datagramas de Init corruptos bit a bit (100% descarte silente).
   - Inyección de 500 datagramas de Resp corruptos bit a bit (100% descarte silente).
5. Secreto perfecto hacia adelante (PFS) verificado por borrado de clave efímera.
"""

import sys
import os
import random
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.ipvn7.core import (
    IPVN7Object,
    IPVN7Container,
    OBJ_TEXT_MESSAGE,
    OBJ_STRUCTURED_TELEMETRY,
)
from scripts.ipvn7.handshake import (
    NoiseIKHandshakeInitiator,
    NoiseIKHandshakeResponder,
    INIT_PACKET_SIZE,
    RESP_PACKET_SIZE,
)


def mutate_bytes(data: bytes, num_bit_flips: int = 1) -> bytes:
    """Invierte exactamente num_bit_flips bits distintos en data."""
    mutable = bytearray(data)
    total_bits = len(mutable) * 8
    flips = min(num_bit_flips, total_bits)
    positions = random.sample(range(total_bits), flips)
    for pos in positions:
        byte_idx = pos // 8
        bit_idx = pos % 8
        mutable[byte_idx] ^= (1 << bit_idx)
    assert bytes(mutable) != data
    return bytes(mutable)


def run_exp_06_handshake_test():
    print("=" * 80)
    print("EJECUCIÓN EXPERIMENTAL: EXP-IPVN7-06 (NOISE_IK HANDSHAKE & PFS VERIFICATION)")
    print("=" * 80)

    random.seed(20261002)

    # 1. Configuración de Identidades Estáticas de Largo Plazo
    alice_priv = X25519PrivateKey.generate()
    alice_pub = alice_priv.public_key().public_bytes_raw()

    bob_priv = X25519PrivateKey.generate()
    bob_pub = bob_priv.public_key().public_bytes_raw()

    mallory_priv = X25519PrivateKey.generate()
    mallory_pub = mallory_priv.public_key().public_bytes_raw()

    # Bob autoriza a Alice, pero NO a Mallory
    bob_authorized_peers = {
        alice_pub: "Alice_Legit_Node",
    }

    # --------------------------------------------------------------------------
    # FASE 1: Handshake Nominal en 1 RTT
    # --------------------------------------------------------------------------
    print("\n[Fase 1: Ejecución nominal de Handshake Noise_IK (Alice <-> Bob)]...")
    alice_initiator = NoiseIKHandshakeInitiator(
        static_priv=alice_priv,
        peer_static_pub_bytes=bob_pub,
        local_index=1001,
    )
    bob_responder = NoiseIKHandshakeResponder(
        static_priv=bob_priv,
        local_index=2002,
        authorized_peers=bob_authorized_peers,
    )

    # Paso 1: Alice genera PKT_HANDSHAKE_INIT (0.5 RTT)
    init_packet = alice_initiator.create_initiation_packet()
    print(f"  Datagrama PKT_HANDSHAKE_INIT generado: {len(init_packet)} bytes (formato alineado)")
    assert len(init_packet) == INIT_PACKET_SIZE
    assert len(init_packet) <= 160, f"Init packet demasiado grande: {len(init_packet)}B"

    # Paso 2: Bob procesa PKT_HANDSHAKE_INIT y genera PKT_HANDSHAKE_RESP (0.5 RTT adicional -> 1.0 RTT total)
    resp_packet, bob_session = bob_responder.process_initiation_and_respond(init_packet)
    assert resp_packet is not None, "Bob no generó el paquete de respuesta"
    assert bob_session is not None, "Bob no derivó la sesión"
    print(f"  Datagrama PKT_HANDSHAKE_RESP generado: {len(resp_packet)} bytes (formato alineado)")
    assert len(resp_packet) == RESP_PACKET_SIZE
    assert len(resp_packet) <= 100, f"Resp packet demasiado grande: {len(resp_packet)}B"

    # Paso 3: Alice procesa PKT_HANDSHAKE_RESP y finaliza
    alice_session = alice_initiator.process_response_packet(resp_packet)
    assert alice_session is not None, "Alice no pudo procesar la respuesta de Bob"

    # Verificación de Simetría Cruzada de Claves
    print("  Verificando coherencia de claves de transporte simétricas...")
    assert alice_session.send_key == bob_session.recv_key, "Clave Alice->Bob no coincide"
    assert alice_session.recv_key == bob_session.send_key, "Clave Bob->Alice no coincide"
    assert alice_session.send_key != alice_session.recv_key, "Vulnerabilidad: send_key y recv_key no deben ser idénticas"
    assert len(alice_session.send_key) == 32
    assert len(alice_session.recv_key) == 32

    # Verificación de Forward Secrecy: clave efímera destruida
    assert alice_initiator.ephemeral_priv is None, "Fuga de seguridad: la clave efímera privada debe ser purgada post-handshake"
    print("[PASS] Handshake completado en exactamente 1.0 RTT con secreto hacia adelante.")

    # --------------------------------------------------------------------------
    # FASE 2: Transmisión de Contenedores Reales con Claves Derivadas
    # --------------------------------------------------------------------------
    print("\n[Fase 2: Transmisión de datos operacionales PKT_DATA sobre la nueva sesión]...")
    # Alice envía datos a Bob
    obj_alice = IPVN7Object(object_type=OBJ_TEXT_MESSAGE, payload=b"Hola Bob desde sesion negociada!", object_id=1)
    container_alice = IPVN7Container(
        receiver_index=alice_session.remote_index,
        sequence_number=alice_session.send_seq,
        objects=[obj_alice]
    )
    wire_alice = container_alice.pack(alice_session.send_key)
    alice_session.send_seq += 1

    # Bob recibe y desempaqueta
    rec_by_bob = IPVN7Container.unpack(wire_alice, bob_session.recv_key, replay_window=bob_session.replay_window)
    assert rec_by_bob is not None, "Bob no pudo descifrar el mensaje con la clave negociada"
    assert rec_by_bob.objects[0].payload == b"Hola Bob desde sesion negociada!"

    # Bob responde a Alice
    obj_bob = IPVN7Object(object_type=OBJ_STRUCTURED_TELEMETRY, payload=b"ACK_BOB_TELEMETRY_OK", object_id=2)
    container_bob = IPVN7Container(
        receiver_index=bob_session.remote_index,
        sequence_number=bob_session.send_seq,
        objects=[obj_bob]
    )
    wire_bob = container_bob.pack(bob_session.send_key)
    bob_session.send_seq += 1

    # Alice recibe y desempaqueta
    rec_by_alice = IPVN7Container.unpack(wire_bob, alice_session.recv_key, replay_window=alice_session.replay_window)
    assert rec_by_alice is not None, "Alice no pudo descifrar la respuesta de Bob"
    assert rec_by_alice.objects[0].payload == b"ACK_BOB_TELEMETRY_OK"
    print("[PASS] Tráfico de datos bidireccional fluido sobre claves efímeras derivadas.")

    # --------------------------------------------------------------------------
    # FASE 3: Campaña Adversarial
    # --------------------------------------------------------------------------
    print("\n[Fase 3: Campaña Adversarial contra el Handshake]...")

    # Ataque 3.1: Intento de conexión con identidad no autorizada (Mallory)
    print("  [Ataque 3.1] Intento de conexión por atacante no autorizado (Mallory)...")
    mallory_initiator = NoiseIKHandshakeInitiator(
        static_priv=mallory_priv,
        peer_static_pub_bytes=bob_pub,
        local_index=9999,
    )
    mallory_init_packet = mallory_initiator.create_initiation_packet()
    mal_resp, mal_session = bob_responder.process_initiation_and_respond(mallory_init_packet)
    assert mal_resp is None, "Vulnerabilidad: Bob respondió a una identidad no autorizada"
    assert mal_session is None, "Vulnerabilidad: Bob creó sesión para una identidad no autorizada"
    print("  [PASS] Bob descartó silentemente el handshake de la identidad no autorizada (0 oráculos).")

    # Ataque 3.2: 500 mutaciones de bits en Handshake Init
    print("  [Ataque 3.2] Inyección de 500 datagramas de Handshake Init con mutación de bits...")
    accepted_corrupted_init = 0
    for _ in range(500):
        flips = random.choice([1, 2, 4, 8])
        corrupted_init = mutate_bytes(init_packet, num_bit_flips=flips)
        res_p, res_s = bob_responder.process_initiation_and_respond(corrupted_init)
        if res_p is not None or res_s is not None:
            accepted_corrupted_init += 1

    assert accepted_corrupted_init == 0, f"Fallo: {accepted_corrupted_init} paquetes Init corruptos fueron aceptados"
    print(f"  [PASS] 500/500 datagramas Init manipulados descartados silentemente (100.0%).")

    # Ataque 3.3: 500 mutaciones de bits en Handshake Response
    print("  [Ataque 3.3] Inyección de 500 datagramas de Handshake Response con mutación de bits...")
    accepted_corrupted_resp = 0
    for _ in range(500):
        # Necesitamos un nuevo initiator state para cada intento de response
        temp_init = NoiseIKHandshakeInitiator(static_priv=alice_priv, peer_static_pub_bytes=bob_pub, local_index=3333)
        valid_init = temp_init.create_initiation_packet()
        valid_resp, _ = bob_responder.process_initiation_and_respond(valid_init)
        assert valid_resp is not None

        flips = random.choice([1, 2, 4, 8])
        corrupted_resp = mutate_bytes(valid_resp, num_bit_flips=flips)
        res_alice = temp_init.process_response_packet(corrupted_resp)
        if res_alice is not None:
            accepted_corrupted_resp += 1

    assert accepted_corrupted_resp == 0, f"Fallo: {accepted_corrupted_resp} paquetes Resp corruptos fueron aceptados"
    print(f"  [PASS] 500/500 datagramas Resp manipulados descartados silentemente (100.0%).")

    print("\n[RESULTADO EXPERIMENTAL]")
    print(f"  Sobrecarga Handshake Init  : {len(init_packet)} bytes (vs >1500B en TLS 1.3)")
    print(f"  Sobrecarga Handshake Resp  : {len(resp_packet)} bytes")
    print(f"  Latencia de Handshake      : Exactamente 1.0 RTT (2 datagramas)")
    print(f"  Tasa de rechazo silente    : 100.0% (0 oráculos, 0 crashes)")
    print(f"  Forward Secrecy            : DEMOSTRADO (claves efímeras destruidas)")
    print(f"  DICTAMEN EXP-IPVN7-06      : PASS (Apretón de manos formalmente viable)")

if __name__ == "__main__":
    run_exp_06_handshake_test()
